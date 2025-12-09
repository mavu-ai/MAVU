import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react'
import { authService } from '../services/authService'

interface WebSocketContextType {
  ws: WebSocket | null
  isConnected: boolean
  sendMessage: (message: any) => void
  lastMessage: any | null
  reconnect: () => void
}

const WebSocketContext = createContext<WebSocketContextType | null>(null)

interface WebSocketProviderProps {
  children: React.ReactNode
  userId?: string
  sessionToken?: string
}

// Global WebSocket instance tracker to prevent duplicates across re-renders
const globalWsInstance = { current: null as WebSocket | null }

export function WebSocketProvider({ children, userId, sessionToken }: WebSocketProviderProps) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<any>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const reconnectAttempts = useRef(0)
  const isConnectingRef = useRef(false)  // Prevent duplicate connection attempts
  const connectionIdRef = useRef<string>('')  // Track connection ID for debugging
  const mountedRef = useRef(false)  // Track if component is mounted

  const connect = useCallback(() => {
    // CRITICAL FIX: Check global instance first to prevent duplicates from React.StrictMode
    if (globalWsInstance.current?.readyState === WebSocket.OPEN) {
      console.log('[WS] Global WebSocket already connected, reusing existing connection')
      wsRef.current = globalWsInstance.current
      setIsConnected(true)
      return
    }

    if (globalWsInstance.current?.readyState === WebSocket.CONNECTING) {
      console.log('[WS] Global WebSocket connecting, waiting...')
      wsRef.current = globalWsInstance.current
      return
    }

    // CRITICAL FIX: Prevent duplicate connection attempts
    if (isConnectingRef.current) {
      console.log('[WS] Connection already in progress, skipping')
      return
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[WS] Already connected, skipping')
      return
    }

    // Check if we're currently connecting
    if (wsRef.current?.readyState === WebSocket.CONNECTING) {
      console.log('[WS] Connection in progress, skipping')
      return
    }

    isConnectingRef.current = true

    // Generate unique connection ID for debugging
    const connectionId = `conn-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    connectionIdRef.current = connectionId

    // Get session token from props or authService
    const token = sessionToken || authService.getSessionToken()
    const userIdParam = userId || authService.getUserId()?.toString() || 'default_user'

    // Use VITE_WS_URL environment variable or fallback to localhost
    const wsBaseUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1'
    let wsUrl = `${wsBaseUrl}/realtime`

    // Add authentication to WebSocket URL
    if (token) {
      // Use session_token query parameter for authentication
      wsUrl += `?session_token=${encodeURIComponent(token)}`
    } else {
      // Fall back to user_id for development
      wsUrl += `?user_id=${encodeURIComponent(userIdParam)}`
    }

    console.log('[WS] CONNECTION_CREATE:', {
      connectionId,
      userId: userIdParam,
      hasToken: !!token,
      timestamp: new Date().toISOString()
    })

    const ws = new WebSocket(wsUrl)

    // Store in global instance to prevent duplicates from React.StrictMode
    globalWsInstance.current = ws
    wsRef.current = ws

    ws.onopen = () => {
      console.log('[WS] CONNECTION_OPEN:', {
        connectionId,
        timestamp: new Date().toISOString()
      })
      setIsConnected(true)
      reconnectAttempts.current = 0
      isConnectingRef.current = false
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        // Log differently based on message type
        if (data.type === 'audio.delta') {
          console.log('[WS] Received audio.delta, base64 length:', data.audio?.length || 0)
        } else if (data.type === 'audio.received') {
          // Skip logging ACK messages
        } else {
          console.log('[WS] WebSocket message:', data.type, data)
        }

        setLastMessage(data)
      } catch (error) {
        console.error('[WS] Failed to parse WebSocket message:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('[WS] WebSocket error:', error)
      isConnectingRef.current = false
    }

    ws.onclose = (event) => {
      console.log('[WS] WebSocket disconnected', event.code, event.reason)
      setIsConnected(false)
      wsRef.current = null
      globalWsInstance.current = null  // Clear global instance
      isConnectingRef.current = false

      // Handle authentication failures (code 1008 or 403-style rejections)
      if (event.code === 1008 || event.reason?.includes('Authentication')) {
        console.error('[WS] Authentication failed - session invalid. Please login again.')
        // Import authService dynamically to avoid circular dependency
        import('../services/authService').then(({ authService }) => {
          authService.logout()
          // Trigger a page reload to show promo code page
          window.location.reload()
        })
        return
      }

      // Auto-reconnect with exponential backoff (only if not a normal closure)
      if (event.code !== 1000 && reconnectAttempts.current < 5) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000)
        console.log(`[WS] Reconnecting in ${delay}ms... (attempt ${reconnectAttempts.current + 1}/5)`)
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttempts.current++
          connect()
        }, delay)
      } else if (event.code === 1000) {
        console.log('[WS] Normal closure, not reconnecting')
      } else {
        console.log('[WS] Max reconnection attempts reached')
      }
    }
  }, [userId, sessionToken])

  useEffect(() => {
    mountedRef.current = true

    // CRITICAL FIX: Only connect if we don't already have an active connection
    // This prevents the infinite reconnection loop caused by connect changing
    const token = sessionToken || authService.getSessionToken()
    const userIdParam = userId || authService.getUserId()?.toString()

    // Check if global WebSocket already exists and is connected
    if (globalWsInstance.current?.readyState === WebSocket.OPEN) {
      console.log('[WS] Reusing existing global WebSocket connection')
      wsRef.current = globalWsInstance.current
      setIsConnected(true)
    } else if ((token || userIdParam) && !wsRef.current) {
      console.log('[WS] Initializing WebSocket connection')
      connect()
    }

    return () => {
      mountedRef.current = false
      console.log('[WS] Cleaning up WebSocket provider')

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = null
      }

      // CRITICAL: Don't close the WebSocket immediately in development
      // React.StrictMode causes quick unmount-remount, so we delay closure
      setTimeout(() => {
        // Only close if component is still unmounted and no new connection was made
        if (!mountedRef.current && wsRef.current && wsRef.current === globalWsInstance.current) {
          console.log('[WS] Closing WebSocket after grace period')
          wsRef.current.close(1000, 'Component unmounting')
          wsRef.current = null
          globalWsInstance.current = null
        }
      }, 100) // 100ms grace period for React.StrictMode remount

      isConnectingRef.current = false
    }
    // CRITICAL: Remove 'connect' from dependencies to prevent infinite loop
    // Only re-run if userId or sessionToken actually change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, sessionToken])

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const msgType = message.type || 'unknown'
      const msgSize = message.audio ? message.audio.length : 0

      if (msgType === 'audio.append') {
        // Only log every 10th audio message to avoid spam
        if (Math.random() < 0.1) {
          console.log('[WS] Sending audio.append, base64 size:', msgSize)
        }
      } else {
        console.log('[WS] Sending message:', msgType, message)
      }

      wsRef.current.send(JSON.stringify(message))
    } else {
      console.error('[WS] WebSocket is not connected, cannot send:', message.type)
    }
  }, [])

  const reconnect = useCallback(() => {
    console.log('[WS] Manual reconnection requested')
    if (wsRef.current) {
      // Close with normal code to prevent auto-reconnect
      wsRef.current.close(1000, 'Manual reconnect')
      wsRef.current = null
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    isConnectingRef.current = false
    reconnectAttempts.current = 0

    // Small delay to ensure cleanup completes
    setTimeout(() => {
      connect()
    }, 100)
  }, [connect])

  const value: WebSocketContextType = {
    ws: wsRef.current,
    isConnected,
    sendMessage,
    lastMessage,
    reconnect
  }

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  )
}

export function useWebSocket() {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider')
  }
  return context
}
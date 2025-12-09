import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import {
  Box,
  IconButton,
  Typography,
  Alert,
  Fade,
  useMediaQuery,
  CircularProgress,
} from '@mui/material'
import {
  Mic,
  MicOff,
  Person,
} from '@mui/icons-material'
import { useWebSocket } from '../hooks/useWebSocket'

interface VoiceChatProps {
  uiMode?: 'light' | 'dark' | 'system'
  onProfileClick?: () => void
}

const VoiceChat: React.FC<VoiceChatProps> = ({ uiMode = 'system', onProfileClick }) => {
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)')

  // Determine effective theme based on ui_mode
  const effectiveTheme = useMemo(() => {
    if (uiMode === 'system') {
      return prefersDarkMode ? 'dark' : 'light'
    }
    return uiMode
  }, [uiMode, prefersDarkMode])

  const { isConnected, sendMessage, lastMessage } = useWebSocket()
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [userText, setUserText] = useState('')
  const [assistantText, setAssistantText] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [audioLevel, setAudioLevel] = useState(0)

  // Refs for audio handling
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const captureContextRef = useRef<AudioContext | null>(null)
  const analyzerNodeRef = useRef<AnalyserNode | null>(null)
  const sourceNodeRef = useRef<MediaStreamAudioSourceNode | null>(null)
  const recordingRef = useRef(false)
  const processingChunksRef = useRef(false)
  const playbackContextRef = useRef<AudioContext | null>(null)
  const nextStartTimeRef = useRef<number>(0)
  const animationFrameRef = useRef<number | null>(null)

  // Audio playback queue for smooth streaming with adaptive buffering
  const audioQueueRef = useRef<AudioBuffer[]>([])
  const isPlayingRef = useRef(false)
  const lastScheduledTimeRef = useRef<number>(0)
  const schedulerIntervalRef = useRef<number | null>(null)

  // Track if we're already processing welcome message to prevent duplicates
  const processingWelcomeRef = useRef(false)

  // Track recently processed audio chunks to prevent duplicates
  const recentAudioHashesRef = useRef<Set<string>>(new Set())
  const AUDIO_HASH_CLEANUP_SIZE = 100  // Clear old hashes after this many chunks

  // Track audio chunk IDs to detect and prevent duplicates
  const processedChunkIdsRef = useRef<Set<string>>(new Set())
  const audioChunkLogRef = useRef<Array<{ chunkId: string, timestamp: number }>>([])

  // Adaptive buffering parameters - OPTIMIZED for smooth playback
  const TARGET_BUFFER_MS = 500  // Target 500ms of buffered audio for extra smoothness (was 300ms)
  const MIN_BUFFER_MS = 250     // Minimum 250ms before starting playback to reduce stuttering (was 150ms)
  const LOOKAHEAD_MS = 150      // Schedule 150ms ahead of current playback for better buffering (was 100ms)

  // CRITICAL FIX: Track audio chunks sent to prevent empty commit
  const audioChunksSentRef = useRef<number>(0)
  const audioChunksAckedRef = useRef<number>(0)
  const pendingAudioChunksRef = useRef<Set<string>>(new Set())

  // CRITICAL FIX: Safety timeout to clear processing state if backend doesn't respond
  const processingTimeoutRef = useRef<number | null>(null)
  const PROCESSING_TIMEOUT_MS = 30000  // 30 seconds max processing time

  // Initialize playback audio context
  useEffect(() => {
    const initPlaybackContext = async () => {
      try {
        playbackContextRef.current = new AudioContext({ sampleRate: 24000 })
        nextStartTimeRef.current = 0
        lastScheduledTimeRef.current = 0

        // Resume the context immediately to avoid suspended state
        if (playbackContextRef.current.state === 'suspended') {
          await playbackContextRef.current.resume()
          console.log('[AUDIO] AudioContext resumed on initialization')
        }

        console.log('[AUDIO] Playback context initialized:', {
          state: playbackContextRef.current.state,
          sampleRate: playbackContextRef.current.sampleRate
        })
      } catch (error) {
        console.error('[AUDIO] Failed to initialize playback context:', error)
      }
    }

    initPlaybackContext()

    return () => {
      if (playbackContextRef.current?.state !== 'closed') {
        playbackContextRef.current?.close()
      }
    }
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanupAudioResources()
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      // Stop audio scheduler
      if (schedulerIntervalRef.current) {
        clearInterval(schedulerIntervalRef.current)
        schedulerIntervalRef.current = null
      }
      // Clear audio queue
      audioQueueRef.current = []
      isPlayingRef.current = false
      // CRITICAL FIX: Clear processing timeout
      if (processingTimeoutRef.current) {
        clearTimeout(processingTimeoutRef.current)
        processingTimeoutRef.current = null
      }
    }
  }, [])

  // Handle WebSocket messages
  useEffect(() => {
    if (!lastMessage) return

    switch (lastMessage.type) {
      case 'session.ready':
        console.log('✓ Session ready with voice:', {
          session_id: lastMessage.session_id,
          voice: lastMessage.voice,
          model: lastMessage.model
        })
        console.warn(`🎤 ACTIVE VOICE: ${lastMessage.voice || 'unknown'}`)
        setError(null)
        break

      case 'audio.preparing':
        // Prepare audio context early to prevent glitches
        console.log('[AUDIO] Preparing for welcome message...')

        // CRITICAL: Prevent duplicate welcome message processing
        if (processingWelcomeRef.current) {
          console.warn('[AUDIO] Already processing welcome message - ignoring duplicate')
          break
        }
        processingWelcomeRef.current = true

        if (!playbackContextRef.current) {
          playbackContextRef.current = new AudioContext({ sampleRate: 24000 })
        }
        // Resume audio context if suspended
        if (playbackContextRef.current.state === 'suspended') {
          playbackContextRef.current.resume()
        }
        // Clear any existing audio queue and stop playback
        audioQueueRef.current = []
        isPlayingRef.current = false
        // Reset next start time for clean playback
        nextStartTimeRef.current = 0
        break

      case 'transcription':
        if (lastMessage.role === 'user') {
          setUserText(lastMessage.text)
        } else {
          setAssistantText((prev) => prev + lastMessage.text)
        }
        break

      case 'text.delta':
        setAssistantText((prev) => prev + lastMessage.delta)
        break

      case 'audio.delta':
        // CRITICAL: Check if audio data exists to prevent duplicate processing
        if (lastMessage.audio) {
          const chunkId = lastMessage.chunk_id || `unknown-${Date.now()}`

          // Check for duplicate chunk
          if (processedChunkIdsRef.current.has(chunkId)) {
            console.warn('[AUDIO] DUPLICATE_DETECTED: Ignoring duplicate audio chunk:', {
              chunkId,
              timestamp: new Date().toISOString()
            })
            break
          }

          // Mark chunk as processed
          processedChunkIdsRef.current.add(chunkId)
          audioChunkLogRef.current.push({ chunkId, timestamp: Date.now() })

          // Clean up old chunk IDs to prevent memory leak
          if (processedChunkIdsRef.current.size > 1000) {
            const oldestChunks = audioChunkLogRef.current.slice(0, 500)
            oldestChunks.forEach(chunk => processedChunkIdsRef.current.delete(chunk.chunkId))
            audioChunkLogRef.current = audioChunkLogRef.current.slice(500)
          }

          console.log('[AUDIO] CHUNK_RECEIVED:', {
            chunkId,
            audioLength: lastMessage.audio.length,
            totalProcessed: processedChunkIdsRef.current.size,
            timestamp: new Date().toISOString()
          })

          playAudioChunk(lastMessage.audio)
        } else {
          console.warn('[AUDIO] Received audio.delta without audio data')
        }
        break

      case 'audio.received':
        // Track ACK for audio chunks
        if (lastMessage.chunk_id) {
          pendingAudioChunksRef.current.delete(lastMessage.chunk_id)
          audioChunksAckedRef.current++
          console.log('[ACK] Audio chunk acknowledged:', {
            chunk_id: lastMessage.chunk_id,
            acked: audioChunksAckedRef.current,
            pending: pendingAudioChunksRef.current.size
          })
        }
        break

      case 'response.done':
        // CRITICAL FIX: Clear processing state when response is complete
        console.log('[RESPONSE] Response complete, clearing processing state')
        setIsProcessing(false)
        // Clear welcome processing flag
        processingWelcomeRef.current = false
        // Clear the safety timeout since we received the expected response
        if (processingTimeoutRef.current) {
          clearTimeout(processingTimeoutRef.current)
          processingTimeoutRef.current = null
        }
        break

      case 'profile.updated':
        // User profile was updated from conversation
        console.log('[PROFILE] User profile updated:', {
          name: lastMessage.name,
          age: lastMessage.age,
          gender: lastMessage.gender
        })
        break

      case 'context.updated':
        // RAG context retrieved and injected
        console.log('[RAG] Context updated:', {
          query: lastMessage.query,
          method: lastMessage.retrieval_method,
          user_contexts: lastMessage.user_context?.length || 0,
          app_contexts: lastMessage.app_context?.length || 0
        })

        // Log detailed RAG sources for debugging
        if (lastMessage.user_context && lastMessage.user_context.length > 0) {
          console.log('[RAG] User context sources:',
            lastMessage.user_context.map((ctx: any) => ({
              text: ctx.text?.substring(0, 100),
              score: ctx.score
            }))
          )
        }

        if (lastMessage.app_context && lastMessage.app_context.length > 0) {
          console.log('[RAG] App context sources:',
            lastMessage.app_context.map((ctx: any) => ({
              text: ctx.text?.substring(0, 100),
              score: ctx.score
            }))
          )
        }
        break

      case 'error':
        setError(lastMessage.message)
        setIsProcessing(false)
        // Clear the safety timeout since we received an error response
        if (processingTimeoutRef.current) {
          clearTimeout(processingTimeoutRef.current)
          processingTimeoutRef.current = null
        }
        break

      default:
        break
    }
  }, [lastMessage])

  const cleanupAudioResources = useCallback(() => {
    console.log('[CLEANUP] Cleaning up audio resources')

    // Stop media stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }

    // Disconnect and clear audio nodes
    if (analyzerNodeRef.current) {
      analyzerNodeRef.current.disconnect()
      analyzerNodeRef.current = null
    }

    if (sourceNodeRef.current) {
      sourceNodeRef.current.disconnect()
      sourceNodeRef.current = null
    }

    // Close capture context
    if (captureContextRef.current?.state !== 'closed') {
      captureContextRef.current?.close().catch(console.error)
      captureContextRef.current = null
    }

    // Clear refs
    mediaRecorderRef.current = null
    recordingRef.current = false
    processingChunksRef.current = false

    console.log('[CLEANUP] Resources cleaned up')
  }, [])

  // ADAPTIVE BUFFERING: Queue incoming audio chunks
  const playAudioChunk = async (base64Audio: string) => {
    try {
      if (!playbackContextRef.current) {
        console.error('[AUDIO] Playback context not initialized')
        return
      }

      const context = playbackContextRef.current

      // Resume AudioContext if suspended
      if (context.state === 'suspended') {
        console.log('[AUDIO] Resuming suspended AudioContext...')
        await context.resume()
        console.log('[AUDIO] AudioContext resumed, state:', context.state)
      }

      // Decode base64 to PCM16
      const audioData = atob(base64Audio)
      const pcmData = new Int16Array(audioData.length / 2)
      const dataView = new DataView(
        Uint8Array.from(audioData, c => c.charCodeAt(0)).buffer
      )

      for (let i = 0; i < pcmData.length; i++) {
        pcmData[i] = dataView.getInt16(i * 2, true)
      }

      // Convert PCM16 to Float32 with proper normalization
      const float32Data = new Float32Array(pcmData.length)
      for (let i = 0; i < pcmData.length; i++) {
        float32Data[i] = pcmData[i] / 32768.0
      }

      // Apply fade-in to first chunk to prevent pops
      const isFirstChunk = audioQueueRef.current.length === 0 && !isPlayingRef.current
      if (isFirstChunk) {
        console.log('[AUDIO] Applying fade-in to first chunk')
        const fadeInSamples = Math.min(1200, float32Data.length) // Fade in over first 50ms at 24kHz
        for (let i = 0; i < fadeInSamples; i++) {
          float32Data[i] *= i / fadeInSamples  // Linear fade-in
        }
      }

      // Create audio buffer
      const audioBuffer = context.createBuffer(
        1,  // mono
        float32Data.length,
        24000  // 24kHz sample rate
      )
      audioBuffer.getChannelData(0).set(float32Data)

      // Add to queue instead of playing immediately
      audioQueueRef.current.push(audioBuffer)

      const queueDurationMs = audioQueueRef.current.reduce((sum, buf) => sum + (buf.duration * 1000), 0)

      console.log('[AUDIO] Chunk queued:', {
        chunkDuration: (audioBuffer.duration * 1000).toFixed(1) + 'ms',
        queueSize: audioQueueRef.current.length,
        queueDurationMs: queueDurationMs.toFixed(1) + 'ms',
        isPlaying: isPlayingRef.current
      })

      // Start playback scheduler if not already running and we have enough buffer
      // Use double-check to prevent race conditions
      if (!isPlayingRef.current && queueDurationMs >= MIN_BUFFER_MS) {
        console.log('[AUDIO] Starting adaptive playback scheduler (buffer reached ' + queueDurationMs.toFixed(1) + 'ms)')
        // Double-check before starting to prevent race condition with multiple chunks
        if (!isPlayingRef.current) {
          startAdaptivePlayback()
        } else {
          console.log('[AUDIO] Playback started by another chunk - skipping')
        }
      }

    } catch (error) {
      console.error('[AUDIO] Failed to queue chunk:', error)
    }
  }

  // ADAPTIVE PLAYBACK: Continuously schedule chunks from queue
  const startAdaptivePlayback = () => {
    // CRITICAL FIX: Set flag immediately to prevent duplicate calls
    if (isPlayingRef.current) {
      console.log('[AUDIO] Playback already active - preventing duplicate')
      return
    }
    isPlayingRef.current = true  // Set immediately to prevent race condition

    if (!playbackContextRef.current) {
      console.error('[AUDIO] No playback context')
      isPlayingRef.current = false  // Reset flag on error
      return
    }

    // CRITICAL FIX: Clear any existing scheduler to prevent duplicates
    if (schedulerIntervalRef.current) {
      console.warn('[AUDIO] Clearing existing scheduler before starting new one')
      clearInterval(schedulerIntervalRef.current)
      schedulerIntervalRef.current = null
    }

    const context = playbackContextRef.current

    // Initialize scheduling time with lookahead buffer
    const currentTime = context.currentTime
    lastScheduledTimeRef.current = currentTime + (LOOKAHEAD_MS / 1000)

    console.log('[AUDIO] Adaptive playback started:', {
      currentTime: currentTime.toFixed(3),
      initialScheduleTime: lastScheduledTimeRef.current.toFixed(3),
      lookaheadMs: LOOKAHEAD_MS
    })

    // Schedule chunks continuously
    const scheduleNextChunk = () => {
      if (!playbackContextRef.current || !isPlayingRef.current) {
        return
      }

      const context = playbackContextRef.current
      const currentTime = context.currentTime

      // Check if we need to schedule more chunks
      const timeUntilNextGap = lastScheduledTimeRef.current - currentTime
      const shouldSchedule = timeUntilNextGap < (TARGET_BUFFER_MS / 1000)

      if (shouldSchedule && audioQueueRef.current.length > 0) {
        const audioBuffer = audioQueueRef.current.shift()!

        // Create and configure audio source
        const source = context.createBufferSource()
        source.buffer = audioBuffer

        // Add gain node with smooth envelope to prevent clicks/pops
        const gainNode = context.createGain()
        const fadeTime = 0.005  // 5ms fade for smoothness

        // Start at 1.0 (no fade-in for continuous playback)
        gainNode.gain.setValueAtTime(1.0, lastScheduledTimeRef.current)

        // Add very slight fade-out at the end to prevent clicks
        const endTime = lastScheduledTimeRef.current + audioBuffer.duration
        gainNode.gain.setValueAtTime(1.0, endTime - fadeTime)
        gainNode.gain.linearRampToValueAtTime(0.95, endTime)

        source.connect(gainNode)
        gainNode.connect(context.destination)

        // Schedule playback
        const scheduledTime = lastScheduledTimeRef.current

        // Handle timing drift - if we've fallen behind, catch up with small buffer
        let actualStartTime = scheduledTime
        if (scheduledTime < currentTime) {
          actualStartTime = currentTime + 0.01  // 10ms buffer to catch up
          console.log('[AUDIO] Timing drift detected, catching up:', {
            scheduled: scheduledTime.toFixed(3),
            current: currentTime.toFixed(3),
            correctedTo: actualStartTime.toFixed(3)
          })
        }

        try {
          source.start(actualStartTime)

          // Update next scheduled time
          lastScheduledTimeRef.current = actualStartTime + audioBuffer.duration

          const remainingQueueMs = audioQueueRef.current.reduce((sum, buf) => sum + (buf.duration * 1000), 0)

          console.log('[AUDIO] Chunk scheduled:', {
            currentTime: currentTime.toFixed(3),
            scheduledTime: actualStartTime.toFixed(3),
            duration: (audioBuffer.duration * 1000).toFixed(1) + 'ms',
            nextScheduleTime: lastScheduledTimeRef.current.toFixed(3),
            bufferAhead: ((lastScheduledTimeRef.current - currentTime) * 1000).toFixed(1) + 'ms',
            queueRemaining: audioQueueRef.current.length,
            queueDurationMs: remainingQueueMs.toFixed(1) + 'ms'
          })
        } catch (startError) {
          console.error('[AUDIO] Failed to start audio source:', startError)
          // Reset on error
          lastScheduledTimeRef.current = currentTime + (LOOKAHEAD_MS / 1000)
        }
      }

      // Stop scheduler if queue is empty and buffer is depleted
      if (audioQueueRef.current.length === 0) {
        const bufferRemaining = (lastScheduledTimeRef.current - currentTime) * 1000
        if (bufferRemaining <= 0) {
          console.log('[AUDIO] Queue empty and buffer depleted, stopping scheduler')
          stopAdaptivePlayback()
        }
      }
    }

    // Schedule chunks every 25ms for smoother playback (was 50ms)
    schedulerIntervalRef.current = setInterval(scheduleNextChunk, 25) as unknown as number

    // Schedule first batch immediately
    scheduleNextChunk()
  }

  // Stop adaptive playback scheduler
  const stopAdaptivePlayback = () => {
    isPlayingRef.current = false

    if (schedulerIntervalRef.current) {
      clearInterval(schedulerIntervalRef.current)
      schedulerIntervalRef.current = null
    }

    console.log('[AUDIO] Adaptive playback stopped')
  }

  const visualizeAudio = useCallback(() => {
    if (!analyzerNodeRef.current || !recordingRef.current) return

    const dataArray = new Uint8Array(analyzerNodeRef.current.frequencyBinCount)
    analyzerNodeRef.current.getByteFrequencyData(dataArray)

    const average = dataArray.reduce((a, b) => a + b) / dataArray.length
    setAudioLevel(average / 255)

    animationFrameRef.current = requestAnimationFrame(visualizeAudio)
  }, [])

  const startRecording = async () => {
    if (isProcessing || recordingRef.current) {
      console.log('[RECORDING] Already processing or recording')
      return
    }

    try {
      console.log('[RECORDING] Starting recording...')
      setError(null)
      setIsProcessing(true)
      processingChunksRef.current = true

      // Reset audio playback state when starting new recording
      stopAdaptivePlayback()  // Stop any ongoing playback
      lastScheduledTimeRef.current = 0
      nextStartTimeRef.current = 0
      audioQueueRef.current = []
      isPlayingRef.current = false

      // CRITICAL FIX: Reset audio chunks counters and pending set
      audioChunksSentRef.current = 0
      audioChunksAckedRef.current = 0
      pendingAudioChunksRef.current.clear()

      // Clean up any existing resources first
      cleanupAudioResources()

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 24000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      })

      streamRef.current = stream
      console.log('[RECORDING] Microphone stream obtained')

      // Setup audio context for capture and visualization
      captureContextRef.current = new AudioContext({ sampleRate: 24000 })
      const source = captureContextRef.current.createMediaStreamSource(stream)
      const analyzer = captureContextRef.current.createAnalyser()
      analyzer.fftSize = 4096

      source.connect(analyzer)
      sourceNodeRef.current = source
      analyzerNodeRef.current = analyzer

      // Start visualization
      recordingRef.current = true
      setIsRecording(true)
      setUserText('')
      setAssistantText('')
      visualizeAudio()

      // Process and send audio chunks
      const processChunk = () => {
        if (!recordingRef.current || !analyzerNodeRef.current) {
          console.log('[RECORDING] Stopping processChunk')
          return
        }

        const dataArray = new Float32Array(analyzerNodeRef.current.fftSize)
        analyzerNodeRef.current.getFloatTimeDomainData(dataArray)

        // Convert Float32 to PCM16
        const pcm16 = new Int16Array(dataArray.length)
        for (let i = 0; i < dataArray.length; i++) {
          const s = Math.max(-1, Math.min(1, dataArray[i]))
          pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
        }

        // Create byte array
        const byteArray = new Uint8Array(pcm16.length * 2)
        const dataView = new DataView(byteArray.buffer)
        for (let i = 0; i < pcm16.length; i++) {
          dataView.setInt16(i * 2, pcm16[i], true)
        }

        // Convert to base64
        let binary = ''
        const chunkSize = 8192
        for (let i = 0; i < byteArray.length; i += chunkSize) {
          const chunk = byteArray.subarray(i, Math.min(i + chunkSize, byteArray.length))
          binary += String.fromCharCode.apply(null, Array.from(chunk))
        }
        const base64 = btoa(binary)

        const chunkId = `${Date.now()}-${audioChunksSentRef.current}`

        // Track pending chunk
        pendingAudioChunksRef.current.add(chunkId)

        sendMessage({
          type: 'audio.append',
          audio: base64,
          chunk_id: chunkId
        })

        // CRITICAL FIX: Increment chunks sent counter
        audioChunksSentRef.current++

        // Schedule next chunk
        if (recordingRef.current) {
          setTimeout(processChunk, (analyzerNodeRef.current.fftSize / 24000) * 1000) as unknown as number
        }
      }

      processChunk()
      console.log('[RECORDING] Recording started successfully')

    } catch (error) {
      console.error('[RECORDING] Failed to start recording:', error)
      setError('Failed to access microphone. Please check permissions.')
      setIsRecording(false)
      setIsProcessing(false)
      cleanupAudioResources()
    }
  }

  const stopRecording = async () => {
    if (!recordingRef.current) {
      console.log('[RECORDING] Not currently recording')
      return
    }

    try {
      console.log('[RECORDING] Stopping recording...')

      recordingRef.current = false
      setIsRecording(false)
      setAudioLevel(0)

      // Cancel animation frame
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
        animationFrameRef.current = null
      }

      // Cleanup audio resources
      cleanupAudioResources()

      // IMPROVED: Wait for pending ACKs with timeout
      console.log('[RECORDING] Waiting for pending audio chunk ACKs...', {
        sent: audioChunksSentRef.current,
        pending: pendingAudioChunksRef.current.size
      })

      // Wait up to 500ms for ACKs, checking every 50ms
      const maxWaitMs = 500
      const checkIntervalMs = 50
      let waitedMs = 0

      while (pendingAudioChunksRef.current.size > 0 && waitedMs < maxWaitMs) {
        await new Promise(resolve => setTimeout(resolve, checkIntervalMs))
        waitedMs += checkIntervalMs
      }

      console.log('[RECORDING] ACK wait complete:', {
        sent: audioChunksSentRef.current,
        acked: audioChunksAckedRef.current,
        pending: pendingAudioChunksRef.current.size,
        waitedMs
      })

      // CRITICAL FIX: Validate that we have sufficient audio before committing
      // Backend requires minimum 100ms of audio. Each chunk is ~170ms (4096 samples at 24kHz)
      // So we need at least 1 confirmed chunk
      const MIN_CHUNKS_REQUIRED = 1

      if (audioChunksAckedRef.current >= MIN_CHUNKS_REQUIRED) {
        console.log(`[RECORDING] Committing audio buffer (${audioChunksAckedRef.current} chunks confirmed, sufficient)`)
        sendMessage({ type: 'audio.commit' })
        console.log('[RECORDING] Sent audio.commit')

        // CRITICAL FIX: Start safety timeout to clear processing state if backend never responds
        processingTimeoutRef.current = setTimeout(() => {
          console.warn('[TIMEOUT] Processing timeout reached, forcing processing state clear')
          setIsProcessing(false)
          setError('Response took too long. Please try again.')
          processingTimeoutRef.current = null
        }, PROCESSING_TIMEOUT_MS) as unknown as number

      } else {
        // Not enough audio captured - gracefully handle without error to OpenAI
        console.warn('[RECORDING] Insufficient audio captured, skipping commit', {
          chunks_acked: audioChunksAckedRef.current,
          chunks_required: MIN_CHUNKS_REQUIRED,
          sent: audioChunksSentRef.current
        })

        // Clear processing state immediately
        setIsProcessing(false)

        // Show helpful feedback based on the scenario
        if (audioChunksSentRef.current === 0) {
          // Instant click - no audio sent at all
          console.log('[RECORDING] Instant click detected (no chunks sent)')
          // Don't show error for instant clicks - user might be testing
        } else if (audioChunksAckedRef.current === 0) {
          // Chunks sent but none ACKed - network issue or very fast click
          console.log('[RECORDING] Network delay or very fast click (chunks sent but not ACKed)')
          setError('Recording too short. Please hold the button longer.')
        } else {
          // Some chunks ACKed but not enough
          console.log('[RECORDING] Recording too short (not enough audio)')
          setError('Recording too short. Please speak a bit longer.')
        }
      }

      console.log('[RECORDING] Recording stopped successfully')

    } catch (error) {
      console.error('[RECORDING] Error stopping recording:', error)
      setIsRecording(false)
      setIsProcessing(false)
      cleanupAudioResources()
    }
  }

  // Debounced toggle handler
  const handleMicrophoneToggle = useCallback(async () => {
    if (isProcessing && !isRecording) {
      console.log('[MICROPHONE] Still processing, ignoring click')
      return
    }

    try {
      if (isRecording) {
        await stopRecording()
      } else {
        await startRecording()
      }
    } catch (error) {
      console.error('[MICROPHONE] Toggle failed:', error)
      setError('An error occurred. Please try again.')
      setIsRecording(false)
      setIsProcessing(false)
      cleanupAudioResources()
    }
  }, [isRecording, isProcessing])

  // Debounce implementation using useMemo
  const debouncedToggle = useMemo(() => {
    let timeoutId: number | null = null

    return () => {
      if (timeoutId) {
        console.log('[DEBOUNCE] Ignoring rapid click')
        return
      }

      timeoutId = setTimeout(() => {
        timeoutId = null
      }, 500) as unknown as number

      handleMicrophoneToggle()
    }
  }, [handleMicrophoneToggle])

  // Theme colors
  const bgColor = effectiveTheme === 'dark' ? '#000000' : '#FFFFFF'
  const textColor = effectiveTheme === 'dark' ? '#FFFFFF' : '#000000'
  const subtleTextColor = effectiveTheme === 'dark' ? '#888888' : '#666666'
  const micGradient = effectiveTheme === 'dark'
    ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'

  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: bgColor,
        color: textColor,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Profile Icon - Top Right */}
      <Box sx={{ position: 'absolute', top: 20, right: 20, zIndex: 10 }}>
        <IconButton
          onClick={onProfileClick}
          sx={{
            bgcolor: effectiveTheme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)',
            '&:hover': {
              bgcolor: effectiveTheme === 'dark' ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.1)',
            }
          }}
        >
          <Person sx={{ color: textColor }} />
        </IconButton>
      </Box>

      {/* Error Display */}
      {error && (
        <Box sx={{ position: 'absolute', top: 20, left: 20, right: 80, zIndex: 10 }}>
          <Alert severity="error" onClose={() => setError(null)} sx={{ borderRadius: 2 }}>
            {error}
          </Alert>
        </Box>
      )}

      {/* Main Content - Centered */}
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 4,
          px: 3,
        }}
      >
        {/* User Text - Above Microphone */}
        <Fade in={!!userText} timeout={300}>
          <Box sx={{ textAlign: 'center', minHeight: 60, maxWidth: 600 }}>
            <Typography
              variant="h6"
              sx={{
                color: textColor,
                fontWeight: 300,
                lineHeight: 1.5,
                opacity: userText ? 1 : 0,
              }}
            >
              {userText}
            </Typography>
          </Box>
        </Fade>

        {/* Microphone Button */}
        <Box sx={{ position: 'relative' }}>
          {/* Pulse animation when recording */}
          {isRecording && (
            <Box
              sx={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                width: 140 + audioLevel * 40,
                height: 140 + audioLevel * 40,
                borderRadius: '50%',
                background: micGradient,
                opacity: 0.2,
                animation: 'pulse 1.5s ease-in-out infinite',
                '@keyframes pulse': {
                  '0%, 100%': { transform: 'translate(-50%, -50%) scale(1)', opacity: 0.2 },
                  '50%': { transform: 'translate(-50%, -50%) scale(1.1)', opacity: 0.3 },
                },
              }}
            />
          )}

          <IconButton
            onClick={debouncedToggle}
            disabled={!isConnected || (isProcessing && !isRecording)}
            sx={{
              width: 120,
              height: 120,
              background: isRecording ? 'rgba(244, 67, 54, 0.9)' : micGradient,
              color: '#FFFFFF',
              boxShadow: isRecording
                ? '0 10px 40px rgba(244, 67, 54, 0.4)'
                : '0 10px 40px rgba(102, 126, 234, 0.4)',
              transition: 'all 0.3s ease',
              transform: isRecording ? 'scale(1.05)' : 'scale(1)',
              '&:hover': {
                background: isRecording ? 'rgba(244, 67, 54, 1)' : micGradient,
                transform: isRecording ? 'scale(1.1)' : 'scale(1.05)',
                boxShadow: isRecording
                  ? '0 15px 50px rgba(244, 67, 54, 0.5)'
                  : '0 15px 50px rgba(102, 126, 234, 0.5)',
              },
              '&:disabled': {
                background: 'rgba(128, 128, 128, 0.3)',
                color: 'rgba(255, 255, 255, 0.5)',
              },
            }}
          >
            {isProcessing && !isRecording ? (
              <CircularProgress size={48} sx={{ color: '#FFFFFF' }} />
            ) : isRecording ? (
              <MicOff sx={{ fontSize: 48 }} />
            ) : (
              <Mic sx={{ fontSize: 48 }} />
            )}
          </IconButton>
        </Box>

        {/* Assistant Text - Below Microphone */}
        <Fade in={!!assistantText} timeout={300}>
          <Box sx={{ textAlign: 'center', minHeight: 60, maxWidth: 600 }}>
            <Typography
              variant="body1"
              sx={{
                color: subtleTextColor,
                fontWeight: 300,
                lineHeight: 1.6,
                opacity: assistantText ? 1 : 0,
              }}
            >
              {assistantText}
            </Typography>
          </Box>
        </Fade>

        {/* Connection Status */}
        <Typography
          variant="caption"
          sx={{
            color: subtleTextColor,
            textAlign: 'center',
          }}
        >
          {isConnected ? 'Connected' : 'Connecting...'}
        </Typography>
      </Box>
    </Box>
  )
}

export default VoiceChat

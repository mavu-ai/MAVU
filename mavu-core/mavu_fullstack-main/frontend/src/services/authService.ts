/**
 * Authentication service for managing user sessions and promo code registration.
 * Supports both web users (session tokens) and Telegram users (initData).
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
const SESSION_TOKEN_KEY = 'mavuai_session_token'
const USER_ID_KEY = 'mavuai_user_id'
const USER_STATUS_KEY = 'mavuai_user_status'
const TELEGRAM_INIT_DATA_KEY = 'telegram_init_data'
const TELEGRAM_ID_KEY = 'telegram_id'

export interface RegisterResponse {
  user_id: number
  session_token: string
  status: string
  created_at: string
  message: string
}

export interface AuthState {
  isAuthenticated: boolean
  sessionToken: string | null
  userId: number | null
  userStatus: string | null
}

export interface ValidateResponse {
  valid: boolean
  user_id?: number
  email?: string
  name?: string
  age?: number
  gender?: string
  is_guest: boolean
  is_registered: boolean
  message: string
}

class AuthService {
  /**
   * Register a new user with a promo code.
   */
  async register(promoCode: string): Promise<RegisterResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          promo_code: promoCode.trim().toUpperCase()
        })
      })

      if (!response.ok) {
        let errorMessage = 'Registration failed'
        try {
          const error = await response.json()
          errorMessage = error.detail || errorMessage
        } catch {
          // If response is not JSON, use status text
          errorMessage = response.statusText || errorMessage
        }

        throw new Error(errorMessage)
      }

      const data: RegisterResponse = await response.json()

      // Store session token and user info in localStorage
      this.setSession(data.session_token, data.user_id, data.status)

      return data
    } catch (error) {
      // Re-throw Error objects as-is
      if (error instanceof Error) {
        throw error
      }
      // Handle network errors and other unexpected errors
      throw new Error('Failed to connect to server. Please check your connection.')
    }
  }

  /**
   * Store session information in localStorage.
   */
  setSession(sessionToken: string, userId: number, status: string = 'guest'): void {
    localStorage.setItem(SESSION_TOKEN_KEY, sessionToken)
    localStorage.setItem(USER_ID_KEY, userId.toString())
    localStorage.setItem(USER_STATUS_KEY, status)
  }

  /**
   * Get current session token.
   */
  getSessionToken(): string | null {
    return localStorage.getItem(SESSION_TOKEN_KEY)
  }

  /**
   * Get current user ID.
   */
  getUserId(): number | null {
    const userId = localStorage.getItem(USER_ID_KEY)
    return userId ? parseInt(userId, 10) : null
  }

  /**
   * Get current user status.
   */
  getUserStatus(): string | null {
    return localStorage.getItem(USER_STATUS_KEY)
  }

  /**
   * Get current authentication state.
   */
  getAuthState(): AuthState {
    const sessionToken = this.getSessionToken()
    const userId = this.getUserId()
    const userStatus = this.getUserStatus()

    return {
      isAuthenticated: !!sessionToken && !!userId,
      sessionToken,
      userId,
      userStatus
    }
  }

  /**
   * Check if user is authenticated.
   */
  isAuthenticated(): boolean {
    return !!this.getSessionToken() && !!this.getUserId()
  }

  /**
   * Validate the current session with the backend.
   * Returns null if session is invalid or an error occurs.
   */
  async validateSession(): Promise<ValidateResponse | null> {
    const sessionToken = this.getSessionToken()

    if (!sessionToken) {
      return null
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/validate`, {
        method: 'GET',
        headers: {
          'X-Session-Token': sessionToken
        }
      })

      if (!response.ok) {
        // If validation endpoint returns error, session is invalid
        return null
      }

      const data: ValidateResponse = await response.json()

      // If session is not valid, clear localStorage
      if (!data.valid) {
        this.logout()
        return null
      }

      return data
    } catch (error) {
      console.error('Session validation error:', error)
      // On network error, assume session might be valid (offline mode)
      // Don't clear localStorage on network errors
      return null
    }
  }

  /**
   * Clear session and logout user.
   */
  logout(): void {
    localStorage.removeItem(SESSION_TOKEN_KEY)
    localStorage.removeItem(USER_ID_KEY)
    localStorage.removeItem(USER_STATUS_KEY)
  }

  /**
   * Get headers with authorization token.
   * Supports both session tokens (web users) and Telegram initData.
   */
  getAuthHeaders(): Record<string, string> {
    // Check for Telegram authentication first
    const telegramInitData = this.getTelegramInitData()
    if (telegramInitData) {
      return {
        'X-Telegram-Init-Data': telegramInitData
      }
    }

    // Fall back to session token
    const sessionToken = this.getSessionToken()
    if (sessionToken) {
      return {
        'X-Session-Token': sessionToken
      }
    }

    return {}
  }

  /**
   * Get Telegram initData.
   */
  getTelegramInitData(): string | null {
    return localStorage.getItem(TELEGRAM_INIT_DATA_KEY)
  }

  /**
   * Get Telegram user ID.
   */
  getTelegramId(): number | null {
    const telegramId = localStorage.getItem(TELEGRAM_ID_KEY)
    return telegramId ? parseInt(telegramId, 10) : null
  }

  /**
   * Check if user is authenticated via Telegram.
   */
  isTelegramUser(): boolean {
    return !!this.getTelegramInitData() && !!this.getTelegramId()
  }

  /**
   * Set Telegram authentication data.
   */
  setTelegramAuth(initData: string, userId: string, telegramId: number): void {
    localStorage.setItem(TELEGRAM_INIT_DATA_KEY, initData)
    localStorage.setItem(USER_ID_KEY, userId)
    localStorage.setItem(TELEGRAM_ID_KEY, telegramId.toString())
    localStorage.setItem(USER_STATUS_KEY, 'telegram')
  }
}

// Export singleton instance
export const authService = new AuthService()

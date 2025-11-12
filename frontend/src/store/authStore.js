/**
 * Authentication state management with Zustand
 */
import { create } from 'zustand'
import authService from '../services/authService'

// TEMPORARY: Disable auth for testing - set to false to re-enable
const AUTH_DISABLED = true

export const useAuthStore = create((set, get) => ({
  authDisabled: AUTH_DISABLED || (
    import.meta.env.VITE_AUTH_DISABLED &&
    import.meta.env.VITE_AUTH_DISABLED.toString().toLowerCase() === 'true'
  ),
  user: (() => {
    const authDisabled = AUTH_DISABLED || (
      import.meta.env.VITE_AUTH_DISABLED &&
      import.meta.env.VITE_AUTH_DISABLED.toString().toLowerCase() === 'true'
    )
    if (authDisabled) {
      return {
        id: '00000000-0000-0000-0000-000000000000',
        pseudonym: 'Test User',
        email: 'test@example.com',
      }
    }
    return authService.getUser()
  })(),
  isAuthenticated: (() => {
    const authDisabled = AUTH_DISABLED || (
      import.meta.env.VITE_AUTH_DISABLED &&
      import.meta.env.VITE_AUTH_DISABLED.toString().toLowerCase() === 'true'
    )
    return authDisabled ? true : authService.isAuthenticated()
  })(),
  loading: false,
  error: null,

  /**
   * Register a new user
   */
  register: async (userData) => {
    set({ loading: true, error: null })
    if (get().authDisabled) {
      const mockUser = {
        id: '00000000-0000-0000-0000-000000000000',
        pseudonym: userData?.pseudonym || 'Test User',
        email: userData?.email || 'test@example.com',
      }
      set({ user: mockUser, isAuthenticated: true, loading: false })
      return { user: mockUser, access_token: 'bypass-token' }
    }
    try {
      const data = await authService.register(userData)
      set({ user: data.user, isAuthenticated: true, loading: false })
      return data
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Registration failed'
      set({ error: errorMessage, loading: false })
      throw error
    }
  },

  /**
   * Login user
   */
  login: async (username, password) => {
    set({ loading: true, error: null })
    if (get().authDisabled) {
      const mockUser = {
        id: '00000000-0000-0000-0000-000000000000',
        pseudonym: username || 'Test User',
        email: 'test@example.com',
      }
      set({ user: mockUser, isAuthenticated: true, loading: false })
      return { user: mockUser, access_token: 'bypass-token' }
    }
    try {
      const data = await authService.login(username, password)
      set({ user: data.user, isAuthenticated: true, loading: false })
      return data
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Login failed'
      set({ error: errorMessage, loading: false })
      throw error
    }
  },

  /**
   * Logout user
   */
  logout: async () => {
    if (get().authDisabled) {
      set({ user: null, isAuthenticated: false, error: null })
      return
    }
    try {
      await authService.logout()
    } finally {
      set({ user: null, isAuthenticated: false, error: null })
    }
  },

  /**
   * Refresh user data
   */
  refreshUser: async () => {
    if (get().authDisabled) {
      return
    }
    try {
      const user = await authService.getCurrentUser()
      set({ user })
      localStorage.setItem('user', JSON.stringify(user))
    } catch (error) {
      console.error('Failed to refresh user:', error)
    }
  },

  /**
   * Clear error
   */
  clearError: () => set({ error: null }),
}))

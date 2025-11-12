/**
 * Authentication state management with Zustand
 */
import { create } from 'zustand'
import authService from '../services/authService'

export const useAuthStore = create((set, get) => ({
  user: authService.getUser(),
  isAuthenticated: authService.isAuthenticated(),
  loading: false,
  error: null,

  /**
   * Register a new user
   */
  register: async (userData) => {
    set({ loading: true, error: null })
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

/**
 * Authentication service
 * Handles user registration, login, and auth state
 */
import api from './api'

class AuthService {
  /**
   * Register a new user
   */
  async register(userData) {
    const response = await api.post('/auth/register', userData)
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('user', JSON.stringify(response.data.user))
    }
    return response.data
  }

  /**
   * Login user
   */
  async login(username, password) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })

    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('user', JSON.stringify(response.data.user))
    }

    return response.data
  }

  /**
   * Logout user
   */
  async logout() {
    try {
      await api.post('/auth/logout')
    } catch (error) {
      // Continue even if API call fails
      console.error('Logout error:', error)
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
    }
  }

  /**
   * Get current user
   */
  async getCurrentUser() {
    const response = await api.get('/auth/me')
    return response.data
  }

  /**
   * Request phone verification
   */
  async requestPhoneVerification(phone) {
    const response = await api.post('/auth/verify-phone/request', { phone })
    return response.data
  }

  /**
   * Confirm phone verification
   */
  async confirmPhoneVerification(phone, code) {
    const response = await api.post('/auth/verify-phone/confirm', { phone, code })
    return response.data
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return !!localStorage.getItem('access_token')
  }

  /**
   * Get current user from local storage
   */
  getUser() {
    const userStr = localStorage.getItem('user')
    return userStr ? JSON.parse(userStr) : null
  }

  /**
   * Get access token
   */
  getToken() {
    return localStorage.getItem('access_token')
  }
}

export default new AuthService()

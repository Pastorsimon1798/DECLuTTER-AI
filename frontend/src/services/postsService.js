/**
 * Posts service for Needs & Offers Board
 * Handles CRUD operations for posts and matches
 */
import api from './api'

class PostsService {
  /**
   * Search posts with filters
   */
  async searchPosts(params = {}) {
    const response = await api.get('/posts', { params })
    return response.data
  }

  /**
   * Get a specific post by ID
   */
  async getPost(postId) {
    const response = await api.get(`/posts/${postId}`)
    return response.data
  }

  /**
   * Create a new post
   */
  async createPost(postData) {
    const response = await api.post('/posts', postData)
    return response.data
  }

  /**
   * Update a post
   */
  async updatePost(postId, updateData) {
    const response = await api.patch(`/posts/${postId}`, updateData)
    return response.data
  }

  /**
   * Delete a post
   */
  async deletePost(postId) {
    await api.delete(`/posts/${postId}`)
  }

  /**
   * Get current user's posts
   */
  async getMyPosts(params = {}) {
    const response = await api.get('/posts/my/posts', { params })
    return response.data
  }

  /**
   * Create a match (respond to a post)
   */
  async createMatch(matchData) {
    const response = await api.post('/matches', matchData)
    return response.data
  }

  /**
   * Get current user's matches
   */
  async getMyMatches(params = {}) {
    const response = await api.get('/matches', { params })
    return response.data
  }

  /**
   * Get a specific match
   */
  async getMatch(matchId) {
    const response = await api.get(`/matches/${matchId}`)
    return response.data
  }

  /**
   * Update match status
   */
  async updateMatch(matchId, updateData) {
    const response = await api.patch(`/matches/${matchId}`, updateData)
    return response.data
  }

  /**
   * Get matches for a specific post
   */
  async getPostMatches(postId) {
    const response = await api.get(`/matches/post/${postId}`)
    return response.data
  }
}

export default new PostsService()

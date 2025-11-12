/**
 * Posts state management with Zustand
 */
import { create } from 'zustand'
import postsService from '../services/postsService'

export const usePostsStore = create((set, get) => ({
  posts: [],
  currentPost: null,
  matches: [],
  myPosts: [],
  loading: false,
  error: null,
  filters: {
    type: null,
    category: null,
    radius: 5000,
  },
  userLocation: null,

  /**
   * Set user location
   */
  setUserLocation: (location) => set({ userLocation: location }),

  /**
   * Set filters
   */
  setFilters: (filters) => set((state) => ({
    filters: { ...state.filters, ...filters }
  })),

  /**
   * Search posts
   */
  searchPosts: async (customParams = {}) => {
    set({ loading: true, error: null })
    try {
      const { filters, userLocation } = get()
      const params = {
        ...filters,
        ...customParams,
      }

      // Add location if available
      if (userLocation) {
        params.lat = userLocation.lat
        params.lon = userLocation.lon
      }

      const posts = await postsService.searchPosts(params)
      set({ posts, loading: false })
      return posts
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to search posts'
      set({ error: errorMessage, loading: false })
      throw error
    }
  },

  /**
   * Get a specific post
   */
  getPost: async (postId) => {
    set({ loading: true, error: null })
    try {
      const post = await postsService.getPost(postId)
      set({ currentPost: post, loading: false })
      return post
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to get post'
      set({ error: errorMessage, loading: false })
      throw error
    }
  },

  /**
   * Create a new post
   */
  createPost: async (postData) => {
    set({ loading: true, error: null })
    try {
      const post = await postsService.createPost(postData)
      set((state) => ({
        posts: [post, ...state.posts],
        myPosts: [post, ...state.myPosts],
        loading: false
      }))
      return post
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to create post'
      set({ error: errorMessage, loading: false })
      throw error
    }
  },

  /**
   * Update a post
   */
  updatePost: async (postId, updateData) => {
    set({ loading: true, error: null })
    try {
      const updatedPost = await postsService.updatePost(postId, updateData)
      set((state) => ({
        posts: state.posts.map(p => p.id === postId ? updatedPost : p),
        myPosts: state.myPosts.map(p => p.id === postId ? updatedPost : p),
        currentPost: state.currentPost?.id === postId ? updatedPost : state.currentPost,
        loading: false
      }))
      return updatedPost
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to update post'
      set({ error: errorMessage, loading: false })
      throw error
    }
  },

  /**
   * Delete a post
   */
  deletePost: async (postId) => {
    set({ loading: true, error: null })
    try {
      await postsService.deletePost(postId)
      set((state) => ({
        posts: state.posts.filter(p => p.id !== postId),
        myPosts: state.myPosts.filter(p => p.id !== postId),
        loading: false
      }))
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to delete post'
      set({ error: errorMessage, loading: false })
      throw error
    }
  },

  /**
   * Get current user's posts
   */
  getMyPosts: async () => {
    set({ loading: true, error: null })
    try {
      const posts = await postsService.getMyPosts()
      set({ myPosts: posts, loading: false })
      return posts
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to get your posts'
      set({ error: errorMessage, loading: false })
      throw error
    }
  },

  /**
   * Create a match (respond to a post)
   */
  createMatch: async (matchData) => {
    set({ loading: true, error: null })
    try {
      const match = await postsService.createMatch(matchData)
      set({ loading: false })
      return match
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to create match'
      set({ error: errorMessage, loading: false })
      throw error
    }
  },

  /**
   * Get current user's matches
   */
  getMyMatches: async () => {
    set({ loading: true, error: null })
    try {
      const matches = await postsService.getMyMatches()
      set({ matches, loading: false })
      return matches
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to get matches'
      set({ error: errorMessage, loading: false })
      throw error
    }
  },

  /**
   * Update match status
   */
  updateMatch: async (matchId, updateData) => {
    set({ loading: true, error: null })
    try {
      const updatedMatch = await postsService.updateMatch(matchId, updateData)
      set((state) => ({
        matches: state.matches.map(m => m.id === matchId ? updatedMatch : m),
        loading: false
      }))
      return updatedMatch
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to update match'
      set({ error: errorMessage, loading: false })
      throw error
    }
  },

  /**
   * Clear error
   */
  clearError: () => set({ error: null }),
}))

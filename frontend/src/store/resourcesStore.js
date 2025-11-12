import { create } from 'zustand';
import { resourcesService } from '../services/resourcesService';

/**
 * Resources Store - State management for pantry locator
 */

export const useResourcesStore = create((set, get) => ({
  // State
  resources: [],
  bookmarks: [],
  currentResource: null,
  loading: false,
  error: null,

  // Filters
  filters: {
    lat: null,
    lon: null,
    radius: 5000,  // 5km default
    category: null,
    subcategory: null,
    query: '',
    open_now: false,
    population_tags: null,  // Phase 3.5
    is_community_contributed: null,  // Phase 3.5
    sort_by: 'distance',  // Default sort: distance (or name if no location)
  },

  // Set filters
  setFilters: (newFilters) => {
    set({ filters: { ...get().filters, ...newFilters } });
  },

  clearFilters: () => {
    set({
      filters: {
        lat: null,
        lon: null,
        radius: 5000,
        category: null,
        subcategory: null,
        query: '',
        open_now: false,
        population_tags: null,
        is_community_contributed: null,
        sort_by: 'distance',
      },
    });
  },

  // Resources
  searchResources: async (customFilters = null) => {
    set({ loading: true, error: null });
    try {
      const filters = customFilters || get().filters;
      const resources = await resourcesService.searchResources(filters);
      set({ resources, loading: false });
      return resources;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to search resources',
        loading: false,
      });
      throw error;
    }
  },

  fetchResource: async (id) => {
    set({ loading: true, error: null });
    try {
      const resource = await resourcesService.getResource(id);
      set({ currentResource: resource, loading: false });
      return resource;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch resource',
        loading: false,
      });
      throw error;
    }
  },

  createResource: async (data) => {
    set({ loading: true, error: null });
    try {
      const resource = await resourcesService.createResource(data);
      set((state) => ({
        resources: [...state.resources, resource],
        loading: false,
      }));
      return resource;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to create resource',
        loading: false,
      });
      throw error;
    }
  },

  updateResource: async (id, data) => {
    set({ loading: true, error: null });
    try {
      const updatedResource = await resourcesService.updateResource(id, data);
      set((state) => ({
        resources: state.resources.map((r) => (r.id === id ? updatedResource : r)),
        currentResource: state.currentResource?.id === id ? updatedResource : state.currentResource,
        loading: false,
      }));
      return updatedResource;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to update resource',
        loading: false,
      });
      throw error;
    }
  },

  deleteResource: async (id) => {
    set({ loading: true, error: null });
    try {
      await resourcesService.deleteResource(id);
      set((state) => ({
        resources: state.resources.filter((r) => r.id !== id),
        loading: false,
      }));
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to delete resource',
        loading: false,
      });
      throw error;
    }
  },

  // Bookmarks
  createBookmark: async (resourceId, notes = '') => {
    set({ loading: true, error: null });
    try {
      const bookmark = await resourcesService.createBookmark(resourceId, notes);

      // Update resource to mark as bookmarked
      set((state) => ({
        resources: state.resources.map((r) =>
          r.id === resourceId
            ? { ...r, is_bookmarked: true, bookmark_id: bookmark.id }
            : r
        ),
        currentResource: state.currentResource?.id === resourceId
          ? { ...state.currentResource, is_bookmarked: true, bookmark_id: bookmark.id }
          : state.currentResource,
        loading: false,
      }));

      return bookmark;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to create bookmark',
        loading: false,
      });
      throw error;
    }
  },

  fetchBookmarks: async () => {
    set({ loading: true, error: null });
    try {
      const bookmarks = await resourcesService.getMyBookmarks();
      set({ bookmarks, loading: false });
      return bookmarks;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch bookmarks',
        loading: false,
      });
      throw error;
    }
  },

  updateBookmark: async (bookmarkId, data) => {
    set({ loading: true, error: null });
    try {
      const updatedBookmark = await resourcesService.updateBookmark(bookmarkId, data);
      set((state) => ({
        bookmarks: state.bookmarks.map((b) => (b.id === bookmarkId ? updatedBookmark : b)),
        loading: false,
      }));
      return updatedBookmark;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to update bookmark',
        loading: false,
      });
      throw error;
    }
  },

  deleteBookmark: async (bookmarkId, resourceId) => {
    set({ loading: true, error: null });
    try {
      await resourcesService.deleteBookmark(bookmarkId);

      // Update resource to mark as not bookmarked
      set((state) => ({
        bookmarks: state.bookmarks.filter((b) => b.id !== bookmarkId),
        resources: state.resources.map((r) =>
          r.id === resourceId
            ? { ...r, is_bookmarked: false, bookmark_id: null }
            : r
        ),
        currentResource: state.currentResource?.id === resourceId
          ? { ...state.currentResource, is_bookmarked: false, bookmark_id: null }
          : state.currentResource,
        loading: false,
      }));
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to delete bookmark',
        loading: false,
      });
      throw error;
    }
  },

  // Phase 3.5: Verify resource
  verifyResource: async (resourceId, isAccurate, notes = '') => {
    set({ loading: true, error: null });
    try {
      const response = await resourcesService.verifyResource(resourceId, isAccurate, notes);

      // Update resource in lists and current resource
      set((state) => ({
        resources: state.resources.map((r) =>
          r.id === resourceId ? { ...r, verification_count: response.verification_count } : r
        ),
        currentResource: state.currentResource?.id === resourceId
          ? { ...state.currentResource, verification_count: response.verification_count }
          : state.currentResource,
        loading: false,
      }));

      return response;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to verify resource',
        loading: false,
      });
      throw error;
    }
  },

  // Clear current resource
  clearCurrent: () => {
    set({ currentResource: null });
  },

  // Clear error
  clearError: () => {
    set({ error: null });
  },
}));

export default useResourcesStore;

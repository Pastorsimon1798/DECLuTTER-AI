import api from './api';

/**
 * Resources Service - API calls for pantry locator
 */

export const resourcesService = {
  // Resources
  async searchResources(filters = {}) {
    const params = new URLSearchParams();

    if (filters.lat) params.append('lat', filters.lat);
    if (filters.lon) params.append('lon', filters.lon);
    if (filters.radius) params.append('radius', filters.radius);
    if (filters.category) params.append('category', filters.category);
    if (filters.query) params.append('query', filters.query);
    if (filters.open_now) params.append('open_now', filters.open_now);

    const response = await api.get(`/resources/search?${params.toString()}`);
    return response.data;
  },

  async getResource(id) {
    const response = await api.get(`/resources/${id}`);
    return response.data;
  },

  async createResource(data) {
    const response = await api.post('/resources', data);
    return response.data;
  },

  async updateResource(id, data) {
    const response = await api.put(`/resources/${id}`, data);
    return response.data;
  },

  async deleteResource(id) {
    await api.delete(`/resources/${id}`);
  },

  // Bookmarks
  async createBookmark(resourceId, notes = '') {
    const response = await api.post('/resources/bookmarks', {
      resource_id: resourceId,
      notes,
    });
    return response.data;
  },

  async getMyBookmarks() {
    const response = await api.get('/resources/bookmarks/my');
    return response.data;
  },

  async updateBookmark(bookmarkId, data) {
    const response = await api.put(`/resources/bookmarks/${bookmarkId}`, data);
    return response.data;
  },

  async deleteBookmark(bookmarkId) {
    await api.delete(`/resources/bookmarks/${bookmarkId}`);
  },
};

export default resourcesService;

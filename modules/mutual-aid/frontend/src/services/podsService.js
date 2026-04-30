import api from './api';

/**
 * Pods Service - API calls for Pods/Micro-Circles
 */

export const podsService = {
  // Pod CRUD
  async getPods() {
    const response = await api.get('/pods');
    return response.data;
  },

  async getPod(id) {
    const response = await api.get(`/pods/${id}`);
    return response.data;
  },

  async createPod(data) {
    const response = await api.post('/pods', data);
    return response.data;
  },

  async updatePod(id, data) {
    const response = await api.put(`/pods/${id}`, data);
    return response.data;
  },

  async deletePod(id) {
    await api.delete(`/pods/${id}`);
  },

  // Member Management
  async joinPod(podId, userId = null) {
    const data = userId ? { user_id: userId } : {};
    const response = await api.post(`/pods/${podId}/members`, data);
    return response.data;
  },

  async getMembers(podId) {
    const response = await api.get(`/pods/${podId}/members`);
    return response.data;
  },

  async updateMember(podId, memberId, data) {
    const response = await api.put(`/pods/${podId}/members/${memberId}`, data);
    return response.data;
  },

  async removeMember(podId, memberId) {
    await api.delete(`/pods/${podId}/members/${memberId}`);
  },

  // Check-Ins
  async submitCheckIn(podId, data) {
    const response = await api.post(`/pods/${podId}/check-ins`, data);
    return response.data;
  },

  async getCheckIns(podId, limit = 50) {
    const response = await api.get(`/pods/${podId}/check-ins`, {
      params: { limit }
    });
    return response.data;
  },

  async getWellnessAlerts(podId) {
    const response = await api.get(`/pods/${podId}/wellness`);
    return response.data;
  },

  // SOS Broadcasts
  async sendSOS(podId, data) {
    const response = await api.post(`/pods/${podId}/sos`, data);
    return response.data;
  },

  async getSOSBroadcasts(podId, includeResolved = false) {
    const response = await api.get(`/pods/${podId}/sos`, {
      params: { include_resolved: includeResolved }
    });
    return response.data;
  },

  async resolveSOS(podId, sosId) {
    const response = await api.put(`/pods/${podId}/sos/${sosId}`, {
      is_resolved: true
    });
    return response.data;
  },

  // Pod Posts
  async createPost(podId, data) {
    const response = await api.post(`/pods/${podId}/posts`, data);
    return response.data;
  },

  async getPosts(podId, skip = 0, limit = 50) {
    const response = await api.get(`/pods/${podId}/posts`, {
      params: { skip, limit }
    });
    return response.data;
  },

  async updatePost(podId, postId, data) {
    const response = await api.put(`/pods/${podId}/posts/${postId}`, data);
    return response.data;
  },

  async deletePost(podId, postId) {
    await api.delete(`/pods/${podId}/posts/${postId}`);
  },

  async pinPost(podId, postId, isPinned) {
    const response = await api.put(`/pods/${podId}/posts/${postId}`, {
      is_pinned: isPinned
    });
    return response.data;
  },
};

export default podsService;

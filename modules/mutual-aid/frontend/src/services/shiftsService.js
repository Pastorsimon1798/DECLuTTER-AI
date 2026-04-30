import api from './api';

/**
 * Shifts Service - API calls for volunteer scheduling
 */

// Organizations
export const organizationsService = {
  async getOrganizations() {
    const response = await api.get('/organizations');
    return response.data;
  },

  async getOrganization(id) {
    const response = await api.get(`/organizations/${id}`);
    return response.data;
  },

  async getOrganizationBySlug(slug) {
    const response = await api.get(`/organizations/slug/${slug}`);
    return response.data;
  },

  async createOrganization(data) {
    const response = await api.post('/organizations', data);
    return response.data;
  },

  async updateOrganization(id, data) {
    const response = await api.put(`/organizations/${id}`, data);
    return response.data;
  },

  async deleteOrganization(id) {
    await api.delete(`/organizations/${id}`);
  },
};

// Shifts
export const shiftsService = {
  async getShifts(filters = {}) {
    const params = new URLSearchParams();

    if (filters.organization_id) params.append('organization_id', filters.organization_id);
    if (filters.start_date) params.append('start_date', filters.start_date);
    if (filters.end_date) params.append('end_date', filters.end_date);
    if (filters.status) params.append('status', filters.status);
    if (filters.available_only) params.append('available_only', filters.available_only);

    const response = await api.get(`/shifts?${params.toString()}`);
    return response.data;
  },

  async getShift(id) {
    const response = await api.get(`/shifts/${id}`);
    return response.data;
  },

  async createShift(data) {
    const response = await api.post('/shifts', data);
    return response.data;
  },

  async updateShift(id, data) {
    const response = await api.put(`/shifts/${id}`, data);
    return response.data;
  },

  async deleteShift(id) {
    await api.delete(`/shifts/${id}`);
  },

  // Shift signups
  async signupForShift(shiftId, notes = '') {
    const response = await api.post(`/shifts/${shiftId}/signup`, { notes });
    return response.data;
  },

  async getMyShifts(filters = {}) {
    const params = new URLSearchParams();

    if (filters.status) params.append('status', filters.status);
    if (filters.upcoming_only) params.append('upcoming_only', filters.upcoming_only);

    const response = await api.get(`/shifts/my-shifts?${params.toString()}`);
    return response.data;
  },

  async updateSignup(signupId, data) {
    const response = await api.put(`/shifts/signups/${signupId}`, data);
    return response.data;
  },

  async cancelSignup(signupId) {
    await api.delete(`/shifts/signups/${signupId}`);
  },
};

export default shiftsService;

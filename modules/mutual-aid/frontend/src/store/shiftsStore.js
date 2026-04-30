import { create } from 'zustand';
import { shiftsService, organizationsService } from '../services/shiftsService';

/**
 * Shifts Store - State management for volunteer scheduling
 */

export const useShiftsStore = create((set, get) => ({
  // State
  shifts: [],
  myShifts: [],
  organizations: [],
  currentShift: null,
  currentOrganization: null,
  loading: false,
  error: null,

  // Filters
  filters: {
    organization_id: null,
    start_date: null,
    end_date: null,
    status: null,
    available_only: false,
  },

  // Set filters
  setFilters: (newFilters) => {
    set({ filters: { ...get().filters, ...newFilters } });
  },

  clearFilters: () => {
    set({
      filters: {
        organization_id: null,
        start_date: null,
        end_date: null,
        status: null,
        available_only: false,
      },
    });
  },

  // Organizations
  fetchOrganizations: async () => {
    set({ loading: true, error: null });
    try {
      const organizations = await organizationsService.getOrganizations();
      set({ organizations, loading: false });
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch organizations',
        loading: false,
      });
    }
  },

  fetchOrganization: async (id) => {
    set({ loading: true, error: null });
    try {
      const organization = await organizationsService.getOrganization(id);
      set({ currentOrganization: organization, loading: false });
      return organization;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch organization',
        loading: false,
      });
      throw error;
    }
  },

  createOrganization: async (data) => {
    set({ loading: true, error: null });
    try {
      const organization = await organizationsService.createOrganization(data);
      set((state) => ({
        organizations: [...state.organizations, organization],
        loading: false,
      }));
      return organization;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to create organization',
        loading: false,
      });
      throw error;
    }
  },

  // Shifts
  fetchShifts: async (customFilters = null) => {
    set({ loading: true, error: null });
    try {
      const filters = customFilters || get().filters;
      const shifts = await shiftsService.getShifts(filters);
      set({ shifts, loading: false });
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch shifts',
        loading: false,
      });
    }
  },

  fetchShift: async (id) => {
    set({ loading: true, error: null });
    try {
      const shift = await shiftsService.getShift(id);
      set({ currentShift: shift, loading: false });
      return shift;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch shift',
        loading: false,
      });
      throw error;
    }
  },

  createShift: async (data) => {
    set({ loading: true, error: null });
    try {
      const shift = await shiftsService.createShift(data);
      set((state) => ({
        shifts: [...state.shifts, shift],
        loading: false,
      }));
      return shift;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to create shift',
        loading: false,
      });
      throw error;
    }
  },

  updateShift: async (id, data) => {
    set({ loading: true, error: null });
    try {
      const updatedShift = await shiftsService.updateShift(id, data);
      set((state) => ({
        shifts: state.shifts.map((s) => (s.id === id ? updatedShift : s)),
        currentShift: state.currentShift?.id === id ? updatedShift : state.currentShift,
        loading: false,
      }));
      return updatedShift;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to update shift',
        loading: false,
      });
      throw error;
    }
  },

  deleteShift: async (id) => {
    set({ loading: true, error: null });
    try {
      await shiftsService.deleteShift(id);
      set((state) => ({
        shifts: state.shifts.filter((s) => s.id !== id),
        loading: false,
      }));
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to delete shift',
        loading: false,
      });
      throw error;
    }
  },

  // Shift Signups
  signupForShift: async (shiftId, notes = '') => {
    set({ loading: true, error: null });
    try {
      const signup = await shiftsService.signupForShift(shiftId, notes);

      // Update shift filled count optimistically
      set((state) => ({
        shifts: state.shifts.map((s) =>
          s.id === shiftId
            ? {
                ...s,
                filled_count: s.filled_count + 1,
                available_spots: s.available_spots - 1,
                is_full: s.filled_count + 1 >= s.capacity,
              }
            : s
        ),
        currentShift: state.currentShift?.id === shiftId
          ? {
              ...state.currentShift,
              filled_count: state.currentShift.filled_count + 1,
              available_spots: state.currentShift.available_spots - 1,
              is_full: state.currentShift.filled_count + 1 >= state.currentShift.capacity,
            }
          : state.currentShift,
        loading: false,
      }));

      return signup;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to sign up for shift',
        loading: false,
      });
      throw error;
    }
  },

  fetchMyShifts: async (filters = {}) => {
    set({ loading: true, error: null });
    try {
      const myShifts = await shiftsService.getMyShifts(filters);
      set({ myShifts, loading: false });
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch your shifts',
        loading: false,
      });
    }
  },

  updateSignup: async (signupId, data) => {
    set({ loading: true, error: null });
    try {
      const updatedSignup = await shiftsService.updateSignup(signupId, data);
      set((state) => ({
        myShifts: state.myShifts.map((s) => (s.id === signupId ? updatedSignup : s)),
        loading: false,
      }));
      return updatedSignup;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to update signup',
        loading: false,
      });
      throw error;
    }
  },

  cancelSignup: async (signupId, shiftId) => {
    set({ loading: true, error: null });
    try {
      await shiftsService.cancelSignup(signupId);

      // Update shift filled count optimistically
      set((state) => ({
        myShifts: state.myShifts.filter((s) => s.id !== signupId),
        shifts: state.shifts.map((s) =>
          s.id === shiftId
            ? {
                ...s,
                filled_count: Math.max(0, s.filled_count - 1),
                available_spots: s.available_spots + 1,
                is_full: false,
              }
            : s
        ),
        loading: false,
      }));
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to cancel signup',
        loading: false,
      });
      throw error;
    }
  },

  // Clear current shift/organization
  clearCurrent: () => {
    set({ currentShift: null, currentOrganization: null });
  },

  // Clear error
  clearError: () => {
    set({ error: null });
  },
}));

export default useShiftsStore;

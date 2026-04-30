import { create } from 'zustand';
import { podsService } from '../services/podsService';

const usePodsStore = create((set, get) => ({
  // State
  pods: [],
  currentPod: null,
  members: [],
  checkIns: [],
  sosses: [],
  posts: [],
  wellnessAlerts: [],
  loading: false,
  error: null,

  // Pod CRUD Operations
  fetchPods: async () => {
    set({ loading: true, error: null });
    try {
      const pods = await podsService.getPods();
      set({ pods, loading: false });
      return pods;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch pods',
        loading: false,
      });
      throw error;
    }
  },

  fetchPod: async (id) => {
    set({ loading: true, error: null });
    try {
      const pod = await podsService.getPod(id);
      set({ currentPod: pod, loading: false });
      return pod;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch pod',
        loading: false,
      });
      throw error;
    }
  },

  createPod: async (data) => {
    set({ loading: true, error: null });
    try {
      const pod = await podsService.createPod(data);
      set((state) => ({
        pods: [pod, ...state.pods],
        loading: false,
      }));
      return pod;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to create pod',
        loading: false,
      });
      throw error;
    }
  },

  updatePod: async (id, data) => {
    set({ loading: true, error: null });
    try {
      const pod = await podsService.updatePod(id, data);
      set((state) => ({
        pods: state.pods.map((p) => (p.id === id ? pod : p)),
        currentPod: state.currentPod?.id === id ? pod : state.currentPod,
        loading: false,
      }));
      return pod;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to update pod',
        loading: false,
      });
      throw error;
    }
  },

  deletePod: async (id) => {
    set({ loading: true, error: null });
    try {
      await podsService.deletePod(id);
      set((state) => ({
        pods: state.pods.filter((p) => p.id !== id),
        currentPod: state.currentPod?.id === id ? null : state.currentPod,
        loading: false,
      }));
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to delete pod',
        loading: false,
      });
      throw error;
    }
  },

  // Member Management
  joinPod: async (podId, userId = null) => {
    set({ loading: true, error: null });
    try {
      const member = await podsService.joinPod(podId, userId);
      set((state) => ({
        members: [member, ...state.members],
        loading: false,
      }));
      return member;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to join pod',
        loading: false,
      });
      throw error;
    }
  },

  fetchMembers: async (podId) => {
    set({ loading: true, error: null });
    try {
      const members = await podsService.getMembers(podId);
      set({ members, loading: false });
      return members;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch members',
        loading: false,
      });
      throw error;
    }
  },

  updateMember: async (podId, memberId, data) => {
    set({ loading: true, error: null });
    try {
      const member = await podsService.updateMember(podId, memberId, data);
      set((state) => ({
        members: state.members.map((m) => (m.id === memberId ? member : m)),
        loading: false,
      }));
      return member;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to update member',
        loading: false,
      });
      throw error;
    }
  },

  removeMember: async (podId, memberId) => {
    set({ loading: true, error: null });
    try {
      await podsService.removeMember(podId, memberId);
      set((state) => ({
        members: state.members.filter((m) => m.id !== memberId),
        loading: false,
      }));
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to remove member',
        loading: false,
      });
      throw error;
    }
  },

  // Check-Ins
  submitCheckIn: async (podId, data) => {
    set({ loading: true, error: null });
    try {
      const checkIn = await podsService.submitCheckIn(podId, data);
      set((state) => ({
        checkIns: [checkIn, ...state.checkIns],
        loading: false,
      }));
      return checkIn;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to submit check-in',
        loading: false,
      });
      throw error;
    }
  },

  fetchCheckIns: async (podId, limit = 50) => {
    set({ loading: true, error: null });
    try {
      const checkIns = await podsService.getCheckIns(podId, limit);
      set({ checkIns, loading: false });
      return checkIns;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch check-ins',
        loading: false,
      });
      throw error;
    }
  },

  fetchWellnessAlerts: async (podId) => {
    set({ loading: true, error: null });
    try {
      const alerts = await podsService.getWellnessAlerts(podId);
      set({ wellnessAlerts: alerts, loading: false });
      return alerts;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch wellness alerts',
        loading: false,
      });
      throw error;
    }
  },

  // SOS Broadcasts
  sendSOS: async (podId, data) => {
    set({ loading: true, error: null });
    try {
      const sos = await podsService.sendSOS(podId, data);
      set((state) => ({
        sosses: [sos, ...state.sosses],
        loading: false,
      }));
      return sos;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to send SOS',
        loading: false,
      });
      throw error;
    }
  },

  fetchSOSBroadcasts: async (podId, includeResolved = false) => {
    set({ loading: true, error: null });
    try {
      const sosses = await podsService.getSOSBroadcasts(podId, includeResolved);
      set({ sosses, loading: false });
      return sosses;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch SOS broadcasts',
        loading: false,
      });
      throw error;
    }
  },

  resolveSOS: async (podId, sosId) => {
    set({ loading: true, error: null });
    try {
      const sos = await podsService.resolveSOS(podId, sosId);
      set((state) => ({
        sosses: state.sosses.map((s) => (s.id === sosId ? sos : s)),
        loading: false,
      }));
      return sos;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to resolve SOS',
        loading: false,
      });
      throw error;
    }
  },

  // Pod Posts
  createPost: async (podId, data) => {
    set({ loading: true, error: null });
    try {
      const post = await podsService.createPost(podId, data);
      set((state) => ({
        posts: [post, ...state.posts],
        loading: false,
      }));
      return post;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to create post',
        loading: false,
      });
      throw error;
    }
  },

  fetchPosts: async (podId, skip = 0, limit = 50) => {
    set({ loading: true, error: null });
    try {
      const posts = await podsService.getPosts(podId, skip, limit);
      set({ posts, loading: false });
      return posts;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch posts',
        loading: false,
      });
      throw error;
    }
  },

  updatePost: async (podId, postId, data) => {
    set({ loading: true, error: null });
    try {
      const post = await podsService.updatePost(podId, postId, data);
      set((state) => ({
        posts: state.posts.map((p) => (p.id === postId ? post : p)),
        loading: false,
      }));
      return post;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to update post',
        loading: false,
      });
      throw error;
    }
  },

  deletePost: async (podId, postId) => {
    set({ loading: true, error: null });
    try {
      await podsService.deletePost(podId, postId);
      set((state) => ({
        posts: state.posts.filter((p) => p.id !== postId),
        loading: false,
      }));
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to delete post',
        loading: false,
      });
      throw error;
    }
  },

  pinPost: async (podId, postId, isPinned) => {
    set({ loading: true, error: null });
    try {
      const post = await podsService.pinPost(podId, postId, isPinned);
      set((state) => ({
        posts: state.posts.map((p) => (p.id === postId ? post : p)),
        loading: false,
      }));
      return post;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to pin post',
        loading: false,
      });
      throw error;
    }
  },

  // Utility
  clearError: () => set({ error: null }),
  clearCurrent: () => set({ currentPod: null, members: [], checkIns: [], sosses: [], posts: [], wellnessAlerts: [] }),
}));

export { usePodsStore };
export default usePodsStore;

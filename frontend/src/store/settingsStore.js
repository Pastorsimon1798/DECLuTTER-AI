import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * Settings Store - User preferences (units, etc.)
 */

export const useSettingsStore = create(
  persist(
    (set, get) => ({
      // Unit system: 'metric' or 'imperial'
      unitSystem: 'metric', // Default to metric

      // Set unit system
      setUnitSystem: (system) => {
        if (system === 'metric' || system === 'imperial') {
          set({ unitSystem: system });
        }
      },

      // Toggle between metric and imperial
      toggleUnitSystem: () => {
        const current = get().unitSystem;
        set({ unitSystem: current === 'metric' ? 'imperial' : 'metric' });
      },
    }),
    {
      name: 'settings-storage', // localStorage key
    }
  )
);


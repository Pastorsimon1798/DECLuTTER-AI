import { useState } from 'react';
import { useSettingsStore } from '../store/settingsStore';
import { Ruler } from 'lucide-react';

/**
 * Unit Selector Component
 * Allows users to switch between metric and imperial units
 */
export default function UnitSelector({ variant = 'dropdown' }) {
  const { unitSystem, setUnitSystem } = useSettingsStore();
  const [isOpen, setIsOpen] = useState(false);

  const changeUnitSystem = (system) => {
    setUnitSystem(system);
    setIsOpen(false);
  };

  if (variant === 'inline') {
    // Inline buttons (good for settings pages)
    return (
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          <Ruler className="inline mr-2" size={16} />
          Units / Unidades
        </label>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => changeUnitSystem('metric')}
            className={`px-4 py-2 rounded-lg border transition-colors ${
              unitSystem === 'metric'
                ? 'bg-blue-600 text-white border-blue-600'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
          >
            Metric (km, m)
          </button>
          <button
            onClick={() => changeUnitSystem('imperial')}
            className={`px-4 py-2 rounded-lg border transition-colors ${
              unitSystem === 'imperial'
                ? 'bg-blue-600 text-white border-blue-600'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
          >
            Imperial (mi, ft)
          </button>
        </div>
      </div>
    );
  }

  // Dropdown variant (default, good for navigation bars)
  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
        aria-label="Select unit system"
        title={unitSystem === 'metric' ? 'Metric (km, m)' : 'Imperial (mi, ft)'}
      >
        <Ruler size={20} />
        <span className="hidden md:inline text-sm">
          {unitSystem === 'metric' ? 'km' : 'mi'}
        </span>
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown menu */}
          <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-20">
            <div className="py-1">
              <button
                onClick={() => changeUnitSystem('metric')}
                className={`w-full text-left px-4 py-2 transition-colors ${
                  unitSystem === 'metric'
                    ? 'bg-blue-50 text-blue-700 font-medium'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span>Metric (km, m)</span>
                  {unitSystem === 'metric' && (
                    <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </div>
                <div className="text-xs text-gray-500">Kilometers, meters</div>
              </button>
              <button
                onClick={() => changeUnitSystem('imperial')}
                className={`w-full text-left px-4 py-2 transition-colors ${
                  unitSystem === 'imperial'
                    ? 'bg-blue-50 text-blue-700 font-medium'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span>Imperial (mi, ft)</span>
                  {unitSystem === 'imperial' && (
                    <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </div>
                <div className="text-xs text-gray-500">Miles, feet</div>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}


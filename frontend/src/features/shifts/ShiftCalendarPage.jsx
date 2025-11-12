import { useState, useEffect, useMemo } from 'react';
import { Calendar, momentLocalizer } from 'react-big-calendar';
import moment from 'moment';
import { useNavigate } from 'react-router-dom';
import { useShiftsStore } from '../../store/shiftsStore';
import { Calendar as CalendarIcon, Filter, Plus } from 'lucide-react';

const localizer = momentLocalizer(moment);

export default function ShiftCalendarPage() {
  const navigate = useNavigate();
  const {
    shifts,
    organizations,
    filters,
    loading,
    error,
    fetchShifts,
    fetchOrganizations,
    setFilters,
    clearFilters,
  } = useShiftsStore();

  const [view, setView] = useState('month');
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchShifts();
    fetchOrganizations();
  }, []);

  // Convert shifts to calendar events
  const events = useMemo(() => {
    return shifts.map((shift) => ({
      id: shift.id,
      title: `${shift.name} (${shift.filled_count}/${shift.capacity})`,
      start: new Date(shift.start_time),
      end: new Date(shift.end_time),
      resource: shift,
    }));
  }, [shifts]);

  const handleSelectEvent = (event) => {
    navigate(`/shifts/${event.id}`);
  };

  const handleFilterChange = (field, value) => {
    setFilters({ [field]: value });
  };

  const applyFilters = () => {
    fetchShifts();
    setShowFilters(false);
  };

  const handleClearFilters = () => {
    clearFilters();
    fetchShifts();
  };

  // Custom event style based on shift status
  const eventStyleGetter = (event) => {
    const shift = event.resource;
    let backgroundColor = '#3174ad';

    if (shift.is_full) {
      backgroundColor = '#9ca3af'; // Gray for full
    } else if (shift.status === 'cancelled') {
      backgroundColor = '#ef4444'; // Red for cancelled
    } else if (shift.available_spots <= 2) {
      backgroundColor = '#f59e0b'; // Orange for almost full
    } else {
      backgroundColor = '#10b981'; // Green for available
    }

    return {
      style: {
        backgroundColor,
        borderRadius: '4px',
        opacity: 0.8,
        color: 'white',
        border: '0px',
        display: 'block',
      },
    };
  };

  if (loading && shifts.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Loading shifts...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
              <CalendarIcon size={32} />
              Volunteer Shifts
            </h1>
            <p className="text-gray-600 mt-1">
              Browse and sign up for volunteer opportunities
            </p>
          </div>
          <button
            onClick={() => navigate('/shifts/create')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus size={20} />
            Create Shift
          </button>
        </div>

        {/* Filters Bar */}
        <div className="flex gap-2 items-center mb-4">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <Filter size={16} />
            Filters
          </button>

          {filters.available_only && (
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
              Available only
            </span>
          )}
          {filters.organization_id && (
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
              Organization filtered
            </span>
          )}

          {(filters.available_only || filters.organization_id) && (
            <button
              onClick={handleClearFilters}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Clear all
            </button>
          )}
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Organization
                </label>
                <select
                  value={filters.organization_id || ''}
                  onChange={(e) => handleFilterChange('organization_id', e.target.value || null)}
                  className="w-full border-gray-300 rounded-lg"
                >
                  <option value="">All Organizations</option>
                  {organizations.map((org) => (
                    <option key={org.id} value={org.id}>
                      {org.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Status
                </label>
                <select
                  value={filters.status || ''}
                  onChange={(e) => handleFilterChange('status', e.target.value || null)}
                  className="w-full border-gray-300 rounded-lg"
                >
                  <option value="">All Statuses</option>
                  <option value="open">Open</option>
                  <option value="full">Full</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>

              <div className="flex items-end">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.available_only}
                    onChange={(e) => handleFilterChange('available_only', e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Show available only
                  </span>
                </label>
              </div>
            </div>

            <div className="mt-4 flex gap-2">
              <button
                onClick={applyFilters}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Apply Filters
              </button>
              <button
                onClick={() => setShowFilters(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="flex flex-wrap gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#10b981' }}></div>
            <span>Available</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#f59e0b' }}></div>
            <span>Almost Full</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#9ca3af' }}></div>
            <span>Full</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#ef4444' }}></div>
            <span>Cancelled</span>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          {error}
        </div>
      )}

      {/* Calendar */}
      <div className="bg-white rounded-lg shadow p-4" style={{ height: '600px' }}>
        <Calendar
          localizer={localizer}
          events={events}
          startAccessor="start"
          endAccessor="end"
          view={view}
          onView={setView}
          onSelectEvent={handleSelectEvent}
          eventPropGetter={eventStyleGetter}
          popup
          style={{ height: '100%' }}
          views={['month', 'week', 'day', 'agenda']}
        />
      </div>
    </div>
  );
}

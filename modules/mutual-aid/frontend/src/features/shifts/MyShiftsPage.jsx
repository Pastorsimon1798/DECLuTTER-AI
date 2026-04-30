import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useShiftsStore } from '../../store/shiftsStore';
import { Calendar, Clock, MapPin, Building, X, CheckCircle } from 'lucide-react';
import { format, isPast, isFuture } from 'date-fns';

export default function MyShiftsPage() {
  const navigate = useNavigate();
  const { myShifts, loading, error, fetchMyShifts, cancelSignup } = useShiftsStore();

  const [filter, setFilter] = useState('upcoming'); // 'upcoming', 'past', 'all'
  const [cancelling, setCancelling] = useState(null);

  useEffect(() => {
    loadShifts();
  }, [filter]);

  const loadShifts = () => {
    const filters = {};
    if (filter === 'upcoming') {
      filters.upcoming_only = true;
    }
    fetchMyShifts(filters);
  };

  const handleCancelSignup = async (signup) => {
    if (!confirm(`Are you sure you want to cancel your signup for "${signup.shift.name}"?`)) {
      return;
    }

    setCancelling(signup.id);
    try {
      await cancelSignup(signup.id, signup.shift_id);
      loadShifts();
    } catch (error) {
      alert('Failed to cancel signup');
    } finally {
      setCancelling(null);
    }
  };

  const filteredShifts = myShifts.filter((signup) => {
    const shiftDate = new Date(signup.shift.start_time);

    if (filter === 'upcoming') {
      return isFuture(shiftDate) && signup.status === 'confirmed';
    } else if (filter === 'past') {
      return isPast(shiftDate) || signup.status !== 'confirmed';
    }
    return true;
  });

  if (loading && myShifts.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Loading your shifts...</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">My Volunteer Shifts</h1>
        <p className="text-gray-600">Manage your shift signups and view your volunteer history</p>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-200">
        <button
          onClick={() => setFilter('upcoming')}
          className={`px-4 py-2 border-b-2 ${
            filter === 'upcoming'
              ? 'border-blue-600 text-blue-600 font-medium'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Upcoming ({myShifts.filter(s => isFuture(new Date(s.shift.start_time)) && s.status === 'confirmed').length})
        </button>
        <button
          onClick={() => setFilter('past')}
          className={`px-4 py-2 border-b-2 ${
            filter === 'past'
              ? 'border-blue-600 text-blue-600 font-medium'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Past
        </button>
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 border-b-2 ${
            filter === 'all'
              ? 'border-blue-600 text-blue-600 font-medium'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          All
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          {error}
        </div>
      )}

      {/* Shifts List */}
      {filteredShifts.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-600 mb-4">
            {filter === 'upcoming'
              ? 'You have no upcoming shifts.'
              : filter === 'past'
              ? 'No past shifts found.'
              : 'You have not signed up for any shifts yet.'}
          </p>
          <button
            onClick={() => navigate('/shifts')}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Browse Shifts
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredShifts.map((signup) => {
            const shift = signup.shift;
            const startTime = new Date(shift.start_time);
            const endTime = new Date(shift.end_time);
            const isUpcoming = isFuture(startTime) && signup.status === 'confirmed';

            return (
              <div
                key={signup.id}
                className="bg-white rounded-lg shadow hover:shadow-md transition-shadow"
              >
                <div className="p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex-1">
                      <h3 className="text-xl font-semibold text-gray-900 mb-1">
                        {shift.name}
                      </h3>
                      <div className="flex items-center gap-2 text-gray-600">
                        <Building size={16} />
                        <span>{shift.organization?.name}</span>
                      </div>
                    </div>

                    {/* Status Badge */}
                    <div>
                      {signup.status === 'confirmed' && isUpcoming && (
                        <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                          <CheckCircle size={14} />
                          Confirmed
                        </span>
                      )}
                      {signup.status === 'cancelled' && (
                        <span className="inline-flex items-center gap-1 px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm">
                          <X size={14} />
                          Cancelled
                        </span>
                      )}
                      {signup.status === 'completed' && (
                        <span className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                          <CheckCircle size={14} />
                          Completed
                        </span>
                      )}
                      {signup.status === 'no_show' && (
                        <span className="inline-flex items-center gap-1 px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm">
                          <X size={14} />
                          No Show
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div className="flex items-center gap-2 text-gray-700">
                      <Calendar size={18} className="text-blue-600" />
                      <span>{format(startTime, 'EEEE, MMM d, yyyy')}</span>
                    </div>

                    <div className="flex items-center gap-2 text-gray-700">
                      <Clock size={18} className="text-blue-600" />
                      <span>
                        {format(startTime, 'h:mm a')} - {format(endTime, 'h:mm a')}
                      </span>
                    </div>

                    {shift.location && (
                      <div className="flex items-center gap-2 text-gray-700 md:col-span-2">
                        <MapPin size={18} className="text-blue-600" />
                        <span>{shift.location}</span>
                      </div>
                    )}
                  </div>

                  {signup.notes && (
                    <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                      <div className="text-sm font-medium text-gray-700 mb-1">Your Notes:</div>
                      <div className="text-sm text-gray-600">{signup.notes}</div>
                    </div>
                  )}

                  <div className="flex gap-3 pt-4 border-t">
                    <button
                      onClick={() => navigate(`/shifts/${shift.id}`)}
                      className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                    >
                      View Details
                    </button>

                    {isUpcoming && (
                      <button
                        onClick={() => handleCancelSignup(signup)}
                        disabled={cancelling === signup.id}
                        className="px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 disabled:opacity-50"
                      >
                        {cancelling === signup.id ? 'Cancelling...' : 'Cancel Signup'}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

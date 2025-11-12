import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useShiftsStore } from '../../store/shiftsStore';
import { useAuthStore } from '../../store/authStore';
import {
  Calendar,
  Clock,
  MapPin,
  Users,
  Building,
  ArrowLeft,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { format } from 'date-fns';

export default function ShiftDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { currentShift, loading, error, fetchShift, signupForShift, clearCurrent } = useShiftsStore();

  const [showSignupModal, setShowSignupModal] = useState(false);
  const [signupNotes, setSignupNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchShift(id);
    return () => clearCurrent();
  }, [id]);

  const handleSignup = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await signupForShift(id, signupNotes);
      setShowSignupModal(false);
      setSignupNotes('');
      alert('Successfully signed up for shift!');
      navigate('/shifts/my-shifts');
    } catch (error) {
      alert(error.message || 'Failed to sign up for shift');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading && !currentShift) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Loading shift details...</div>
      </div>
    );
  }

  if (error && !currentShift) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
          {error}
        </div>
        <button
          onClick={() => navigate('/shifts')}
          className="mt-4 text-blue-600 hover:underline"
        >
          ← Back to Shifts
        </button>
      </div>
    );
  }

  if (!currentShift) return null;

  const isAvailable = currentShift.status === 'open' && !currentShift.is_full;
  const startTime = new Date(currentShift.start_time);
  const endTime = new Date(currentShift.end_time);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back Button */}
      <button
        onClick={() => navigate('/shifts')}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft size={20} />
        Back to Calendar
      </button>

      {/* Shift Details Card */}
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-6 text-white">
          <h1 className="text-3xl font-bold mb-2">{currentShift.name}</h1>
          <div className="flex items-center gap-2">
            <Building size={20} />
            <span className="text-lg">{currentShift.organization?.name}</span>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Status Badge */}
          <div className="mb-6">
            {currentShift.is_full ? (
              <span className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-800 rounded-full">
                <XCircle size={16} />
                Full - No spots available
              </span>
            ) : currentShift.status === 'cancelled' ? (
              <span className="inline-flex items-center gap-2 px-4 py-2 bg-red-100 text-red-800 rounded-full">
                <XCircle size={16} />
                Cancelled
              </span>
            ) : (
              <span className="inline-flex items-center gap-2 px-4 py-2 bg-green-100 text-green-800 rounded-full">
                <CheckCircle size={16} />
                {currentShift.available_spots} spot(s) available
              </span>
            )}
          </div>

          {/* Shift Info Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="flex items-start gap-3">
              <Calendar className="text-blue-600 mt-1" size={24} />
              <div>
                <div className="font-medium text-gray-900">Date</div>
                <div className="text-gray-600">{format(startTime, 'EEEE, MMMM d, yyyy')}</div>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Clock className="text-blue-600 mt-1" size={24} />
              <div>
                <div className="font-medium text-gray-900">Time</div>
                <div className="text-gray-600">
                  {format(startTime, 'h:mm a')} - {format(endTime, 'h:mm a')}
                </div>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <MapPin className="text-blue-600 mt-1" size={24} />
              <div>
                <div className="font-medium text-gray-900">Location</div>
                <div className="text-gray-600">
                  {currentShift.location || currentShift.organization?.address || 'TBD'}
                </div>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Users className="text-blue-600 mt-1" size={24} />
              <div>
                <div className="font-medium text-gray-900">Volunteers</div>
                <div className="text-gray-600">
                  {currentShift.filled_count} / {currentShift.capacity} signed up
                </div>
              </div>
            </div>
          </div>

          {/* Description */}
          {currentShift.description && (
            <div className="mb-6">
              <h2 className="text-xl font-semibold mb-2">Description</h2>
              <p className="text-gray-700 whitespace-pre-wrap">{currentShift.description}</p>
            </div>
          )}

          {/* Sign Up Button */}
          {isAvailable && (
            <div className="border-t pt-6">
              <button
                onClick={() => setShowSignupModal(true)}
                className="w-full md:w-auto px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
              >
                Sign Up for This Shift
              </button>
            </div>
          )}

          {!isAvailable && currentShift.status === 'open' && (
            <div className="border-t pt-6 text-gray-600">
              This shift is currently full. Check back later for cancellations.
            </div>
          )}
        </div>
      </div>

      {/* Sign Up Modal */}
      {showSignupModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h2 className="text-2xl font-bold mb-4">Sign Up for Shift</h2>
            <form onSubmit={handleSignup}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Notes (optional)
                </label>
                <textarea
                  value={signupNotes}
                  onChange={(e) => setSignupNotes(e.target.value)}
                  placeholder="Any special requirements or notes..."
                  className="w-full border-gray-300 rounded-lg"
                  rows={4}
                />
              </div>

              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={submitting}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {submitting ? 'Signing up...' : 'Confirm Sign Up'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowSignupModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  disabled={submitting}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useShiftsStore } from '../../store/shiftsStore';
import { Calendar, ArrowLeft } from 'lucide-react';

export default function CreateShiftPage() {
  const navigate = useNavigate();
  const { organizations, loading, error, fetchOrganizations, createShift, clearError } = useShiftsStore();

  const [formData, setFormData] = useState({
    organization_id: '',
    name: '',
    description: '',
    location: '',
    start_time: '',
    end_time: '',
    capacity: 1,
    reminder_24h: true,
    reminder_2h: true,
  });

  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchOrganizations();
    return () => clearError();
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      // Validate dates
      const startTime = new Date(formData.start_time);
      const endTime = new Date(formData.end_time);

      if (endTime <= startTime) {
        alert('End time must be after start time');
        setSubmitting(false);
        return;
      }

      // Create shift
      const newShift = await createShift({
        ...formData,
        capacity: parseInt(formData.capacity),
      });

      alert('Shift created successfully!');
      navigate(`/shifts/${newShift.id}`);
    } catch (error) {
      alert(error.message || 'Failed to create shift');
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back Button */}
      <button
        onClick={() => navigate('/shifts')}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft size={20} />
        Back to Calendar
      </button>

      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2 mb-2">
          <Calendar size={32} />
          Create New Shift
        </h1>
        <p className="text-gray-600">Set up a new volunteer shift for your organization</p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          {error}
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-lg p-6 space-y-6">
        {/* Organization */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Organization <span className="text-red-500">*</span>
          </label>
          <select
            name="organization_id"
            value={formData.organization_id}
            onChange={handleChange}
            required
            className="w-full border-gray-300 rounded-lg"
          >
            <option value="">Select an organization...</option>
            {organizations.map((org) => (
              <option key={org.id} value={org.id}>
                {org.name}
              </option>
            ))}
          </select>
          <p className="mt-1 text-sm text-gray-500">
            Don't see your organization?{' '}
            <button
              type="button"
              onClick={() => navigate('/organizations/create')}
              className="text-blue-600 hover:underline"
            >
              Create one first
            </button>
          </p>
        </div>

        {/* Shift Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Shift Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            placeholder="e.g., Food Pantry Volunteer"
            className="w-full border-gray-300 rounded-lg"
          />
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Description
          </label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="What will volunteers be doing? Any special instructions?"
            className="w-full border-gray-300 rounded-lg"
            rows={4}
          />
        </div>

        {/* Location */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Location
          </label>
          <input
            type="text"
            name="location"
            value={formData.location}
            onChange={handleChange}
            placeholder="123 Main St, City, State"
            className="w-full border-gray-300 rounded-lg"
          />
        </div>

        {/* Date and Time */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Start Time <span className="text-red-500">*</span>
            </label>
            <input
              type="datetime-local"
              name="start_time"
              value={formData.start_time}
              onChange={handleChange}
              required
              className="w-full border-gray-300 rounded-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              End Time <span className="text-red-500">*</span>
            </label>
            <input
              type="datetime-local"
              name="end_time"
              value={formData.end_time}
              onChange={handleChange}
              required
              className="w-full border-gray-300 rounded-lg"
            />
          </div>
        </div>

        {/* Capacity */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Volunteer Capacity <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            name="capacity"
            value={formData.capacity}
            onChange={handleChange}
            required
            min="1"
            className="w-full border-gray-300 rounded-lg"
          />
          <p className="mt-1 text-sm text-gray-500">
            How many volunteers are needed for this shift?
          </p>
        </div>

        {/* Reminders */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Automated Reminders
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              name="reminder_24h"
              checked={formData.reminder_24h}
              onChange={handleChange}
              className="rounded border-gray-300"
            />
            <span className="text-sm text-gray-700">
              Send reminder 24 hours before shift
            </span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              name="reminder_2h"
              checked={formData.reminder_2h}
              onChange={handleChange}
              className="rounded border-gray-300"
            />
            <span className="text-sm text-gray-700">
              Send reminder 2 hours before shift
            </span>
          </label>
        </div>

        {/* Submit Buttons */}
        <div className="flex gap-3 pt-4 border-t">
          <button
            type="submit"
            disabled={submitting || loading}
            className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
          >
            {submitting ? 'Creating Shift...' : 'Create Shift'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/shifts')}
            disabled={submitting}
            className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

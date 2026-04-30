import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePodsStore } from '../../store/podsStore';
import { ArrowLeft, Users, Shield, Bell, AlertTriangle } from 'lucide-react';

export default function CreatePodPage() {
  const navigate = useNavigate();
  const { createPod, loading } = usePodsStore();

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    is_private: true,
    max_members: 20,
    check_in_frequency_days: 7,
    enable_wellness_alerts: true,
    missed_checkins_threshold: 2,
    enable_sos_broadcasts: true,
  });

  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : type === 'number' ? parseInt(value) : value,
    });
    // Clear error for this field
    if (errors[name]) {
      setErrors({ ...errors, [name]: null });
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.name.trim()) {
      newErrors.name = 'Pod name is required';
    }
    if (formData.max_members < 2 || formData.max_members > 100) {
      newErrors.max_members = 'Max members must be between 2 and 100';
    }
    if (formData.check_in_frequency_days < 1 || formData.check_in_frequency_days > 30) {
      newErrors.check_in_frequency_days = 'Check-in frequency must be between 1 and 30 days';
    }
    if (formData.missed_checkins_threshold < 1 || formData.missed_checkins_threshold > 10) {
      newErrors.missed_checkins_threshold = 'Missed check-ins threshold must be between 1 and 10';
    }
    return newErrors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const newErrors = validate();
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      const pod = await createPod(formData);
      navigate(`/pods/${pod.id}`);
    } catch (error) {
      setErrors({ submit: error.message || 'Failed to create pod' });
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Header */}
      <button
        onClick={() => navigate('/pods')}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft size={20} />
        Back to Pods
      </button>

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Create a Pod</h1>
        <p className="text-gray-600 mt-2">
          Set up a close-knit circle for mutual support and wellness
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-6">
        {/* Basic Information */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>

          {/* Name */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Pod Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="e.g., Downtown Neighbors"
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                errors.name ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
          </div>

          {/* Description */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Describe the purpose and focus of your pod..."
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Privacy & Capacity */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Shield size={20} />
            Privacy & Capacity
          </h2>

          {/* Privacy */}
          <div className="mb-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                name="is_private"
                checked={formData.is_private}
                onChange={handleChange}
                className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <div>
                <span className="font-medium text-gray-900">Private Pod</span>
                <p className="text-sm text-gray-600">
                  Members must be approved by admins to join
                </p>
              </div>
            </label>
          </div>

          {/* Max Members */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Maximum Members
            </label>
            <input
              type="number"
              name="max_members"
              value={formData.max_members}
              onChange={handleChange}
              min="2"
              max="100"
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                errors.max_members ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            <p className="text-sm text-gray-600 mt-1">
              Recommended: 5-20 members for close-knit circles
            </p>
            {errors.max_members && <p className="text-red-500 text-sm mt-1">{errors.max_members}</p>}
          </div>
        </div>

        {/* Wellness Settings */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Bell size={20} />
            Wellness Check-Ins
          </h2>

          {/* Check-in Frequency */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Check-in Frequency (days)
            </label>
            <input
              type="number"
              name="check_in_frequency_days"
              value={formData.check_in_frequency_days}
              onChange={handleChange}
              min="1"
              max="30"
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                errors.check_in_frequency_days ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            <p className="text-sm text-gray-600 mt-1">
              How often members are expected to check in
            </p>
            {errors.check_in_frequency_days && (
              <p className="text-red-500 text-sm mt-1">{errors.check_in_frequency_days}</p>
            )}
          </div>

          {/* Enable Wellness Alerts */}
          <div className="mb-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                name="enable_wellness_alerts"
                checked={formData.enable_wellness_alerts}
                onChange={handleChange}
                className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <div>
                <span className="font-medium text-gray-900">Enable Wellness Alerts</span>
                <p className="text-sm text-gray-600">
                  Admins receive alerts when members miss check-ins
                </p>
              </div>
            </label>
          </div>

          {/* Missed Check-ins Threshold */}
          {formData.enable_wellness_alerts && (
            <div className="mb-4 ml-8">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Alert after missed check-ins
              </label>
              <input
                type="number"
                name="missed_checkins_threshold"
                value={formData.missed_checkins_threshold}
                onChange={handleChange}
                min="1"
                max="10"
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                  errors.missed_checkins_threshold ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              <p className="text-sm text-gray-600 mt-1">
                Number of consecutive missed check-ins before triggering an alert
              </p>
              {errors.missed_checkins_threshold && (
                <p className="text-red-500 text-sm mt-1">{errors.missed_checkins_threshold}</p>
              )}
            </div>
          )}
        </div>

        {/* Emergency Settings */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertTriangle size={20} />
            Emergency Features
          </h2>

          <div className="mb-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                name="enable_sos_broadcasts"
                checked={formData.enable_sos_broadcasts}
                onChange={handleChange}
                className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <div>
                <span className="font-medium text-gray-900">Enable SOS Broadcasts</span>
                <p className="text-sm text-gray-600">
                  Members can send emergency alerts to the entire pod
                </p>
              </div>
            </label>
          </div>
        </div>

        {/* Submit Error */}
        {errors.submit && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {errors.submit}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-4 pt-4">
          <button
            type="button"
            onClick={() => navigate('/pods')}
            className="flex-1 px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? 'Creating...' : 'Create Pod'}
          </button>
        </div>
      </form>
    </div>
  );
}

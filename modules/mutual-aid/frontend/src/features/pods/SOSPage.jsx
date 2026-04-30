import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { usePodsStore } from '../../store/podsStore';
import { ArrowLeft, AlertTriangle, MapPin, Bell } from 'lucide-react';

export default function SOSPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { sendSOS, loading } = usePodsStore();

  const [formData, setFormData] = useState({
    message: '',
    urgency: 'high',
    location: '',
  });

  const [errors, setErrors] = useState({});
  const [showConfirm, setShowConfirm] = useState(false);

  const urgencyOptions = [
    {
      value: 'high',
      label: 'High Priority',
      description: 'Need help soon (within hours)',
      icon: '⚠️',
      color: 'orange',
      bgColor: 'bg-orange-50',
      borderColor: 'border-orange-200',
      textColor: 'text-orange-700',
      selectedBorder: 'border-orange-500',
    },
    {
      value: 'critical',
      label: 'Critical / Urgent',
      description: 'Need immediate assistance (right now)',
      icon: '🚨',
      color: 'red',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      textColor: 'text-red-700',
      selectedBorder: 'border-red-500',
    },
  ];

  const validate = () => {
    const newErrors = {};
    if (!formData.message.trim()) {
      newErrors.message = 'Please describe what you need help with';
    }
    if (formData.message.trim().length < 10) {
      newErrors.message = 'Please provide more details (at least 10 characters)';
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

    // Show confirmation dialog
    setShowConfirm(true);
  };

  const handleConfirm = async () => {
    try {
      await sendSOS(id, formData);
      navigate(`/pods/${id}`, {
        state: { message: 'SOS broadcast sent to all pod members!' },
      });
    } catch (error) {
      setErrors({ submit: error.message || 'Failed to send SOS broadcast' });
      setShowConfirm(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Header */}
      <button
        onClick={() => navigate(`/pods/${id}`)}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft size={20} />
        Back to Pod
      </button>

      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <AlertTriangle size={32} className="text-red-600" />
          <h1 className="text-3xl font-bold text-gray-900">Send SOS Broadcast</h1>
        </div>
        <p className="text-gray-600">
          Alert all pod members that you need assistance. Use this when you need urgent help from your community.
        </p>
      </div>

      {/* Emergency Notice */}
      <div className="bg-red-50 border-2 border-red-300 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <AlertTriangle size={24} className="text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-900 mb-2">For Life-Threatening Emergencies</h3>
            <p className="text-red-800 text-sm mb-3">
              If this is a medical emergency, fire, or you're in immediate danger, call 911 or your local
              emergency services first, then send the SOS.
            </p>
            <div className="space-y-1 text-sm text-red-800">
              <p><strong>Emergency Services:</strong> 911</p>
              <p><strong>Crisis Text Line:</strong> Text HOME to 741741</p>
              <p><strong>National Suicide Prevention Lifeline:</strong> 1-800-273-8255</p>
            </div>
          </div>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-6">
        {/* Urgency Level */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Urgency Level <span className="text-red-500">*</span>
          </label>
          <div className="space-y-3">
            {urgencyOptions.map((option) => {
              const isSelected = formData.urgency === option.value;

              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setFormData({ ...formData, urgency: option.value })}
                  className={`w-full p-4 rounded-lg border-2 transition-all ${
                    isSelected
                      ? `${option.bgColor} ${option.selectedBorder}`
                      : `bg-white ${option.borderColor} hover:${option.bgColor}`
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <div className="text-3xl">{option.icon}</div>
                    <div className="text-left flex-1">
                      <div className="font-semibold text-gray-900">{option.label}</div>
                      <div className="text-sm text-gray-600">{option.description}</div>
                    </div>
                    {isSelected && (
                      <div className="flex-shrink-0">
                        <div className={`w-6 h-6 rounded-full ${option.textColor} flex items-center justify-center`}>
                          ✓
                        </div>
                      </div>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Message */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            What do you need help with? <span className="text-red-500">*</span>
          </label>
          <textarea
            name="message"
            value={formData.message}
            onChange={(e) => {
              setFormData({ ...formData, message: e.target.value });
              if (errors.message) setErrors({ ...errors, message: null });
            }}
            placeholder="Be specific about what kind of help you need. Examples:&#10;- Need a ride to the hospital&#10;- Out of medication and need assistance&#10;- Stuck at home and need groceries&#10;- Feeling unsafe and need someone to call me"
            rows={6}
            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-red-500 ${
              errors.message ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.message && <p className="text-red-500 text-sm mt-1">{errors.message}</p>}
          <p className="text-sm text-gray-600 mt-2">
            💡 Be clear and specific so pod members know exactly how to help.
          </p>
        </div>

        {/* Location */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
            <MapPin size={16} />
            Location (Optional)
          </label>
          <input
            type="text"
            name="location"
            value={formData.location}
            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            placeholder="e.g., 123 Main St, Apt 4B or general area"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500"
          />
          <p className="text-sm text-gray-600 mt-2">
            Share your location if it's relevant for the help you need. You can be as specific or general
            as you're comfortable with.
          </p>
        </div>

        {/* Who Will Be Notified */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Bell size={20} className="text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-blue-800">
              <p className="font-medium mb-1">Who will be notified?</p>
              <p>
                <strong>All active members</strong> of your pod will receive this SOS broadcast. This helps
                ensure someone can respond quickly to your request for help.
              </p>
            </div>
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
            onClick={() => navigate(`/pods/${id}`)}
            className="flex-1 px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="flex-1 px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <AlertTriangle size={18} />
            {loading ? 'Sending...' : 'Send SOS Broadcast'}
          </button>
        </div>
      </form>

      {/* Confirmation Modal */}
      {showConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle size={24} className="text-red-600" />
              <h3 className="text-xl font-bold text-gray-900">Confirm SOS Broadcast</h3>
            </div>

            <p className="text-gray-700 mb-4">
              You're about to send an <strong className="text-red-600">{formData.urgency}</strong> priority
              SOS to all pod members with the following message:
            </p>

            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <p className="text-gray-900 whitespace-pre-wrap">{formData.message}</p>
              {formData.location && (
                <p className="text-gray-600 mt-2 flex items-center gap-1">
                  <MapPin size={14} />
                  {formData.location}
                </p>
              )}
            </div>

            <p className="text-sm text-gray-600 mb-6">
              All active pod members will be notified. Are you sure you want to proceed?
            </p>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setShowConfirm(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                disabled={loading}
              >
                Go Back
              </button>
              <button
                type="button"
                onClick={handleConfirm}
                disabled={loading}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400"
              >
                {loading ? 'Sending...' : 'Yes, Send SOS'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

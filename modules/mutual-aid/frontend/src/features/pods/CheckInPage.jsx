import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { usePodsStore } from '../../store/podsStore';
import { ArrowLeft, Heart, AlertCircle, AlertTriangle, Smile } from 'lucide-react';

export default function CheckInPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { submitCheckIn, loading } = usePodsStore();

  const [formData, setFormData] = useState({
    status: 'doing_well',
    message: '',
    is_private: false,
  });

  const [errors, setErrors] = useState({});

  const statusOptions = [
    {
      value: 'doing_well',
      label: 'Doing Well',
      description: 'Everything is fine, feeling good',
      icon: Smile,
      color: 'green',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      textColor: 'text-green-700',
      selectedBorder: 'border-green-500',
    },
    {
      value: 'need_support',
      label: 'Need Support',
      description: 'Could use some help or company',
      icon: AlertCircle,
      color: 'yellow',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      textColor: 'text-yellow-700',
      selectedBorder: 'border-yellow-500',
    },
    {
      value: 'emergency',
      label: 'Emergency',
      description: 'Need urgent assistance',
      icon: AlertTriangle,
      color: 'red',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      textColor: 'text-red-700',
      selectedBorder: 'border-red-500',
    },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate
    const newErrors = {};
    if (formData.status === 'emergency' && !formData.message.trim()) {
      newErrors.message = 'Please provide details for emergency check-in';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      await submitCheckIn(id, formData);
      navigate(`/pods/${id}`);
    } catch (error) {
      setErrors({ submit: error.message || 'Failed to submit check-in' });
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
          <Heart size={32} className="text-green-600" />
          <h1 className="text-3xl font-bold text-gray-900">Wellness Check-In</h1>
        </div>
        <p className="text-gray-600">
          Let your pod know how you're doing. Regular check-ins help maintain connection and community care.
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-6">
        {/* Status Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            How are you doing? <span className="text-red-500">*</span>
          </label>
          <div className="space-y-3">
            {statusOptions.map((option) => {
              const Icon = option.icon;
              const isSelected = formData.status === option.value;

              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setFormData({ ...formData, status: option.value })}
                  className={`w-full p-4 rounded-lg border-2 transition-all ${
                    isSelected
                      ? `${option.bgColor} ${option.selectedBorder}`
                      : `bg-white ${option.borderColor} hover:${option.bgColor}`
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <div className={`p-3 rounded-full ${option.bgColor}`}>
                      <Icon size={24} className={option.textColor} />
                    </div>
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
            Message {formData.status === 'emergency' && <span className="text-red-500">*</span>}
          </label>
          <textarea
            name="message"
            value={formData.message}
            onChange={(e) => setFormData({ ...formData, message: e.target.value })}
            placeholder={
              formData.status === 'doing_well'
                ? "Share something positive (optional)..."
                : formData.status === 'need_support'
                ? "Let us know what kind of support would help..."
                : "Please describe the emergency situation..."
            }
            rows={5}
            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
              errors.message ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.message && <p className="text-red-500 text-sm mt-1">{errors.message}</p>}

          {formData.status === 'emergency' && (
            <p className="text-sm text-red-600 mt-2">
              💡 For life-threatening emergencies, please call 911 or your local emergency services immediately.
            </p>
          )}

          {formData.status === 'need_support' && (
            <p className="text-sm text-yellow-600 mt-2">
              💡 Be specific about what would help - company, groceries, a phone call, etc.
            </p>
          )}
        </div>

        {/* Privacy Toggle */}
        <div className="bg-gray-50 rounded-lg p-4">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              name="is_private"
              checked={formData.is_private}
              onChange={(e) => setFormData({ ...formData, is_private: e.target.checked })}
              className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 mt-0.5"
            />
            <div className="flex-1">
              <span className="font-medium text-gray-900">Private check-in (admin only)</span>
              <p className="text-sm text-gray-600 mt-1">
                Only pod admins will see this check-in. Use this if you need admin support but don't want
                to share with all members.
              </p>
            </div>
          </label>
        </div>

        {/* Info Box */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Heart size={20} className="text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-blue-800">
              <p className="font-medium mb-1">Why check in?</p>
              <ul className="list-disc list-inside space-y-1">
                <li>Maintains connection with your pod members</li>
                <li>Helps identify when members need support</li>
                <li>Builds trust and community care</li>
                <li>Resets your missed check-in counter</li>
              </ul>
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
            className={`flex-1 px-6 py-3 rounded-lg text-white ${
              formData.status === 'doing_well'
                ? 'bg-green-600 hover:bg-green-700'
                : formData.status === 'need_support'
                ? 'bg-yellow-600 hover:bg-yellow-700'
                : 'bg-red-600 hover:bg-red-700'
            } disabled:bg-gray-400 disabled:cursor-not-allowed`}
          >
            {loading ? 'Submitting...' : 'Submit Check-In'}
          </button>
        </div>
      </form>

      {/* Additional Help */}
      {formData.status === 'emergency' && (
        <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="font-semibold text-red-900 mb-3">Need Immediate Help?</h3>
          <div className="space-y-2 text-sm text-red-800">
            <p><strong>Emergency Services:</strong> 911</p>
            <p><strong>Crisis Text Line:</strong> Text HOME to 741741</p>
            <p><strong>National Suicide Prevention Lifeline:</strong> 1-800-273-8255</p>
            <p><strong>Domestic Violence Hotline:</strong> 1-800-799-7233</p>
          </div>
        </div>
      )}
    </div>
  );
}

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePodsStore } from '../../store/podsStore';
import { Users, Plus, Shield, Clock, AlertCircle } from 'lucide-react';

export default function PodsListPage() {
  const navigate = useNavigate();
  const { pods, loading, error, fetchPods } = usePodsStore();

  useEffect(() => {
    fetchPods();
  }, [fetchPods]);

  const getPodStatusColor = (pod) => {
    if (pod.my_role === 'admin') return 'bg-purple-100 text-purple-800';
    if (pod.my_role === 'member') return 'bg-blue-100 text-blue-800';
    return 'bg-gray-100 text-gray-800';
  };

  if (loading && pods.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">My Pods</h1>
            <p className="text-gray-600 mt-2">
              Close-knit circles for mutual support and wellness
            </p>
          </div>
          <button
            onClick={() => navigate('/pods/create')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus size={20} />
            Create Pod
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Pods List */}
      {pods.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Users size={48} className="mx-auto text-gray-400 mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            No pods yet
          </h3>
          <p className="text-gray-600 mb-6">
            Create or join a pod to start building your close-knit mutual aid circle
          </p>
          <button
            onClick={() => navigate('/pods/create')}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Create Your First Pod
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {pods.map((pod) => (
            <div
              key={pod.id}
              onClick={() => navigate(`/pods/${pod.id}`)}
              className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 cursor-pointer"
            >
              {/* Pod Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-gray-900 mb-1">
                    {pod.name}
                  </h3>
                  <span className={`inline-block px-2 py-1 text-xs rounded-full ${getPodStatusColor(pod)}`}>
                    {pod.my_role === 'admin' ? '👑 Admin' : '👤 Member'}
                  </span>
                </div>
                {pod.is_private && (
                  <Shield size={20} className="text-gray-400" title="Private Pod" />
                )}
              </div>

              {/* Pod Description */}
              {pod.description && (
                <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                  {pod.description}
                </p>
              )}

              {/* Pod Stats */}
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
                <div className="flex items-center gap-2 text-sm">
                  <Users size={16} className="text-gray-400" />
                  <span className="text-gray-600">
                    {pod.member_count} / {pod.max_members} members
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Clock size={16} className="text-gray-400" />
                  <span className="text-gray-600">
                    Check-in: {pod.check_in_frequency_days}d
                  </span>
                </div>
              </div>

              {/* Wellness Alerts */}
              {pod.enable_wellness_alerts && (
                <div className="mt-3 flex items-center gap-2 text-xs text-amber-600">
                  <AlertCircle size={14} />
                  <span>Wellness monitoring enabled</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Info Card */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 mb-2">What are Pods?</h3>
        <p className="text-blue-800 text-sm">
          Pods are small, close-knit circles (typically 5-20 people) for mutual support.
          Members can check in on each other's wellness, share resources internally, send
          emergency SOS broadcasts, and build stronger community bonds.
        </p>
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { usePodsStore } from '../../store/podsStore';
import {
  ArrowLeft,
  Users,
  Heart,
  AlertTriangle,
  MessageSquare,
  Settings,
  UserPlus,
  Bell,
  Calendar,
  Shield,
  Lock,
  Globe,
} from 'lucide-react';

export default function PodDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const {
    currentPod,
    members,
    checkIns,
    sosses,
    posts,
    loading,
    error,
    fetchPod,
    fetchMembers,
    fetchCheckIns,
    fetchSOSBroadcasts,
    fetchPosts,
  } = usePodsStore();

  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (id) {
      fetchPod(id);
      fetchMembers(id);
      fetchCheckIns(id);
      fetchSOSBroadcasts(id);
      fetchPosts(id);
    }
  }, [id, fetchPod, fetchMembers, fetchCheckIns, fetchSOSBroadcasts, fetchPosts]);

  if (loading && !currentPod) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      </div>
    );
  }

  if (!currentPod) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="text-center text-gray-600">Pod not found</div>
      </div>
    );
  }

  const isAdmin = currentPod.my_role === 'admin';
  const activeSOSCount = sosses.filter((sos) => !sos.is_resolved).length;
  const recentCheckIns = checkIns.slice(0, 5);
  const activePosts = posts.filter((post) => post.is_pinned).concat(
    posts.filter((post) => !post.is_pinned)
  );

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Users },
    { id: 'members', label: 'Members', icon: Users, badge: members.length },
    { id: 'checkins', label: 'Check-ins', icon: Heart, badge: checkIns.length },
    { id: 'sos', label: 'SOS', icon: AlertTriangle, badge: activeSOSCount, urgent: activeSOSCount > 0 },
    { id: 'posts', label: 'Posts', icon: MessageSquare, badge: posts.length },
    ...(isAdmin ? [{ id: 'settings', label: 'Settings', icon: Settings }] : []),
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <button
        onClick={() => navigate('/pods')}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft size={20} />
        Back to Pods
      </button>

      {/* Pod Header */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold text-gray-900">{currentPod.name}</h1>
              {currentPod.is_private ? (
                <span className="flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                  <Lock size={14} />
                  Private
                </span>
              ) : (
                <span className="flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                  <Globe size={14} />
                  Public
                </span>
              )}
              {isAdmin && (
                <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">
                  👑 Admin
                </span>
              )}
            </div>
            {currentPod.description && (
              <p className="text-gray-600">{currentPod.description}</p>
            )}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-gray-600 mb-1">
              <Users size={16} />
              <span className="text-sm">Members</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {currentPod.member_count} / {currentPod.max_members}
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-gray-600 mb-1">
              <Calendar size={16} />
              <span className="text-sm">Check-in Frequency</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {currentPod.check_in_frequency_days}d
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-gray-600 mb-1">
              <Heart size={16} />
              <span className="text-sm">Recent Check-ins</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">{checkIns.length}</div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-gray-600 mb-1">
              <AlertTriangle size={16} />
              <span className="text-sm">Active SOS</span>
            </div>
            <div className={`text-2xl font-bold ${activeSOSCount > 0 ? 'text-red-600' : 'text-gray-900'}`}>
              {activeSOSCount}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex gap-3 mt-6">
          <button
            onClick={() => navigate(`/pods/${id}/check-in`)}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <Heart size={18} />
            Check In
          </button>
          {currentPod.enable_sos_broadcasts && (
            <button
              onClick={() => navigate(`/pods/${id}/sos`)}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              <AlertTriangle size={18} />
              Send SOS
            </button>
          )}
          <button
            onClick={() => navigate(`/pods/${id}/posts/new`)}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <MessageSquare size={18} />
            New Post
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow">
        {/* Tab Navigation */}
        <div className="border-b border-gray-200">
          <div className="flex overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-6 py-4 border-b-2 transition-colors whitespace-nowrap ${
                    activeTab === tab.id
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
                  }`}
                >
                  <Icon size={18} />
                  <span>{tab.label}</span>
                  {tab.badge !== undefined && (
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs ${
                        tab.urgent
                          ? 'bg-red-100 text-red-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {tab.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'overview' && (
            <OverviewTab
              pod={currentPod}
              members={members}
              recentCheckIns={recentCheckIns}
              activeSOS={sosses.filter((sos) => !sos.is_resolved)}
              recentPosts={activePosts.slice(0, 3)}
            />
          )}

          {activeTab === 'members' && (
            <MembersTab members={members} podId={id} isAdmin={isAdmin} />
          )}

          {activeTab === 'checkins' && (
            <CheckInsTab checkIns={checkIns} podId={id} />
          )}

          {activeTab === 'sos' && (
            <SOSTab sosses={sosses} podId={id} />
          )}

          {activeTab === 'posts' && (
            <PostsTab posts={activePosts} podId={id} isAdmin={isAdmin} />
          )}

          {activeTab === 'settings' && isAdmin && (
            <SettingsTab pod={currentPod} />
          )}
        </div>
      </div>
    </div>
  );
}

// Overview Tab Component
function OverviewTab({ pod, members, recentCheckIns, activeSOS, recentPosts }) {
  return (
    <div className="space-y-6">
      {/* Active SOS Alerts */}
      {activeSOS.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-700 font-semibold mb-2">
            <AlertTriangle size={20} />
            Active SOS Broadcasts ({activeSOS.length})
          </div>
          <div className="space-y-2">
            {activeSOS.map((sos) => (
              <div key={sos.id} className="bg-white rounded p-3">
                <div className="font-medium">{sos.message}</div>
                <div className="text-sm text-gray-600 mt-1">
                  {new Date(sos.created_at).toLocaleString()} - {sos.urgency}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Check-ins */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Recent Check-ins</h3>
        {recentCheckIns.length === 0 ? (
          <div className="text-center text-gray-500 py-8">No check-ins yet</div>
        ) : (
          <div className="space-y-2">
            {recentCheckIns.map((checkIn) => (
              <div key={checkIn.id} className="bg-gray-50 rounded-lg p-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${getCheckInColor(checkIn.status)}`}></div>
                  <div>
                    <div className="font-medium">{getCheckInLabel(checkIn.status)}</div>
                    {checkIn.message && !checkIn.is_private && (
                      <div className="text-sm text-gray-600">{checkIn.message}</div>
                    )}
                  </div>
                </div>
                <div className="text-sm text-gray-500">
                  {new Date(checkIn.created_at).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Posts */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Recent Posts</h3>
        {recentPosts.length === 0 ? (
          <div className="text-center text-gray-500 py-8">No posts yet</div>
        ) : (
          <div className="space-y-3">
            {recentPosts.map((post) => (
              <div key={post.id} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-semibold text-gray-900">{post.title}</h4>
                  {post.is_pinned && (
                    <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded">
                      Pinned
                    </span>
                  )}
                </div>
                <p className="text-gray-600 text-sm line-clamp-2">{post.content}</p>
                <div className="text-xs text-gray-500 mt-2">
                  {new Date(post.created_at).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pod Settings Summary */}
      <div className="bg-blue-50 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-3">Pod Configuration</h3>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="text-blue-700">Privacy:</span>{' '}
            <span className="text-blue-900 font-medium">
              {pod.is_private ? 'Private' : 'Public'}
            </span>
          </div>
          <div>
            <span className="text-blue-700">Max Members:</span>{' '}
            <span className="text-blue-900 font-medium">{pod.max_members}</span>
          </div>
          <div>
            <span className="text-blue-700">Check-in Frequency:</span>{' '}
            <span className="text-blue-900 font-medium">{pod.check_in_frequency_days} days</span>
          </div>
          <div>
            <span className="text-blue-700">Wellness Alerts:</span>{' '}
            <span className="text-blue-900 font-medium">
              {pod.enable_wellness_alerts ? 'Enabled' : 'Disabled'}
            </span>
          </div>
          <div>
            <span className="text-blue-700">SOS Broadcasts:</span>{' '}
            <span className="text-blue-900 font-medium">
              {pod.enable_sos_broadcasts ? 'Enabled' : 'Disabled'}
            </span>
          </div>
          {pod.enable_wellness_alerts && (
            <div>
              <span className="text-blue-700">Alert Threshold:</span>{' '}
              <span className="text-blue-900 font-medium">
                {pod.missed_checkins_threshold} missed
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Members Tab Component
function MembersTab({ members, podId, isAdmin }) {
  const navigate = useNavigate();

  return (
    <div className="space-y-4">
      {isAdmin && (
        <div className="flex justify-end">
          <button
            onClick={() => navigate(`/pods/${podId}/members/invite`)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <UserPlus size={18} />
            Invite Member
          </button>
        </div>
      )}

      {members.length === 0 ? (
        <div className="text-center text-gray-500 py-12">No members yet</div>
      ) : (
        <div className="grid gap-3">
          {members.map((member) => (
            <div
              key={member.id}
              className="bg-gray-50 rounded-lg p-4 flex items-center justify-between"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-semibold">
                  {member.user_id?.substring(0, 2).toUpperCase()}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">Member {member.user_id?.substring(0, 8)}</span>
                    {member.role === 'admin' && (
                      <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                        Admin
                      </span>
                    )}
                    <span
                      className={`text-xs px-2 py-0.5 rounded ${
                        member.status === 'active'
                          ? 'bg-green-100 text-green-700'
                          : member.status === 'pending'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {member.status}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    {member.last_check_in_at ? (
                      <>Last check-in: {new Date(member.last_check_in_at).toLocaleDateString()}</>
                    ) : (
                      'No check-ins yet'
                    )}
                    {member.consecutive_missed_checkins > 0 && (
                      <span className="text-orange-600 ml-2">
                        ⚠️ {member.consecutive_missed_checkins} missed
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="text-sm text-gray-500">
                Joined {new Date(member.joined_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Check-ins Tab Component
function CheckInsTab({ checkIns, podId }) {
  const navigate = useNavigate();

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button
          onClick={() => navigate(`/pods/${podId}/check-in`)}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
        >
          <Heart size={18} />
          Submit Check-in
        </button>
      </div>

      {checkIns.length === 0 ? (
        <div className="text-center text-gray-500 py-12">No check-ins yet</div>
      ) : (
        <div className="space-y-3">
          {checkIns.map((checkIn) => (
            <div key={checkIn.id} className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-3">
                  <div className={`w-4 h-4 rounded-full ${getCheckInColor(checkIn.status)}`}></div>
                  <div>
                    <div className="font-semibold text-gray-900">
                      {getCheckInLabel(checkIn.status)}
                    </div>
                    {checkIn.message && !checkIn.is_private && (
                      <p className="text-gray-600 mt-1">{checkIn.message}</p>
                    )}
                    {checkIn.is_private && (
                      <span className="text-xs text-gray-500 italic">Private (admin only)</span>
                    )}
                  </div>
                </div>
                <div className="text-sm text-gray-500">
                  {new Date(checkIn.created_at).toLocaleString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// SOS Tab Component
function SOSTab({ sosses, podId }) {
  const navigate = useNavigate();

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button
          onClick={() => navigate(`/pods/${podId}/sos`)}
          className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
        >
          <AlertTriangle size={18} />
          Send SOS
        </button>
      </div>

      {sosses.length === 0 ? (
        <div className="text-center text-gray-500 py-12">No SOS broadcasts</div>
      ) : (
        <div className="space-y-3">
          {sosses.map((sos) => (
            <div
              key={sos.id}
              className={`rounded-lg p-4 ${
                sos.is_resolved ? 'bg-gray-50' : 'bg-red-50 border border-red-200'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <AlertTriangle
                    size={20}
                    className={sos.is_resolved ? 'text-gray-400' : 'text-red-600'}
                  />
                  <span
                    className={`text-xs px-2 py-1 rounded ${
                      sos.urgency === 'critical'
                        ? 'bg-red-600 text-white'
                        : 'bg-orange-100 text-orange-700'
                    }`}
                  >
                    {sos.urgency}
                  </span>
                  {sos.is_resolved && (
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                      Resolved
                    </span>
                  )}
                </div>
                <div className="text-sm text-gray-500">
                  {new Date(sos.created_at).toLocaleString()}
                </div>
              </div>
              <p className={`${sos.is_resolved ? 'text-gray-600' : 'text-red-900 font-medium'}`}>
                {sos.message}
              </p>
              {sos.location && (
                <div className="text-sm text-gray-600 mt-2">📍 {sos.location}</div>
              )}
              {sos.is_resolved && sos.resolved_at && (
                <div className="text-sm text-gray-500 mt-2">
                  Resolved {new Date(sos.resolved_at).toLocaleString()}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Posts Tab Component
function PostsTab({ posts, podId, isAdmin }) {
  const navigate = useNavigate();

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button
          onClick={() => navigate(`/pods/${podId}/posts/new`)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <MessageSquare size={18} />
          New Post
        </button>
      </div>

      {posts.length === 0 ? (
        <div className="text-center text-gray-500 py-12">No posts yet</div>
      ) : (
        <div className="space-y-4">
          {posts.map((post) => (
            <div
              key={post.id}
              className={`rounded-lg p-4 ${
                post.is_pinned ? 'bg-yellow-50 border border-yellow-200' : 'bg-gray-50'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-gray-900">{post.title}</h3>
                    {post.is_pinned && (
                      <span className="text-xs bg-yellow-200 text-yellow-800 px-2 py-0.5 rounded">
                        📌 Pinned
                      </span>
                    )}
                    <span className="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded">
                      {post.post_type}
                    </span>
                  </div>
                  <p className="text-gray-700 whitespace-pre-wrap">{post.content}</p>
                </div>
              </div>
              <div className="flex items-center justify-between mt-3 text-sm text-gray-500">
                <div>{new Date(post.created_at).toLocaleString()}</div>
                {isAdmin && (
                  <button
                    onClick={() => navigate(`/pods/${podId}/posts/${post.id}/edit`)}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    Edit
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Settings Tab Component
function SettingsTab({ pod }) {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-center gap-2 text-yellow-700 mb-2">
          <Shield size={20} />
          <span className="font-semibold">Admin Settings</span>
        </div>
        <p className="text-yellow-700 text-sm">
          You have admin permissions for this pod. You can modify settings, manage members, and pin posts.
        </p>
      </div>

      <div className="space-y-4">
        <button
          onClick={() => navigate(`/pods/${pod.id}/edit`)}
          className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2"
        >
          <Settings size={18} />
          Edit Pod Settings
        </button>

        <button
          className="w-full px-4 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center justify-center gap-2"
          onClick={() => {
            if (confirm('Are you sure you want to delete this pod? This action cannot be undone.')) {
              // Handle delete
            }
          }}
        >
          Delete Pod
        </button>
      </div>
    </div>
  );
}

// Helper functions
function getCheckInColor(status) {
  switch (status) {
    case 'doing_well':
      return 'bg-green-500';
    case 'need_support':
      return 'bg-yellow-500';
    case 'emergency':
      return 'bg-red-500';
    default:
      return 'bg-gray-500';
  }
}

function getCheckInLabel(status) {
  switch (status) {
    case 'doing_well':
      return 'Doing Well';
    case 'need_support':
      return 'Need Support';
    case 'emergency':
      return 'Emergency';
    default:
      return status;
  }
}

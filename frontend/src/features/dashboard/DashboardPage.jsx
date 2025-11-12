import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { usePostsStore } from '../../store/postsStore'
import { useShiftsStore } from '../../store/shiftsStore'
import { Plus, MessageCircle, FileText, TrendingUp, MapPin, Calendar } from 'lucide-react'

export function DashboardPage() {
  const { user } = useAuthStore()
  const { myPosts, matches, getMyPosts, getMyMatches } = usePostsStore()
  const { myShifts, fetchMyShifts } = useShiftsStore()
  const [stats, setStats] = useState({
    activePosts: 0,
    pendingMatches: 0,
    completedMatches: 0,
    upcomingShifts: 0,
  })

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      const [postsData, matchesData] = await Promise.all([
        getMyPosts(),
        getMyMatches(),
        fetchMyShifts({ upcoming_only: true }),
      ])

      setStats({
        activePosts: postsData.filter(p => p.status === 'open').length,
        pendingMatches: matchesData.filter(m => m.status === 'pending').length,
        completedMatches: matchesData.filter(m => m.status === 'completed').length,
        upcomingShifts: myShifts.filter(s => s.status === 'confirmed').length,
      })
    } catch (err) {
      console.error('Failed to load dashboard data:', err)
    }
  }

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 18) return 'Good afternoon'
    return 'Good evening'
  }

  return (
    <div className="container py-6">
      {/* Welcome Section */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          {getGreeting()}, {user?.pseudonym}! 👋
        </h1>
        <p className="mt-2 text-gray-600">
          Welcome to your CommunityCircle dashboard
        </p>
      </div>

      {/* Quick Stats */}
      <div className="mb-8 grid gap-6 md:grid-cols-4">
        <div className="card bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-blue-600">Active Posts</p>
              <p className="mt-2 text-3xl font-bold text-blue-900">{stats.activePosts}</p>
            </div>
            <FileText className="text-blue-600" size={40} />
          </div>
          <Link
            to="/posts/my"
            className="mt-4 inline-flex items-center text-sm font-medium text-blue-700 hover:text-blue-900"
          >
            View all posts →
          </Link>
        </div>

        <div className="card bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-yellow-600">Pending Matches</p>
              <p className="mt-2 text-3xl font-bold text-yellow-900">{stats.pendingMatches}</p>
            </div>
            <MessageCircle className="text-yellow-600" size={40} />
          </div>
          <Link
            to="/matches"
            className="mt-4 inline-flex items-center text-sm font-medium text-yellow-700 hover:text-yellow-900"
          >
            View matches →
          </Link>
        </div>

        <div className="card bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-green-600">Completed</p>
              <p className="mt-2 text-3xl font-bold text-green-900">{stats.completedMatches}</p>
            </div>
            <TrendingUp className="text-green-600" size={40} />
          </div>
          <p className="mt-4 text-sm text-green-700">
            Great job helping your community!
          </p>
        </div>

        <div className="card bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-purple-600">Upcoming Shifts</p>
              <p className="mt-2 text-3xl font-bold text-purple-900">{stats.upcomingShifts}</p>
            </div>
            <Calendar className="text-purple-600" size={40} />
          </div>
          <Link
            to="/shifts/my-shifts"
            className="mt-4 inline-flex items-center text-sm font-medium text-purple-700 hover:text-purple-900"
          >
            View my shifts →
          </Link>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="mb-4 text-xl font-semibold text-gray-900">Quick Actions</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <Link
            to="/posts/create"
            className="card hover:shadow-md transition-shadow text-center p-6"
          >
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-primary-100">
              <Plus className="text-primary-600" size={24} />
            </div>
            <h3 className="font-semibold text-gray-900">Post Need/Offer</h3>
            <p className="mt-1 text-sm text-gray-600">
              Share what you need or can offer
            </p>
          </Link>

          <Link
            to="/posts"
            className="card hover:shadow-md transition-shadow text-center p-6"
          >
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100">
              <MapPin className="text-blue-600" size={24} />
            </div>
            <h3 className="font-semibold text-gray-900">Browse Posts</h3>
            <p className="mt-1 text-sm text-gray-600">
              Find needs and offers nearby
            </p>
          </Link>

          <Link
            to="/matches"
            className="card hover:shadow-md transition-shadow text-center p-6"
          >
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
              <MessageCircle className="text-green-600" size={24} />
            </div>
            <h3 className="font-semibold text-gray-900">My Matches</h3>
            <p className="mt-1 text-sm text-gray-600">
              View your connections
            </p>
          </Link>

          <Link
            to="/posts/my"
            className="card hover:shadow-md transition-shadow text-center p-6"
          >
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-purple-100">
              <FileText className="text-purple-600" size={24} />
            </div>
            <h3 className="font-semibold text-gray-900">My Posts</h3>
            <p className="mt-1 text-sm text-gray-600">
              Manage your posts
            </p>
          </Link>

          <Link
            to="/shifts"
            className="card hover:shadow-md transition-shadow text-center p-6"
          >
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100">
              <Calendar className="text-indigo-600" size={24} />
            </div>
            <h3 className="font-semibold text-gray-900">Browse Shifts</h3>
            <p className="mt-1 text-sm text-gray-600">
              Find volunteer opportunities
            </p>
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div>
        <h2 className="mb-4 text-xl font-semibold text-gray-900">Recent Activity</h2>
        <div className="card">
          {myPosts.length === 0 && matches.length === 0 ? (
            <div className="py-8 text-center text-gray-600">
              <p className="mb-2">No recent activity</p>
              <p className="text-sm text-gray-500">
                Start by posting a need or offer, or browse existing posts
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Recent posts */}
              {myPosts.slice(0, 3).map((post) => (
                <Link
                  key={post.id}
                  to={`/posts/${post.id}`}
                  className="block rounded-lg border border-gray-200 p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span
                          className={`text-xs font-medium px-2 py-0.5 rounded ${
                            post.type === 'NEED'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-green-100 text-green-800'
                          }`}
                        >
                          {post.type}
                        </span>
                        <span className="text-xs text-gray-500">{post.category}</span>
                      </div>
                      <h3 className="font-semibold text-gray-900">{post.title}</h3>
                      <p className="mt-1 text-sm text-gray-600 line-clamp-1">
                        {post.description}
                      </p>
                    </div>
                    <span
                      className={`text-xs ${
                        post.status === 'open'
                          ? 'text-green-600'
                          : 'text-gray-600'
                      }`}
                    >
                      {post.status}
                    </span>
                  </div>
                </Link>
              ))}

              {/* Recent matches */}
              {matches.slice(0, 2).map((match) => (
                <Link
                  key={match.id}
                  to={`/posts/${match.post_id}`}
                  className="block rounded-lg border border-gray-200 p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <MessageCircle size={14} className="text-gray-500" />
                        <span className="text-xs text-gray-500">Match</span>
                      </div>
                      <h3 className="font-semibold text-gray-900">{match.post_title}</h3>
                      <p className="mt-1 text-sm text-gray-600">
                        With {match.responder_pseudonym}
                      </p>
                    </div>
                    <span
                      className={`text-xs ${
                        match.status === 'pending'
                          ? 'text-yellow-600'
                          : match.status === 'accepted'
                          ? 'text-green-600'
                          : 'text-gray-600'
                      }`}
                    >
                      {match.status}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Coming Soon Features */}
      <div className="mt-8 card bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200">
        <h2 className="mb-4 text-lg font-semibold text-purple-900">Coming Soon</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="text-center">
            <div className="text-3xl mb-2">📍</div>
            <h3 className="font-semibold text-purple-900">Pantry Locator</h3>
            <p className="text-sm text-purple-700">Find food pantries nearby (Phase 3)</p>
          </div>
          <div className="text-center">
            <div className="text-3xl mb-2">👥</div>
            <h3 className="font-semibold text-purple-900">Pods</h3>
            <p className="text-sm text-purple-700">Join micro-support circles (Phase 4)</p>
          </div>
        </div>
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../../store/authStore'
import { usePostsStore } from '../../store/postsStore'
import { useShiftsStore } from '../../store/shiftsStore'
import { usePodsStore } from '../../store/podsStore'
import { Plus, MessageCircle, FileText, TrendingUp, MapPin, Calendar, CircleDot, Heart } from 'lucide-react'

export function DashboardPage() {
  const { t } = useTranslation(['dashboard', 'common'])
  const { user } = useAuthStore()
  const { myPosts, matches, getMyPosts, getMyMatches } = usePostsStore()
  const { myShifts, fetchMyShifts } = useShiftsStore()
  const { pods, fetchPods } = usePodsStore()
  const [stats, setStats] = useState({
    activePosts: 0,
    pendingMatches: 0,
    completedMatches: 0,
    upcomingShifts: 0,
    myPods: 0,
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
        fetchPods(),
      ])

      setStats({
        activePosts: postsData.filter(p => p.status === 'open').length,
        pendingMatches: matchesData.filter(m => m.status === 'pending').length,
        completedMatches: matchesData.filter(m => m.status === 'completed').length,
        upcomingShifts: myShifts.filter(s => s.status === 'confirmed').length,
        myPods: pods.length,
      })
    } catch (err) {
      console.error('Failed to load dashboard data:', err)
    }
  }

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return t('greeting.morning', 'Good morning')
    if (hour < 18) return t('greeting.afternoon', 'Good afternoon')
    return t('greeting.evening', 'Good evening')
  }

  return (
    <div className="container py-6">
      {/* Welcome Section */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          {getGreeting()}, {user?.pseudonym}! 👋
        </h1>
        <p className="mt-2 text-gray-600">
          {t('welcome.subtitle', 'Welcome to your CommunityCircle dashboard')}
        </p>
      </div>

      {/* Quick Stats */}
      <div className="mb-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-5">
        <div className="card bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-blue-600">{t('stats.activePosts')}</p>
              <p className="mt-2 text-3xl font-bold text-blue-900">{stats.activePosts}</p>
            </div>
            <FileText className="text-blue-600" size={40} />
          </div>
          <Link
            to="/posts/my"
            className="mt-4 inline-flex items-center text-sm font-medium text-blue-700 hover:text-blue-900"
          >
            {t('stats.viewAllPosts', 'View all posts')} →
          </Link>
        </div>

        <div className="card bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-yellow-600">{t('stats.pendingMatches', 'Pending Matches')}</p>
              <p className="mt-2 text-3xl font-bold text-yellow-900">{stats.pendingMatches}</p>
            </div>
            <MessageCircle className="text-yellow-600" size={40} />
          </div>
          <Link
            to="/matches"
            className="mt-4 inline-flex items-center text-sm font-medium text-yellow-700 hover:text-yellow-900"
          >
            {t('stats.viewMatches', 'View matches')} →
          </Link>
        </div>

        <div className="card bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-green-600">{t('stats.completed', 'Completed')}</p>
              <p className="mt-2 text-3xl font-bold text-green-900">{stats.completedMatches}</p>
            </div>
            <TrendingUp className="text-green-600" size={40} />
          </div>
          <p className="mt-4 text-sm text-green-700">
            {t('stats.completedMessage', 'Great job helping your community!')}
          </p>
        </div>

        <div className="card bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-purple-600">{t('stats.upcomingShifts')}</p>
              <p className="mt-2 text-3xl font-bold text-purple-900">{stats.upcomingShifts}</p>
            </div>
            <Calendar className="text-purple-600" size={40} />
          </div>
          <Link
            to="/shifts/my-shifts"
            className="mt-4 inline-flex items-center text-sm font-medium text-purple-700 hover:text-purple-900"
          >
            {t('stats.viewMyShifts', 'View my shifts')} →
          </Link>
        </div>

        <div className="card bg-gradient-to-br from-pink-50 to-pink-100 border-pink-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-pink-600">{t('stats.myPods', 'My Pods')}</p>
              <p className="mt-2 text-3xl font-bold text-pink-900">{stats.myPods}</p>
            </div>
            <CircleDot className="text-pink-600" size={40} />
          </div>
          <Link
            to="/pods"
            className="mt-4 inline-flex items-center text-sm font-medium text-pink-700 hover:text-pink-900"
          >
            {t('stats.viewMyPods', 'View my pods')} →
          </Link>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="mb-4 text-xl font-semibold text-gray-900">{t('quickActions.title')}</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          <Link
            to="/posts/create"
            className="card hover:shadow-md transition-shadow text-center p-6"
          >
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-primary-100">
              <Plus className="text-primary-600" size={24} />
            </div>
            <h3 className="font-semibold text-gray-900">{t('quickActions.postNeedOffer', 'Post Need/Offer')}</h3>
            <p className="mt-1 text-sm text-gray-600">
              {t('quickActions.postNeedOfferDesc', 'Share what you need or can offer')}
            </p>
          </Link>

          <Link
            to="/posts"
            className="card hover:shadow-md transition-shadow text-center p-6"
          >
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100">
              <MapPin className="text-blue-600" size={24} />
            </div>
            <h3 className="font-semibold text-gray-900">{t('quickActions.browsePosts', 'Browse Posts')}</h3>
            <p className="mt-1 text-sm text-gray-600">
              {t('quickActions.browsePostsDesc', 'Find needs and offers nearby')}
            </p>
          </Link>

          <Link
            to="/matches"
            className="card hover:shadow-md transition-shadow text-center p-6"
          >
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
              <MessageCircle className="text-green-600" size={24} />
            </div>
            <h3 className="font-semibold text-gray-900">{t('quickActions.myMatches', 'My Matches')}</h3>
            <p className="mt-1 text-sm text-gray-600">
              {t('quickActions.myMatchesDesc', 'View your connections')}
            </p>
          </Link>

          <Link
            to="/posts/my"
            className="card hover:shadow-md transition-shadow text-center p-6"
          >
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-purple-100">
              <FileText className="text-purple-600" size={24} />
            </div>
            <h3 className="font-semibold text-gray-900">{t('quickActions.myPosts', 'My Posts')}</h3>
            <p className="mt-1 text-sm text-gray-600">
              {t('quickActions.myPostsDesc', 'Manage your posts')}
            </p>
          </Link>

          <Link
            to="/shifts"
            className="card hover:shadow-md transition-shadow text-center p-6"
          >
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100">
              <Calendar className="text-indigo-600" size={24} />
            </div>
            <h3 className="font-semibold text-gray-900">{t('quickActions.browseShifts')}</h3>
            <p className="mt-1 text-sm text-gray-600">
              {t('quickActions.browseShiftsDesc', 'Find volunteer opportunities')}
            </p>
          </Link>

          <Link
            to="/pods/create"
            className="card hover:shadow-md transition-shadow text-center p-6"
          >
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-pink-100">
              <CircleDot className="text-pink-600" size={24} />
            </div>
            <h3 className="font-semibold text-gray-900">{t('quickActions.createPod', 'Create Pod')}</h3>
            <p className="mt-1 text-sm text-gray-600">
              {t('quickActions.createPodDesc', 'Start a close-knit support circle')}
            </p>
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div>
        <h2 className="mb-4 text-xl font-semibold text-gray-900">{t('recentActivity.title')}</h2>
        <div className="card">
          {myPosts.length === 0 && matches.length === 0 ? (
            <div className="py-8 text-center text-gray-600">
              <p className="mb-2">{t('recentActivity.noActivity')}</p>
              <p className="text-sm text-gray-500">
                {t('recentActivity.noActivityDescription')}
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
    </div>
  )
}

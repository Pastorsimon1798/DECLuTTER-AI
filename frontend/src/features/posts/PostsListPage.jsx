import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { usePostsStore } from '../../store/postsStore'
import { MapPin, Calendar, User, Filter, Plus } from 'lucide-react'

export function PostsListPage() {
  const {
    posts,
    loading,
    error,
    filters,
    setFilters,
    searchPosts,
    userLocation,
    setUserLocation,
  } = usePostsStore()

  const [showFilters, setShowFilters] = useState(false)
  const [localFilters, setLocalFilters] = useState(filters)

  useEffect(() => {
    // Get user location
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation({
            lat: position.coords.latitude,
            lon: position.coords.longitude,
          })
        },
        (error) => {
          console.error('Error getting location:', error)
        }
      )
    }

    // Load posts
    searchPosts()
  }, [])

  const handleFilterChange = (key, value) => {
    setLocalFilters({ ...localFilters, [key]: value })
  }

  const applyFilters = () => {
    setFilters(localFilters)
    searchPosts()
    setShowFilters(false)
  }

  const resetFilters = () => {
    const defaultFilters = {
      type: null,
      category: null,
      radius: 5000,
    }
    setLocalFilters(defaultFilters)
    setFilters(defaultFilters)
    searchPosts()
  }

  const categories = [
    { value: 'food', label: 'Food' },
    { value: 'transport', label: 'Transportation' },
    { value: 'housing', label: 'Housing' },
    { value: 'childcare', label: 'Childcare' },
    { value: 'eldercare', label: 'Eldercare' },
    { value: 'medical', label: 'Medical' },
    { value: 'education', label: 'Education' },
    { value: 'employment', label: 'Employment' },
    { value: 'legal', label: 'Legal' },
    { value: 'other', label: 'Other' },
  ]

  const formatDistance = (meters) => {
    if (!meters) return ''
    if (meters < 1000) return `${Math.round(meters)}m away`
    return `${(meters / 1000).toFixed(1)}km away`
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  return (
    <div className="container py-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Needs & Offers</h1>
          <p className="mt-1 text-sm text-gray-600">
            Find help or offer support in your community
          </p>
        </div>
        <Link to="/posts/create" className="btn-primary flex items-center gap-2">
          <Plus size={20} />
          Post Need/Offer
        </Link>
      </div>

      {/* Filters Bar */}
      <div className="mb-6 card">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="btn-secondary flex items-center gap-2"
            >
              <Filter size={18} />
              Filters
              {(localFilters.type || localFilters.category) && (
                <span className="ml-1 rounded-full bg-primary-600 px-2 py-0.5 text-xs text-white">
                  Active
                </span>
              )}
            </button>

            {/* Quick filter buttons */}
            <div className="hidden md:flex items-center gap-2">
              <button
                onClick={() => {
                  handleFilterChange('type', localFilters.type === 'NEED' ? null : 'NEED')
                  applyFilters()
                }}
                className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                  localFilters.type === 'NEED'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Needs
              </button>
              <button
                onClick={() => {
                  handleFilterChange('type', localFilters.type === 'OFFER' ? null : 'OFFER')
                  applyFilters()
                }}
                className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                  localFilters.type === 'OFFER'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Offers
              </button>
            </div>
          </div>

          <div className="text-sm text-gray-600">
            {posts.length} {posts.length === 1 ? 'post' : 'posts'} found
            {userLocation && ' near you'}
          </div>
        </div>

        {/* Expanded filters */}
        {showFilters && (
          <div className="mt-4 border-t pt-4">
            <div className="grid gap-4 md:grid-cols-3">
              {/* Type filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700">Type</label>
                <select
                  value={localFilters.type || ''}
                  onChange={(e) => handleFilterChange('type', e.target.value || null)}
                  className="input mt-1"
                >
                  <option value="">All</option>
                  <option value="NEED">Needs</option>
                  <option value="OFFER">Offers</option>
                </select>
              </div>

              {/* Category filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700">Category</label>
                <select
                  value={localFilters.category || ''}
                  onChange={(e) => handleFilterChange('category', e.target.value || null)}
                  className="input mt-1"
                >
                  <option value="">All categories</option>
                  {categories.map((cat) => (
                    <option key={cat.value} value={cat.value}>
                      {cat.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Radius filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Radius: {(localFilters.radius / 1000).toFixed(1)}km
                </label>
                <input
                  type="range"
                  min="500"
                  max="50000"
                  step="500"
                  value={localFilters.radius}
                  onChange={(e) => handleFilterChange('radius', parseInt(e.target.value))}
                  className="mt-1 w-full"
                />
              </div>
            </div>

            <div className="mt-4 flex gap-2">
              <button onClick={applyFilters} className="btn-primary">
                Apply Filters
              </button>
              <button onClick={resetFilters} className="btn-secondary">
                Reset
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="mb-6 rounded-lg bg-red-50 p-4 text-sm text-red-800">
          {error}
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      )}

      {/* Posts list */}
      {!loading && posts.length === 0 && (
        <div className="card text-center py-12">
          <p className="text-gray-600">No posts found matching your filters.</p>
          <p className="mt-2 text-sm text-gray-500">
            Try adjusting your filters or{' '}
            <Link to="/posts/create" className="text-primary-600 hover:underline">
              create a new post
            </Link>
          </p>
        </div>
      )}

      {!loading && posts.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {posts.map((post) => (
            <Link
              key={post.id}
              to={`/posts/${post.id}`}
              className="card hover:shadow-md transition-shadow"
            >
              {/* Post type badge */}
              <div className="mb-3 flex items-center justify-between">
                <span
                  className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${
                    post.type === 'NEED'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-green-100 text-green-800'
                  }`}
                >
                  {post.type}
                </span>
                <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700 capitalize">
                  {post.category}
                </span>
              </div>

              {/* Post title */}
              <h3 className="mb-2 text-lg font-semibold text-gray-900 line-clamp-2">
                {post.title}
              </h3>

              {/* Post description */}
              {post.description && (
                <p className="mb-3 text-sm text-gray-600 line-clamp-2">
                  {post.description}
                </p>
              )}

              {/* Post metadata */}
              <div className="space-y-2 text-xs text-gray-500">
                <div className="flex items-center gap-2">
                  <User size={14} />
                  <span>{post.author_pseudonym}</span>
                </div>
                <div className="flex items-center gap-2">
                  <MapPin size={14} />
                  <span>
                    {post.distance_meters
                      ? formatDistance(post.distance_meters)
                      : 'Location hidden'}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar size={14} />
                  <span>{formatDate(post.created_at)}</span>
                </div>
              </div>

              {/* Status badge */}
              <div className="mt-3 pt-3 border-t">
                <span
                  className={`text-xs font-medium ${
                    post.status === 'open'
                      ? 'text-green-600'
                      : post.status === 'matched'
                      ? 'text-blue-600'
                      : 'text-gray-600'
                  }`}
                >
                  {post.status === 'open' && '🟢 Available'}
                  {post.status === 'matched' && '🔵 Matched'}
                  {post.status === 'completed' && '✅ Completed'}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

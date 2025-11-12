import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePostsStore } from '../../store/postsStore'
import { MapPin, ArrowLeft } from 'lucide-react'

export function CreatePostPage() {
  const navigate = useNavigate()
  const { createPost, loading, error, clearError } = usePostsStore()

  const [formData, setFormData] = useState({
    type: 'NEED',
    category: 'food',
    title: '',
    description: '',
    radius_meters: 2000,
    visibility: 'public',
    location: null,
  })

  const [locationError, setLocationError] = useState(null)
  const [gettingLocation, setGettingLocation] = useState(false)

  useEffect(() => {
    clearError()
  }, [])

  const categories = [
    { value: 'food', label: 'Food & Groceries' },
    { value: 'transport', label: 'Transportation' },
    { value: 'housing', label: 'Housing' },
    { value: 'childcare', label: 'Childcare' },
    { value: 'eldercare', label: 'Elder Care' },
    { value: 'medical', label: 'Medical' },
    { value: 'education', label: 'Education & Tutoring' },
    { value: 'employment', label: 'Employment' },
    { value: 'legal', label: 'Legal Assistance' },
    { value: 'companionship', label: 'Companionship' },
    { value: 'technology', label: 'Technology Help' },
    { value: 'other', label: 'Other' },
  ]

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData({
      ...formData,
      [name]: value,
    })
  }

  const getCurrentLocation = () => {
    setGettingLocation(true)
    setLocationError(null)

    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by your browser')
      setGettingLocation(false)
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setFormData({
          ...formData,
          location: {
            lat: position.coords.latitude,
            lon: position.coords.longitude,
          },
        })
        setGettingLocation(false)
      },
      (error) => {
        setLocationError('Unable to get your location. Please try again.')
        setGettingLocation(false)
        console.error('Geolocation error:', error)
      }
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!formData.location) {
      setLocationError('Please set your location')
      return
    }

    try {
      const post = await createPost(formData)
      navigate(`/posts/${post.id}`)
    } catch (err) {
      // Error is handled by store
      console.error('Failed to create post:', err)
    }
  }

  return (
    <div className="container max-w-2xl py-6">
      {/* Back button */}
      <button
        onClick={() => navigate('/posts')}
        className="mb-6 flex items-center gap-2 text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft size={20} />
        Back to posts
      </button>

      <div className="card">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          Post a Need or Offer
        </h1>

        {error && (
          <div className="mb-6 rounded-lg bg-red-50 p-4 text-sm text-red-800">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Type selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              What would you like to do? *
            </label>
            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => setFormData({ ...formData, type: 'NEED' })}
                className={`rounded-lg border-2 p-4 text-center transition-all ${
                  formData.type === 'NEED'
                    ? 'border-red-500 bg-red-50 text-red-900'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <div className="text-3xl mb-2">🙏</div>
                <div className="font-semibold">I Need Help</div>
                <div className="text-xs text-gray-600 mt-1">
                  Request support from the community
                </div>
              </button>
              <button
                type="button"
                onClick={() => setFormData({ ...formData, type: 'OFFER' })}
                className={`rounded-lg border-2 p-4 text-center transition-all ${
                  formData.type === 'OFFER'
                    ? 'border-green-500 bg-green-50 text-green-900'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <div className="text-3xl mb-2">🤝</div>
                <div className="font-semibold">I Can Help</div>
                <div className="text-xs text-gray-600 mt-1">
                  Offer support to others
                </div>
              </button>
            </div>
          </div>

          {/* Category */}
          <div>
            <label htmlFor="category" className="block text-sm font-medium text-gray-700">
              Category *
            </label>
            <select
              id="category"
              name="category"
              required
              value={formData.category}
              onChange={handleChange}
              className="input mt-1"
            >
              {categories.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>

          {/* Title */}
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700">
              Title *
            </label>
            <input
              type="text"
              id="title"
              name="title"
              required
              maxLength={200}
              value={formData.title}
              onChange={handleChange}
              className="input mt-1"
              placeholder={
                formData.type === 'NEED'
                  ? 'e.g., Need ride to medical appointment'
                  : 'e.g., Can give rides on weekends'
              }
            />
            <p className="mt-1 text-xs text-gray-500">
              {formData.title.length}/200 characters
            </p>
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700">
              Description
            </label>
            <textarea
              id="description"
              name="description"
              rows={4}
              maxLength={2000}
              value={formData.description}
              onChange={handleChange}
              className="input mt-1"
              placeholder="Provide more details about what you need or can offer..."
            />
            <p className="mt-1 text-xs text-gray-500">
              {formData.description.length}/2000 characters
            </p>
          </div>

          {/* Location */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Location *
            </label>
            {formData.location ? (
              <div className="flex items-center justify-between rounded-lg border border-green-500 bg-green-50 p-4">
                <div className="flex items-center gap-2 text-green-900">
                  <MapPin size={20} />
                  <div>
                    <div className="font-medium">Location set</div>
                    <div className="text-sm">
                      {formData.location.lat.toFixed(4)}, {formData.location.lon.toFixed(4)}
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, location: null })}
                  className="text-sm text-green-700 hover:text-green-900 underline"
                >
                  Change
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={getCurrentLocation}
                disabled={gettingLocation}
                className="btn-secondary w-full flex items-center justify-center gap-2"
              >
                <MapPin size={20} />
                {gettingLocation ? 'Getting location...' : 'Use my current location'}
              </button>
            )}
            {locationError && (
              <p className="mt-2 text-sm text-red-600">{locationError}</p>
            )}
            <p className="mt-2 text-xs text-gray-500">
              Your exact location is never shared. We use approximate location for privacy.
            </p>
          </div>

          {/* Radius */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Search radius: {(formData.radius_meters / 1000).toFixed(1)}km
            </label>
            <input
              type="range"
              name="radius_meters"
              min="500"
              max="50000"
              step="500"
              value={formData.radius_meters}
              onChange={handleChange}
              className="mt-2 w-full"
            />
            <p className="mt-1 text-xs text-gray-500">
              {formData.type === 'NEED'
                ? 'How far are you willing to travel or have someone come?'
                : 'How far are you willing to travel to help?'}
            </p>
          </div>

          {/* Visibility */}
          <div>
            <label htmlFor="visibility" className="block text-sm font-medium text-gray-700">
              Who can see this post?
            </label>
            <select
              id="visibility"
              name="visibility"
              value={formData.visibility}
              onChange={handleChange}
              className="input mt-1"
            >
              <option value="public">Everyone (recommended)</option>
              <option value="circles">My circles only</option>
              <option value="private">Private (only me)</option>
            </select>
          </div>

          {/* Submit buttons */}
          <div className="flex gap-4">
            <button
              type="submit"
              disabled={loading || !formData.location}
              className="btn-primary flex-1"
            >
              {loading ? 'Posting...' : `Post ${formData.type === 'NEED' ? 'Need' : 'Offer'}`}
            </button>
            <button
              type="button"
              onClick={() => navigate('/posts')}
              className="btn-secondary"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

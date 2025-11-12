import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { usePostsStore } from '../../store/postsStore'
import { useAuthStore } from '../../store/authStore'
import { MapPin, Calendar, User, ArrowLeft, MessageCircle, Edit, Trash2 } from 'lucide-react'

export function PostDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const {
    currentPost,
    loading,
    error,
    getPost,
    deletePost,
    createMatch,
    updatePost,
  } = usePostsStore()

  const [showRespondModal, setShowRespondModal] = useState(false)
  const [responseNotes, setResponseNotes] = useState('')
  const [responding, setResponding] = useState(false)

  useEffect(() => {
    if (id) {
      getPost(id)
    }
  }, [id])

  const formatDistance = (meters) => {
    if (!meters) return 'Location hidden for privacy'
    if (meters < 1000) return `${Math.round(meters)}m away`
    return `${(meters / 1000).toFixed(1)}km away`
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const handleRespond = async () => {
    setResponding(true)
    try {
      await createMatch({
        post_id: currentPost.id,
        notes: responseNotes,
        method: 'in_app',
      })
      setShowRespondModal(false)
      alert('Response sent successfully! The post author will be notified.')
      navigate('/posts')
    } catch (err) {
      console.error('Failed to respond:', err)
    } finally {
      setResponding(false)
    }
  }

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this post?')) {
      try {
        await deletePost(currentPost.id)
        navigate('/posts')
      } catch (err) {
        console.error('Failed to delete post:', err)
      }
    }
  }

  const handleMarkCompleted = async () => {
    try {
      await updatePost(currentPost.id, { status: 'completed' })
      getPost(id) // Refresh post
    } catch (err) {
      console.error('Failed to update post:', err)
    }
  }

  if (loading) {
    return (
      <div className="container py-12">
        <div className="flex justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </div>
    )
  }

  if (error || !currentPost) {
    return (
      <div className="container py-12">
        <div className="card text-center">
          <p className="text-red-600">{error || 'Post not found'}</p>
          <Link to="/posts" className="mt-4 inline-block text-primary-600 hover:underline">
            Back to posts
          </Link>
        </div>
      </div>
    )
  }

  const isAuthor = user && currentPost.author_id === user.id
  const canRespond = user && !isAuthor && currentPost.status === 'open'

  return (
    <div className="container max-w-4xl py-6">
      {/* Back button */}
      <button
        onClick={() => navigate('/posts')}
        className="mb-6 flex items-center gap-2 text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft size={20} />
        Back to posts
      </button>

      <div className="card">
        {/* Header */}
        <div className="mb-6 flex items-start justify-between">
          <div className="flex-1">
            <div className="mb-3 flex items-center gap-2">
              <span
                className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${
                  currentPost.type === 'NEED'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-green-100 text-green-800'
                }`}
              >
                {currentPost.type}
              </span>
              <span className="rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700 capitalize">
                {currentPost.category}
              </span>
              <span
                className={`text-sm font-medium ${
                  currentPost.status === 'open'
                    ? 'text-green-600'
                    : currentPost.status === 'matched'
                    ? 'text-blue-600'
                    : 'text-gray-600'
                }`}
              >
                {currentPost.status === 'open' && '🟢 Available'}
                {currentPost.status === 'matched' && '🔵 Matched'}
                {currentPost.status === 'completed' && '✅ Completed'}
                {currentPost.status === 'cancelled' && '❌ Cancelled'}
              </span>
            </div>
            <h1 className="text-3xl font-bold text-gray-900">{currentPost.title}</h1>
          </div>

          {/* Author actions */}
          {isAuthor && (
            <div className="flex gap-2">
              <button
                onClick={() => navigate(`/posts/${currentPost.id}/edit`)}
                className="btn-secondary flex items-center gap-2"
                title="Edit post"
              >
                <Edit size={18} />
              </button>
              <button
                onClick={handleDelete}
                className="btn-danger flex items-center gap-2"
                title="Delete post"
              >
                <Trash2 size={18} />
              </button>
            </div>
          )}
        </div>

        {/* Description */}
        {currentPost.description && (
          <div className="mb-6">
            <h2 className="text-sm font-semibold text-gray-700 mb-2">Description</h2>
            <p className="text-gray-600 whitespace-pre-wrap">{currentPost.description}</p>
          </div>
        )}

        {/* Metadata */}
        <div className="mb-6 space-y-3 rounded-lg bg-gray-50 p-4">
          <div className="flex items-center gap-3 text-sm text-gray-700">
            <User size={18} className="text-gray-500" />
            <div>
              <span className="font-medium">Posted by:</span> {currentPost.author_pseudonym}
              {isAuthor && <span className="ml-2 text-xs text-gray-500">(You)</span>}
            </div>
          </div>

          <div className="flex items-center gap-3 text-sm text-gray-700">
            <MapPin size={18} className="text-gray-500" />
            <div>
              <span className="font-medium">Location:</span> {formatDistance(currentPost.distance_meters)}
              <span className="ml-2 text-xs text-gray-500">
                (within {(currentPost.radius_meters / 1000).toFixed(1)}km radius)
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 text-sm text-gray-700">
            <Calendar size={18} className="text-gray-500" />
            <div>
              <span className="font-medium">Posted:</span> {formatDate(currentPost.created_at)}
            </div>
          </div>

          {currentPost.expires_at && (
            <div className="flex items-center gap-3 text-sm text-gray-700">
              <Calendar size={18} className="text-gray-500" />
              <div>
                <span className="font-medium">Expires:</span> {formatDate(currentPost.expires_at)}
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-4">
          {canRespond && (
            <button
              onClick={() => setShowRespondModal(true)}
              className="btn-primary flex-1 flex items-center justify-center gap-2"
            >
              <MessageCircle size={20} />
              {currentPost.type === 'NEED' ? 'I Can Help' : 'I Need This'}
            </button>
          )}

          {isAuthor && currentPost.status === 'matched' && (
            <button
              onClick={handleMarkCompleted}
              className="btn-primary flex-1"
            >
              Mark as Completed
            </button>
          )}

          {isAuthor && currentPost.status === 'open' && (
            <Link
              to="/posts"
              className="btn-secondary flex-1 text-center"
            >
              View My Posts
            </Link>
          )}
        </div>

        {/* Privacy notice */}
        <div className="mt-6 rounded-lg bg-blue-50 p-4 text-sm text-blue-800">
          <strong>Privacy:</strong> Your exact location is never shared. Only approximate
          location is visible to maintain your privacy and safety.
        </div>
      </div>

      {/* Respond Modal */}
      {showRespondModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="card max-w-md w-full">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Respond to {currentPost.type === 'NEED' ? 'Need' : 'Offer'}
            </h2>

            <p className="text-sm text-gray-600 mb-4">
              Send a message to {currentPost.author_pseudonym} to coordinate.
            </p>

            <textarea
              value={responseNotes}
              onChange={(e) => setResponseNotes(e.target.value)}
              rows={4}
              className="input mb-4"
              placeholder="Introduce yourself and explain how you can help..."
            />

            <div className="flex gap-4">
              <button
                onClick={handleRespond}
                disabled={responding || !responseNotes.trim()}
                className="btn-primary flex-1"
              >
                {responding ? 'Sending...' : 'Send Response'}
              </button>
              <button
                onClick={() => setShowRespondModal(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { usePostsStore } from '../../store/postsStore'
import { MessageCircle, CheckCircle, XCircle, Clock, User, Calendar } from 'lucide-react'

export function MatchesPage() {
  const { matches, loading, error, getMyMatches, updateMatch } = usePostsStore()
  const [filter, setFilter] = useState('all') // all, as_requester, as_responder

  useEffect(() => {
    loadMatches()
  }, [filter])

  const loadMatches = () => {
    const params = {}
    if (filter === 'as_requester') {
      params.as_requester = true
      params.as_responder = false
    } else if (filter === 'as_responder') {
      params.as_requester = false
      params.as_responder = true
    }
    getMyMatches(params)
  }

  const handleAccept = async (matchId) => {
    try {
      await updateMatch(matchId, { status: 'accepted' })
      loadMatches()
    } catch (err) {
      console.error('Failed to accept match:', err)
    }
  }

  const handleDecline = async (matchId) => {
    if (window.confirm('Are you sure you want to decline this match?')) {
      try {
        await updateMatch(matchId, { status: 'declined' })
        loadMatches()
      } catch (err) {
        console.error('Failed to decline match:', err)
      }
    }
  }

  const handleComplete = async (matchId) => {
    if (window.confirm('Mark this match as completed?')) {
      try {
        await updateMatch(matchId, { status: 'completed' })
        loadMatches()
      } catch (err) {
        console.error('Failed to complete match:', err)
      }
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now - date
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  const getStatusBadge = (status) => {
    const badges = {
      pending: { color: 'bg-yellow-100 text-yellow-800', icon: Clock, text: 'Pending' },
      accepted: { color: 'bg-green-100 text-green-800', icon: CheckCircle, text: 'Accepted' },
      declined: { color: 'bg-red-100 text-red-800', icon: XCircle, text: 'Declined' },
      completed: { color: 'bg-blue-100 text-blue-800', icon: CheckCircle, text: 'Completed' },
      cancelled: { color: 'bg-gray-100 text-gray-800', icon: XCircle, text: 'Cancelled' },
    }

    const badge = badges[status] || badges.pending
    const Icon = badge.icon

    return (
      <span className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium ${badge.color}`}>
        <Icon size={14} />
        {badge.text}
      </span>
    )
  }

  return (
    <div className="container py-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">My Matches</h1>
        <p className="mt-1 text-sm text-gray-600">
          View and manage your connections
        </p>
      </div>

      {/* Filters */}
      <div className="mb-6 card">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setFilter('all')}
            className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
              filter === 'all'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All Matches
          </button>
          <button
            onClick={() => setFilter('as_requester')}
            className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
              filter === 'as_requester'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            My Posts
          </button>
          <button
            onClick={() => setFilter('as_responder')}
            className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
              filter === 'as_responder'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            My Responses
          </button>
        </div>
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

      {/* Empty state */}
      {!loading && matches.length === 0 && (
        <div className="card text-center py-12">
          <MessageCircle size={48} className="mx-auto text-gray-400 mb-4" />
          <p className="text-gray-600 mb-2">No matches yet</p>
          <p className="text-sm text-gray-500 mb-4">
            {filter === 'as_requester'
              ? 'When someone responds to your posts, they will appear here'
              : filter === 'as_responder'
              ? 'When you respond to posts, your responses will appear here'
              : 'Start by posting a need or offer, or respond to existing posts'}
          </p>
          <Link to="/posts" className="text-primary-600 hover:underline">
            Browse Posts
          </Link>
        </div>
      )}

      {/* Matches list */}
      {!loading && matches.length > 0 && (
        <div className="space-y-4">
          {matches.map((match) => (
            <div key={match.id} className="card hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <Link
                    to={`/posts/${match.post_id}`}
                    className="text-lg font-semibold text-gray-900 hover:text-primary-600"
                  >
                    {match.post_title}
                  </Link>
                  <div className="mt-1 flex items-center gap-4 text-sm text-gray-600">
                    <div className="flex items-center gap-1">
                      <User size={14} />
                      <span>
                        {filter === 'as_requester' || !filter
                          ? `Response from ${match.responder_pseudonym}`
                          : `To ${match.requester_pseudonym}`}
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Calendar size={14} />
                      <span>{formatDate(match.created_at)}</span>
                    </div>
                  </div>
                </div>
                {getStatusBadge(match.status)}
              </div>

              {/* Notes */}
              {match.notes && (
                <div className="mb-4 rounded-lg bg-gray-50 p-3 text-sm text-gray-700">
                  <strong className="text-gray-900">Message:</strong> {match.notes}
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2">
                {/* Requester actions (for pending matches) */}
                {match.status === 'pending' && filter === 'as_requester' && (
                  <>
                    <button
                      onClick={() => handleAccept(match.id)}
                      className="btn-primary flex items-center gap-2"
                    >
                      <CheckCircle size={18} />
                      Accept
                    </button>
                    <button
                      onClick={() => handleDecline(match.id)}
                      className="btn-secondary flex items-center gap-2"
                    >
                      <XCircle size={18} />
                      Decline
                    </button>
                  </>
                )}

                {/* Accepted matches - mark as complete */}
                {match.status === 'accepted' && (
                  <button
                    onClick={() => handleComplete(match.id)}
                    className="btn-primary flex items-center gap-2"
                  >
                    <CheckCircle size={18} />
                    Mark as Completed
                  </button>
                )}

                {/* View post link */}
                <Link
                  to={`/posts/${match.post_id}`}
                  className="btn-secondary flex items-center gap-2"
                >
                  View Post
                </Link>
              </div>

              {/* Contact info note */}
              {match.status === 'accepted' && (
                <div className="mt-4 text-xs text-gray-500 border-t pt-3">
                  💡 <strong>Next steps:</strong> Coordinate through the platform or exchange
                  contact information as needed. Remember to prioritize safety!
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

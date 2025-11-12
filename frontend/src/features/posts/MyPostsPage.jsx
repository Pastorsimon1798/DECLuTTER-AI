import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { usePostsStore } from '../../store/postsStore'
import { Plus, Edit, Trash2, Eye } from 'lucide-react'

export function MyPostsPage() {
  const { myPosts, loading, error, getMyPosts, deletePost, updatePost } = usePostsStore()
  const [filter, setFilter] = useState('all') // all, open, matched, completed

  useEffect(() => {
    loadPosts()
  }, [filter])

  const loadPosts = () => {
    const params = {}
    if (filter !== 'all') {
      params.status = filter
    }
    getMyPosts(params)
  }

  const handleDelete = async (postId) => {
    if (window.confirm('Are you sure you want to delete this post?')) {
      try {
        await deletePost(postId)
        loadPosts()
      } catch (err) {
        console.error('Failed to delete post:', err)
      }
    }
  }

  const handleStatusChange = async (postId, newStatus) => {
    try {
      await updatePost(postId, { status: newStatus })
      loadPosts()
    } catch (err) {
      console.error('Failed to update post:', err)
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  const getStatusColor = (status) => {
    const colors = {
      open: 'bg-green-100 text-green-800',
      matched: 'bg-blue-100 text-blue-800',
      in_progress: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-gray-100 text-gray-800',
      cancelled: 'bg-red-100 text-red-800',
    }
    return colors[status] || colors.open
  }

  return (
    <div className="container py-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Posts</h1>
          <p className="mt-1 text-sm text-gray-600">
            Manage your needs and offers
          </p>
        </div>
        <Link to="/posts/create" className="btn-primary flex items-center gap-2">
          <Plus size={20} />
          New Post
        </Link>
      </div>

      {/* Filters */}
      <div className="mb-6 card">
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setFilter('all')}
            className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
              filter === 'all'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All ({myPosts.length})
          </button>
          <button
            onClick={() => setFilter('open')}
            className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
              filter === 'open'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Open
          </button>
          <button
            onClick={() => setFilter('matched')}
            className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
              filter === 'matched'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Matched
          </button>
          <button
            onClick={() => setFilter('completed')}
            className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
              filter === 'completed'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Completed
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
      {!loading && myPosts.length === 0 && (
        <div className="card text-center py-12">
          <p className="text-gray-600 mb-2">No posts yet</p>
          <p className="text-sm text-gray-500 mb-4">
            Create your first post to get started
          </p>
          <Link to="/posts/create" className="btn-primary inline-flex items-center gap-2">
            <Plus size={20} />
            Create Post
          </Link>
        </div>
      )}

      {/* Posts list */}
      {!loading && myPosts.length > 0 && (
        <div className="space-y-4">
          {myPosts.map((post) => (
            <div key={post.id} className="card">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className={`text-xs font-medium px-2 py-1 rounded ${
                        post.type === 'NEED'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-green-100 text-green-800'
                      }`}
                    >
                      {post.type}
                    </span>
                    <span className="text-xs text-gray-500 capitalize">{post.category}</span>
                    <span className={`text-xs font-medium px-2 py-1 rounded ${getStatusColor(post.status)}`}>
                      {post.status}
                    </span>
                  </div>

                  <Link
                    to={`/posts/${post.id}`}
                    className="text-lg font-semibold text-gray-900 hover:text-primary-600"
                  >
                    {post.title}
                  </Link>

                  {post.description && (
                    <p className="mt-2 text-sm text-gray-600 line-clamp-2">
                      {post.description}
                    </p>
                  )}

                  <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
                    <span>Posted {formatDate(post.created_at)}</span>
                    <span>Expires {formatDate(post.expires_at)}</span>
                    <span className="capitalize">Radius: {(post.radius_meters / 1000).toFixed(1)}km</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 ml-4">
                  <Link
                    to={`/posts/${post.id}`}
                    className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"
                    title="View"
                  >
                    <Eye size={18} />
                  </Link>
                  <button
                    onClick={() => handleDelete(post.id)}
                    className="p-2 text-red-600 hover:text-red-900 hover:bg-red-50 rounded"
                    title="Delete"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>

              {/* Quick actions */}
              {post.status === 'open' && (
                <div className="pt-4 border-t flex gap-2">
                  <button
                    onClick={() => handleStatusChange(post.id, 'completed')}
                    className="btn-secondary text-sm"
                  >
                    Mark as Completed
                  </button>
                  <button
                    onClick={() => handleStatusChange(post.id, 'cancelled')}
                    className="btn-secondary text-sm"
                  >
                    Cancel
                  </button>
                </div>
              )}

              {post.status === 'matched' && (
                <div className="pt-4 border-t">
                  <p className="text-sm text-blue-600 mb-2">
                    ✓ Someone has responded to your post
                  </p>
                  <Link
                    to="/matches"
                    className="btn-primary text-sm inline-block"
                  >
                    View Matches
                  </Link>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

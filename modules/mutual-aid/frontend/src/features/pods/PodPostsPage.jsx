import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { usePodsStore } from '../../store/podsStore';
import { ArrowLeft, MessageSquare, Pin, Edit2, Trash2, Plus } from 'lucide-react';

export default function PodPostsPage() {
  const { id, postId } = useParams();
  const navigate = useNavigate();
  const {
    currentPod,
    posts,
    loading,
    error,
    fetchPod,
    fetchPosts,
    createPost,
    updatePost,
    deletePost,
  } = usePodsStore();

  const [showForm, setShowForm] = useState(false);
  const [editingPost, setEditingPost] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    post_type: 'general',
  });
  const [formErrors, setFormErrors] = useState({});

  useEffect(() => {
    if (id) {
      fetchPod(id);
      fetchPosts(id);
    }
  }, [id, fetchPod, fetchPosts]);

  // Open form for new post
  useEffect(() => {
    if (postId === 'new') {
      setShowForm(true);
    }
  }, [postId]);

  const postTypes = [
    { value: 'general', label: 'General', icon: '💬', description: 'Regular post or discussion' },
    { value: 'announcement', label: 'Announcement', icon: '📢', description: 'Important pod news' },
    { value: 'question', label: 'Question', icon: '❓', description: 'Ask the pod a question' },
    { value: 'resource', label: 'Resource', icon: '📚', description: 'Share helpful resources' },
  ];

  const isAdmin = currentPod?.my_role === 'admin';

  const validate = () => {
    const errors = {};
    if (!formData.title.trim()) {
      errors.title = 'Title is required';
    }
    if (formData.title.trim().length < 3) {
      errors.title = 'Title must be at least 3 characters';
    }
    if (!formData.content.trim()) {
      errors.content = 'Content is required';
    }
    if (formData.content.trim().length < 10) {
      errors.content = 'Content must be at least 10 characters';
    }
    return errors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const errors = validate();
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    try {
      if (editingPost) {
        await updatePost(id, editingPost.id, formData);
      } else {
        await createPost(id, formData);
      }

      // Reset form
      setFormData({ title: '', content: '', post_type: 'general' });
      setShowForm(false);
      setEditingPost(null);
      setFormErrors({});

      // Navigate back if we came from /posts/new
      if (postId === 'new') {
        navigate(`/pods/${id}`);
      }
    } catch (error) {
      setFormErrors({ submit: error.message || 'Failed to save post' });
    }
  };

  const handleEdit = (post) => {
    setEditingPost(post);
    setFormData({
      title: post.title,
      content: post.content,
      post_type: post.post_type,
    });
    setShowForm(true);
  };

  const handleDelete = async (postId) => {
    if (!confirm('Are you sure you want to delete this post? This action cannot be undone.')) {
      return;
    }

    try {
      await deletePost(id, postId);
    } catch (error) {
      alert('Failed to delete post: ' + error.message);
    }
  };

  const handleTogglePin = async (post) => {
    if (!isAdmin) return;

    try {
      await updatePost(id, post.id, {
        is_pinned: !post.is_pinned,
      });
    } catch (error) {
      alert('Failed to pin/unpin post: ' + error.message);
    }
  };

  const handleCancelForm = () => {
    setFormData({ title: '', content: '', post_type: 'general' });
    setShowForm(false);
    setEditingPost(null);
    setFormErrors({});

    if (postId === 'new') {
      navigate(`/pods/${id}`);
    }
  };

  // Sort posts: pinned first, then by date
  const sortedPosts = [...posts].sort((a, b) => {
    if (a.is_pinned && !b.is_pinned) return -1;
    if (!a.is_pinned && b.is_pinned) return 1;
    return new Date(b.created_at) - new Date(a.created_at);
  });

  if (loading && !currentPod) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <button
        onClick={() => navigate(`/pods/${id}`)}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft size={20} />
        Back to Pod
      </button>

      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <MessageSquare size={32} className="text-blue-600" />
            Pod Posts
          </h1>
          <p className="text-gray-600 mt-2">
            Share updates, ask questions, and communicate with your pod
          </p>
        </div>
        {!showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus size={18} />
            New Post
          </button>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700">
          {error}
        </div>
      )}

      {/* Post Form */}
      {showForm && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            {editingPost ? 'Edit Post' : 'Create New Post'}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Post Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Post Type
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {postTypes.map((type) => (
                  <button
                    key={type.value}
                    type="button"
                    onClick={() => setFormData({ ...formData, post_type: type.value })}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      formData.post_type === type.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="text-2xl mb-1">{type.icon}</div>
                    <div className="text-sm font-medium text-gray-900">{type.label}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => {
                  setFormData({ ...formData, title: e.target.value });
                  if (formErrors.title) setFormErrors({ ...formErrors, title: null });
                }}
                placeholder="Give your post a clear title..."
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                  formErrors.title ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {formErrors.title && (
                <p className="text-red-500 text-sm mt-1">{formErrors.title}</p>
              )}
            </div>

            {/* Content */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Content <span className="text-red-500">*</span>
              </label>
              <textarea
                value={formData.content}
                onChange={(e) => {
                  setFormData({ ...formData, content: e.target.value });
                  if (formErrors.content) setFormErrors({ ...formErrors, content: null });
                }}
                placeholder="What would you like to share with your pod?"
                rows={8}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                  formErrors.content ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {formErrors.content && (
                <p className="text-red-500 text-sm mt-1">{formErrors.content}</p>
              )}
            </div>

            {formErrors.submit && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                {formErrors.submit}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={handleCancelForm}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
              >
                {loading ? 'Saving...' : editingPost ? 'Update Post' : 'Create Post'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Posts List */}
      <div className="space-y-4">
        {sortedPosts.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <MessageSquare size={48} className="mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No posts yet</h3>
            <p className="text-gray-600 mb-6">
              Be the first to start a conversation with your pod!
            </p>
            {!showForm && (
              <button
                onClick={() => setShowForm(true)}
                className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus size={18} />
                Create First Post
              </button>
            )}
          </div>
        ) : (
          sortedPosts.map((post) => (
            <div
              key={post.id}
              className={`bg-white rounded-lg shadow p-6 ${
                post.is_pinned ? 'border-2 border-yellow-300' : ''
              }`}
            >
              {/* Post Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    {post.is_pinned && (
                      <Pin size={16} className="text-yellow-600" />
                    )}
                    <h3 className="text-xl font-bold text-gray-900">{post.title}</h3>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <span className="px-2 py-1 bg-gray-100 rounded text-xs">
                      {postTypes.find((t) => t.value === post.post_type)?.icon}{' '}
                      {postTypes.find((t) => t.value === post.post_type)?.label}
                    </span>
                    <span>•</span>
                    <span>{new Date(post.created_at).toLocaleDateString()}</span>
                    {post.updated_at && post.updated_at !== post.created_at && (
                      <>
                        <span>•</span>
                        <span className="text-gray-500">Edited</span>
                      </>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  {isAdmin && (
                    <button
                      onClick={() => handleTogglePin(post)}
                      className={`p-2 rounded-lg transition-colors ${
                        post.is_pinned
                          ? 'bg-yellow-100 text-yellow-600 hover:bg-yellow-200'
                          : 'text-gray-400 hover:bg-gray-100 hover:text-gray-600'
                      }`}
                      title={post.is_pinned ? 'Unpin post' : 'Pin post'}
                    >
                      <Pin size={18} />
                    </button>
                  )}
                  <button
                    onClick={() => handleEdit(post)}
                    className="p-2 text-gray-400 hover:bg-gray-100 hover:text-blue-600 rounded-lg"
                    title="Edit post"
                  >
                    <Edit2 size={18} />
                  </button>
                  <button
                    onClick={() => handleDelete(post.id)}
                    className="p-2 text-gray-400 hover:bg-gray-100 hover:text-red-600 rounded-lg"
                    title="Delete post"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>

              {/* Post Content */}
              <div className="prose max-w-none">
                <p className="text-gray-700 whitespace-pre-wrap">{post.content}</p>
              </div>

              {/* Post Footer */}
              {post.is_pinned && (
                <div className="mt-4 pt-4 border-t border-yellow-200">
                  <p className="text-sm text-yellow-700 flex items-center gap-2">
                    <Pin size={14} />
                    This post is pinned by admins
                  </p>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

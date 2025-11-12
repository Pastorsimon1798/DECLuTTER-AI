import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useResourcesStore } from '../../store/resourcesStore';
import {
  ArrowLeft,
  MapPin,
  Phone,
  Globe,
  Clock,
  Bookmark,
  Mail,
  FileText,
  Users,
} from 'lucide-react';

export default function ResourceDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const {
    currentResource,
    loading,
    error,
    fetchResource,
    createBookmark,
    deleteBookmark,
    clearCurrent,
  } = useResourcesStore();

  const [bookmarkNotes, setBookmarkNotes] = useState('');
  const [showBookmarkModal, setShowBookmarkModal] = useState(false);

  useEffect(() => {
    fetchResource(id);
    return () => clearCurrent();
  }, [id]);

  const handleToggleBookmark = async () => {
    try {
      if (currentResource.is_bookmarked) {
        await deleteBookmark(currentResource.bookmark_id, currentResource.id);
      } else {
        setShowBookmarkModal(true);
      }
    } catch (error) {
      alert('Failed to update bookmark');
    }
  };

  const handleSaveBookmark = async () => {
    try {
      await createBookmark(currentResource.id, bookmarkNotes);
      setShowBookmarkModal(false);
      setBookmarkNotes('');
      await fetchResource(id); // Refresh to update bookmark status
    } catch (error) {
      alert('Failed to save bookmark');
    }
  };

  if (loading && !currentResource) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Loading resource details...</div>
      </div>
    );
  }

  if (error && !currentResource) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
          {error}
        </div>
        <button
          onClick={() => navigate('/resources')}
          className="mt-4 text-blue-600 hover:underline"
        >
          ← Back to Resources
        </button>
      </div>
    );
  }

  if (!currentResource) return null;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back Button */}
      <button
        onClick={() => navigate('/resources')}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft size={20} />
        Back to Resources
      </button>

      {/* Resource Details Card */}
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-green-600 to-green-700 p-6 text-white">
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <h1 className="text-3xl font-bold mb-2">{currentResource.name}</h1>
              <span className="inline-block px-3 py-1 bg-white bg-opacity-20 rounded-full text-sm">
                {currentResource.category.replace('_', ' ')}
              </span>
            </div>
            <button
              onClick={handleToggleBookmark}
              className={`p-3 rounded-lg ${
                currentResource.is_bookmarked
                  ? 'bg-yellow-500 text-white'
                  : 'bg-white bg-opacity-20 hover:bg-opacity-30'
              }`}
            >
              <Bookmark size={24} fill={currentResource.is_bookmarked ? 'currentColor' : 'none'} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Description */}
          {currentResource.description && (
            <div className="mb-6">
              <h2 className="text-xl font-semibold mb-2">About</h2>
              <p className="text-gray-700 whitespace-pre-wrap">{currentResource.description}</p>
            </div>
          )}

          {/* Contact Information */}
          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-3">Contact Information</h2>
            <div className="space-y-3">
              {currentResource.location_address && (
                <div className="flex items-start gap-3">
                  <MapPin className="text-green-600 mt-1" size={20} />
                  <div>
                    <div className="font-medium text-gray-900">Address</div>
                    <div className="text-gray-600">{currentResource.location_address}</div>
                  </div>
                </div>
              )}

              {currentResource.phone && (
                <div className="flex items-start gap-3">
                  <Phone className="text-green-600 mt-1" size={20} />
                  <div>
                    <div className="font-medium text-gray-900">Phone</div>
                    <a href={`tel:${currentResource.phone}`} className="text-blue-600 hover:underline">
                      {currentResource.phone}
                    </a>
                  </div>
                </div>
              )}

              {currentResource.email && (
                <div className="flex items-start gap-3">
                  <Mail className="text-green-600 mt-1" size={20} />
                  <div>
                    <div className="font-medium text-gray-900">Email</div>
                    <a href={`mailto:${currentResource.email}`} className="text-blue-600 hover:underline">
                      {currentResource.email}
                    </a>
                  </div>
                </div>
              )}

              {currentResource.website && (
                <div className="flex items-start gap-3">
                  <Globe className="text-green-600 mt-1" size={20} />
                  <div>
                    <div className="font-medium text-gray-900">Website</div>
                    <a
                      href={currentResource.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      {currentResource.website}
                    </a>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Hours */}
          {currentResource.hours && (
            <div className="mb-6">
              <h2 className="text-xl font-semibold mb-3 flex items-center gap-2">
                <Clock size={20} />
                Hours
              </h2>
              <div className="bg-gray-50 rounded-lg p-4">
                <pre className="text-sm text-gray-700">{JSON.stringify(currentResource.hours, null, 2)}</pre>
              </div>
            </div>
          )}

          {/* Services */}
          {currentResource.services && currentResource.services.length > 0 && (
            <div className="mb-6">
              <h2 className="text-xl font-semibold mb-3 flex items-center gap-2">
                <FileText size={20} />
                Services Offered
              </h2>
              <div className="flex flex-wrap gap-2">
                {currentResource.services.map((service, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm"
                  >
                    {service}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Languages */}
          {currentResource.languages && currentResource.languages.length > 0 && (
            <div className="mb-6">
              <h2 className="text-xl font-semibold mb-3 flex items-center gap-2">
                <Users size={20} />
                Languages
              </h2>
              <div className="flex flex-wrap gap-2">
                {currentResource.languages.map((lang, idx) => (
                  <span key={idx} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                    {lang}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Eligibility */}
          {currentResource.eligibility_requirements && (
            <div className="mb-6">
              <h2 className="text-xl font-semibold mb-2">Eligibility Requirements</h2>
              <p className="text-gray-700">{currentResource.eligibility_requirements}</p>
            </div>
          )}

          {/* Documents Required */}
          {currentResource.documents_required && currentResource.documents_required.length > 0 && (
            <div className="mb-6">
              <h2 className="text-xl font-semibold mb-2">Documents Required</h2>
              <ul className="list-disc list-inside text-gray-700">
                {currentResource.documents_required.map((doc, idx) => (
                  <li key={idx}>{doc}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Call to Action */}
          <div className="border-t pt-6">
            <p className="text-gray-600 text-sm mb-4">
              Need help? Consider posting a need on our community board.
            </p>
            <button
              onClick={() => navigate('/posts/create')}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Post a Need
            </button>
          </div>
        </div>
      </div>

      {/* Bookmark Modal */}
      {showBookmarkModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h2 className="text-2xl font-bold mb-4">Save Bookmark</h2>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Notes (optional)
              </label>
              <textarea
                value={bookmarkNotes}
                onChange={(e) => setBookmarkNotes(e.target.value)}
                placeholder="Add any personal notes about this resource..."
                className="w-full border-gray-300 rounded-lg"
                rows={4}
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleSaveBookmark}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Save Bookmark
              </button>
              <button
                onClick={() => {
                  setShowBookmarkModal(false);
                  setBookmarkNotes('');
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

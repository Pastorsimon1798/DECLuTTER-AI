import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useResourcesStore } from '../../store/resourcesStore';
import { useSettingsStore } from '../../store/settingsStore';
import { formatDistance, radiusFromMeters, radiusToMeters, getRadiusSliderConfig } from '../../utils/units';
import ResourceMapView from './ResourceMapView';
import { MapPin, Search, Filter, List, Map, Bookmark, Phone, Globe, Clock, ArrowUpDown } from 'lucide-react';

export default function ResourceSearchPage() {
  const { t } = useTranslation('resources');
  const navigate = useNavigate();
  const {
    resources,
    filters,
    loading,
    error,
    searchResources,
    setFilters,
    clearFilters,
    createBookmark,
    deleteBookmark,
  } = useResourcesStore();
  const { unitSystem } = useSettingsStore();

  const [viewMode, setViewMode] = useState('list'); // 'list' or 'map'
  const [showFilters, setShowFilters] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    // Get user's location
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setFilters({
            lat: position.coords.latitude,
            lon: position.coords.longitude,
          });
          searchResources();
        },
        (error) => {
          console.error('Error getting location:', error);
          // Search without location
          searchResources();
        }
      );
    } else {
      searchResources();
    }
  }, []);

  const handleSearch = () => {
    setFilters({ query: searchQuery });
    searchResources();
  };

  const handleCategoryFilter = (category) => {
    setFilters({ category: category || null });
    searchResources();
  };

  const handleToggleBookmark = async (resource) => {
    try {
      if (resource.is_bookmarked) {
        await deleteBookmark(resource.bookmark_id, resource.id);
      } else {
        await createBookmark(resource.id);
      }
      searchResources(); // Refresh to update bookmark status
    } catch (error) {
      alert('Failed to update bookmark');
    }
  };

  // Phase 3.5: Expanded categories (Option A: 8 main categories)
  const categories = [
    { value: 'food', label: t('categories.food'), icon: '🍎' },
    { value: 'shelter', label: t('categories.shelter'), icon: '🏠' },
    { value: 'healthcare', label: t('categories.healthcare'), icon: '⚕️' },
    { value: 'clothing_household', label: t('categories.clothing_household'), icon: '👕' },
    { value: 'legal', label: t('categories.legal'), icon: '⚖️' },
    { value: 'financial', label: t('categories.financial'), icon: '💰' },
    { value: 'employment_education', label: t('categories.employment_education'), icon: '💼' },
    { value: 'transportation', label: t('categories.transportation'), icon: '🚌' },
  ];

  // Phase 3.5: Population-specific filters
  const populationFilters = [
    { value: 'veterans', label: t('populationTags.veterans'), icon: '🎖️' },
    { value: 'lgbtq', label: t('populationTags.lgbtq'), icon: '🏳️‍🌈' },
    { value: 'families', label: t('populationTags.families'), icon: '👨‍👩‍👧' },
    { value: 'immigrants', label: t('populationTags.immigrants'), icon: '🌍' },
    { value: 'disability_accessible', label: t('populationTags.disability_accessible'), icon: '♿' },
    { value: 'youth', label: t('populationTags.youth'), icon: '👶' },
    { value: 'seniors', label: t('populationTags.seniors'), icon: '👴' },
  ];

  if (loading && resources.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">{t('common:loading', 'Loading...')}</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2 mb-2">
          <MapPin size={32} />
          {t('search.title')}
        </h1>
        <p className="text-gray-600">{t('search.subtitle', 'Discover food pantries, shelters, and community resources nearby')}</p>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder={t('search.searchPlaceholder')}
              className="w-full pl-10 pr-4 py-3 border-gray-300 rounded-lg"
            />
            <Search className="absolute left-3 top-3.5 text-gray-400" size={20} />
          </div>
          <button
            onClick={handleSearch}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            {t('search.searchButton', 'Search')}
          </button>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
            title={showFilters ? t('search.hideFilters') : t('search.showFilters')}
          >
            <Filter size={20} />
          </button>
        </div>
      </div>

      {/* Category Pills */}
      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={() => handleCategoryFilter(null)}
          className={`px-4 py-2 rounded-full text-sm font-medium ${
            !filters.category
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          {t('common:all')}
        </button>
        {categories.map((cat) => (
          <button
            key={cat.value}
            onClick={() => handleCategoryFilter(cat.value)}
            className={`px-4 py-2 rounded-full text-sm font-medium flex items-center gap-2 ${
              filters.category === cat.value
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <span>{cat.icon}</span>
            {cat.label}
          </button>
        ))}
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="mb-6 bg-white border border-gray-200 rounded-lg p-4">
          <div className="space-y-4">
            {/* Basic Filters */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('search.radius')}
                </label>
                <select
                  value={filters.radius}
                  onChange={(e) => {
                    setFilters({ radius: parseInt(e.target.value) });
                    searchResources();
                  }}
                  className="w-full border-gray-300 rounded-lg"
                >
                  {unitSystem === 'imperial' ? (
                    <>
                      <option value="1609">1 mi</option>
                      <option value="8047">5 mi</option>
                      <option value="16093">10 mi</option>
                      <option value="24140">15 mi</option>
                      <option value="32187">20 mi</option>
                      <option value="40234">25 mi</option>
                      <option value="48280">30 mi</option>
                      <option value="80467">50 mi</option>
                      <option value="160934">100 mi</option>
                      <option value="241401">150 mi</option>
                      <option value="321869">200 mi</option>
                      <option value="402336">250 mi</option>
                      <option value="482803">300 mi</option>
                      <option value="563270">350 mi</option>
                      <option value="643738">400 mi</option>
                      <option value="724205">450 mi</option>
                      <option value="804672">500 mi</option>
                    </>
                  ) : (
                    <>
                      <option value="1000">1 km</option>
                      <option value="5000">5 km</option>
                      <option value="10000">10 km</option>
                      <option value="25000">25 km</option>
                      <option value="50000">50 km</option>
                      <option value="100000">100 km</option>
                      <option value="200000">200 km</option>
                      <option value="400000">400 km</option>
                      <option value="600000">600 km</option>
                      <option value="804672">800 km</option>
                    </>
                  )}
                </select>
              </div>

              <div className="flex items-end">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.open_now}
                    onChange={(e) => {
                      setFilters({ open_now: e.target.checked });
                      searchResources();
                    }}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm font-medium text-gray-700">{t('search.openNow')}</span>
                </label>
              </div>

              <div className="flex items-end gap-2">
                <button
                  onClick={() => {
                    clearFilters();
                    setSearchQuery('');
                    searchResources();
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  {t('search.clearFilters')}
                </button>
              </div>
            </div>

            {/* Phase 3.5: Population Filters */}
            <div className="border-t pt-4">
              <label className="block text-sm font-medium text-gray-700 mb-3">
                {t('search.populationFiltersTitle')}
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {populationFilters.map((filter) => (
                  <label key={filter.value} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={filters.population_tags?.includes(filter.value) || false}
                      onChange={(e) => {
                        const currentTags = filters.population_tags || [];
                        const newTags = e.target.checked
                          ? [...currentTags, filter.value]
                          : currentTags.filter(t => t !== filter.value);
                        setFilters({ population_tags: newTags.length > 0 ? newTags : null });
                        searchResources();
                      }}
                      className="rounded border-gray-300"
                    />
                    <span className="text-sm flex items-center gap-1">
                      <span>{filter.icon}</span>
                      <span>{filter.label}</span>
                    </span>
                  </label>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {t('search.populationFiltersDisclaimer')}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* View Mode Toggle */}
      <div className="mb-4 flex justify-between items-center">
        <div className="text-sm text-gray-600">
          {t('search.resultsCount', { count: resources.length })}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('list')}
            className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
              viewMode === 'list'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <List size={16} />
            {t('search.listView')}
          </button>
          <button
            onClick={() => setViewMode('map')}
            className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
              viewMode === 'map'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <Map size={16} />
            {t('search.mapView')}
          </button>
        </div>
        
        {/* Sort Dropdown */}
        <div className="flex items-center gap-2">
          <ArrowUpDown size={16} className="text-gray-500" />
          <select
            value={filters.sort_by || 'distance'}
            onChange={(e) => {
              setFilters({ sort_by: e.target.value });
              searchResources();
            }}
            className="px-4 py-2 border border-gray-300 rounded-lg bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="distance">{t('search.sortDistance', 'Distance (Closest First)')}</option>
            <option value="name_asc">{t('search.sortNameAsc', 'Name (A-Z)')}</option>
            <option value="name_desc">{t('search.sortNameDesc', 'Name (Z-A)')}</option>
            <option value="recent">{t('search.sortRecent', 'Recently Added')}</option>
            <option value="verified">{t('search.sortVerified', 'Most Verified')}</option>
            <option value="category">{t('search.sortCategory', 'Category')}</option>
          </select>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          {error}
        </div>
      )}

      {/* Resources List */}
      {viewMode === 'list' && (
        <div className="space-y-4">
          {resources.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <p className="text-gray-600 mb-4">{t('search.noResults')}</p>
              <p className="text-sm text-gray-500">
                {t('search.noResultsDescription')}
              </p>
            </div>
          ) : (
            resources.map((resource) => (
              <div
                key={resource.id}
                className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-start gap-2 mb-2 flex-wrap">
                      <h3
                        className="text-xl font-semibold text-gray-900 hover:text-blue-600 cursor-pointer"
                        onClick={() => navigate(`/resources/${resource.id}`)}
                      >
                        {resource.name}
                      </h3>
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                        {resource.category.replace('_', ' ')}
                      </span>
                      {/* Phase 3.5: Community-Contributed Badge */}
                      {resource.is_community_contributed && (
                        <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded-full flex items-center gap-1">
                          <span>👥</span> {t('badges.community')}
                        </span>
                      )}
                      {/* Phase 3.5: Verification Badge */}
                      {resource.verification_count > 0 && (
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full flex items-center gap-1">
                          <span>✓</span> {t('badges.verified', { count: resource.verification_count })}
                        </span>
                      )}
                    </div>

                    {resource.description && (
                      <p className="text-gray-600 mb-3 line-clamp-2">{resource.description}</p>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                      {resource.location_address && (
                        <div className="flex items-center gap-2 text-gray-700">
                          <MapPin size={16} className="text-gray-400" />
                          <span>{resource.location_address}</span>
                        </div>
                      )}

                      {resource.phone && (
                        <div className="flex items-center gap-2 text-gray-700">
                          <Phone size={16} className="text-gray-400" />
                          <span>{resource.phone}</span>
                        </div>
                      )}

                      {resource.website && (
                        <div className="flex items-center gap-2 text-gray-700">
                          <Globe size={16} className="text-gray-400" />
                          <a
                            href={resource.website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline"
                          >
                            {t('detail.visitWebsite')}
                          </a>
                        </div>
                      )}

                      {resource.hours && (
                        <div className="flex items-center gap-2 text-gray-700">
                          <Clock size={16} className="text-gray-400" />
                          <span>{t('detail.hours')}</span>
                        </div>
                      )}
                    </div>

                    {resource.services && resource.services.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {resource.services.slice(0, 3).map((service, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                          >
                            {service}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => handleToggleBookmark(resource)}
                    className={`ml-4 p-2 rounded-lg ${
                      resource.is_bookmarked
                        ? 'bg-yellow-100 text-yellow-600'
                        : 'bg-gray-100 text-gray-400 hover:text-yellow-600'
                    }`}
                  >
                    <Bookmark size={20} fill={resource.is_bookmarked ? 'currentColor' : 'none'} />
                  </button>
                </div>

                <div className="mt-4 pt-4 border-t flex gap-2">
                  <button
                    onClick={() => navigate(`/resources/${resource.id}`)}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    {t('detail.viewDetails')}
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Map View - Phase 3.5: Interactive Map with Leaflet */}
      {viewMode === 'map' && (
        <div>
          {resources.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <Map size={48} className="mx-auto text-gray-400 mb-4" />
              <p className="text-gray-600 mb-2">{t('search.mapNoResults')}</p>
              <p className="text-sm text-gray-500">
                {t('search.mapNoResultsDescription')}
              </p>
            </div>
          ) : (
            <ResourceMapView
              resources={resources}
              center={filters.lat && filters.lon ? [filters.lat, filters.lon] : null}
            />
          )}
        </div>
      )}
    </div>
  );
}

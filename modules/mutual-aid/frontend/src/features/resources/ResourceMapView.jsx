import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { MapPin, Phone, Navigation } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default marker icons in React Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Component to update map center when location changes
function ChangeMapCenter({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, zoom);
    }
  }, [center, zoom, map]);
  return null;
}

export default function ResourceMapView({ resources, center, onMarkerClick }) {
  const navigate = useNavigate();
  const mapRef = useRef();

  // Default center (US center) if no location provided
  const defaultCenter = center || [39.8283, -98.5795];
  const defaultZoom = center ? 12 : 4;

  return (
    <div className="h-[600px] rounded-lg overflow-hidden shadow-lg">
      <MapContainer
        center={defaultCenter}
        zoom={defaultZoom}
        style={{ height: '100%', width: '100%' }}
        ref={mapRef}
      >
        <ChangeMapCenter center={center} zoom={defaultZoom} />

        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {resources.map((resource) => {
          // Skip resources without location coordinates
          if (!resource.lat || !resource.lon) return null;

          // Use lat/lon from API response
          const position = [resource.lat, resource.lon];

          return (
            <Marker key={resource.id} position={position}>
              <Popup>
                <div className="p-2">
                  <h3 className="font-semibold text-lg mb-2">{resource.name}</h3>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <MapPin size={14} />
                      <span className="text-gray-600">{resource.location_address}</span>
                    </div>
                    {resource.phone && (
                      <div className="flex items-center gap-2 text-sm">
                        <Phone size={14} />
                        <a href={`tel:${resource.phone}`} className="text-blue-600 hover:underline">
                          {resource.phone}
                        </a>
                      </div>
                    )}
                    {resource.is_community_contributed && (
                      <span className="inline-block px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">
                        👥 Community
                      </span>
                    )}
                  </div>
                  <div className="mt-3 flex gap-2">
                    <button
                      onClick={() => navigate(`/resources/${resource.id}`)}
                      className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                    >
                      View Details
                    </button>
                    {resource.location_address && (
                      <a
                        href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(resource.location_address)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 flex items-center gap-1"
                      >
                        <Navigation size={14} />
                        Directions
                      </a>
                    )}
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}

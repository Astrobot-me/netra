// 1. Import necessary Leaflet and React Leaflet components
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// 2. Import marker images
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

// 3. Fix default Leaflet marker icon paths
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
})

interface MiniMapProps {
  lat: number;
  lng: number;
}

const MiniMap = ({ lat, lng }: MiniMapProps) => {
  return (
    <div className="bg-gray-800 rounded-lg p-4 shadow-lg h-full">
      <h3 className="text-lg font-medium mb-2 flex items-center text-white">
        <i className="fas fa-map-marker-alt mr-2 text-red-400"></i>
        Current Location
      </h3>
      <div className="h-40 rounded overflow-hidden">
        <MapContainer center={[lat, lng]} zoom={13} scrollWheelZoom={false} className="h-full w-full">
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="http://osm.org/copyright">OpenStreetMap</a>'
          />
          <Marker position={[lat, lng]}>
            <Popup>Vehicle Location</Popup>
          </Marker>
        </MapContainer>
      </div>
      <p className="text-gray-400 text-sm mt-2 text-center">Live GPS feed</p>
    </div>
  );
};

export default MiniMap;

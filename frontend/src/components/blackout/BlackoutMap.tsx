import React from "react";
import { MapContainer, TileLayer, Polygon } from "react-leaflet";
import "leaflet/dist/leaflet.css";

// TODO: Should read from Redux/blackoutSlice
const blackoutZones = [
  { id: 'z1', name: 'Zone 1', status: 'ONLINE', positions: [[19.091, 72.881],[19.094, 72.881],[19.094, 72.886],[19.091, 72.886]] },
  { id: 'z2', name: 'Zone 2', status: 'OFFLINE', positions: [[19.089, 72.889],[19.092, 72.889],[19.092, 72.894],[19.089, 72.894]] },
];
const getPowerStateColor = (status: string) => {
  if(status === 'ONLINE') return 'green';
  if(status === 'OFFLINE') return 'red';
  if(status === 'WARNING') return 'yellow';
  if(status === 'CRITICAL') return 'darkred';
  return 'gray';
};

const BlackoutMap: React.FC = () => (
  <div className="w-full h-[350px] rounded-xl overflow-hidden shadow-lg">
    <MapContainer center={[19.092, 72.886]} zoom={15} scrollWheelZoom={false} style={{ height: '100%', width: '100%' }}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {blackoutZones.map(zone => (
        <Polygon key={zone.id} positions={zone.positions} pathOptions={{ color: getPowerStateColor(zone.status), fillOpacity: 0.4 }} />
      ))}
    </MapContainer>
  </div>
);

export default BlackoutMap;

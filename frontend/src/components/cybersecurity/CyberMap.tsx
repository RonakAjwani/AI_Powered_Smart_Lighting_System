import React from "react";
import { MapContainer, TileLayer, Polygon } from "react-leaflet";
import "leaflet/dist/leaflet.css";

// TODO: Should read from Redux/cyberSlice
const cyberZones = [
  { id: 'downtown', name: 'Downtown', security_state: "GREEN", positions: [[19.08, 72.85],[19.085, 72.85],[19.085, 72.865],[19.08, 72.865]] },
  { id: 'midtown', name: 'Midtown', security_state: "RED", positions: [[19.09, 72.86],[19.094, 72.86],[19.094, 72.87],[19.09, 72.87]] },
];
const getStateColor = (state: string) => {
  if(state === "GREEN") return "green";
  if(state === "YELLOW") return "yellow";
  if(state === "RED") return "red";
  return "gray";
};

const CyberMap: React.FC = () => (
  <div className="w-full h-[350px] rounded-xl overflow-hidden shadow-lg">
    <MapContainer center={[19.09, 72.86]} zoom={14} scrollWheelZoom={false} style={{ height: '100%', width: '100%' }}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {cyberZones.map(zone => (
        <Polygon key={zone.id} positions={zone.positions} pathOptions={{ color: getStateColor(zone.security_state), fillOpacity: 0.4 }} />
      ))}
    </MapContainer>
  </div>
);

export default CyberMap;

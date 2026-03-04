import React from "react";
import { MapContainer, TileLayer, Polygon, CircleMarker } from "react-leaflet";
import "leaflet/dist/leaflet.css";

// TODO: Read zones/lightpoles from Redux; for now, use static example
const ZONES = [
  { id: 'air', name: 'Airport', color: 'orange', positions: [[19.09, 72.86],[19.10, 72.86],[19.10, 72.88],[19.09, 72.88]] },
];
const LIGHT_POLES = [
  { id: 1, lat: 19.095, lng: 72.87, status: 'ONLINE', brightness: 80 },
  { id: 2, lat: 19.098, lng: 72.865, status: 'OFFLINE', brightness: 0 },
];
const getPoleColor = (status: string, brightness: number) => {
  if(status === "OFFLINE") return "red";
  if(status === "MAINTENANCE") return "yellow";
  return `rgba(16, 185, 129, ${brightness / 100})`; // greenish, opacity by brightness
};

const InteractiveMap: React.FC = () => (
  <div className="w-full h-[350px] rounded-xl overflow-hidden shadow-lg">
    <MapContainer center={[19.095, 72.87]} zoom={15} scrollWheelZoom={false} style={{ height: '100%', width: '100%' }}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {ZONES.map(zone => (
        <Polygon key={zone.id} positions={zone.positions} pathOptions={{ color: zone.color, fillOpacity: 0.4 }} />
      ))}
      {LIGHT_POLES.map(pole => (
        <CircleMarker
          key={pole.id}
          center={[pole.lat, pole.lng]}
          radius={10}
          pathOptions={{ color: getPoleColor(pole.status, pole.brightness), fillColor: getPoleColor(pole.status, pole.brightness), fillOpacity: 0.65 }}
        />
      ))}
    </MapContainer>
  </div>
);

export default InteractiveMap;

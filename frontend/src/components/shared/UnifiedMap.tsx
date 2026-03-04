'use client';

import React, { useState } from 'react';
import dynamic from 'next/dynamic';
import { useDashboardStore } from '@/store/useDashboardStore';
import toast from 'react-hot-toast';
import 'leaflet/dist/leaflet.css';

const MapContainer = dynamic(() => import('react-leaflet').then((m) => m.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import('react-leaflet').then((m) => m.TileLayer), { ssr: false });
const Polygon = dynamic(() => import('react-leaflet').then((m) => m.Polygon), { ssr: false });
const CircleMarker = dynamic(() => import('react-leaflet').then((m) => m.CircleMarker), { ssr: false });
const Popup = dynamic(() => import('react-leaflet').then((m) => m.Popup), { ssr: false });
const Tooltip = dynamic(() => import('react-leaflet').then((m) => m.Tooltip), { ssr: false });

const weatherZones = [
  { id: 'air', name: 'Airport Zone', color: 'orange', temp: 28, humidity: 65, condition: 'Clear', positions: [[19.09, 72.86],[19.10, 72.86],[19.10, 72.88],[19.09, 72.88]] },
  { id: 'downtown', name: 'Downtown', color: 'blue', temp: 26, humidity: 70, condition: 'Cloudy', positions: [[19.08, 72.85],[19.085, 72.85],[19.085, 72.865],[19.08, 72.865]] },
];
const weatherPoles = [
  { id: 1, lat: 19.095, lng: 72.87, status: 'ONLINE', brightness: 80, zone: 'Airport' },
  { id: 2, lat: 19.098, lng: 72.865, status: 'OFFLINE', brightness: 0, zone: 'Airport' },
  { id: 3, lat: 19.083, lng: 72.855, status: 'ONLINE', brightness: 90, zone: 'Downtown' },
];
const getPoleColor = (status: string, brightness: number) => {
  if (status === 'OFFLINE') return 'red';
  if (status === 'MAINTENANCE') return 'yellow';
  return `rgba(16, 185, 129, ${brightness / 100})`;
};

const cyberZones = [
  { id: 'downtown', name: 'Downtown Sector', security_state: 'GREEN', threats: 0, lastScan: '2 min ago', positions: [[19.08, 72.85],[19.085, 72.85],[19.085, 72.865],[19.08, 72.865]] },
  { id: 'midtown', name: 'Midtown Sector', security_state: 'RED', threats: 3, lastScan: '1 min ago', positions: [[19.09, 72.86],[19.094, 72.86],[19.094, 72.87],[19.09, 72.87]] },
  { id: 'residential', name: 'Residential Area', security_state: 'YELLOW', threats: 1, lastScan: '5 min ago', positions: [[19.075, 72.875],[19.08, 72.875],[19.08, 72.89],[19.075, 72.89]] },
];
const getStateColor = (state: string) => {
  if (state === 'GREEN') return 'green';
  if (state === 'YELLOW') return 'yellow';
  if (state === 'RED') return 'red';
  return 'gray';
};

const blackoutZones = [
  { id: 'z1', name: 'Power Zone 1', status: 'ONLINE', load: 850, capacity: 1000, positions: [[19.091, 72.881],[19.094, 72.881],[19.094, 72.886],[19.091, 72.886]] },
  { id: 'z2', name: 'Power Zone 2', status: 'OFFLINE', load: 0, capacity: 1000, positions: [[19.089, 72.889],[19.092, 72.889],[19.092, 72.894],[19.089, 72.894]] },
  { id: 'z3', name: 'Power Zone 3', status: 'WARNING', load: 920, capacity: 1000, positions: [[19.095, 72.895],[19.098, 72.895],[19.098, 72.90],[19.095, 72.90]] },
];
const getPowerStateColor = (status: string) => {
  if (status === 'ONLINE') return 'green';
  if (status === 'OFFLINE') return 'red';
  if (status === 'WARNING') return 'yellow';
  if (status === 'CRITICAL') return 'darkred';
  return 'gray';
};

const UnifiedMap: React.FC = () => {
  const selectedAgentView = useDashboardStore((state) => state.selectedAgentView);
  const weatherScenario = useDashboardStore((s) => s.weatherScenario);
  const cyberAttackType = useDashboardStore((s) => s.cyberAttackType);
  const cyberTargetZone = useDashboardStore((s) => s.cyberTargetZone);
  const blackoutScenario = useDashboardStore((s) => s.blackoutScenario);
  const [isClient, setIsClient] = React.useState(false);
  const [selectedZone, setSelectedZone] = useState<string | null>(null);

  React.useEffect(() => setIsClient(true), []);

  const handleZoneClick = (zoneId: string, zoneName: string) => {
    setSelectedZone(zoneId);
    toast.success(`Selected ${zoneName}`, { icon: 'OK', duration: 2000 });
  };

  if (!isClient) {
    return (
      <div className="w-full h-[350px] rounded-xl overflow-hidden shadow-lg bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
        <p className="text-gray-500 dark:text-gray-400">Loading map...</p>
      </div>
    );
  }

  let polygons: any[] = [];
  let markers: any[] = [];

  if (selectedAgentView === 'weather') {
    polygons = weatherZones.map((zone) => (
      <Polygon
        key={zone.id}
        positions={zone.positions}
        pathOptions={{ color: zone.color, fillOpacity: weatherScenario === 'dense-fog' ? 0.2 : (selectedZone === zone.id ? 0.6 : 0.4), weight: selectedZone === zone.id ? 3 : 2 }}
        eventHandlers={{ click: () => handleZoneClick(zone.id, zone.name) }}
      >
        <Tooltip direction="top" offset={[0, -10]} opacity={0.9}>
          <div className="text-xs">
            <strong>{zone.name}</strong>
            <br />
            Temp: {zone.temp} C
            <br />
            Humidity: {zone.humidity}%
            <br />
            Condition: {zone.condition}
          </div>
        </Tooltip>
      </Polygon>
    ));
    markers = weatherPoles.map((pole) => (
      <CircleMarker key={pole.id} center={[pole.lat, pole.lng]} radius={10} pathOptions={{ color: getPoleColor(pole.status, pole.brightness), fillColor: getPoleColor(pole.status, pole.brightness), fillOpacity: 0.75 }}>
        <Tooltip direction="top" offset={[0, -5]} opacity={0.9}>
          <div className="text-xs">
            <strong>Light Pole #{pole.id}</strong>
            <br />
            Zone: {pole.zone}
            <br />
            Status: {pole.status}
            <br />
            Brightness: {pole.brightness}%
          </div>
        </Tooltip>
      </CircleMarker>
    ));
  } else if (selectedAgentView === 'cybersecurity') {
    polygons = cyberZones.map((zone) => (
      <Polygon
        key={zone.id}
        positions={zone.positions}
        pathOptions={{
          color: getStateColor(
            cyberAttackType && cyberTargetZone && zone.id === (cyberTargetZone as string)
              ? 'RED'
              : zone.security_state
          ),
          fillOpacity: selectedZone === zone.id ? 0.6 : 0.4,
          weight: selectedZone === zone.id ? 3 : 2,
        }}
        eventHandlers={{ click: () => handleZoneClick(zone.id, zone.name) }}
      >
        <Tooltip direction="top" offset={[0, -10]} opacity={0.9}>
          <div className="text-xs">
            <strong>{zone.name}</strong>
            <br />
            Security: {zone.security_state}
            <br />
            Threats: {zone.threats}
            <br />
            Last Scan: {zone.lastScan}
          </div>
        </Tooltip>
        <Popup>
          <div className="text-sm">
            <h3 className="font-bold mb-2">{zone.name}</h3>
            <p>
              Security State: <span className="font-semibold">{zone.security_state}</span>
            </p>
            <p>
              Active Threats: <span className="font-semibold">{zone.threats}</span>
            </p>
            <p>
              Last Scan: <span className="font-semibold">{zone.lastScan}</span>
            </p>
            <button className="mt-2 px-3 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600" onClick={() => toast.success(`Initiated security scan for ${zone.name}`)}>
              Run Scan
            </button>
          </div>
        </Popup>
      </Polygon>
    ));
    markers = [];
  } else if (selectedAgentView === 'power') {
    const decorateStatus = (status: string, id: string) => {
      if (blackoutScenario === 'cyber-major' && id === 'z2') return 'OFFLINE';
      if (blackoutScenario === 'equipment-minor' && id === 'z3') return 'WARNING';
      if (blackoutScenario === 'weather-catastrophe') return 'WARNING';
      return status;
    };
    polygons = blackoutZones.map((zone) => (
      <Polygon
        key={zone.id}
        positions={zone.positions}
        pathOptions={{ color: getPowerStateColor(decorateStatus(zone.status, zone.id)), fillOpacity: selectedZone === zone.id ? 0.6 : 0.4, weight: selectedZone === zone.id ? 3 : 2 }}
        eventHandlers={{ click: () => handleZoneClick(zone.id, zone.name) }}
      >
        <Tooltip direction="top" offset={[0, -10]} opacity={0.9}>
          <div className="text-xs">
            <strong>{zone.name}</strong>
            <br />
            Status: {zone.status}
            <br />
            Load: {zone.load} kW
            <br />
            Capacity: {zone.capacity} kW
            <br />
            Usage: {Math.round((zone.load / zone.capacity) * 100)}%
          </div>
        </Tooltip>
        <Popup>
          <div className="text-sm">
            <h3 className="font-bold mb-2">{zone.name}</h3>
            <p>
              Status: <span className="font-semibold">{zone.status}</span>
            </p>
            <p>
              Current Load: <span className="font-semibold">{zone.load} kW</span>
            </p>
            <p>
              Capacity: <span className="font-semibold">{zone.capacity} kW</span>
            </p>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
              <div className="bg-green-500 h-2 rounded-full" style={{ width: `${(zone.load / zone.capacity) * 100}%` }} />
            </div>
          </div>
        </Popup>
      </Polygon>
    ));
    markers = [];
  }

  // Simple legend based on view
  const legend = () => {
    if (selectedAgentView === 'cybersecurity') {
      return (
        <div className="absolute top-3 right-3 bg-[#0d1b2e] border border-gray-800 rounded px-3 py-2 text-xs text-gray-300">
          <div className="font-semibold mb-1">Security</div>
          <div className="flex items-center gap-2"><span className="w-2 h-2 bg-green-500 rounded-full"/>Secure</div>
          <div className="flex items-center gap-2"><span className="w-2 h-2 bg-yellow-500 rounded-full"/>Warning</div>
          <div className="flex items-center gap-2"><span className="w-2 h-2 bg-red-500 rounded-full"/>Under Attack</div>
        </div>
      );
    }
    if (selectedAgentView === 'power') {
      return (
        <div className="absolute top-3 right-3 bg-[#0d1b2e] border border-gray-800 rounded px-3 py-2 text-xs text-gray-300">
          <div className="font-semibold mb-1">Grid</div>
          <div className="flex items-center gap-2"><span className="w-2 h-2 bg-green-500 rounded-full"/>Online</div>
          <div className="flex items-center gap-2"><span className="w-2 h-2 bg-yellow-500 rounded-full"/>Warning</div>
          <div className="flex items-center gap-2"><span className="w-2 h-2 bg-red-500 rounded-full"/>Offline</div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="relative w-full h-[350px] rounded-xl overflow-hidden shadow-lg">
      <MapContainer center={[19.092, 72.886]} zoom={15} scrollWheelZoom={false} style={{ height: '100%', width: '100%' }}>
        <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
        {polygons}
        {markers}
      </MapContainer>
      {legend()}
    </div>
  );
};

export default UnifiedMap;




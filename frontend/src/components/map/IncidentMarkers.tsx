'use client';

import React from 'react';
import { Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';
import { Coordinates } from '@/utils/streetLightGenerator';

export interface Incident {
  id: string;
  type: 'CYBER_ATTACK' | 'POWER_OUTAGE' | 'WEATHER_EVENT' | 'EQUIPMENT_FAILURE';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  location: Coordinates;
  affectedRadius: number; // in km
  timestamp: Date;
  description: string;
  affectedLights: number;
  status: 'ACTIVE' | 'RESOLVING' | 'RESOLVED';
}

interface IncidentMarkersProps {
  incidents: Incident[];
  onIncidentClick?: (incident: Incident) => void;
}

/**
 * Get icon for incident type
 */
const getIncidentIcon = (incident: Incident) => {
  let iconHtml = '';
  let colorClass = 'bg-red-500';

  switch (incident.type) {
    case 'CYBER_ATTACK':
      iconHtml = '🛡️';
      colorClass = 'bg-red-600';
      break;
    case 'POWER_OUTAGE':
      iconHtml = '⚡';
      colorClass = 'bg-orange-600';
      break;
    case 'WEATHER_EVENT':
      iconHtml = '🌧️';
      colorClass = 'bg-blue-600';
      break;
    case 'EQUIPMENT_FAILURE':
      iconHtml = '⚙️';
      colorClass = 'bg-yellow-600';
      break;
  }

  const pulseClass = incident.status === 'ACTIVE' ? 'animate-pulse' : '';

  return L.divIcon({
    html: `
      <div class="relative flex items-center justify-center">
        <div class="absolute w-12 h-12 ${colorClass} opacity-30 rounded-full ${pulseClass}"></div>
        <div class="relative text-2xl z-10 drop-shadow-lg">${iconHtml}</div>
      </div>
    `,
    className: 'incident-marker',
    iconSize: [48, 48],
    iconAnchor: [24, 24],
  });
};

/**
 * Get color for incident radius circle
 */
const getRadiusColor = (incident: Incident): string => {
  switch (incident.severity) {
    case 'CRITICAL':
      return '#dc2626'; // Red
    case 'HIGH':
      return '#ea580c'; // Orange
    case 'MEDIUM':
      return '#ca8a04'; // Yellow
    case 'LOW':
      return '#65a30d'; // Green
    default:
      return '#6b7280'; // Gray
  }
};

/**
 * Format timestamp to relative time
 */
const formatRelativeTime = (timestamp: Date): string => {
  const now = new Date();
  const diff = now.getTime() - timestamp.getTime();
  const minutes = Math.floor(diff / 60000);

  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  const days = Math.floor(hours / 24);
  return `${days}d ago`;
};

export const IncidentMarkers: React.FC<IncidentMarkersProps> = ({
  incidents,
  onIncidentClick,
}) => {
  return (
    <>
      {incidents.map(incident => (
        <React.Fragment key={incident.id}>
          {/* Affected radius circle */}
          <Circle
            center={[incident.location.lat, incident.location.lng]}
            radius={incident.affectedRadius * 1000} // Convert km to meters
            pathOptions={{
              color: getRadiusColor(incident),
              fillColor: getRadiusColor(incident),
              fillOpacity: 0.15,
              weight: 2,
              dashArray: incident.status === 'ACTIVE' ? '10, 5' : undefined,
            }}
          />

          {/* Incident marker */}
          <Marker
            position={[incident.location.lat, incident.location.lng]}
            icon={getIncidentIcon(incident)}
            eventHandlers={{
              click: () => onIncidentClick?.(incident),
            }}
          >
            <Popup maxWidth={300}>
              <div className="space-y-3 p-2">
                {/* Header */}
                <div className="border-b border-gray-300 dark:border-gray-600 pb-2">
                  <h3 className="font-bold text-lg text-gray-800 dark:text-gray-100">
                    {incident.type.replace(/_/g, ' ')}
                  </h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        incident.severity === 'CRITICAL'
                          ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200'
                          : incident.severity === 'HIGH'
                          ? 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-200'
                          : incident.severity === 'MEDIUM'
                          ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-200'
                          : 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200'
                      }`}
                    >
                      {incident.severity}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        incident.status === 'ACTIVE'
                          ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200'
                          : incident.status === 'RESOLVING'
                          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200'
                          : 'bg-gray-100 text-gray-700 dark:bg-gray-900 dark:text-gray-200'
                      }`}
                    >
                      {incident.status}
                    </span>
                  </div>
                </div>

                {/* Details */}
                <div className="space-y-2 text-sm">
                  <p className="text-gray-700 dark:text-gray-300">
                    {incident.description}
                  </p>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Affected Lights:</span>
                      <p className="font-semibold text-gray-800 dark:text-gray-100">
                        {incident.affectedLights}
                      </p>
                    </div>

                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Impact Radius:</span>
                      <p className="font-semibold text-gray-800 dark:text-gray-100">
                        {incident.affectedRadius.toFixed(2)} km
                      </p>
                    </div>

                    <div className="col-span-2">
                      <span className="text-gray-600 dark:text-gray-400">Reported:</span>
                      <p className="font-semibold text-gray-800 dark:text-gray-100">
                        {formatRelativeTime(incident.timestamp)}
                      </p>
                    </div>

                    <div className="col-span-2">
                      <span className="text-gray-600 dark:text-gray-400">Location:</span>
                      <p className="font-mono text-xs text-gray-600 dark:text-gray-400">
                        {incident.location.lat.toFixed(4)}, {incident.location.lng.toFixed(4)}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                {incident.status === 'ACTIVE' && (
                  <div className="pt-2 border-t border-gray-300 dark:border-gray-600">
                    <button
                      onClick={() => onIncidentClick?.(incident)}
                      className="w-full px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm font-medium transition-colors"
                    >
                      View Details & Response
                    </button>
                  </div>
                )}
              </div>
            </Popup>
          </Marker>
        </React.Fragment>
      ))}
    </>
  );
};

export default IncidentMarkers;

'use client';

import React, { useMemo } from 'react';
import { CircleMarker, Tooltip } from 'react-leaflet';
import { StreetLight } from '@/utils/streetLightGenerator';
import { motion } from 'framer-motion';

interface LiveStreetLightMarkersProps {
  streetLights: StreetLight[];
  onLightClick?: (light: StreetLight) => void;
  showAll?: boolean;
  zoomLevel?: number;
}

/**
 * Get color based on street light status
 */
const getStatusColor = (light: StreetLight): string => {
  switch (light.status) {
    case 'ONLINE':
      return `rgba(16, 185, 129, ${light.brightness / 100})`; // Green with brightness opacity
    case 'OFFLINE':
      return '#ef4444'; // Red
    case 'MAINTENANCE':
      return '#f59e0b'; // Amber
    case 'WARNING':
      return '#eab308'; // Yellow
    default:
      return '#6b7280'; // Gray
  }
};

/**
 * Get radius based on zoom and status
 */
const getMarkerRadius = (zoomLevel: number = 15, light: StreetLight): number => {
  const baseRadius = Math.max(2, Math.min(8, zoomLevel - 10));

  if (light.status === 'WARNING' || light.status === 'OFFLINE') {
    return baseRadius * 1.5; // Make problem lights more visible
  }

  return baseRadius;
};

/**
 * Format uptime in human-readable format
 */
const formatUptime = (hours: number): string => {
  if (hours < 24) {
    return `${Math.floor(hours)}h`;
  }
  const days = Math.floor(hours / 24);
  return `${days}d ${Math.floor(hours % 24)}h`;
};

export const LiveStreetLightMarkers: React.FC<LiveStreetLightMarkersProps> = ({
  streetLights,
  onLightClick,
  showAll = false,
  zoomLevel = 15,
}) => {
  // Filter lights based on zoom level for performance
  const visibleLights = useMemo(() => {
    if (showAll || zoomLevel >= 14) {
      return streetLights;
    }

    // At lower zoom levels, show only important lights (offline, warning, or high security)
    return streetLights.filter(
      light =>
        light.status !== 'ONLINE' ||
        light.securityLevel === 'HIGH' ||
        light.securityLevel === 'CRITICAL'
    );
  }, [streetLights, zoomLevel, showAll]);

  // Group lights by status for statistics
  const stats = useMemo(() => {
    return {
      online: streetLights.filter(l => l.status === 'ONLINE').length,
      offline: streetLights.filter(l => l.status === 'OFFLINE').length,
      warning: streetLights.filter(l => l.status === 'WARNING').length,
      maintenance: streetLights.filter(l => l.status === 'MAINTENANCE').length,
      total: streetLights.length,
    };
  }, [streetLights]);

  return (
    <>
      {visibleLights.map(light => (
        <CircleMarker
          key={light.id}
          center={[light.coordinates.lat, light.coordinates.lng]}
          radius={getMarkerRadius(zoomLevel, light)}
          pathOptions={{
            color: getStatusColor(light),
            fillColor: getStatusColor(light),
            fillOpacity: 0.8,
            weight: light.status === 'WARNING' || light.status === 'OFFLINE' ? 2 : 1,
          }}
          eventHandlers={{
            click: () => onLightClick?.(light),
          }}
        >
          <Tooltip
            direction="top"
            offset={[0, -5]}
            opacity={0.95}
            className="street-light-tooltip"
          >
            <div className="text-xs space-y-1 min-w-[200px]">
              <div className="font-bold text-sm border-b border-gray-300 dark:border-gray-600 pb-1">
                {light.id}
              </div>

              <div className="grid grid-cols-2 gap-x-3 gap-y-1 mt-2">
                <span className="text-gray-600 dark:text-gray-400">Status:</span>
                <span
                  className={`font-semibold ${
                    light.status === 'ONLINE'
                      ? 'text-green-600 dark:text-green-400'
                      : light.status === 'OFFLINE'
                      ? 'text-red-600 dark:text-red-400'
                      : 'text-yellow-600 dark:text-yellow-400'
                  }`}
                >
                  {light.status}
                </span>

                <span className="text-gray-600 dark:text-gray-400">Zone:</span>
                <span className="font-medium">{light.zoneId}</span>

                <span className="text-gray-600 dark:text-gray-400">Brightness:</span>
                <span className="font-medium">{light.brightness.toFixed(0)}%</span>

                {light.status === 'ONLINE' && (
                  <>
                    <span className="text-gray-600 dark:text-gray-400">Voltage:</span>
                    <span className="font-medium">{light.voltage.toFixed(1)}V</span>

                    <span className="text-gray-600 dark:text-gray-400">Power:</span>
                    <span className="font-medium">{light.powerRating.toFixed(0)}W</span>

                    <span className="text-gray-600 dark:text-gray-400">Current:</span>
                    <span className="font-medium">{light.current.toFixed(2)}A</span>

                    <span className="text-gray-600 dark:text-gray-400">Temp:</span>
                    <span className="font-medium">{light.temperature.toFixed(1)}°C</span>
                  </>
                )}

                <span className="text-gray-600 dark:text-gray-400">Security:</span>
                <span
                  className={`font-medium ${
                    light.securityLevel === 'CRITICAL' || light.securityLevel === 'HIGH'
                      ? 'text-red-600 dark:text-red-400'
                      : 'text-green-600 dark:text-green-400'
                  }`}
                >
                  {light.securityLevel}
                </span>

                <span className="text-gray-600 dark:text-gray-400">Uptime:</span>
                <span className="font-medium">{formatUptime(light.uptime)}</span>

                <span className="text-gray-600 dark:text-gray-400">Firmware:</span>
                <span className="font-medium text-xs">{light.firmwareVersion}</span>

                <span className="text-gray-600 dark:text-gray-400">Last Comm:</span>
                <span className="font-medium text-xs">
                  {Math.floor((Date.now() - light.lastCommunication.getTime()) / 1000)}s ago
                </span>
              </div>

              {light.connectedLights.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-300 dark:border-gray-600">
                  <span className="text-gray-600 dark:text-gray-400">
                    Connected to {light.connectedLights.length} light{light.connectedLights.length > 1 ? 's' : ''}
                  </span>
                </div>
              )}
            </div>
          </Tooltip>
        </CircleMarker>
      ))}
    </>
  );
};

export default LiveStreetLightMarkers;

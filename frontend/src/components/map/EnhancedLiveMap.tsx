'use client';

import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { useDashboardStore } from '@/store/useDashboardStore';
import { generatePowerGridTopology, PowerGridTopology, updateGridState } from '@/utils/streetLightGenerator';
import toast from 'react-hot-toast';
import { Incident } from './IncidentMarkers';

// Standard Leaflet import
import L from 'leaflet';
import { useMap, useMapEvents } from 'react-leaflet';

// Dynamic Imports — only UI components (NOT hooks)
const MapContainer = dynamic(() => import('react-leaflet').then((m) => m.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import('react-leaflet').then((m) => m.TileLayer), { ssr: false });
const Polygon = dynamic(() => import('react-leaflet').then((m) => m.Polygon), { ssr: false });

// Markers
const LiveStreetLightMarkers = dynamic(() => import('./LiveStreetLightMarkers').then(m => m.LiveStreetLightMarkers), { ssr: false });
const IncidentMarkers = dynamic(() => import('./IncidentMarkers').then(m => m.IncidentMarkers), { ssr: false });

// ── Cybersecurity WebSocket URL ──
const CYBER_WS_URL = 'ws://localhost:8003/ws';

// Component to fix map sizing bugs
const MapRefixer = () => {
  const map = useMap();
  useEffect(() => {
    setTimeout(() => { map.invalidateSize(); }, 100);
    const resizeObserver = new ResizeObserver(() => { map.invalidateSize(); });
    const container = map.getContainer();
    if (container) resizeObserver.observe(container);
    return () => resizeObserver.disconnect();
  }, [map]);
  return null;
};

// Wrapper component for useMapEvents (hooks can't be dynamically imported)
const ZoomTracker = ({ onZoomChange }: { onZoomChange: (zoom: number) => void }) => {
  useMapEvents({
    zoomend: (e) => { onZoomChange(e.target.getZoom()); },
  });
  return null;
};

// Zone colors matching backend simulator
const ZONE_COLORS: Record<string, string> = {
  'SL-ZONE-A': '#ef4444', // Airport — red/critical
  'SL-ZONE-B': '#f97316', // Port — orange/high
  'SL-ZONE-C': '#eab308', // Industrial — yellow/high
  'SL-ZONE-D': '#22c55e', // Residential — green/medium
  'SL-ZONE-E': '#06b6d4', // Hospital — cyan/critical
  'SL-ZONE-F': '#8b5cf6', // Commercial — purple/high
  'SL-ZONE-G': '#ec4899', // Transport Hub — pink/high
};

// Zone names for display
const ZONE_NAMES: Record<string, string> = {
  'SL-ZONE-A': 'Airport Zone',
  'SL-ZONE-B': 'Port Zone',
  'SL-ZONE-C': 'Industrial Zone',
  'SL-ZONE-D': 'Residential Zone',
  'SL-ZONE-E': 'Hospital Zone',
  'SL-ZONE-F': 'Commercial Zone',
  'SL-ZONE-G': 'Transport Hub',
};

interface EnhancedLiveMapProps {
  height?: string;
  showControls?: boolean;
}

export const EnhancedLiveMap: React.FC<EnhancedLiveMapProps> = ({
  height = '600px',
  showControls = true,
}) => {
  const weatherScenario = useDashboardStore((s) => s.weatherScenario);
  const blackoutScenario = useDashboardStore((s) => s.blackoutScenario);
  const activeAttacks = useDashboardStore((s) => s.activeAttacks);
  const addAttack = useDashboardStore((s) => s.addAttack);
  const clearAttack = useDashboardStore((s) => s.clearAttack);

  const [isClient, setIsClient] = useState(false);
  const [gridTopology, setGridTopology] = useState<PowerGridTopology | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [zoomLevel, setZoomLevel] = useState(12);
  const [showAllLights, setShowAllLights] = useState(false);
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  // Track zones that have had attack events recently (for auto-clear)
  const attackTimeoutsRef = useRef<Record<string, NodeJS.Timeout>>({});

  useEffect(() => {
    setIsClient(true);

    // Fix default icons
    const DefaultIcon = L.Icon.Default as any;
    delete DefaultIcon.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
      iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
    });

    const grid = generatePowerGridTopology(600);
    setGridTopology(grid);
  }, []);

  // ── Cybersecurity WebSocket — listen for attack events ──
  const connectWs = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;
    setWsStatus('connecting');

    try {
      const ws = new WebSocket(CYBER_WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setWsStatus('connected');
        console.log('[CyberWS] Connected to cybersecurity backend');
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          const data = msg.data || msg;

          // Attack simulation started
          if (data.event_type === 'attack_simulation_started') {
            const zoneId = data.target_zone || data.zone_id;
            const zoneName = data.target_zone_name || ZONE_NAMES[zoneId] || zoneId;
            addAttack({
              attackId: data.attack_id || `attack-${Date.now()}`,
              attackType: data.attack_type || 'unknown',
              zoneId,
              zoneName,
              intensity: data.intensity || 0.8,
              startedAt: Date.now(),
              severity: data.severity || 'critical',
            });

            // Add incident marker
            if (gridTopology) {
              const zone = gridTopology.zones.find(z => z.id === zoneId);
              if (zone) {
                setIncidents(prev => [...prev, {
                  id: `cyber-${Date.now()}`,
                  type: 'CYBER_ATTACK',
                  severity: 'CRITICAL',
                  location: zone.center,
                  affectedRadius: 1.5,
                  timestamp: new Date(),
                  description: `${data.attack_type?.replace(/_/g, ' ') || 'Attack'} on ${zoneName}`,
                  affectedLights: 30,
                  status: 'ACTIVE',
                }]);

                // Apply visual effect to grid
                setGridTopology(prev => {
                  if (!prev) return prev;
                  return updateGridState(prev, { zoneId, incident: 'CYBER_ATTACK' });
                });
              }
            }

            toast.error(
              `🚨 ATTACK: ${data.attack_type?.replace(/_/g, ' ').toUpperCase() || 'ATTACK'} on ${zoneName}`,
              { duration: 6000, style: { background: '#1e1e2e', color: '#f38ba8', border: '1px solid #f38ba8' } }
            );

            // Auto-clear attack after duration (default 30s) + buffer
            const duration = (data.duration_seconds || 30) * 1000 + 5000;
            if (attackTimeoutsRef.current[zoneId]) clearTimeout(attackTimeoutsRef.current[zoneId]);
            attackTimeoutsRef.current[zoneId] = setTimeout(() => {
              clearAttack(zoneId);
              setIncidents(prev => prev.filter(i => !(i.type === 'CYBER_ATTACK' && i.description?.includes(zoneName))));
              toast.success(`✅ Attack on ${zoneName} has ended`, {
                duration: 4000,
                style: { background: '#1e1e2e', color: '#a6e3a1', border: '1px solid #a6e3a1' },
              });
            }, duration);
          }

          // Suspicious events during active attack — update severity flashes
          if (data.suspicious === true && data.zone_id) {
            const existing = useDashboardStore.getState().activeAttacks[data.zone_id];
            if (!existing) {
              // Suspicious traffic without explicit attack_start — still mark as under attack
              addAttack({
                attackId: data.event_id || `suspicious-${Date.now()}`,
                attackType: data.event_type || 'suspicious_activity',
                zoneId: data.zone_id,
                zoneName: data.zone_name || ZONE_NAMES[data.zone_id] || data.zone_id,
                intensity: 0.5,
                startedAt: Date.now(),
                severity: data.severity || 'high',
              });
              // Auto-clear after 15s if no more events
              if (attackTimeoutsRef.current[data.zone_id]) clearTimeout(attackTimeoutsRef.current[data.zone_id]);
              attackTimeoutsRef.current[data.zone_id] = setTimeout(() => {
                clearAttack(data.zone_id);
              }, 15000);
            } else {
              // Reset the auto-clear timer — attack is still active
              if (attackTimeoutsRef.current[data.zone_id]) clearTimeout(attackTimeoutsRef.current[data.zone_id]);
              attackTimeoutsRef.current[data.zone_id] = setTimeout(() => {
                clearAttack(data.zone_id);
              }, 15000);
            }
          }
        } catch { /* ignore parse errors */ }
      };

      ws.onclose = () => {
        setWsStatus('disconnected');
        console.log('[CyberWS] Disconnected, will retry in 5s');
        reconnectTimerRef.current = setTimeout(connectWs, 5000);
      };

      ws.onerror = () => {
        setWsStatus('disconnected');
      };
    } catch {
      setWsStatus('disconnected');
      reconnectTimerRef.current = setTimeout(connectWs, 5000);
    }
  }, [addAttack, clearAttack, gridTopology]);

  useEffect(() => {
    if (!isClient) return;
    connectWs();
    // Heartbeat
    const ping = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 20000);

    return () => {
      clearInterval(ping);
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      Object.values(attackTimeoutsRef.current).forEach(clearTimeout);
      if (wsRef.current) wsRef.current.close();
    };
  }, [isClient, connectWs]);

  // Update logic for local scenarios (weather, blackout)
  useEffect(() => {
    if (!gridTopology) return;
    let updatedGrid = gridTopology;
    const newIncidents: Incident[] = [];

    const addIncident = (type: any, zoneIdx: number) => {
      const zone = gridTopology.zones[zoneIdx];
      if (!zone) return;
      updatedGrid = updateGridState(updatedGrid, { zoneId: zone.id, incident: type });
      newIncidents.push({
        id: `${type}-${Date.now()}`,
        type,
        severity: 'HIGH',
        location: zone.center,
        affectedRadius: 2.0,
        timestamp: new Date(),
        description: `${type} detected in ${zone.name}`,
        affectedLights: 50,
        status: 'ACTIVE',
      });
    };

    if (weatherScenario !== 'clear') addIncident('WEATHER_EVENT', 0);
    if (blackoutScenario) addIncident('POWER_OUTAGE', 1);

    setGridTopology(updatedGrid);
    setIncidents(prev => [...prev, ...newIncidents]);
  }, [weatherScenario, blackoutScenario]);

  const visibleZones = useMemo(() => {
    if (!gridTopology) return [];
    return gridTopology.zones;
  }, [gridTopology]);

  if (!isClient || !gridTopology) {
    return (
      <div className="w-full h-full flex items-center justify-center text-slate-500 bg-[#0d1b2e]">
        Initializing Map...
      </div>
    );
  }

  const stats = {
    online: gridTopology.streetLights.filter(l => l.status === 'ONLINE').length,
    offline: gridTopology.streetLights.filter(l => l.status === 'OFFLINE').length,
    attackCount: Object.keys(activeAttacks).length,
  };

  return (
    <div
      className="relative w-full z-0 isolate rounded-xl overflow-hidden shadow-2xl border border-slate-700 bg-[#0d1b2e]"
      style={{ height }}
    >
      <MapContainer
        center={[19.05, 72.85]}
        zoom={12}
        scrollWheelZoom={true}
        style={{ height: '100%', width: '100%', background: '#0d1b2e' }}
      >
        <MapRefixer />
        <ZoomTracker onZoomChange={setZoomLevel} />

        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; CARTO'
        />

        {/* Zone polygons — 7 Mumbai zones, red when under attack */}
        {visibleZones.map(zone => {
          const isUnderAttack = !!activeAttacks[zone.id];
          const zoneColor = isUnderAttack ? '#ef4444' : (ZONE_COLORS[zone.id] || '#3b82f6');
          return (
            <Polygon
              key={zone.id}
              positions={zone.bounds.map(b => [b.lat, b.lng])}
              pathOptions={{
                color: zoneColor,
                fillColor: zoneColor,
                fillOpacity: isUnderAttack ? 0.4 : 0.15,
                weight: isUnderAttack ? 3 : 1.5,
                dashArray: isUnderAttack ? '8, 4' : undefined,
              }}
            />
          );
        })}

        <LiveStreetLightMarkers
          streetLights={gridTopology.streetLights}
          showAll={showAllLights}
          zoomLevel={zoomLevel}
          onLightClick={(l) => toast(`Light: ${l.id}`)}
        />

        <IncidentMarkers incidents={incidents} />
      </MapContainer>

      {showControls && (
        <div className="absolute top-4 right-4 bg-slate-900/90 backdrop-blur border border-slate-700 p-4 rounded-xl text-white shadow-xl z-[1000] w-64">
          <h3 className="font-bold border-b border-slate-700 pb-2 mb-2 text-sm text-slate-300">
            GRID STATUS
          </h3>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <span className="text-slate-400">ONLINE</span>
            <span className="text-emerald-400 font-mono text-right">{stats.online}</span>
            <span className="text-slate-400">OFFLINE</span>
            <span className="text-rose-400 font-mono text-right">{stats.offline}</span>
            <span className="text-slate-400">CYBER WS</span>
            <span className={`font-mono text-right ${wsStatus === 'connected' ? 'text-emerald-400' : wsStatus === 'connecting' ? 'text-yellow-400' : 'text-rose-400'}`}>
              {wsStatus === 'connected' ? '● LIVE' : wsStatus === 'connecting' ? '◌ ...' : '○ OFF'}
            </span>
          </div>

          {/* Active attacks banner */}
          {stats.attackCount > 0 && (
            <div className="mt-3 p-2 rounded-lg bg-red-900/40 border border-red-500/40 animate-pulse">
              <div className="text-red-400 font-bold text-xs mb-1">
                🚨 {stats.attackCount} ACTIVE ATTACK{stats.attackCount > 1 ? 'S' : ''}
              </div>
              {Object.values(activeAttacks).map(atk => (
                <div key={atk.zoneId} className="text-[10px] text-red-300 truncate">
                  {atk.attackType.replace(/_/g, ' ')} → {atk.zoneName}
                </div>
              ))}
            </div>
          )}

          <div className="mt-3 pt-2 border-t border-slate-700">
            <label className="flex items-center gap-2 cursor-pointer select-none group">
              <input
                type="checkbox"
                checked={showAllLights}
                onChange={e => setShowAllLights(e.target.checked)}
                className="rounded bg-slate-800 border-slate-600 text-blue-500 focus:ring-0 focus:ring-offset-0"
              />
              <span className="text-[10px] uppercase tracking-wider text-slate-400 group-hover:text-slate-200 transition-colors">
                Show All Nodes
              </span>
            </label>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedLiveMap;

'use client';

import React, { useEffect } from 'react';
import dynamic from 'next/dynamic';
import type { SimulatorStatus, ZoneInfo } from '@/lib/api';

// Standard Leaflet import (only runs client-side due to 'use client')
import L from 'leaflet';
import { useMap } from 'react-leaflet';

// Dynamic imports for react-leaflet components (SSR-safe)
const MapContainer = dynamic(() => import('react-leaflet').then((m) => m.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import('react-leaflet').then((m) => m.TileLayer), { ssr: false });
const Polygon = dynamic(() => import('react-leaflet').then((m) => m.Polygon), { ssr: false });
const CircleMarker = dynamic(() => import('react-leaflet').then((m) => m.CircleMarker), { ssr: false });
const Popup = dynamic(() => import('react-leaflet').then((m) => m.Popup), { ssr: false });
const LeafletTooltip = dynamic(() => import('react-leaflet').then((m) => m.Tooltip), { ssr: false });

// Component to fix map sizing bugs
const MapRefixer = () => {
    const map = useMap();
    useEffect(() => {
        setTimeout(() => {
            map.invalidateSize();
        }, 100);

        const resizeObserver = new ResizeObserver(() => {
            map.invalidateSize();
        });
        const container = map.getContainer();
        if (container) {
            resizeObserver.observe(container);
        }
        return () => resizeObserver.disconnect();
    }, [map]);
    return null;
};

interface Props {
    zones: ZoneInfo[];
    simulatorStatus: SimulatorStatus | null;
}

const PRIORITY_OPACITY: Record<string, number> = {
    critical: 0.5,
    high: 0.35,
    medium: 0.25,
    low: 0.15,
};

export default function CyberMapLeaflet({ zones, simulatorStatus }: Props) {
    const [isClient, setIsClient] = React.useState(false);

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
    }, []);

    if (!isClient) {
        return (
            <div style={{ height: '100%', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#1a1a2e', color: '#6c757d' }}>
                Initializing Map...
            </div>
        );
    }

    const activeAttackZones = new Set(
        simulatorStatus?.active_attacks?.map((a) => a.zone) ?? []
    );

    return (
        <MapContainer
            center={[19.05, 72.85] as any}
            zoom={12}
            style={{ height: '100%', width: '100%', background: '#1a1a2e' }}
            scrollWheelZoom={true}
        >
            <MapRefixer />

            {/* Dark tile layer */}
            <TileLayer
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                attribution='&copy; <a href="https://carto.com">CARTO</a>'
            />

            {/* Zone polygons */}
            {zones.map((zone) => {
                if (!zone.bounds || zone.bounds.length < 2) return null;
                const isUnderAttack = activeAttackZones.has(zone.id);
                const bounds = zone.bounds;
                const polygon: [number, number][] = [
                    [bounds[0][0], bounds[0][1]],
                    [bounds[0][0], bounds[1][1]],
                    [bounds[1][0], bounds[1][1]],
                    [bounds[1][0], bounds[0][1]],
                ];

                return (
                    <Polygon
                        key={zone.id}
                        positions={polygon as any}
                        pathOptions={{
                            color: isUnderAttack ? '#ff0000' : zone.color,
                            weight: isUnderAttack ? 3 : 2,
                            fillColor: zone.color,
                            fillOpacity: PRIORITY_OPACITY[zone.priority] || 0.25,
                            dashArray: isUnderAttack ? '8, 4' : undefined,
                        }}
                    >
                        <LeafletTooltip sticky>
                            <div style={{ fontWeight: 600 }}>{zone.name}</div>
                            <div style={{ fontSize: '0.8rem' }}>{zone.area}</div>
                            <div style={{ fontSize: '0.8rem' }}>
                                Type: {zone.type} | Priority: {zone.priority} | Devices: {zone.device_count}
                            </div>
                            {isUnderAttack && (
                                <div style={{ color: '#dc3545', fontWeight: 700 }}>⚠ UNDER ATTACK</div>
                            )}
                        </LeafletTooltip>
                    </Polygon>
                );
            })}

            {/* Device markers (smart light poles) */}
            {zones.flatMap((zone) =>
                (zone.devices || []).map((device) => {
                    const isZoneAttacked = activeAttackZones.has(device.zone_id);
                    return (
                        <CircleMarker
                            key={device.device_id}
                            center={[device.lat, device.lng] as any}
                            radius={4}
                            pathOptions={{
                                color: isZoneAttacked ? '#ff4444' : zone.color,
                                fillColor: isZoneAttacked ? '#ff4444' : zone.color,
                                fillOpacity: 0.8,
                                weight: 1,
                            }}
                        >
                            <Popup>
                                <div style={{ fontSize: '0.85rem' }}>
                                    <strong>{device.device_id}</strong>
                                    <br />Zone: {device.zone_name}
                                    <br />Status: {device.status}
                                    <br />Brightness: {device.brightness}%
                                    <br />Lat: {device.lat}, Lng: {device.lng}
                                </div>
                            </Popup>
                        </CircleMarker>
                    );
                })
            )}

            {/* Legend */}
            <MapLegend />
        </MapContainer>
    );
}

function MapLegend() {
    const map = useMap();

    React.useEffect(() => {
        const legend = new L.Control({ position: 'bottomright' });
        legend.onAdd = () => {
            const div = L.DomUtil.create('div', 'leaflet-legend');
            div.style.cssText = `
                background: rgba(30, 30, 46, 0.92);
                color: #cdd6f4;
                padding: 10px 14px;
                border-radius: 8px;
                font-size: 12px;
                line-height: 1.8;
                box-shadow: 0 2px 12px rgba(0,0,0,0.3);
            `;
            div.innerHTML = `
                <div style="font-weight:700;margin-bottom:4px">🗺️ Zone Legend</div>
                <div><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#ef4444;margin-right:6px"></span>Airport (Critical)</div>
                <div><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#f97316;margin-right:6px"></span>Port (High)</div>
                <div><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#eab308;margin-right:6px"></span>Industrial (High)</div>
                <div><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#22c55e;margin-right:6px"></span>Residential (Medium)</div>
                <div><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#06b6d4;margin-right:6px"></span>Hospital (Critical)</div>
                <div><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#8b5cf6;margin-right:6px"></span>Commercial (High)</div>
                <div><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#ec4899;margin-right:6px"></span>Transport Hub (High)</div>
                <hr style="border-color:#444;margin:4px 0"/>
                <div><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#ff4444;margin-right:6px"></span>Under Attack</div>
                <div style="margin-top:2px"><span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#89b4fa;margin-right:8px"></span>Smart Light Pole</div>
            `;
            return div;
        };
        legend.addTo(map);

        return () => {
            legend.remove();
        };
    }, [map]);

    return null;
}

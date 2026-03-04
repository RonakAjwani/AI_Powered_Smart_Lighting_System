'use client';

import React, { useMemo, useState } from 'react';
import { CloudSun, Lightbulb, Zap, AlertTriangle, Activity, CloudRain, Wind } from 'lucide-react';
import dynamic from 'next/dynamic';
import MetricCard from '@/components/shared/MetricCard';
import LiveBadge from '@/components/shared/LiveBadge';
import { useDashboardStore } from '@/store/useDashboardStore';
import { LIGHTING_ZONES, MUMBAI_CENTER, LightingZone, LightPole } from '@/types/zones';

// Dynamically import map components
const MapContainer = dynamic(
  () => import('react-leaflet').then((mod) => mod.MapContainer),
  { ssr: false }
);
const TileLayer = dynamic(
  () => import('react-leaflet').then((mod) => mod.TileLayer),
  { ssr: false }
);
const Circle = dynamic(
  () => import('react-leaflet').then((mod) => mod.Circle),
  { ssr: false }
);
const CircleMarker = dynamic(
  () => import('react-leaflet').then((mod) => mod.CircleMarker),
  { ssr: false }
);
const Popup = dynamic(
  () => import('react-leaflet').then((mod) => mod.Popup),
  { ssr: false }
);

const WeatherLightingView: React.FC = () => {
  const weatherScenario = useDashboardStore((s) => s.weatherScenario);
  const systemStatus = useDashboardStore((s) => s.systemStatus);
  const [selectedZone, setSelectedZone] = useState<LightingZone | null>(null);
  const [activeTab, setActiveTab] = useState<'analysis' | 'anomalies'>('analysis');

  // Update zones and poles based on weather
  const zones = useMemo(() => {
    return LIGHTING_ZONES.map(zone => {
      const isCyclone = weatherScenario === 'cyclone';
      const isRain = weatherScenario === 'heavy-rain';
      const isFog = weatherScenario === 'dense-fog';

      let offlinePoles = 0;
      if (isCyclone) offlinePoles = Math.floor(zone.totalPoles * 0.3);
      else if (isRain) offlinePoles = Math.floor(zone.totalPoles * 0.15);

      const onlinePoles = zone.totalPoles - offlinePoles;
      const avgBrightness = isFog ? 95 : isRain ? 90 : isCyclone ? 100 : 85;

      // Update pole statuses
      const updatedPoles = zone.poles.map((pole, idx) => ({
        ...pole,
        status: idx < offlinePoles ? ('offline' as const) : ('online' as const),
        brightness: pole.status === 'online' ? avgBrightness + (Math.random() * 10 - 5) : 0
      }));

      return {
        ...zone,
        onlinePoles,
        avgBrightness,
        poles: updatedPoles
      };
    });
  }, [weatherScenario]);

  const metrics = useMemo(() => {
    const totalPoles = zones.reduce((sum, z) => sum + z.totalPoles, 0);
    const onlinePoles = zones.reduce((sum, z) => sum + z.onlinePoles, 0);
    const avgBrightness = Math.round(
      zones.reduce((sum, z) => sum + z.avgBrightness, 0) / zones.length
    );

    const isCyclone = weatherScenario === 'cyclone';
    const isRain = weatherScenario === 'heavy-rain';
    const isFog = weatherScenario === 'dense-fog';

    const powerLoad = isCyclone ? 1.80 : isRain ? 1.65 : isFog ? 1.60 : 1.53;
    const alert = isCyclone
      ? { v: 'Severe', color: 'text-red-400' as const }
      : isRain
      ? { v: 'Rain', color: 'text-yellow-400' as const }
      : isFog
      ? { v: 'Fog', color: 'text-blue-400' as const }
      : { v: 'Clear', color: 'text-green-400' as const };

    return {
      polesOnline: `${onlinePoles} / ${totalPoles}`,
      onlinePercentage: ((onlinePoles / totalPoles) * 100).toFixed(1),
      avgBrightness: `${avgBrightness}%`,
      powerLoad: powerLoad.toFixed(2),
      alert
    };
  }, [zones, weatherScenario]);

  const getPoleColor = (pole: LightPole) => {
    if (pole.status === 'offline') return '#ef4444';
    if (pole.status === 'maintenance') return '#f59e0b';
    return '#10b981';
  };

  const handleWeatherChange = (scenario: typeof weatherScenario) => {
    useDashboardStore.getState().setWeatherScenario(scenario);
    if (scenario === 'cyclone') {
      useDashboardStore.getState().setSystemStatus('CRITICAL');
    } else if (scenario === 'heavy-rain') {
      useDashboardStore.getState().setSystemStatus('WARNING');
    } else {
      useDashboardStore.getState().setSystemStatus('OPERATIONAL');
    }
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-[#0a1628] to-[#06111f]">
      {/* Header */}
      <div className="bg-[#0a1628]/50 backdrop-blur-sm border-b border-blue-500/20 px-8 py-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-xl border border-blue-500/30 shadow-lg shadow-blue-500/20">
              <CloudSun className="w-8 h-8 text-blue-400" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white mb-1">
                Weather & Lighting Command
              </h2>
              <p className="text-gray-400 text-sm">
                Real-time environmental monitoring & smart grid control
              </p>
            </div>
          </div>
          <LiveBadge
            variant={systemStatus === 'OPERATIONAL' ? 'success' : systemStatus === 'WARNING' ? 'warning' : 'default'}
          />
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="px-8 py-6 bg-[#0a1628]/50">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            icon={Lightbulb}
            iconColor="text-blue-400"
            label="Poles Online"
            value={metrics.polesOnline}
            subtitle={`${metrics.onlinePercentage}% operational`}
            valueColor="text-blue-400"
          />
          <MetricCard
            icon={Activity}
            iconColor="text-yellow-400"
            label="Avg. Brightness"
            value={metrics.avgBrightness}
            subtitle="Network average"
            valueColor="text-yellow-400"
          />
          <MetricCard
            icon={Zap}
            iconColor="text-green-400"
            label="Est. Power Load"
            value={metrics.powerLoad}
            subtitle="kW"
            valueColor="text-green-400"
          />
          <MetricCard
            icon={AlertTriangle}
            iconColor={metrics.alert.color}
            label="Weather Alert"
            value={metrics.alert.v}
            subtitle={metrics.alert.v === 'Clear' ? 'All systems normal' : 'Environmental impact detected'}
            valueColor={metrics.alert.color}
          />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 px-8 py-6 overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
          {/* Map Section */}
          <div className="lg:col-span-2 flex flex-col">
            <div className="bg-[#0d1b2e]/80 backdrop-blur-sm border border-gray-800/50 rounded-xl overflow-hidden shadow-2xl flex-1 relative">
              {typeof window !== 'undefined' && (
                <MapContainer
                  center={MUMBAI_CENTER}
                  zoom={12}
                  style={{ height: '100%', width: '100%' }}
                  className="z-0"
                >
                  <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                    attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                  />

                  {/* Zone boundaries */}
                  {zones.map(zone => (
                    <Circle
                      key={`zone-${zone.id}`}
                      center={zone.position}
                      radius={800}
                      pathOptions={{
                        color: '#3b82f6',
                        fillColor: '#3b82f6',
                        fillOpacity: 0.05,
                        weight: 1,
                        dashArray: '5, 5'
                      }}
                    />
                  ))}

                  {/* Light poles */}
                  {zones.flatMap(zone =>
                    zone.poles.map(pole => (
                      <CircleMarker
                        key={pole.id}
                        center={pole.position}
                        radius={pole.status === 'offline' ? 6 : 5}
                        pathOptions={{
                          color: getPoleColor(pole),
                          fillColor: getPoleColor(pole),
                          fillOpacity: pole.status === 'offline' ? 0.9 : 0.7,
                          weight: 2
                        }}
                      >
                        <Popup>
                          <div className="text-xs">
                            <div className="font-bold text-gray-900 mb-1">{pole.id}</div>
                            <div className="space-y-1">
                              <div>Status: <span className="font-semibold">{pole.status}</span></div>
                              <div>Brightness: <span className="font-semibold">{Math.round(pole.brightness)}%</span></div>
                              <div>Power: <span className="font-semibold">{Math.round(pole.powerConsumption)}W</span></div>
                            </div>
                          </div>
                        </Popup>
                      </CircleMarker>
                    ))
                  )}
                </MapContainer>
              )}

              {/* Zone Info when clicked */}
              {selectedZone && (
                <div className="absolute bottom-4 left-4 bg-[#0d1b2e]/95 backdrop-blur-md border border-gray-700/50 rounded-xl p-4 shadow-2xl z-[1000] max-w-xs">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-bold text-white">{selectedZone.name}</h4>
                    <button
                      onClick={() => setSelectedZone(null)}
                      className="text-gray-400 hover:text-white"
                    >
                      ✕
                    </button>
                  </div>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Total Poles</span>
                      <span className="text-white font-semibold">{selectedZone.totalPoles}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Online</span>
                      <span className="text-green-400 font-semibold">{selectedZone.onlinePoles}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Offline</span>
                      <span className="text-red-400 font-semibold">{selectedZone.totalPoles - selectedZone.onlinePoles}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Avg. Brightness</span>
                      <span className="text-yellow-400 font-semibold">{Math.round(selectedZone.avgBrightness)}%</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Sidebar */}
          <div className="lg:col-span-1 space-y-4 overflow-y-auto max-h-full">
            {/* Weather Simulator */}
            <div className="bg-[#0d1b2e]/80 backdrop-blur-sm border border-gray-800/50 rounded-xl overflow-hidden shadow-xl">
              <div className="p-4 border-b border-gray-800/50 bg-[#0a1628]/50">
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-blue-500/20 rounded-lg">
                    <CloudRain className="w-5 h-5 text-blue-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">Weather Simulation</h3>
                </div>
                <p className="text-xs text-gray-400 mt-2">Environmental scenario testing</p>
              </div>

              <div className="p-4 space-y-2">
                <button
                  onClick={() => handleWeatherChange('heavy-rain')}
                  className="w-full px-4 py-3 rounded-lg bg-gradient-to-r from-blue-600 to-blue-700 text-white font-medium hover:from-blue-700 hover:to-blue-800 transition-all shadow-lg shadow-blue-500/20 flex items-center gap-2"
                >
                  <CloudRain className="w-4 h-4" />
                  <span className="flex-1 text-left">Heavy Rainfall</span>
                </button>

                <button
                  onClick={() => handleWeatherChange('dense-fog')}
                  className="w-full px-4 py-3 rounded-lg bg-gradient-to-r from-gray-600 to-gray-700 text-white font-medium hover:from-gray-700 hover:to-gray-800 transition-all shadow-lg shadow-gray-500/20 flex items-center gap-2"
                >
                  <CloudSun className="w-4 h-4" />
                  <span className="flex-1 text-left">Dense Fog</span>
                </button>

                <button
                  onClick={() => handleWeatherChange('cyclone')}
                  className="w-full px-4 py-3 rounded-lg bg-gradient-to-r from-red-600 to-red-700 text-white font-medium hover:from-red-700 hover:to-red-800 transition-all shadow-lg shadow-red-500/20 flex items-center gap-2"
                >
                  <Wind className="w-4 h-4" />
                  <span className="flex-1 text-left">Cyclone Alert</span>
                </button>

                <button
                  onClick={() => handleWeatherChange('clear')}
                  className="w-full px-4 py-2 rounded-lg bg-gradient-to-r from-green-600 to-green-700 text-white font-medium hover:from-green-700 hover:to-green-800 transition-all shadow-lg shadow-green-500/20"
                >
                  Clear Conditions
                </button>
              </div>
            </div>

            {/* Latest Agent Run Analysis */}
            <div className="bg-[#0d1b2e]/80 backdrop-blur-sm border border-gray-800/50 rounded-xl overflow-hidden shadow-xl">
              <div className="p-4 border-b border-gray-800/50 bg-[#0a1628]/50 flex gap-2">
                <button
                  onClick={() => setActiveTab('analysis')}
                  className={`flex-1 px-3 py-2 text-xs font-medium rounded-lg transition-colors ${
                    activeTab === 'analysis'
                      ? 'bg-blue-500/20 text-blue-400'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  Live Analysis
                </button>
                <button
                  onClick={() => setActiveTab('anomalies')}
                  className={`flex-1 px-3 py-2 text-xs font-medium rounded-lg transition-colors ${
                    activeTab === 'anomalies'
                      ? 'bg-blue-500/20 text-blue-400'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  Anomalies
                </button>
              </div>

              <div className="p-6 space-y-4">
                {activeTab === 'analysis' ? (
                  <>
                    <h3 className="text-sm font-semibold text-white">Latest Agent Run Analysis</h3>

                    <div className="bg-[#0a1628]/50 border border-gray-800 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-medium text-blue-400">Comprehensive Risk</span>
                        <div className="flex items-center gap-2">
                          <div className={`w-14 h-14 rounded-full border-4 flex items-center justify-center ${
                            weatherScenario === 'cyclone' ? 'border-red-500' :
                            weatherScenario === 'heavy-rain' ? 'border-yellow-500' :
                            'border-green-500'
                          }`}>
                            <span className={`text-lg font-bold ${
                              weatherScenario === 'cyclone' ? 'text-red-500' :
                              weatherScenario === 'heavy-rain' ? 'text-yellow-500' :
                              'text-green-500'
                            }`}>
                              {weatherScenario === 'cyclone' ? '95' :
                               weatherScenario === 'heavy-rain' ? '65' :
                               weatherScenario === 'dense-fog' ? '45' : '15'}
                            </span>
                          </div>
                        </div>
                      </div>
                      <p className="text-xs text-gray-400">Risk Score</p>
                    </div>

                    <div className="bg-[#0a1628]/50 border border-gray-800 rounded-lg p-4">
                      <div className="text-xs font-medium text-yellow-400 mb-3">Anomalies by Severity</div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-3">
                          <div className="w-16 h-2.5 bg-orange-500 rounded" />
                          <span className="text-xs text-gray-400">High</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="w-24 h-2.5 bg-yellow-500 rounded" />
                          <span className="text-xs text-gray-400">Medium</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-2.5 bg-blue-500 rounded" />
                          <span className="text-xs text-gray-400">Low</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-xs font-medium text-white mb-2">Anomaly Detection Summary</h4>
                      <div className="bg-[#0a1628]/50 border border-gray-800 rounded-lg p-3">
                        <p className="text-xs text-gray-400 leading-relaxed">
                          {weatherScenario === 'cyclone' && 'Critical weather detected. Multiple poles offline. AI recommends maximum brightness for safety.'}
                          {weatherScenario === 'heavy-rain' && 'Heavy rainfall detected. Some poles offline. Brightness increased for visibility.'}
                          {weatherScenario === 'dense-fog' && 'Dense fog detected. Maximum brightness engaged for public safety.'}
                          {weatherScenario === 'clear' && 'Clear conditions. All systems optimal. AI recommends maintaining current brightness levels.'}
                        </p>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="space-y-3">
                    <h3 className="text-sm font-semibold text-white">Zone Status</h3>
                    {zones.map(zone => (
                      <button
                        key={zone.id}
                        onClick={() => setSelectedZone(zone)}
                        className="w-full bg-[#0a1628]/50 border border-gray-800 rounded-lg p-3 hover:border-blue-500/30 transition-colors text-left"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-medium text-white">{zone.name}</span>
                          <span className="text-xs text-gray-400">{zone.onlinePoles}/{zone.totalPoles}</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-1.5">
                          <div
                            className="bg-blue-500 h-1.5 rounded-full"
                            style={{ width: `${(zone.onlinePoles / zone.totalPoles) * 100}%` }}
                          />
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WeatherLightingView;

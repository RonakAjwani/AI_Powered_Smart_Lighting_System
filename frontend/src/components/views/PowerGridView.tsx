'use client';

import React, { useMemo, useState } from 'react';
import { Zap, Activity, Battery, AlertTriangle, Settings } from 'lucide-react';
import dynamic from 'next/dynamic';
import MetricCard from '@/components/shared/MetricCard';
import LiveBadge from '@/components/shared/LiveBadge';
import { useDashboardStore } from '@/store/useDashboardStore';
import { POWER_ZONES, MUMBAI_CENTER, PowerZone } from '@/types/zones';

// Dynamically import map to avoid SSR issues
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

const PowerGridView: React.FC = () => {
  const blackoutScenario = useDashboardStore((s) => s.blackoutScenario);
  const blackoutCause = useDashboardStore((s) => s.blackoutCause);
  const systemStatus = useDashboardStore((s) => s.systemStatus);

  // Calculate outage impact based on scenario
  const outageData = useMemo(() => {
    if (!blackoutScenario) return null;

    const scenarios = {
      'weather-catastrophe': {
        capacityLost: 450,
        recoveryTime: '12h',
        cascadeRisk: 80,
        affectedZones: ['hospital-power', 'defense-power', 'airport-power', 'commercial-power']
      },
      'cyber-major': {
        capacityLost: 305,
        recoveryTime: '6h',
        cascadeRisk: 60,
        affectedZones: ['defense-power', 'commercial-power', 'airport-power']
      },
      'equipment-minor': {
        capacityLost: 120,
        recoveryTime: '2h',
        cascadeRisk: 30,
        affectedZones: ['commercial-power']
      }
    };

    return scenarios[blackoutScenario] || null;
  }, [blackoutScenario]);

  // Update zones based on blackout
  const zones = useMemo(() => {
    return POWER_ZONES.map(zone => {
      const isAffected = outageData?.affectedZones.includes(zone.id);
      if (isAffected) {
        const lossPercentage = blackoutScenario === 'weather-catastrophe' ? 80 :
                               blackoutScenario === 'cyber-major' ? 60 : 40;
        return {
          ...zone,
          affectedByOutage: true,
          capacityLoss: lossPercentage,
          status: lossPercentage > 70 ? 'critical' as const : 'degraded' as const,
          currentLoad: zone.capacity * (1 - lossPercentage / 100) * 0.85
        };
      }
      return zone;
    });
  }, [blackoutScenario, outageData]);

  const metrics = useMemo(() => {
    const totalCapacity = zones.reduce((sum, z) => sum + z.capacity, 0);
    const currentLoad = zones.reduce((sum, z) => sum + z.currentLoad, 0);
    const backup = 285;
    const activeIncidents = blackoutScenario ? 1 : 0;
    const gridHealth = outageData ? '40.0%' : '100.0%';

    return {
      gridHealth,
      totalCapacity,
      currentLoad: Math.round(currentLoad),
      loadPercentage: ((currentLoad / totalCapacity) * 100).toFixed(1),
      backup,
      activeIncidents
    };
  }, [zones, outageData, blackoutScenario]);

  const getZoneColor = (zone: PowerZone) => {
    if (zone.status === 'critical') return '#ef4444';
    if (zone.status === 'degraded') return '#f59e0b';
    return '#10b981';
  };

  const handleInitiateBlackout = (scenario: 'weather-catastrophe' | 'cyber-major' | 'equipment-minor') => {
    useDashboardStore.getState().setBlackoutScenario(scenario);
    useDashboardStore.getState().setSystemStatus(
      scenario === 'equipment-minor' ? 'WARNING' : 'CRITICAL'
    );
  };

  const handleClearIncident = () => {
    useDashboardStore.getState().setBlackoutScenario(null);
    useDashboardStore.getState().setSystemStatus('OPERATIONAL');
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-[#0a1628] to-[#06111f]">
      {/* Header */}
      <div className={`backdrop-blur-sm border-b px-8 py-6 ${
        blackoutScenario
          ? 'bg-[#2a0a0a]/50 border-red-500/20'
          : 'bg-[#0d1b2e]/50 border-emerald-500/20'
      }`}>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-xl border shadow-lg ${
              blackoutScenario
                ? 'bg-gradient-to-br from-red-500/20 to-orange-500/20 border-red-500/30 shadow-red-500/20'
                : 'bg-gradient-to-br from-emerald-500/20 to-green-500/20 border-emerald-500/30 shadow-emerald-500/20'
            }`}>
              <Zap className={`w-8 h-8 ${blackoutScenario ? 'text-red-400' : 'text-emerald-400'}`} />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white mb-1">
                Mumbai Power Grid - Blackout Management
              </h2>
              <p className="text-gray-400 text-sm">
                Real-time power allocation & emergency response system
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
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          <MetricCard
            icon={Activity}
            iconColor={blackoutScenario ? 'text-red-400' : 'text-emerald-400'}
            label="Grid Health"
            value={metrics.gridHealth}
            subtitle="System capacity"
            valueColor={blackoutScenario ? 'text-red-400' : 'text-emerald-400'}
          />
          <MetricCard
            icon={Zap}
            iconColor="text-blue-400"
            label="Total Capacity"
            value={metrics.totalCapacity.toString()}
            subtitle="MW"
            valueColor="text-blue-400"
          />
          <MetricCard
            icon={Zap}
            iconColor="text-yellow-400"
            label="Current Load"
            value={metrics.currentLoad.toString()}
            subtitle={`${metrics.loadPercentage}% of capacity`}
            valueColor="text-yellow-400"
          />
          <MetricCard
            icon={Battery}
            iconColor="text-green-400"
            label="Backup Available"
            value={metrics.backup.toString()}
            subtitle="MW capacity"
            valueColor="text-green-400"
          />
          <MetricCard
            icon={AlertTriangle}
            iconColor={blackoutScenario ? 'text-red-400' : 'text-green-400'}
            label="Active Incidents"
            value={metrics.activeIncidents.toString()}
            subtitle={blackoutScenario ? 'Emergency Response Active' : 'All Systems Normal'}
            valueColor={blackoutScenario ? 'text-red-400' : 'text-green-400'}
          />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 px-8 py-6 overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
          {/* Map Section */}
          <div className="lg:col-span-2 flex flex-col">
            <div className="bg-[#0d1b2e]/80 backdrop-blur-sm border border-gray-800/50 rounded-xl overflow-hidden shadow-2xl flex-1">
              {typeof window !== 'undefined' && (
                <MapContainer
                  center={MUMBAI_CENTER}
                  zoom={11}
                  style={{ height: '100%', width: '100%' }}
                  className="z-0"
                >
                  <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                    attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                  />

                  {zones.map(zone => (
                    <Circle
                      key={zone.id}
                      center={zone.position}
                      radius={1500}
                      pathOptions={{
                        color: getZoneColor(zone),
                        fillColor: getZoneColor(zone),
                        fillOpacity: zone.affectedByOutage ? 0.4 : 0.2,
                        weight: zone.affectedByOutage ? 3 : 2
                      }}
                    />
                  ))}
                </MapContainer>
              )}
            </div>
          </div>

          {/* Right Sidebar */}
          <div className="lg:col-span-1 space-y-4 overflow-y-auto max-h-full">
            {/* Blackout Simulator */}
            <div className="bg-[#0d1b2e]/80 backdrop-blur-sm border border-gray-800/50 rounded-xl overflow-hidden shadow-xl">
              <div className="p-4 border-b border-gray-800/50 bg-[#0a1628]/50">
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-yellow-500/20 rounded-lg">
                    <Zap className="w-5 h-5 text-yellow-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">Blackout Simulator</h3>
                </div>
                <p className="text-xs text-gray-400 mt-2">AI-driven blackout management</p>
              </div>

              <div className="p-4">
                <div className="mb-4">
                  <label className="text-xs font-medium text-gray-400 mb-2 block">Quick Scenarios</label>
                  <div className="space-y-2">
                    <button
                      onClick={() => handleInitiateBlackout('weather-catastrophe')}
                      className="w-full px-4 py-3 rounded-lg bg-gradient-to-r from-purple-600 to-purple-700 text-white font-medium hover:from-purple-700 hover:to-purple-800 transition-all shadow-lg shadow-purple-500/20 flex items-center gap-2"
                    >
                      <Zap className="w-4 h-4" />
                      <span className="flex-1 text-left">Weather Catastrophe</span>
                    </button>

                    <button
                      onClick={() => handleInitiateBlackout('cyber-major')}
                      className="w-full px-4 py-3 rounded-lg bg-gradient-to-r from-red-600 to-red-700 text-white font-medium hover:from-red-700 hover:to-red-800 transition-all shadow-lg shadow-red-500/20 flex items-center gap-2"
                    >
                      <AlertTriangle className="w-4 h-4" />
                      <span className="flex-1 text-left">Cyber Attack - Major</span>
                    </button>

                    <button
                      onClick={() => handleInitiateBlackout('equipment-minor')}
                      className="w-full px-4 py-3 rounded-lg bg-gradient-to-r from-yellow-600 to-yellow-700 text-white font-medium hover:from-yellow-700 hover:to-yellow-800 transition-all shadow-lg shadow-yellow-500/20 flex items-center gap-2"
                    >
                      <Settings className="w-4 h-4" />
                      <span className="flex-1 text-left">Equipment Failure - Minor</span>
                    </button>

                    <button
                      onClick={handleClearIncident}
                      className="w-full px-4 py-2 rounded-lg bg-gradient-to-r from-green-600 to-green-700 text-white font-medium hover:from-green-700 hover:to-green-800 transition-all shadow-lg shadow-green-500/20"
                    >
                      Clear Incident
                    </button>
                  </div>
                </div>

                {outageData && (
                  <div className="mt-4 pt-4 border-t border-gray-800">
                    <div className="space-y-3">
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-gray-400">Blackout Cause</span>
                        <select
                          value={blackoutCause}
                          onChange={(e) => useDashboardStore.getState().setBlackoutCause(e.target.value as any)}
                          className="px-2 py-1 bg-[#0a1628] border border-gray-700 rounded text-white text-xs"
                        >
                          <option value="grid-failure">Grid Failure</option>
                          <option value="cyber-attack">Cyber Attack</option>
                          <option value="weather-event">Weather Event</option>
                          <option value="equipment-failure">Equipment Failure</option>
                        </select>
                      </div>
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-gray-400">Severity Level</span>
                        <span className="text-white font-medium">
                          {blackoutScenario === 'equipment-minor' ? 'MODERATE' : 'CRITICAL'}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Active Incident Panel */}
            <div className="bg-[#0d1b2e]/80 backdrop-blur-sm border border-gray-800/50 rounded-xl overflow-hidden shadow-xl">
              <div className="p-4 border-b border-gray-800/50 bg-[#0a1628]/50">
                <h3 className="text-lg font-semibold text-white mb-2">Active Incident</h3>
                <div className={`inline-flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg ${
                  blackoutScenario
                    ? 'bg-red-500/10 text-red-400 border border-red-500/30'
                    : 'bg-green-500/10 text-green-400 border border-green-500/30'
                }`}>
                  {blackoutScenario ? 'ACTIVE' : 'NORMAL'}
                </div>
              </div>

              <div className="p-6 space-y-4">
                {outageData ? (
                  <>
                    <div className="text-xs text-gray-400">
                      Incident ID: <span className="text-gray-300 font-mono">227e2af86a2f</span>
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <div className="text-gray-400 text-xs mb-1">Cause</div>
                        <div className="font-semibold text-white uppercase text-xs">
                          {blackoutScenario === 'weather-catastrophe' && 'GRID FAILURE'}
                          {blackoutScenario === 'cyber-major' && 'CYBER ATTACK'}
                          {blackoutScenario === 'equipment-minor' && 'EQUIPMENT'}
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-400 text-xs mb-1">Status</div>
                        <div className="font-semibold text-red-400 text-xs">ACTIVE</div>
                      </div>
                      <div>
                        <div className="text-gray-400 text-xs mb-1">Capacity Lost</div>
                        <div className="font-semibold text-white text-xs">
                          {outageData.capacityLost} MW
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-400 text-xs mb-1">Recovery Time</div>
                        <div className="font-semibold text-blue-400 text-xs">
                          ~ {outageData.recoveryTime}
                        </div>
                      </div>
                    </div>

                    <div>
                      <div className="text-gray-400 text-sm mb-2 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-yellow-400" />
                        Cascade Risk
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-2.5">
                        <div
                          className="bg-gradient-to-r from-yellow-500 to-red-500 h-2.5 rounded-full transition-all duration-500"
                          style={{ width: `${outageData.cascadeRisk}%` }}
                        />
                      </div>
                      <div className="text-right text-xs text-gray-400 mt-1">
                        {outageData.cascadeRisk}%
                      </div>
                    </div>

                    <div>
                      <div className="text-gray-400 text-sm mb-3">Affected Zones ({outageData.affectedZones.length})</div>
                      <div className="space-y-2">
                        {zones.filter(z => z.affectedByOutage).map(zone => (
                          <div
                            key={zone.id}
                            className="bg-[#0a1628]/50 border border-gray-800 rounded-lg p-3 hover:border-red-500/30 transition-colors"
                          >
                            <div className="flex items-center justify-between text-xs text-gray-300 mb-2">
                              <span className="font-medium">{zone.name}</span>
                              <span className="text-red-400 font-bold">{zone.capacityLoss}%</span>
                            </div>
                            <div className="w-full bg-gray-700 rounded-full h-1.5">
                              <div
                                className={`h-1.5 rounded-full ${
                                  zone.capacityLoss > 70 ? 'bg-red-500' :
                                  zone.capacityLoss > 40 ? 'bg-yellow-500' :
                                  'bg-green-500'
                                }`}
                                style={{ width: `${100 - zone.capacityLoss}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-8 text-gray-400">
                    <Zap className="w-12 h-12 mx-auto mb-3 text-gray-600" />
                    <p className="text-sm">No active incidents</p>
                    <p className="text-xs mt-1">Use the simulator above to trigger scenarios</p>
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

export default PowerGridView;

'use client';

import React, { useState, useMemo } from 'react';
import { ShieldAlert, ShieldCheck, AlertTriangle, Globe, Bell, CheckCircle, Database, Activity } from 'lucide-react';
import dynamic from 'next/dynamic';
import MetricCard from '@/components/shared/MetricCard';
import LiveBadge from '@/components/shared/LiveBadge';
import { useDashboardStore } from '@/store/useDashboardStore';
import { SECURITY_ZONES, MUMBAI_CENTER, SecurityZone } from '@/types/zones';

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

const CyberDefenseView: React.FC = () => {
  const systemStatus = useDashboardStore((s) => s.systemStatus);
  const cyberAttackType = useDashboardStore((s) => s.cyberAttackType);
  const cyberTargetZone = useDashboardStore((s) => s.cyberTargetZone);
  const [selectedZone, setSelectedZone] = useState<SecurityZone | null>(SECURITY_ZONES[0]);
  const [attackTarget, setAttackTarget] = useState<string>('');

  // Update zones based on attack
  const zones = useMemo(() => {
    return SECURITY_ZONES.map(zone => {
      if (cyberAttackType && zone.id === cyberTargetZone) {
        return {
          ...zone,
          securityState: cyberAttackType === 'ransomware' ? 'RED' as const : 'YELLOW' as const,
          threatLevel: cyberAttackType === 'ransomware' ? 'CRITICAL' as const : 'HIGH' as const,
          activeIncidents: 2
        };
      }
      return zone;
    });
  }, [cyberAttackType, cyberTargetZone]);

  const metrics = useMemo(() => {
    const activeIncidents = zones.reduce((sum, z) => sum + z.activeIncidents, 0);
    const zonesAtRisk = zones.filter(z => z.securityState !== 'SECURE').length;
    const hasActiveThreat = activeIncidents > 0;
    const threatLevel = hasActiveThreat ? 'ELEVATED' : 'LOW';

    return {
      protectedZones: zones.length,
      activeIncidents,
      zonesAtRisk,
      threatLevel,
      recentAlerts: hasActiveThreat ? 2 : 0
    };
  }, [zones]);

  const getZoneColor = (state: string) => {
    switch (state) {
      case 'RED': return '#ef4444';
      case 'YELLOW': return '#f59e0b';
      case 'SECURE': return '#10b981';
      default: return '#10b981';
    }
  };

  const handleLaunchAttack = (type: 'ransomware' | 'brute-force', target: string) => {
    if (!target) return;
    useDashboardStore.getState().setCyberAttackType(type);
    useDashboardStore.getState().setCyberTargetZone(target);
    useDashboardStore.getState().setSystemStatus(type === 'ransomware' ? 'CRITICAL' : 'WARNING');

    // Auto-select the attacked zone
    const zone = zones.find(z => z.id === target);
    if (zone) setSelectedZone(zone);
  };

  const handleClearThreats = () => {
    useDashboardStore.getState().setCyberAttackType(null);
    useDashboardStore.getState().setCyberTargetZone(null);
    useDashboardStore.getState().setSystemStatus('OPERATIONAL');
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-[#0a1628] to-[#06111f]">
      {/* Header */}
      <div className="bg-[#1a0a1e]/50 backdrop-blur-sm border-b border-pink-500/20 px-8 py-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-pink-500/20 to-purple-500/20 rounded-xl border border-pink-500/30 shadow-lg shadow-pink-500/20">
              <ShieldAlert className="w-8 h-8 text-pink-400" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white mb-1 flex items-center gap-3">
                Cyber Defense Command Center
              </h2>
              <p className="text-gray-400 text-sm">
                Real-time Security Operations & Incident Response
              </p>
            </div>
          </div>
          <LiveBadge
            variant={systemStatus === 'OPERATIONAL' ? 'success' : systemStatus === 'WARNING' ? 'warning' : 'default'}
            showNetwork
          />
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="px-8 py-6 bg-[#0a1628]/50">
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          <MetricCard
            icon={ShieldCheck}
            iconColor="text-blue-400"
            label="Protected Zones"
            value={metrics.protectedZones.toString()}
            subtitle="Active security regions"
            valueColor="text-blue-400"
          />
          <MetricCard
            icon={AlertTriangle}
            iconColor="text-orange-400"
            label="Active Incidents"
            value={metrics.activeIncidents.toString()}
            subtitle="Incidents under investigation"
            valueColor="text-orange-400"
          />
          <MetricCard
            icon={ShieldAlert}
            iconColor="text-red-400"
            label="Zones at Risk"
            value={metrics.zonesAtRisk.toString()}
            subtitle="Requires immediate attention"
            valueColor="text-red-400"
          />
          <MetricCard
            icon={Globe}
            iconColor={metrics.threatLevel === 'LOW' ? 'text-green-400' : 'text-yellow-400'}
            label="Global Threat Level"
            value={metrics.threatLevel}
            subtitle="Dynamic global status"
            valueColor={metrics.threatLevel === 'LOW' ? 'text-green-400' : 'text-yellow-400'}
          />
          <MetricCard
            icon={Bell}
            iconColor="text-yellow-400"
            label="Recent Alerts"
            value={metrics.recentAlerts.toString()}
            subtitle="Last 24 hours"
            valueColor="text-yellow-400"
          />
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 px-8 py-6 overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
          {/* Map Section */}
          <div className="lg:col-span-2 flex flex-col">
            <div className="bg-[#0d1b2e]/80 backdrop-blur-sm border border-gray-800/50 rounded-xl overflow-hidden shadow-2xl flex-1 flex flex-col">
              {/* Security Status Legend */}
              <div className="p-4 border-b border-gray-800/50 bg-[#0a1628]/50">
                <h3 className="text-sm font-semibold text-white mb-3">Security Status</h3>
                <div className="flex gap-6 text-xs">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full shadow-lg shadow-green-500/50" />
                    <span className="text-gray-300">Secure</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-yellow-500 rounded-full shadow-lg shadow-yellow-500/50" />
                    <span className="text-gray-300">Warning</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full shadow-lg shadow-red-500/50 animate-pulse" />
                    <span className="text-gray-300">Under Attack</span>
                  </div>
                </div>
              </div>

              {/* Map */}
              <div className="flex-1 relative">
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

                    {zones.map(zone => (
                      <React.Fragment key={zone.id}>
                        <Circle
                          center={zone.position}
                          radius={zone.radius}
                          pathOptions={{
                            color: getZoneColor(zone.securityState),
                            fillColor: getZoneColor(zone.securityState),
                            fillOpacity: 0.2,
                            weight: 2
                          }}
                          eventHandlers={{
                            click: () => setSelectedZone(zone)
                          }}
                        />
                      </React.Fragment>
                    ))}
                  </MapContainer>
                )}

                {/* Zone Count Overlay */}
                <div className="absolute top-4 right-4 bg-[#0d1b2e]/95 backdrop-blur-md border border-gray-700/50 rounded-xl px-4 py-3 shadow-2xl z-[1000]">
                  <div className="text-3xl font-bold text-white">{zones.length}</div>
                  <div className="text-xs text-gray-400">Monitored Zones</div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Sidebar */}
          <div className="lg:col-span-1 space-y-4 overflow-y-auto max-h-full">
            {/* Attack Simulator */}
            <div className="bg-gradient-to-br from-[#1a0a1e]/90 to-[#0d1b2e]/90 backdrop-blur-sm border border-pink-500/20 rounded-xl overflow-hidden shadow-xl">
              <div className="p-4 border-b border-pink-500/20 bg-gradient-to-r from-pink-500/10 to-purple-500/10">
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-red-500/20 rounded-lg">
                    <ShieldAlert className="w-5 h-5 text-red-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">Attack Simulator</h3>
                </div>
                <p className="text-xs text-gray-400 mt-2">Test SOAR pipeline response</p>
              </div>

              <div className="p-4 space-y-4">
                {/* Target Zone Selection */}
                <div>
                  <label className="text-xs font-medium text-gray-400 mb-2 block">Target Zone</label>
                  <select
                    value={attackTarget}
                    onChange={(e) => setAttackTarget(e.target.value)}
                    className="w-full px-3 py-2 bg-[#0a1628] border border-gray-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-pink-500/50"
                  >
                    <option value="">Select a zone...</option>
                    {zones.map(zone => (
                      <option key={zone.id} value={zone.id}>{zone.name}</option>
                    ))}
                  </select>
                </div>

                {/* Attack Type Buttons */}
                <div>
                  <label className="text-xs font-medium text-gray-400 mb-2 block">Attack Type</label>
                  <div className="space-y-2">
                    <button
                      onClick={() => handleLaunchAttack('ransomware', attackTarget)}
                      disabled={!attackTarget}
                      className="w-full px-4 py-3 rounded-lg bg-gradient-to-r from-red-600 to-red-700 text-white font-medium hover:from-red-700 hover:to-red-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-red-500/20 flex items-center justify-center gap-2"
                    >
                      <span className="w-2 h-2 bg-white rounded-full"></span>
                      Ransomware
                      <span className="text-xs ml-auto bg-white/20 px-2 py-0.5 rounded">Data encryption attack</span>
                    </button>

                    <button
                      onClick={() => handleLaunchAttack('brute-force', attackTarget)}
                      disabled={!attackTarget}
                      className="w-full px-4 py-3 rounded-lg bg-gradient-to-r from-orange-600 to-orange-700 text-white font-medium hover:from-orange-700 hover:to-orange-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-orange-500/20 flex items-center justify-center gap-2"
                    >
                      <span className="w-2 h-2 bg-white rounded-full"></span>
                      Brute Force
                      <span className="text-xs ml-auto bg-white/20 px-2 py-0.5 rounded">Password cracking attempt</span>
                    </button>

                    <button
                      onClick={handleClearThreats}
                      className="w-full px-4 py-2 rounded-lg bg-gradient-to-r from-green-600 to-green-700 text-white font-medium hover:from-green-700 hover:to-green-800 transition-all shadow-lg shadow-green-500/20"
                    >
                      Clear All Threats
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Zone Details Panel */}
            {selectedZone && (
              <div className="bg-[#0d1b2e]/80 backdrop-blur-sm border border-gray-800/50 rounded-xl overflow-hidden shadow-xl">
                <div className="p-4 border-b border-gray-800/50 bg-[#0a1628]/50 flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-blue-400" />
                  <h3 className="text-lg font-semibold text-white">Zone Details</h3>
                  <button className="ml-auto text-gray-400 hover:text-white transition-colors">
                    <Activity className="w-4 h-4" />
                  </button>
                </div>

                <div className="p-6 space-y-5">
                  {/* Zone Name */}
                  <div>
                    <h4 className="text-xl font-bold text-white mb-1">{selectedZone.name}</h4>
                    <p className="text-sm text-gray-400 capitalize">{selectedZone.type} Zone</p>
                  </div>

                  {/* Security State Badge */}
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <ShieldAlert className={`w-4 h-4 ${
                        selectedZone.securityState === 'RED' ? 'text-red-400' :
                        selectedZone.securityState === 'YELLOW' ? 'text-yellow-400' :
                        'text-green-400'
                      }`} />
                      <span className="text-sm text-gray-400">Security State</span>
                    </div>
                    <div className={`${
                      selectedZone.securityState === 'RED' ? 'bg-red-500/10 border-red-500/30 text-red-400' :
                      selectedZone.securityState === 'YELLOW' ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400' :
                      'bg-green-500/10 border-green-500/30 text-green-400'
                    } border rounded-lg px-4 py-3`}>
                      <span className="text-lg font-bold">{selectedZone.securityState}</span>
                    </div>
                  </div>

                  {/* Metrics Grid */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-[#0a1628]/50 border border-gray-800 rounded-lg p-3">
                      <div className="text-xs text-gray-400 mb-1">Threat Level</div>
                      <div className={`text-sm font-semibold ${
                        selectedZone.threatLevel === 'CRITICAL' ? 'text-red-400' :
                        selectedZone.threatLevel === 'HIGH' ? 'text-orange-400' :
                        selectedZone.threatLevel === 'MEDIUM' ? 'text-yellow-400' :
                        'text-green-400'
                      }`}>
                        {selectedZone.threatLevel}
                      </div>
                    </div>

                    <div className="bg-[#0a1628]/50 border border-gray-800 rounded-lg p-3">
                      <div className="text-xs text-gray-400 mb-1">Active Incidents</div>
                      <div className="text-sm font-semibold text-orange-400">
                        {selectedZone.activeIncidents}
                      </div>
                    </div>
                  </div>

                  {/* Compliance */}
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="w-4 h-4 text-green-400" />
                      <span className="text-sm text-gray-400">Compliance</span>
                    </div>
                    <div className="bg-green-500/10 border border-green-500/30 rounded-lg px-4 py-2">
                      <span className="text-sm font-bold text-green-400">{selectedZone.compliance}</span>
                    </div>
                  </div>

                  {/* Critical Assets */}
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <Database className="w-4 h-4 text-blue-400" />
                      <span className="text-sm text-gray-400">Critical Assets</span>
                    </div>
                    <div className="space-y-2">
                      {selectedZone.criticalAssets.map((asset, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-2 bg-[#0a1628]/50 border border-gray-800 rounded-lg px-3 py-2.5 hover:border-blue-500/30 transition-colors"
                        >
                          <div className="w-2 h-2 bg-blue-400 rounded-full shadow-lg shadow-blue-400/50" />
                          <span className="text-xs text-gray-300">{asset}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CyberDefenseView;

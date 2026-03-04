'use client';

import React, { useState, useEffect } from 'react';
import { PowerGridTopology, generatePowerGridTopology } from '@/utils/streetLightGenerator';
import { Incident } from '@/components/map/IncidentMarkers';
import { useSimulatedWebSocket } from '@/hooks/useWebSocket';
import EnhancedLiveMap from '@/components/map/EnhancedLiveMap';
import AdvancedDemoPanel from '@/components/simulation/AdvancedDemoPanel';
import AgentActivityFeed from '@/components/shared/AgentActivityFeed';
import LiveBadge from '@/components/shared/LiveBadge';
import { Activity, Zap, AlertTriangle } from 'lucide-react';
import { motion } from 'framer-motion';

export default function EnhancedDemoPage() {
  const [gridTopology, setGridTopology] = useState<PowerGridTopology | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [stats, setStats] = useState({
    totalLights: 0,
    onlineLights: 0,
    offlineLights: 0,
    warningLights: 0,
    powerLoad: 0,
    activeIncidents: 0,
  });

  // Initialize grid on mount
  useEffect(() => {
    const grid = generatePowerGridTopology(600);
    setGridTopology(grid);
    updateStats(grid);
  }, []);

  // WebSocket for real-time updates (simulated for now)
  const websocket = useSimulatedWebSocket();

  useEffect(() => {
    if (!websocket) return;

    const unsubscribe = websocket.subscribe('enhanced-demo', (message) => {
      console.log('[Enhanced Demo] WebSocket message:', message);

      // Handle different message types
      switch (message.type) {
        case 'LIGHT_STATUS':
          // Update individual light status
          if (gridTopology && message.data.lightId) {
            const updatedGrid = { ...gridTopology };
            const light = updatedGrid.streetLights.find(l => l.id === message.data.lightId);
            if (light) {
              light.status = message.data.status;
              light.brightness = message.data.brightness;
              light.powerRating = message.data.powerConsumption || light.powerRating;
              setGridTopology(updatedGrid);
              updateStats(updatedGrid);
            }
          }
          break;

        case 'POWER_ALERT':
        case 'CYBER_ALERT':
        case 'WEATHER_ALERT':
          // These are handled by incident system
          console.log(`[${message.type}]:`, message.data);
          break;
      }
    });

    return () => unsubscribe();
  }, [websocket, gridTopology]);

  const updateStats = (grid: PowerGridTopology) => {
    const newStats = {
      totalLights: grid.streetLights.length,
      onlineLights: grid.streetLights.filter(l => l.status === 'ONLINE').length,
      offlineLights: grid.streetLights.filter(l => l.status === 'OFFLINE').length,
      warningLights: grid.streetLights.filter(l => l.status === 'WARNING').length,
      powerLoad: grid.totalLoad,
      activeIncidents: incidents.filter(i => i.status === 'ACTIVE').length,
    };
    setStats(newStats);
  };

  const handleGridUpdate = (updatedGrid: PowerGridTopology, newIncidents: Incident[]) => {
    setGridTopology(updatedGrid);
    setIncidents(prev => [...prev, ...newIncidents]);
    updateStats(updatedGrid);
  };

  if (!gridTopology) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0a1628] via-[#0d1b2e] to-[#0a1628] flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400 text-lg">Initializing Enhanced Demo...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a1628] via-[#0d1b2e] to-[#0a1628]">
      {/* Header */}
      <header className="border-b border-gray-800 bg-[#0d1b2e]/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-[1800px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-blue-600 rounded-xl flex items-center justify-center shadow-lg">
                <Activity className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">
                  Enhanced Simulation Dashboard
                </h1>
                <p className="text-sm text-gray-400">
                  Real-time AI-Powered Smart Lighting System • 600+ Street Lights • 12 Zones
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <LiveBadge />

              {websocket.isConnected && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex items-center gap-2 px-3 py-1.5 bg-green-500/20 border border-green-500/30 rounded-lg"
                >
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  <span className="text-xs font-semibold text-green-400">
                    STREAMING
                  </span>
                </motion.div>
              )}

              <button
                onClick={() => window.location.href = '/'}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors text-sm font-medium"
              >
                ← Back to Dashboard
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Stats Bar */}
      <div className="bg-[#0d1b2e]/50 border-b border-gray-800">
        <div className="max-w-[1800px] mx-auto px-6 py-4">
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700">
              <div className="flex items-center gap-2 mb-1">
                <Activity className="w-4 h-4 text-blue-400" />
                <span className="text-xs text-gray-400">Total Lights</span>
              </div>
              <p className="text-2xl font-bold text-white">
                {stats.totalLights}
              </p>
            </div>

            <div className="bg-green-900/20 rounded-lg p-3 border border-green-700/30">
              <div className="flex items-center gap-2 mb-1">
                <Zap className="w-4 h-4 text-green-400" />
                <span className="text-xs text-gray-400">Online</span>
              </div>
              <p className="text-2xl font-bold text-green-400">
                {stats.onlineLights}
              </p>
            </div>

            <div className="bg-red-900/20 rounded-lg p-3 border border-red-700/30">
              <div className="flex items-center gap-2 mb-1">
                <AlertTriangle className="w-4 h-4 text-red-400" />
                <span className="text-xs text-gray-400">Offline</span>
              </div>
              <p className="text-2xl font-bold text-red-400">
                {stats.offlineLights}
              </p>
            </div>

            <div className="bg-yellow-900/20 rounded-lg p-3 border border-yellow-700/30">
              <div className="flex items-center gap-2 mb-1">
                <AlertTriangle className="w-4 h-4 text-yellow-400" />
                <span className="text-xs text-gray-400">Warning</span>
              </div>
              <p className="text-2xl font-bold text-yellow-400">
                {stats.warningLights}
              </p>
            </div>

            <div className="bg-purple-900/20 rounded-lg p-3 border border-purple-700/30">
              <div className="flex items-center gap-2 mb-1">
                <Activity className="w-4 h-4 text-purple-400" />
                <span className="text-xs text-gray-400">Power Load</span>
              </div>
              <p className="text-2xl font-bold text-purple-400">
                {stats.powerLoad.toFixed(1)} <span className="text-sm">kW</span>
              </p>
            </div>

            <div className="bg-orange-900/20 rounded-lg p-3 border border-orange-700/30">
              <div className="flex items-center gap-2 mb-1">
                <AlertTriangle className="w-4 h-4 text-orange-400" />
                <span className="text-xs text-gray-400">Incidents</span>
              </div>
              <p className="text-2xl font-bold text-orange-400">
                {stats.activeIncidents}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-[1800px] mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column - Map */}
          <div className="lg:col-span-8 space-y-6">
            <div className="bg-gray-800/30 rounded-xl p-1 border border-gray-700">
              <EnhancedLiveMap height="700px" showControls={true} />
            </div>

            {/* Agent Activity */}
            <AgentActivityFeed />
          </div>

          {/* Right Column - Controls */}
          <div className="lg:col-span-4 space-y-6">
            <AdvancedDemoPanel
              onGridUpdate={handleGridUpdate}
              initialGrid={gridTopology}
            />

            {/* Quick Stats Card */}
            <div className="bg-gray-800/30 rounded-xl p-5 border border-gray-700">
              <h3 className="font-bold text-lg text-white mb-4">
                System Health
              </h3>
              <div className="space-y-3">
                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-400">System Uptime</span>
                    <span className="text-green-400 font-semibold">99.7%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div className="bg-green-500 h-2 rounded-full" style={{ width: '99.7%' }} />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-400">Grid Capacity</span>
                    <span className="text-blue-400 font-semibold">
                      {((stats.powerLoad / gridTopology.totalCapacity) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: `${(stats.powerLoad / gridTopology.totalCapacity) * 100}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-400">Lights Operational</span>
                    <span className="text-purple-400 font-semibold">
                      {((stats.onlineLights / stats.totalLights) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-purple-500 h-2 rounded-full"
                      style={{ width: `${(stats.onlineLights / stats.totalLights) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Info Card */}
            <div className="bg-gradient-to-br from-purple-900/30 to-blue-900/30 rounded-xl p-5 border border-purple-500/30">
              <h3 className="font-bold text-lg text-white mb-2">
                🚀 What's New
              </h3>
              <ul className="space-y-2 text-sm text-gray-300">
                <li className="flex items-start gap-2">
                  <span className="text-green-400 mt-0.5">✓</span>
                  <span>600+ dynamic street lights with real telemetry</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400 mt-0.5">✓</span>
                  <span>12 zones with realistic power grid topology</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400 mt-0.5">✓</span>
                  <span>Physics-based cascading failure simulations</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400 mt-0.5">✓</span>
                  <span>Real-time WebSocket streaming (simulated)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400 mt-0.5">✓</span>
                  <span>Advanced multi-agent coordination scenarios</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

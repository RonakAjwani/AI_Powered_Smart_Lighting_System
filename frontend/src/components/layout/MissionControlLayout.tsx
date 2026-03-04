'use client';

import React, { useState } from 'react';
import { useDashboardStore } from '@/store/useDashboardStore';
import {
  CloudSun,
  ShieldAlert,
  Zap,
  CloudRain,
  CloudFog,
  Wind,
  Sun,
  Target,
  Activity,
} from 'lucide-react';

interface MissionControlLayoutProps {
  children: React.ReactNode;
}

const MissionControlLayout: React.FC<MissionControlLayoutProps> = ({ children }) => {
  const {
    selectedAgentView,
    setSelectedAgentView,
    weatherScenario,
    setWeatherScenario,
    cyberAttackType,
    setCyberAttackType,
    cyberTargetZone,
    setCyberTargetZone,
    blackoutScenario,
    setBlackoutScenario,
    blackoutCause,
    setBlackoutCause,
    systemStatus,
  } = useDashboardStore();
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  const navSections = [
    {
      id: 'weather',
      label: 'Weather & Lighting',
      icon: CloudSun,
      bgColor: 'bg-blue-500/10',
      hoverColor: 'hover:bg-blue-500/20',
      activeColor: 'bg-blue-500/30',
      textColor: 'text-blue-400',
      status: 'ACTIVE',
    },
    {
      id: 'cybersecurity',
      label: 'Cybersecurity',
      icon: ShieldAlert,
      bgColor: 'bg-pink-500/10',
      hoverColor: 'hover:bg-pink-500/20',
      activeColor: 'bg-pink-500/30',
      textColor: 'text-pink-400',
      status: '',
    },
    {
      id: 'power',
      label: 'Power Grid',
      icon: Zap,
      bgColor: 'bg-orange-500/10',
      hoverColor: 'hover:bg-orange-500/20',
      activeColor: 'bg-orange-500/30',
      textColor: 'text-orange-400',
      status: '',
    },
  ];

  const weatherSimulations = [
    { id: 'heavy-rain', label: 'Heavy Rainfall', icon: CloudRain },
    { id: 'dense-fog', label: 'Dense Fog', icon: CloudFog },
    { id: 'cyclone', label: 'Cyclone Alert', icon: Wind },
    { id: 'clear', label: 'Clear Sky', icon: Sun },
  ];

  const toggleSection = (sectionId: string) => {
    setExpandedSection((prev) => (prev === sectionId ? null : sectionId));
    if (sectionId !== selectedAgentView) setSelectedAgentView(sectionId as any);
  };

  return (
    <div className="flex min-h-screen bg-[#0a1628]">
      {/* Left Sidebar — fixed so it stays while content scrolls */}
      <aside className="w-64 bg-[#0d1b2e] border-r border-gray-800 flex flex-col fixed top-0 left-0 h-screen overflow-y-auto z-40">
        {/* Mission Control Header */}
        <div className="p-6 border-b border-gray-800">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-white font-bold text-lg">Mission Control</h1>
              <p className="text-gray-400 text-xs">Smart City Operations</p>
            </div>
          </div>

          {/* System Status */}
          <div className="flex items-center gap-2 mt-4">
            <span className="text-gray-400 text-sm">System Status</span>
            <div className="flex items-center gap-1.5 ml-auto">
              <div className={`w-2 h-2 rounded-full animate-pulse ${systemStatus === 'OPERATIONAL' ? 'bg-green-500' : systemStatus === 'WARNING' ? 'bg-yellow-500' : 'bg-red-500'
                }`} />
              <span className={`text-xs font-medium ${systemStatus === 'OPERATIONAL' ? 'text-green-500' : systemStatus === 'WARNING' ? 'text-yellow-400' : 'text-red-400'
                }`}>
                {systemStatus}
              </span>
            </div>
          </div>

          {/* Quick Mode */}
          <div className="mt-3 flex gap-2">
            {(
              [
                { id: 'OPERATIONAL', label: 'Operational', cls: 'text-green-400 border-green-500/30 hover:bg-green-500/10' },
                { id: 'WARNING', label: 'Warning', cls: 'text-yellow-400 border-yellow-500/30 hover:bg-yellow-500/10' },
                { id: 'CRITICAL', label: 'Critical', cls: 'text-red-400 border-red-500/30 hover:bg-red-500/10' },
              ] as const
            ).map((m) => (
              <button
                key={m.id}
                onClick={() => useDashboardStore.getState().setSystemStatus(m.id)}
                className={`text-[10px] px-2 py-1 rounded border transition-colors ${systemStatus === m.id ? m.cls + ' bg-white/5' : 'text-gray-400 border-gray-700 hover:bg-gray-800'
                  }`}
                title={`Set ${m.label}`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>

        {/* Navigation Sections */}
        <nav className="flex-1 overflow-y-auto p-4">
          {navSections.map((section) => {
            const Icon = section.icon;
            const isActive = selectedAgentView === section.id;
            const isExpanded = expandedSection === section.id;

            return (
              <div key={section.id} className="mb-2">
                <button
                  onClick={() => toggleSection(section.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${isActive
                      ? `${section.activeColor} ${section.textColor} border border-current border-opacity-30`
                      : `${section.bgColor} ${section.hoverColor} text-gray-300`
                    }`}
                >
                  <Icon className="w-5 h-5" />
                  <div className="flex-1 text-left">
                    <div className="text-sm font-medium">{section.label}</div>
                    {section.status && (
                      <div className="text-xs text-green-400 mt-0.5">• {section.status}</div>
                    )}
                  </div>
                </button>

                {/* Weather Simulation Panel */}
                {section.id === 'weather' && isExpanded && (
                  <div className="mt-3 ml-4 space-y-2 border-l-2 border-blue-500/30 pl-4">
                    <div className="text-xs text-orange-400 font-medium mb-2 flex items-center gap-1">
                      <CloudSun className="w-3 h-3" />
                      Weather Simulation
                    </div>
                    <p className="text-xs text-gray-400 mb-3">Environmental scenario testing</p>

                    {weatherSimulations.map((sim) => {
                      const SimIcon = sim.icon;
                      return (
                        <button
                          key={sim.id}
                          onClick={() => setWeatherScenario(sim.id as any)}
                          className={`w-full flex items-center gap-2 px-3 py-2 rounded text-xs transition-colors ${weatherScenario === (sim.id as any)
                              ? 'bg-blue-900/40 text-blue-300 border border-blue-500/30'
                              : 'bg-gray-800/50 hover:bg-gray-700/50 text-gray-300'
                            }`}
                        >
                          <SimIcon className="w-4 h-4" />
                          <span>{sim.label}</span>
                        </button>
                      );
                    })}
                  </div>
                )}

                {/* Cybersecurity Simulation Panel */}
                {section.id === 'cybersecurity' && isExpanded && (
                  <div className="mt-3 ml-4 space-y-2 border-l-2 border-pink-500/30 pl-4">
                    <div className="text-xs text-red-400 font-medium mb-2 flex items-center gap-1">
                      <Target className="w-3 h-3" />
                      Attack Simulator
                    </div>
                    <p className="text-xs text-gray-400 mb-3">Test SOAR pipeline response</p>

                    <div className="space-y-2">
                      <div className="text-xs text-gray-500">Target Zone</div>
                      <select
                        className="w-full px-2 py-1.5 bg-gray-800 text-gray-300 text-xs rounded border border-gray-700"
                        value={cyberTargetZone ?? ''}
                        onChange={(e) => setCyberTargetZone(e.target.value || null)}
                      >
                        <option value="">Select a zone...</option>
                        <option value="SL-ZONE-A">Airport Zone (CSM)</option>
                        <option value="SL-ZONE-B">Port Zone (Mumbai Port)</option>
                        <option value="SL-ZONE-C">Industrial Zone (MIDC)</option>
                        <option value="SL-ZONE-D">Residential Zone (Bandra)</option>
                        <option value="SL-ZONE-E">Hospital Zone (Hinduja)</option>
                        <option value="SL-ZONE-F">Commercial Zone (BKC)</option>
                        <option value="SL-ZONE-G">Transport Hub (CSMT)</option>
                      </select>

                      <div className="text-xs text-gray-500 mt-3">Attack Type</div>
                      <button
                        onClick={() => setCyberAttackType('ransomware')}
                        className={`w-full px-3 py-2 text-xs rounded border transition-colors ${cyberAttackType === 'ransomware'
                            ? 'bg-red-900/40 text-red-300 border-red-500/30'
                            : 'bg-red-900/30 hover:bg-red-900/50 text-red-400 border-red-500/30'
                          }`}
                      >
                        Ransomware
                      </button>
                      <button
                        onClick={() => setCyberAttackType('brute-force')}
                        className={`w-full px-3 py-2 text-xs rounded transition-colors ${cyberAttackType === 'brute-force'
                            ? 'bg-gray-700 text-gray-200'
                            : 'bg-gray-800/50 hover:bg-gray-700/50 text-gray-300'
                          }`}
                      >
                        Brute Force
                      </button>
                    </div>
                  </div>
                )}

                {/* Power Grid Simulation Panel */}
                {section.id === 'power' && isExpanded && (
                  <div className="mt-3 ml-4 space-y-2 border-l-2 border-orange-500/30 pl-4">
                    <div className="text-xs text-yellow-400 font-medium mb-2 flex items-center gap-1">
                      <Zap className="w-3 h-3" />
                      Blackout Simulator
                    </div>
                    <p className="text-xs text-gray-400 mb-3">AI-driven blackout management. Use the simulator to test power allocation.</p>

                    <div className="text-xs text-gray-500 mb-2">Quick Scenarios</div>
                    <button
                      onClick={() => setBlackoutScenario('weather-catastrophe')}
                      className={`w-full px-3 py-2 text-xs rounded transition-colors ${blackoutScenario === 'weather-catastrophe'
                          ? 'bg-purple-900/50 text-purple-300 border border-purple-500/30'
                          : 'bg-purple-900/30 hover:bg-purple-900/50 text-purple-400'
                        }`}
                    >
                      Weather Catastrophe
                    </button>
                    <button
                      onClick={() => setBlackoutScenario('cyber-major')}
                      className={`w-full px-3 py-2 text-xs rounded transition-colors ${blackoutScenario === 'cyber-major'
                          ? 'bg-red-900/50 text-red-300 border border-red-500/30'
                          : 'bg-red-900/30 hover:bg-red-900/50 text-red-400'
                        }`}
                    >
                      Cyber Attack - Major
                    </button>
                    <button
                      onClick={() => setBlackoutScenario('equipment-minor')}
                      className={`w-full px-3 py-2 text-xs rounded transition-colors ${blackoutScenario === 'equipment-minor'
                          ? 'bg-orange-900/50 text-orange-300 border border-orange-500/30'
                          : 'bg-orange-900/30 hover:bg-orange-900/50 text-orange-400'
                        }`}
                    >
                      Equipment Failure - Minor
                    </button>

                    <div className="text-xs text-gray-500 mt-3 mb-2">Blackout Cause</div>
                    <select
                      className="w-full px-2 py-1.5 bg-gray-800 text-gray-300 text-xs rounded border border-gray-700"
                      value={blackoutCause}
                      onChange={(e) => setBlackoutCause(e.target.value as any)}
                    >
                      <option value="grid-failure">Grid Failure</option>
                      <option value="cyber-attack">Cyber Attack</option>
                      <option value="weather-event">Weather Event</option>
                      <option value="equipment-failure">Equipment Failure</option>
                    </select>
                  </div>
                )}
              </div>
            );
          })}
        </nav>
      </aside>

      {/* Main Content — offset by sidebar width */}
      <main className="flex-1 overflow-x-hidden ml-64">{children}</main>
    </div>
  );
};

export default MissionControlLayout;

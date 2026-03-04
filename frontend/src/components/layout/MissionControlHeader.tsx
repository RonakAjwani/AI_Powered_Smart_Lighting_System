'use client';

import React, { useState, useEffect } from 'react';
import { Sun, CloudSun, ShieldAlert, Zap } from 'lucide-react';
import { useDashboardStore, AgentView } from '@/store/useDashboardStore';

const MissionControlHeader: React.FC = () => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const selectedAgentView = useDashboardStore((s) => s.selectedAgentView);
  const setSelectedAgentView = useDashboardStore((s) => s.setSelectedAgentView);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (date: Date) =>
    date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });

  const formatDate = (date: Date) =>
    date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });

  const weatherData = { temp: 31, condition: 'Sunny', icon: Sun } as const;
  const WeatherIcon = weatherData.icon;

  const navItems: { id: AgentView; label: string; icon: typeof CloudSun }[] = [
    { id: 'overview', label: 'Overview', icon: Sun },
    { id: 'weather', label: 'Weather & Lighting', icon: CloudSun },
    { id: 'cybersecurity', label: 'Cyber Defense', icon: ShieldAlert },
    { id: 'power', label: 'Power Grid', icon: Zap },
  ];

  return (
    <header className="bg-[#0d1b2e] border-b border-gray-800">
      <div className="px-8 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-5xl font-bold text-white mb-1">{formatTime(currentTime)}</h1>
            <p className="text-gray-400 text-sm">{formatDate(currentTime)}</p>
          </div>
          <div className="flex items-center gap-4">
            <a
              href="/enhanced-demo"
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors text-sm font-medium"
            >
              Enhanced Demo (600+ Lights)
            </a>
            <div className="flex items-center gap-3 bg-[#0a1628] px-6 py-4 rounded-lg border border-gray-800">
              <WeatherIcon className="w-10 h-10 text-yellow-400" />
              <div>
                <div className="text-3xl font-bold text-white">{weatherData.temp}°C</div>
                <div className="text-gray-400 text-sm">{weatherData.condition}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="px-8 py-0">
        <div className="flex gap-2 border-t border-gray-800 pt-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = selectedAgentView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setSelectedAgentView(item.id)}
                className={`flex items-center gap-2 px-6 py-3 rounded-t-lg transition-colors ${
                  isActive
                    ? 'bg-[#0a1628] text-blue-400 border-t-2 border-blue-400'
                    : 'text-gray-400 hover:text-gray-300 hover:bg-[#0a1628]/50'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};

export default MissionControlHeader;


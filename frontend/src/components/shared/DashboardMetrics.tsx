'use client';

import React from "react";
import { useWeatherData } from '@/hooks/useWeatherData';
import { usePowerData } from '@/hooks/usePowerData';
import { useCyberData } from '@/hooks/useCyberData';
import { Activity } from 'lucide-react';

const DashboardMetrics: React.FC = () => {
  const weatherData = useWeatherData();
  const powerData = usePowerData();
  const cyberData = useCyberData();

  // Calculate metrics from real data
  const activeSensors = weatherData.status?.system_health?.agents
    ? Object.values(weatherData.status.system_health.agents).filter((s: any) => s === 'operational').length
    : 0;

  const totalAlerts = [
    ...(weatherData.alerts?.alerts || []),
    ...(cyberData.metrics?.threats || []),
  ].length;

  const powerUptime = powerData.status?.system_availability || '0';

  const isLoading = weatherData.loading || powerData.loading || cyberData.loading;

  return (
    <div className="flex flex-wrap gap-6 justify-center">
      <div className="flex flex-col bg-gray-800 rounded-xl p-6 shadow w-64 items-center border border-gray-700 hover:border-blue-500 transition-colors">
        {isLoading ? (
          <Activity className="w-8 h-8 text-blue-400 animate-pulse" />
        ) : (
          <span className="text-3xl font-bold font-mono text-blue-400">{activeSensors}</span>
        )}
        <span className="text-gray-300 mt-2 text-md text-center">Active Agents</span>
      </div>

      <div className="flex flex-col bg-gray-800 rounded-xl p-6 shadow w-64 items-center border border-gray-700 hover:border-yellow-500 transition-colors">
        {isLoading ? (
          <Activity className="w-8 h-8 text-yellow-300 animate-pulse" />
        ) : (
          <span className="text-3xl font-bold font-mono text-yellow-300">{totalAlerts}</span>
        )}
        <span className="text-gray-300 mt-2 text-md text-center">Active Alerts</span>
      </div>

      <div className="flex flex-col bg-gray-800 rounded-xl p-6 shadow w-64 items-center border border-gray-700 hover:border-green-500 transition-colors">
        {isLoading ? (
          <Activity className="w-8 h-8 text-green-400 animate-pulse" />
        ) : (
          <span className="text-3xl font-bold font-mono text-green-400">
            {typeof powerUptime === 'number' ? powerUptime.toFixed(2) : powerUptime}%
          </span>
        )}
        <span className="text-gray-300 mt-2 text-md text-center">System Uptime</span>
      </div>
    </div>
  );
};

export default DashboardMetrics;

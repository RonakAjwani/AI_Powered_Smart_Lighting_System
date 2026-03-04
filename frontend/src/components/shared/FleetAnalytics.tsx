'use client';

import React, { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { useDashboardStore } from '@/store/useDashboardStore';
import { Activity } from 'lucide-react';

interface ZoneData {
  zone: string;
  lights: number;
  status: 'online' | 'offline' | 'maintenance';
}

const FleetAnalytics: React.FC = () => {
  const selectedAgentView = useDashboardStore((state) => state.selectedAgentView);
  const [zoneData, setZoneData] = useState<ZoneData[]>([]);

  useEffect(() => {
    // Generate zone data based on selected view
    const zones = ['Zone A', 'Zone B', 'Zone C', 'Zone D'];
    const data = zones.map(zone => {
      const lights = Math.floor(Math.random() * 100) + 50;
      const statusRandom = Math.random();
      let status: 'online' | 'offline' | 'maintenance' = 'online';

      if (selectedAgentView === 'power' && statusRandom < 0.2) {
        status = 'offline';
      } else if (statusRandom < 0.1) {
        status = 'maintenance';
      }

      return { zone, lights, status };
    });

    setZoneData(data);
  }, [selectedAgentView]);

  const getBarColor = (status: string) => {
    switch (status) {
      case 'online': return '#10b981';
      case 'offline': return '#ef4444';
      case 'maintenance': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  const totalLights = zoneData.reduce((sum, d) => sum + d.lights, 0);
  const onlineLights = zoneData.filter(d => d.status === 'online').reduce((sum, d) => sum + d.lights, 0);
  const uptime = totalLights > 0 ? Math.round((onlineLights / totalLights) * 100) : 0;

  return (
    <div className="bg-gray-800 rounded-xl shadow-lg p-6 flex flex-col w-full border border-gray-700">
      <h3 className="text-lg font-semibold text-gray-100 mb-4">Zone Analytics</h3>

      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={zoneData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="zone"
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
          />
          <YAxis
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '0.5rem',
              color: '#f3f4f6'
            }}
            cursor={{ fill: 'rgba(59, 130, 246, 0.1)' }}
          />
          <Bar dataKey="lights" radius={[4, 4, 0, 0]}>
            {zoneData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry.status)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="flex gap-8 mt-4 justify-center">
        <div className="flex flex-col items-center">
          <span className="text-2xl text-blue-400 font-bold">{totalLights}</span>
          <span className="text-xs text-gray-300">Total Lights</span>
        </div>
        <div className="flex flex-col items-center">
          <span className="text-2xl text-green-400 font-bold">{uptime}%</span>
          <span className="text-xs text-gray-300">Uptime</span>
        </div>
      </div>

      <div className="mt-3 flex gap-4 justify-center text-xs">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-green-500 rounded"></div>
          <span className="text-gray-400">Online</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-red-500 rounded"></div>
          <span className="text-gray-400">Offline</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-yellow-500 rounded"></div>
          <span className="text-gray-400">Maintenance</span>
        </div>
      </div>
    </div>
  );
};

export default FleetAnalytics;

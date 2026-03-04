'use client';

import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { useCyberData } from '@/hooks/useCyberData';
import { Activity, Shield } from 'lucide-react';

interface ThreatDataPoint {
  time: string;
  threats: number;
  blocked: number;
  severity: 'low' | 'medium' | 'high';
}

export const ThreatTimelineChart: React.FC = () => {
  const cyberData = useCyberData();
  const [chartData, setChartData] = useState<ThreatDataPoint[]>([]);

  useEffect(() => {
    // Generate realistic threat detection data
    const now = new Date();
    const data: ThreatDataPoint[] = [];

    for (let i = 11; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 2 * 60 * 60 * 1000); // 2-hour intervals

      // Random threat patterns (more during business hours)
      const hour = time.getHours();
      const isBusinessHours = hour >= 9 && hour <= 17;

      const threats = isBusinessHours
        ? Math.floor(Math.random() * 15) + 5
        : Math.floor(Math.random() * 8) + 1;

      const blocked = Math.floor(threats * (0.7 + Math.random() * 0.25)); // 70-95% blocked

      // Determine severity based on threat count
      let severity: 'low' | 'medium' | 'high' = 'low';
      if (threats > 12) severity = 'high';
      else if (threats > 6) severity = 'medium';

      data.push({
        time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        threats,
        blocked,
        severity,
      });
    }

    setChartData(data);
  }, [cyberData.lastUpdated]);

  if (cyberData.loading && chartData.length === 0) {
    return (
      <div className="bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-700 h-80 flex items-center justify-center">
        <Activity className="w-8 h-8 text-blue-400 animate-pulse" />
      </div>
    );
  }

  const totalThreats = chartData.reduce((sum, d) => sum + d.threats, 0);
  const totalBlocked = chartData.reduce((sum, d) => sum + d.blocked, 0);
  const blockRate = totalThreats > 0 ? Math.round((totalBlocked / totalThreats) * 100) : 0;

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#6b7280';
    }
  };

  return (
    <div className="bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-700">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-100">Threat Detection Timeline</h3>
        <p className="text-sm text-gray-400">Last 24 hours - Threats detected & blocked</p>
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="time"
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
          />
          <YAxis
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            label={{ value: 'Count', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
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
          <Legend wrapperStyle={{ color: '#9ca3af' }} />
          <Bar dataKey="threats" fill="#ef4444" name="Threats Detected" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getSeverityColor(entry.severity)} />
            ))}
          </Bar>
          <Bar dataKey="blocked" fill="#10b981" name="Blocked" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-4 grid grid-cols-3 gap-4">
        <div className="text-center p-3 bg-gray-900 rounded-lg">
          <p className="text-xs text-gray-400">Total Threats</p>
          <p className="text-xl font-bold text-red-400">{totalThreats}</p>
        </div>
        <div className="text-center p-3 bg-gray-900 rounded-lg">
          <p className="text-xs text-gray-400">Blocked</p>
          <p className="text-xl font-bold text-green-400">{totalBlocked}</p>
        </div>
        <div className="text-center p-3 bg-gray-900 rounded-lg">
          <p className="text-xs text-gray-400">Block Rate</p>
          <p className="text-xl font-bold text-blue-400">{blockRate}%</p>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-center gap-2 text-xs text-gray-400">
        <Shield className="w-4 h-4" />
        <span>Security agents actively monitoring</span>
      </div>
    </div>
  );
};

export default ThreatTimelineChart;

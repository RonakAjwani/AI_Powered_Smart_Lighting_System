'use client';

import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { useSystemData } from '@/hooks/useSystemData';
import { Activity, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

export const SystemHealthChart: React.FC = () => {
  const { data, isLoading } = useSystemData(true, 30000);

  // Calculate agent health statistics
  const getAgentStats = () => {
    let operational = 0;
    let degraded = 0;
    let offline = 0;

    // Weather agents
    if (data.weather.status?.system_health?.agents) {
      const agents = Object.values(data.weather.status.system_health.agents);
      operational += agents.filter((s: any) => s === 'operational' || s === 'active').length;
      degraded += agents.filter((s: any) => s === 'degraded' || s === 'warning').length;
      offline += agents.filter((s: any) => s === 'offline' || s === 'error').length;
    }

    // Power agents
    if (data.power.status?.agents) {
      const agents = Object.values(data.power.status.agents);
      operational += agents.filter((s: any) => s === 'active' || s === 'operational').length;
      degraded += agents.filter((s: any) => s === 'degraded' || s === 'warning').length;
      offline += agents.filter((s: any) => s === 'offline' || s === 'error').length;
    }

    return [
      { name: 'Operational', value: operational, color: '#10b981' },
      { name: 'Degraded', value: degraded, color: '#f59e0b' },
      { name: 'Offline', value: offline, color: '#ef4444' },
    ];
  };

  const agentStats = getAgentStats();
  const totalAgents = agentStats.reduce((sum, stat) => sum + stat.value, 0);

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-700 h-80 flex items-center justify-center">
        <Activity className="w-8 h-8 text-purple-400 animate-pulse" />
      </div>
    );
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-3">
          <p className="text-gray-100 font-semibold">{payload[0].name}</p>
          <p className="text-gray-400">
            {payload[0].value} agents ({Math.round((payload[0].value / totalAgents) * 100)}%)
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-700">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-100">System Health Overview</h3>
        <p className="text-sm text-gray-400">Agent status distribution</p>
      </div>

      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={agentStats}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {agentStats.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </ResponsiveContainer>

      <div className="mt-6 space-y-3">
        <div className="flex items-center justify-between p-3 bg-gray-900 rounded-lg">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-400" />
            <span className="text-gray-300">Operational</span>
          </div>
          <span className="text-xl font-bold text-green-400">{agentStats[0].value}</span>
        </div>

        <div className="flex items-center justify-between p-3 bg-gray-900 rounded-lg">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
            <span className="text-gray-300">Degraded</span>
          </div>
          <span className="text-xl font-bold text-yellow-400">{agentStats[1].value}</span>
        </div>

        <div className="flex items-center justify-between p-3 bg-gray-900 rounded-lg">
          <div className="flex items-center gap-2">
            <XCircle className="w-5 h-5 text-red-400" />
            <span className="text-gray-300">Offline</span>
          </div>
          <span className="text-xl font-bold text-red-400">{agentStats[2].value}</span>
        </div>
      </div>

      <div className="mt-4 text-center">
        <p className="text-sm text-gray-400">
          Total Agents: <span className="font-bold text-gray-200">{totalAgents}</span>
        </p>
        <p className="text-xs text-gray-500 mt-1">
          Health Score: <span className="font-bold text-green-400">
            {Math.round((agentStats[0].value / totalAgents) * 100)}%
          </span>
        </p>
      </div>
    </div>
  );
};

export default SystemHealthChart;

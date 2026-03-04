'use client';

import React from 'react';
import { useSystemData } from '@/hooks/useSystemData';
import { CloudSun, ShieldCheck, Zap, Activity, AlertTriangle, CheckCircle, RefreshCw } from 'lucide-react';
import Card from '@/components/shared/Card';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import AgentActivityFeed from '@/components/shared/AgentActivityFeed';
import SystemHealthChart from '@/components/charts/SystemHealthChart';
import PowerConsumptionChart from '@/components/charts/PowerConsumptionChart';
import WeatherTrendsChart from '@/components/charts/WeatherTrendsChart';
import ThreatTimelineChart from '@/components/charts/ThreatTimelineChart';

const SystemOverview: React.FC = () => {
  const { data, refetch, isLoading } = useSystemData(true, 30000);

  const getStatusColor = (status: string | undefined) => {
    if (!status) return 'text-gray-400';
    const statusLower = status.toLowerCase();
    if (statusLower === 'healthy' || statusLower === 'operational' || statusLower === 'active') {
      return 'text-green-500';
    }
    if (statusLower.includes('warning') || statusLower.includes('degraded')) {
      return 'text-yellow-500';
    }
    if (statusLower.includes('error') || statusLower.includes('critical')) {
      return 'text-red-500';
    }
    return 'text-blue-500';
  };

  const getStatusIcon = (status: string | undefined) => {
    if (!status) return <Activity className="w-5 h-5 text-gray-400" />;
    const statusLower = status.toLowerCase();
    if (statusLower === 'healthy' || statusLower === 'operational' || statusLower === 'active') {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    }
    if (statusLower.includes('warning') || statusLower.includes('degraded')) {
      return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
    }
    if (statusLower.includes('error') || statusLower.includes('critical')) {
      return <AlertTriangle className="w-5 h-5 text-red-500" />;
    }
    return <Activity className="w-5 h-5 text-blue-500" />;
  };

  if (isLoading && !data.lastUpdated) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="w-full max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-gray-800 dark:text-gray-100">
            System Overview
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            AI-Powered Smart Lighting Management System
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
          disabled={isLoading}
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Last Updated */}
      {data.lastUpdated && (
        <div className="text-sm text-gray-500 dark:text-gray-400">
          Last updated: {data.lastUpdated.toLocaleString()}
        </div>
      )}

      {/* Service Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Weather Service */}
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <CloudSun className="w-8 h-8 text-yellow-500" />
            <div>
              <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                Weather Service
              </h3>
              <p className="text-sm text-gray-500">Port 8001</p>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              {getStatusIcon(data.weather.status?.status)}
              <span className={`text-sm font-medium ${getStatusColor(data.weather.status?.status)}`}>
                {data.weather.status?.status || 'Unknown'}
              </span>
            </div>
            {data.weather.status?.system_health?.agents && (
              <div className="mt-3 space-y-1">
                <p className="text-xs font-semibold text-gray-600 dark:text-gray-400">Agents:</p>
                {Object.entries(data.weather.status.system_health.agents).map(([agent, status]) => (
                  <div key={agent} className="flex items-center justify-between text-xs">
                    <span className="text-gray-600 dark:text-gray-400 capitalize">
                      {agent.replace(/_/g, ' ')}
                    </span>
                    <span className={getStatusColor(status as string)}>
                      {status as string}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>

        {/* Power Service */}
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <Zap className="w-8 h-8 text-green-500" />
            <div>
              <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                Power Grid
              </h3>
              <p className="text-sm text-gray-500">Port 8002</p>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              {getStatusIcon(data.power.status?.status)}
              <span className={`text-sm font-medium ${getStatusColor(data.power.status?.status)}`}>
                {data.power.status?.status || 'Unknown'}
              </span>
            </div>
            {data.power.status?.agents && (
              <div className="mt-3 space-y-1">
                <p className="text-xs font-semibold text-gray-600 dark:text-gray-400">Agents:</p>
                {Object.entries(data.power.status.agents).map(([agent, status]) => (
                  <div key={agent} className="flex items-center justify-between text-xs">
                    <span className="text-gray-600 dark:text-gray-400 capitalize">
                      {agent.replace(/_/g, ' ')}
                    </span>
                    <span className={getStatusColor(status as string)}>
                      {status as string}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>

        {/* Cybersecurity Service */}
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <ShieldCheck className="w-8 h-8 text-blue-500" />
            <div>
              <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                Cybersecurity
              </h3>
              <p className="text-sm text-gray-500">Port 8000</p>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              {getStatusIcon(data.cybersecurity.agentStatus?.status)}
              <span className={`text-sm font-medium ${getStatusColor(data.cybersecurity.agentStatus?.status)}`}>
                {data.cybersecurity.agentStatus?.status || 'Unknown'}
              </span>
            </div>
            {data.cybersecurity.agentStatus && (
              <div className="mt-3">
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Service: {data.cybersecurity.agentStatus.service}
                </p>
              </div>
            )}
          </div>
        </Card>

        {/* Coordinator Service */}
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <Activity className="w-8 h-8 text-purple-500" />
            <div>
              <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                Coordinator
              </h3>
              <p className="text-sm text-gray-500">Port 8004</p>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              {getStatusIcon(data.coordinator.status?.status)}
              <span className={`text-sm font-medium ${getStatusColor(data.coordinator.status?.status)}`}>
                {data.coordinator.status?.status || 'Unknown'}
              </span>
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-3">
              Central decision-making hub
            </p>
          </div>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SystemHealthChart />
        <PowerConsumptionChart />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <WeatherTrendsChart />
        <ThreatTimelineChart />
      </div>

      {/* Agent Activity Feed */}
      <AgentActivityFeed />

      {/* Weather Alerts Section */}
      {data.weather.alerts && !data.weather.alerts.error && data.weather.alerts.alerts?.length > 0 && (
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-5 h-5 text-yellow-500" />
            <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-100">
              Active Weather Alerts
            </h3>
          </div>
          <div className="space-y-2">
            {data.weather.alerts.alerts.map((alert: any, index: number) => (
              <div
                key={index}
                className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg"
              >
                <p className="text-sm font-medium text-gray-800 dark:text-gray-100">
                  {alert.title || alert.message || 'Weather Alert'}
                </p>
                {alert.description && (
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    {alert.description}
                  </p>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* System State Details */}
      {data.coordinator.systemState && !data.coordinator.systemState.error && (
        <Card>
          <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-4">
            Coordinator System State
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Cyber Alerts
              </p>
              <p className="text-2xl font-bold text-gray-800 dark:text-gray-100">
                {data.coordinator.systemState.cyber_alerts?.length || 0}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Weather Alerts
              </p>
              <p className="text-2xl font-bold text-gray-800 dark:text-gray-100">
                {data.coordinator.systemState.weather_alerts?.length || 0}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Power Alerts
              </p>
              <p className="text-2xl font-bold text-gray-800 dark:text-gray-100">
                {data.coordinator.systemState.power_alerts?.length || 0}
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Error Messages */}
      {(data.weather.error || data.power.error || data.cybersecurity.error || data.coordinator.error) && (
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-5 h-5 text-red-500" />
            <h3 className="text-xl font-semibold text-red-600 dark:text-red-400">
              Service Errors
            </h3>
          </div>
          <div className="space-y-2">
            {data.weather.error && (
              <p className="text-sm text-red-600 dark:text-red-400">
                Weather Service: {data.weather.error.message || 'Unknown error'}
              </p>
            )}
            {data.power.error && (
              <p className="text-sm text-red-600 dark:text-red-400">
                Power Service: {data.power.error.message || 'Unknown error'}
              </p>
            )}
            {data.cybersecurity.error && (
              <p className="text-sm text-red-600 dark:text-red-400">
                Cybersecurity Service: {data.cybersecurity.error.message || 'Unknown error'}
              </p>
            )}
            {data.coordinator.error && (
              <p className="text-sm text-red-600 dark:text-red-400">
                Coordinator Service: {data.coordinator.error.message || 'Unknown error'}
              </p>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};

export default SystemOverview;

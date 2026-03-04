import { useState, useEffect, useCallback } from 'react';
import {
  getWeatherSystemStatus,
  getCurrentWeatherData,
  getWeatherAlerts,
  getPowerSystemStatus,
  getCybersecurityAgentStatus,
  getCybersecurityMetrics,
  getCoordinatorStatus,
  getSystemState,
} from '@/utils/api';

export interface SystemData {
  weather: {
    status: any;
    currentData: any;
    alerts: any;
    loading: boolean;
    error: any;
  };
  power: {
    status: any;
    loading: boolean;
    error: any;
  };
  cybersecurity: {
    agentStatus: any;
    metrics: any;
    loading: boolean;
    error: any;
  };
  coordinator: {
    status: any;
    systemState: any;
    loading: boolean;
    error: any;
  };
  overallLoading: boolean;
  lastUpdated: Date | null;
}

export const useSystemData = (autoRefresh = true, refreshInterval = 30000) => {
  const [data, setData] = useState<SystemData>({
    weather: { status: null, currentData: null, alerts: null, loading: true, error: null },
    power: { status: null, loading: true, error: null },
    cybersecurity: { agentStatus: null, metrics: null, loading: true, error: null },
    coordinator: { status: null, systemState: null, loading: true, error: null },
    overallLoading: true,
    lastUpdated: null,
  });

  const fetchAllData = useCallback(async () => {
    setData(prev => ({ ...prev, overallLoading: true }));

    try {
      // Fetch all services in parallel
      const [
        weatherStatus,
        weatherData,
        weatherAlerts,
        powerStatus,
        cyberAgentStatus,
        cyberMetrics,
        coordinatorStatus,
        systemState,
      ] = await Promise.allSettled([
        getWeatherSystemStatus(),
        getCurrentWeatherData(),
        getWeatherAlerts(),
        getPowerSystemStatus(),
        getCybersecurityAgentStatus(),
        getCybersecurityMetrics(),
        getCoordinatorStatus(),
        getSystemState(),
      ]);

      setData({
        weather: {
          status: weatherStatus.status === 'fulfilled' ? weatherStatus.value : null,
          currentData: weatherData.status === 'fulfilled' ? weatherData.value : null,
          alerts: weatherAlerts.status === 'fulfilled' ? weatherAlerts.value : null,
          loading: false,
          error:
            weatherStatus.status === 'rejected'
              ? weatherStatus.reason
              : weatherData.status === 'rejected'
              ? weatherData.reason
              : null,
        },
        power: {
          status: powerStatus.status === 'fulfilled' ? powerStatus.value : null,
          loading: false,
          error: powerStatus.status === 'rejected' ? powerStatus.reason : null,
        },
        cybersecurity: {
          agentStatus: cyberAgentStatus.status === 'fulfilled' ? cyberAgentStatus.value : null,
          metrics: cyberMetrics.status === 'fulfilled' ? cyberMetrics.value : null,
          loading: false,
          error: cyberAgentStatus.status === 'rejected' ? cyberAgentStatus.reason : null,
        },
        coordinator: {
          status: coordinatorStatus.status === 'fulfilled' ? coordinatorStatus.value : null,
          systemState: systemState.status === 'fulfilled' ? systemState.value : null,
          loading: false,
          error: coordinatorStatus.status === 'rejected' ? coordinatorStatus.reason : null,
        },
        overallLoading: false,
        lastUpdated: new Date(),
      });
    } catch (error) {
      console.error('Error fetching system data:', error);
      setData(prev => ({
        ...prev,
        overallLoading: false,
      }));
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchAllData();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchAllData]);

  return {
    data,
    refetch: fetchAllData,
    isLoading: data.overallLoading,
  };
};

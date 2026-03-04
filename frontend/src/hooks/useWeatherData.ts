import { useState, useEffect, useCallback } from 'react';
import { getWeatherSystemStatus, getCurrentWeatherData, getWeatherAlerts } from '@/utils/api';

export interface WeatherData {
  status: any;
  currentData: any;
  alerts: any;
  loading: boolean;
  error: any;
  lastUpdated: Date | null;
}

export const useWeatherData = (autoRefresh = true, refreshInterval = 5000) => {
  const [data, setData] = useState<WeatherData>({
    status: null,
    currentData: null,
    alerts: null,
    loading: true,
    error: null,
    lastUpdated: null,
  });

  const fetchData = useCallback(async () => {
    try {
      const [statusRes, currentRes, alertsRes] = await Promise.all([
        getWeatherSystemStatus(),
        getCurrentWeatherData(),
        getWeatherAlerts(),
      ]);

      setData({
        status: statusRes,
        currentData: currentRes,
        alerts: alertsRes,
        loading: false,
        error: null,
        lastUpdated: new Date(),
      });
    } catch (error) {
      console.error('Error fetching weather data:', error);
      setData(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      }));
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchData();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchData]);

  return {
    ...data,
    refetch: fetchData,
  };
};

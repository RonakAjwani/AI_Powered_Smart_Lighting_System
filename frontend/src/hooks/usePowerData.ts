import { useState, useEffect, useCallback } from 'react';
import { getPowerSystemStatus } from '@/utils/api';

export interface PowerData {
  status: any;
  loading: boolean;
  error: any;
  lastUpdated: Date | null;
}

export const usePowerData = (autoRefresh = true, refreshInterval = 5000) => {
  const [data, setData] = useState<PowerData>({
    status: null,
    loading: true,
    error: null,
    lastUpdated: null,
  });

  const fetchData = useCallback(async () => {
    try {
      const statusRes = await getPowerSystemStatus();

      setData({
        status: statusRes,
        loading: false,
        error: null,
        lastUpdated: new Date(),
      });
    } catch (error) {
      console.error('Error fetching power data:', error);
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

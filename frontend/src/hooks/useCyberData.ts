import { useState, useEffect, useCallback } from 'react';
import { getCybersecurityAgentStatus, getCybersecurityMetrics } from '@/utils/api';

export interface CyberData {
  agentStatus: any;
  metrics: any;
  loading: boolean;
  error: any;
  lastUpdated: Date | null;
}

export const useCyberData = (autoRefresh = true, refreshInterval = 5000) => {
  const [data, setData] = useState<CyberData>({
    agentStatus: null,
    metrics: null,
    loading: true,
    error: null,
    lastUpdated: null,
  });

  const fetchData = useCallback(async () => {
    try {
      const [agentRes, metricsRes] = await Promise.all([
        getCybersecurityAgentStatus(),
        getCybersecurityMetrics(),
      ]);

      setData({
        agentStatus: agentRes,
        metrics: metricsRes,
        loading: false,
        error: null,
        lastUpdated: new Date(),
      });
    } catch (error) {
      console.error('Error fetching cybersecurity data:', error);
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

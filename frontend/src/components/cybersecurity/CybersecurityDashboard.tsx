'use client';
import React, { useState, useEffect } from 'react';
import { getCybersecurityAgentStatus, triggerCybersecurityAnalysis, getCybersecurityMetrics } from '@/utils/api';

import Card from '@/components/shared/Card';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import { ShieldCheck, Activity, AlertTriangle } from 'lucide-react';
import CyberMap from './CyberMap';
import ZoneStatusPanel from './ZoneStatusPanel';
import AttackSimulator from './AttackSimulator';

const CybersecurityDashboard: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [isLoadingStatus, setIsLoadingStatus] = useState(true);
  const [isLoadingMetrics, setIsLoadingMetrics] = useState(true);
  const [isLoadingAnalysis, setIsLoadingAnalysis] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoadingStatus(true);
      setIsLoadingMetrics(true);
      setError(null);
      try {
        const [statusData, metricsData] = await Promise.all([
          getCybersecurityAgentStatus(),
          getCybersecurityMetrics()
        ]);

        if (statusData.error) throw new Error(`Status fetch failed: ${statusData.message}`);
        setStatus(statusData);

        if (metricsData.error) throw new Error(`Metrics fetch failed: ${metricsData.message}`);
        setMetrics(metricsData);

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch initial data');
        console.error(err);
      } finally {
        setIsLoadingStatus(false);
        setIsLoadingMetrics(false);
      }
    };
    fetchData();
  }, []);

  const handleRunAnalysis = async () => {
    setIsLoadingAnalysis(true);
    setError(null);
    setAnalysisResult(null);
    try {
      const result = await triggerCybersecurityAnalysis();
      if (result.error) throw new Error(`Analysis trigger failed: ${result.message}`);
      setAnalysisResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run analysis');
      console.error(err);
    } finally {
      setIsLoadingAnalysis(false);
    }
  };

  return (
    <div className="flex flex-col lg:flex-row gap-8 w-full">
      {/* Left: Main Info & Map */}
      <div className="flex-1 flex flex-col gap-6">
        <div className="flex items-center gap-3 mb-2">
          <ShieldCheck className="text-blue-400 w-8 h-8" />
          <h2 className="text-3xl font-bold text-gray-800 dark:text-gray-100 tracking-tight">Cybersecurity Dashboard</h2>
        </div>
        {error && <Card title="Error" className="bg-red-100 border-red-400 text-red-700 dark:bg-red-900 dark:border-red-700 dark:text-red-200">{error}</Card>}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card title={<span className="flex items-center gap-2"><Activity className="text-green-400 w-5 h-5" /> Agent Status</span>}>
            {isLoadingStatus ? <LoadingSpinner /> : (
              status ? <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(status.agents || status, null, 2)}</pre> : <p>No status data</p>
            )}
          </Card>
          <Card title={<span className="flex items-center gap-2"><AlertTriangle className="text-yellow-400 w-5 h-5" /> Security Metrics</span>}>
            {isLoadingMetrics ? <LoadingSpinner /> : (
              metrics ? <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(metrics.current_status || metrics.metrics || metrics, null, 2)}</pre> : <p>No metrics data</p>
            )}
          </Card>
        </div>
        <Card title="Run Analysis">
          <button
            onClick={handleRunAnalysis}
            disabled={isLoadingAnalysis}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoadingAnalysis ? 'Running...' : 'Trigger Full Analysis'}
          </button>
        </Card>
        <CyberMap />
        {analysisResult && (
          <Card title={`Analysis Result (${analysisResult?.analysis_id})`}>
            {isLoadingAnalysis ? <LoadingSpinner /> : (
              <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(analysisResult.result || analysisResult, null, 2)}</pre>
            )}
          </Card>
        )}
      </div>
      {/* Right: Side Panels */}
      <div className="w-full lg:w-[350px] flex flex-col gap-6">
        <ZoneStatusPanel />
        <AttackSimulator />
      </div>
    </div>
  );
};

export default CybersecurityDashboard;
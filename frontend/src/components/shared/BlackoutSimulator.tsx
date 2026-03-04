'use client';

import React, { useState } from 'react';
import toast from 'react-hot-toast';
import { triggerPowerOutage, runPowerWorkflow, runEnergyOptimization, detectPowerOutages } from '@/utils/simulators';
import { logAgentActivity } from '@/components/shared/AgentActivityFeed';
import { Loader2, Zap, Power } from 'lucide-react';

const BlackoutSimulator: React.FC = () => {
  const [loading, setLoading] = useState<string | null>(null);
  const [status, setStatus] = useState('No blackout simulated yet');

  const handleBlackoutSimulation = async () => {
    setLoading('blackout');
    const toastId = toast.loading('Triggering power outage...');
    logAgentActivity('Power Outage Detector', 'Detecting power outage', 'running');

    try {
      const result = await triggerPowerOutage(['zone_1', 'zone_2']);
      setStatus(`Blackout simulated at ${new Date().toLocaleTimeString()}`);
      toast.success('Power outage triggered! Agents responding...', { id: toastId });
      logAgentActivity('Power Outage Detector', 'Outage detected in zones 1 & 2', 'completed');
      console.log('Blackout result:', result);

      // Run power workflow to handle the outage
      setTimeout(async () => {
        try {
          logAgentActivity('Energy Rerouting Agent', 'Rerouting energy to affected zones', 'running');
          await runPowerWorkflow('emergency');
          toast.success('Power agents rerouting energy!');
          logAgentActivity('Energy Rerouting Agent', 'Energy rerouted successfully', 'completed');
        } catch (error) {
          logAgentActivity('Energy Rerouting Agent', 'Rerouting failed', 'error');
          console.error('Workflow error:', error);
        }
      }, 1500);
    } catch (error) {
      toast.error(`Failed to trigger blackout: ${error instanceof Error ? error.message : 'Unknown error'}`, { id: toastId });
      logAgentActivity('Power Outage Detector', 'Detection failed', 'error');
    } finally {
      setLoading(null);
    }
  };

  const handleOutageDetection = async () => {
    setLoading('detect');
    const toastId = toast.loading('Running outage detection...');

    try {
      const result = await detectPowerOutages();
      toast.success('Outage detection complete!', { id: toastId });
      console.log('Detection result:', result);
    } catch (error) {
      toast.error(`Detection failed: ${error instanceof Error ? error.message : 'Unknown error'}`, { id: toastId });
    } finally {
      setLoading(null);
    }
  };

  const handleOptimization = async () => {
    setLoading('optimize');
    const toastId = toast.loading('Running energy optimization...');

    try {
      const result = await runEnergyOptimization();
      toast.success('Energy optimization complete!', { id: toastId });
      console.log('Optimization result:', result);
    } catch (error) {
      toast.error(`Optimization failed: ${error instanceof Error ? error.message : 'Unknown error'}`, { id: toastId });
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="bg-gray-800 rounded-xl p-6 shadow w-full flex flex-col">
      <div className="flex items-center gap-2 mb-4">
        <Zap className="w-5 h-5 text-yellow-500" />
        <h3 className="font-bold text-lg text-gray-100">Power Grid Simulator</h3>
      </div>

      <div className="flex flex-col gap-2 mb-4">
        <button
          className="flex items-center justify-center gap-2 px-5 py-2 rounded bg-red-600 text-white hover:bg-red-700 font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          onClick={handleBlackoutSimulation}
          disabled={loading !== null}
        >
          {loading === 'blackout' && <Loader2 className="w-4 h-4 animate-spin" />}
          <Power className="w-4 h-4" />
          Trigger Blackout
        </button>

        <button
          className="flex items-center justify-center gap-2 px-5 py-2 rounded bg-orange-600 text-white hover:bg-orange-700 font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          onClick={handleOutageDetection}
          disabled={loading !== null}
        >
          {loading === 'detect' && <Loader2 className="w-4 h-4 animate-spin" />}
          Detect Outages
        </button>

        <button
          className="flex items-center justify-center gap-2 px-5 py-2 rounded bg-green-600 text-white hover:bg-green-700 font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          onClick={handleOptimization}
          disabled={loading !== null}
        >
          {loading === 'optimize' && <Loader2 className="w-4 h-4 animate-spin" />}
          Optimize Energy
        </button>
      </div>

      <div className="text-xs text-gray-300 p-2 bg-gray-900 rounded">{status}</div>
    </div>
  );
};

export default BlackoutSimulator;

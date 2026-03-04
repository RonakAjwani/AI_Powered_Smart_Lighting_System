'use client';

import React, { useState } from "react";
import toast from 'react-hot-toast';
import { simulateWeatherEvent, executeWeatherWorkflow } from '@/utils/simulators';
import { logAgentActivity } from '@/components/shared/AgentActivityFeed';
import { Loader2 } from 'lucide-react';

const zones = [
  { id: 'airport', name: 'Airport' },
  { id: 'midtown', name: 'Midtown' }
];

const ZoneControlPanel: React.FC = () => {
  const [selectedZone, setSelectedZone] = useState(zones[0].id);
  const [loading, setLoading] = useState<string | null>(null);

  const handleWeatherSimulation = async (eventType: 'heatwave' | 'heavyrain' | 'storm') => {
    setLoading(eventType);
    const toastId = toast.loading(`Simulating ${eventType}...`);
    logAgentActivity('Weather Agent', `Simulating ${eventType} scenario`, 'running');

    try {
      const result = await simulateWeatherEvent(eventType);
      toast.success(`Weather Agent executed ${eventType} scenario successfully!`, { id: toastId });
      logAgentActivity('Weather Agent', `${eventType} scenario completed`, 'completed');
      console.log('Weather simulation result:', result);

      // Trigger full workflow after simulation
      setTimeout(async () => {
        logAgentActivity('Weather Intelligence', 'Executing emergency workflow', 'running');
        await executeWeatherWorkflow('emergency');
        logAgentActivity('Weather Intelligence', 'Emergency workflow complete', 'completed');
      }, 1000);
    } catch (error) {
      toast.error(`Failed to simulate ${eventType}: ${error instanceof Error ? error.message : 'Unknown error'}`, { id: toastId });
      logAgentActivity('Weather Agent', `Failed: ${eventType}`, 'error');
      console.error('Weather simulation error:', error);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="bg-gray-800 rounded-xl p-6 shadow flex flex-col gap-4 w-full">
      <h3 className="font-bold text-lg text-gray-100">Weather Simulator</h3>
      <label className="text-gray-300 text-sm mb-1" htmlFor="zone-select">Select Zone:</label>
      <select
        id="zone-select"
        value={selectedZone}
        className="rounded px-3 py-2 bg-gray-700 text-gray-100"
        onChange={e => setSelectedZone(e.target.value)}
      >
        {zones.map(z => (<option key={z.id} value={z.id}>{z.name}</option>))}
      </select>
      <div className="flex flex-col gap-2 mt-3">
        <button
          className="flex items-center justify-center gap-2 px-3 py-2 rounded bg-yellow-500 hover:bg-yellow-600 text-white font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          onClick={() => handleWeatherSimulation('heatwave')}
          disabled={loading !== null}
        >
          {loading === 'heatwave' && <Loader2 className="w-4 h-4 animate-spin" />}
          Simulate Heatwave
        </button>
        <button
          className="flex items-center justify-center gap-2 px-3 py-2 rounded bg-blue-500 hover:bg-blue-600 text-white font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          onClick={() => handleWeatherSimulation('heavyrain')}
          disabled={loading !== null}
        >
          {loading === 'heavyrain' && <Loader2 className="w-4 h-4 animate-spin" />}
          Simulate Heavy Rain
        </button>
        <button
          className="flex items-center justify-center gap-2 px-3 py-2 rounded bg-red-500 hover:bg-red-600 text-white font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          onClick={() => handleWeatherSimulation('storm')}
          disabled={loading !== null}
        >
          {loading === 'storm' && <Loader2 className="w-4 h-4 animate-spin" />}
          Simulate Storm
        </button>
      </div>
    </div>
  );
};

export default ZoneControlPanel;

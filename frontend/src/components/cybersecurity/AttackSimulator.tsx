'use client';

import React, { useState } from "react";
import toast from 'react-hot-toast';
import { simulateCyberAttack, runSecurityAnalysis, triggerIntrusionResponse } from '@/utils/simulators';
import { logAgentActivity } from '@/components/shared/AgentActivityFeed';
import { Loader2, Shield, AlertTriangle } from 'lucide-react';

const AttackSimulator: React.FC = () => {
  const [loading, setLoading] = useState<string | null>(null);
  const [lastAttack, setLastAttack] = useState<string | null>(null);

  const handleAttackSimulation = async (attackType: 'ddos' | 'malware' | 'intrusion' | 'data_breach') => {
    setLoading(attackType);
    const toastId = toast.loading(`Simulating ${attackType} attack...`);
    logAgentActivity('Threat Detection Agent', `Detecting ${attackType} attack`, 'running');

    try {
      const result = await simulateCyberAttack(attackType);
      setLastAttack(`${attackType} attack simulated at ${new Date().toLocaleTimeString()}`);
      toast.success(`Cyber threat simulated! Security agents detecting...`, { id: toastId });
      logAgentActivity('Threat Detection Agent', `${attackType} threat detected`, 'completed');
      console.log('Cyber attack result:', result);

      // Trigger security analysis after attack
      setTimeout(async () => {
        try {
          logAgentActivity('Security Analysis Agent', 'Running full security analysis', 'running');
          await runSecurityAnalysis();
          toast.success('Security analysis complete!');
          logAgentActivity('Security Analysis Agent', 'Analysis complete', 'completed');
        } catch (error) {
          logAgentActivity('Security Analysis Agent', 'Analysis failed', 'error');
          console.error('Analysis error:', error);
        }
      }, 1500);
    } catch (error) {
      toast.error(`Failed to simulate attack: ${error instanceof Error ? error.message : 'Unknown error'}`, { id: toastId });
      logAgentActivity('Threat Detection Agent', `Failed to detect ${attackType}`, 'error');
      console.error('Cyber attack error:', error);
    } finally {
      setLoading(null);
    }
  };

  const handleIntrusionResponse = async () => {
    setLoading('response');
    const toastId = toast.loading('Triggering intrusion response...');

    try {
      const result = await triggerIntrusionResponse();
      toast.success('Intrusion response agent activated!', { id: toastId });
      console.log('Intrusion response result:', result);
    } catch (error) {
      toast.error(`Failed to trigger response: ${error instanceof Error ? error.message : 'Unknown error'}`, { id: toastId });
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="bg-gray-800 rounded-xl p-6 shadow w-full">
      <div className="flex items-center gap-2 mb-4">
        <Shield className="w-5 h-5 text-red-500" />
        <h3 className="font-bold text-lg text-gray-100">Attack Simulator</h3>
      </div>

      <div className="flex flex-col gap-2 mb-4">
        <button
          className="flex items-center justify-center gap-2 px-4 py-2 rounded bg-red-600 text-white font-semibold hover:bg-red-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={() => handleAttackSimulation('intrusion')}
          disabled={loading !== null}
        >
          {loading === 'intrusion' && <Loader2 className="w-4 h-4 animate-spin" />}
          Intrusion Attack
        </button>

        <button
          className="flex items-center justify-center gap-2 px-4 py-2 rounded bg-orange-600 text-white font-semibold hover:bg-orange-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={() => handleAttackSimulation('ddos')}
          disabled={loading !== null}
        >
          {loading === 'ddos' && <Loader2 className="w-4 h-4 animate-spin" />}
          DDoS Attack
        </button>

        <button
          className="flex items-center justify-center gap-2 px-4 py-2 rounded bg-purple-600 text-white font-semibold hover:bg-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={() => handleAttackSimulation('malware')}
          disabled={loading !== null}
        >
          {loading === 'malware' && <Loader2 className="w-4 h-4 animate-spin" />}
          Malware Attack
        </button>

        <button
          className="flex items-center justify-center gap-2 px-4 py-2 rounded bg-blue-600 text-white font-semibold hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={handleIntrusionResponse}
          disabled={loading !== null}
        >
          {loading === 'response' && <Loader2 className="w-4 h-4 animate-spin" />}
          <AlertTriangle className="w-4 h-4" />
          Activate Response
        </button>
      </div>

      <div className="text-xs text-gray-400 mt-2 p-2 bg-gray-900 rounded">
        {lastAttack || 'No simulated attack yet'}
      </div>
    </div>
  );
};

export default AttackSimulator;

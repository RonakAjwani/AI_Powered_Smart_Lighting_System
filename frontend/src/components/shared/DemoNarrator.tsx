'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Square, Volume2 } from 'lucide-react';
import { DemoStep, DemoScenario } from '@/utils/demoOrchestrator';

interface DemoEvent {
  type: 'start' | 'step' | 'complete' | 'error';
  data?: any;
  timestamp: Date;
}

interface NarrationEntry {
  id: string;
  narration: string;
  timestamp: Date;
  icon: string;
}

export const DemoNarrator: React.FC = () => {
  const [isActive, setIsActive] = useState(false);
  const [currentScenario, setCurrentScenario] = useState<DemoScenario | null>(null);
  const [narrations, setNarrations] = useState<NarrationEntry[]>([]);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const handleDemoEvent = (event: Event) => {
      const customEvent = event as CustomEvent<DemoEvent>;
      const { type, data } = customEvent.detail;

      if (type === 'start') {
        setIsActive(true);
        setCurrentScenario(data.scenario);
        setNarrations([]);
        setProgress(0);
      } else if (type === 'step') {
        const step: DemoStep = data.step;
        const index: number = data.index;

        setNarrations(prev => [
          ...prev,
          {
            id: step.id,
            narration: step.narration,
            timestamp: new Date(),
            icon: getStepIcon(step.agent),
          }
        ]);

        if (currentScenario) {
          setProgress(((index + 1) / currentScenario.steps.length) * 100);
        }
      } else if (type === 'complete' || type === 'error') {
        setTimeout(() => {
          setIsActive(false);
          setProgress(100);
        }, 3000);
      }
    };

    window.addEventListener('demo-event', handleDemoEvent);
    return () => window.removeEventListener('demo-event', handleDemoEvent);
  }, [currentScenario]);

  const getStepIcon = (agent: string): string => {
    if (agent.includes('Weather')) return '🌤️';
    if (agent.includes('Power') || agent.includes('Grid')) return '⚡';
    if (agent.includes('Cyber') || agent.includes('Security')) return '🔐';
    if (agent.includes('Coordinator') || agent.includes('Manager')) return '🎯';
    if (agent.includes('Emergency')) return '🚨';
    if (agent.includes('Backup')) return '🔋';
    return '📡';
  };

  if (!isActive && narrations.length === 0) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="fixed bottom-6 right-6 z-50 w-[420px]"
    >
      <div className="bg-gray-900 border-2 border-purple-500 rounded-xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-blue-600 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
              <div>
                <h3 className="text-white font-bold text-sm">Demo Running</h3>
                <p className="text-purple-100 text-xs">
                  {currentScenario?.name || 'System Demo'}
                </p>
              </div>
            </div>
            <Volume2 className="w-5 h-5 text-white animate-pulse" />
          </div>

          {/* Progress bar */}
          <div className="mt-3 w-full bg-purple-900/50 rounded-full h-2">
            <motion.div
              className="bg-gradient-to-r from-green-400 to-blue-400 h-2 rounded-full"
              initial={{ width: '0%' }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>

        {/* Narration feed */}
        <div className="p-4 max-h-[400px] overflow-y-auto space-y-3">
          <AnimatePresence mode="popLayout">
            {narrations.map((narration, index) => (
              <motion.div
                key={narration.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ delay: 0.1 }}
                className="flex items-start gap-3 p-3 bg-gray-800 rounded-lg border border-gray-700"
              >
                <span className="text-2xl">{narration.icon}</span>
                <div className="flex-1">
                  <p className="text-gray-100 text-sm leading-relaxed">
                    {narration.narration}
                  </p>
                  <p className="text-gray-500 text-xs mt-1">
                    {narration.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Footer */}
        {isActive && (
          <div className="p-3 bg-gray-950 border-t border-gray-800">
            <div className="flex items-center justify-between text-xs text-gray-400">
              <span>
                Step {narrations.length} of {currentScenario?.steps.length || 0}
              </span>
              <span className="flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                Live Demo
              </span>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default DemoNarrator;

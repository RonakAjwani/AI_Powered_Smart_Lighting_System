'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Play, Square, Clock, Zap } from 'lucide-react';
import { demoScenarios, demoRunner, DemoScenario } from '@/utils/demoOrchestrator';
import Card from './Card';

export const DemoControlPanel: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [currentScenario, setCurrentScenario] = useState<DemoScenario | null>(null);

  useEffect(() => {
    const handleDemoEvent = (event: Event) => {
      const customEvent = event as CustomEvent;
      const { type, data } = customEvent.detail;

      if (type === 'start') {
        setIsRunning(true);
        setCurrentScenario(data.scenario);
      } else if (type === 'complete' || type === 'error') {
        setTimeout(() => {
          setIsRunning(false);
          setCurrentScenario(null);
        }, 2000);
      }
    };

    window.addEventListener('demo-event', handleDemoEvent);
    return () => window.removeEventListener('demo-event', handleDemoEvent);
  }, []);

  const handleRunDemo = async (scenario: DemoScenario) => {
    if (isRunning) {
      return;
    }
    await demoRunner.runScenario(scenario);
  };

  const handleStopDemo = () => {
    demoRunner.stop();
    setIsRunning(false);
    setCurrentScenario(null);
  };

  return (
    <Card>
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100 flex items-center gap-2">
            <Zap className="w-6 h-6 text-purple-500" />
            Auto-Demo Mode
          </h2>
          {isRunning && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center gap-2 px-3 py-1 bg-red-500 rounded-full"
            >
              <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
              <span className="text-white text-sm font-medium">Running</span>
            </motion.div>
          )}
        </div>
        <p className="text-gray-600 dark:text-gray-400 text-sm">
          Watch complete scenarios demonstrating multi-agent coordination in action
        </p>
      </div>

      {/* Stop button if running */}
      {isRunning && currentScenario && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 p-4 bg-purple-50 dark:bg-purple-900/20 border-2 border-purple-300 dark:border-purple-700 rounded-lg"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="font-semibold text-gray-800 dark:text-gray-100">
                {currentScenario.icon} {currentScenario.name}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Demo in progress... Watch the timeline below
              </p>
            </div>
            <button
              onClick={handleStopDemo}
              className="flex items-center gap-2 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors"
            >
              <Square className="w-4 h-4" />
              Stop
            </button>
          </div>
        </motion.div>
      )}

      {/* Demo scenario cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {demoScenarios.map((scenario) => (
          <motion.div
            key={scenario.id}
            whileHover={{ scale: isRunning ? 1 : 1.02 }}
            className={`
              p-5 rounded-xl border-2 transition-all
              ${
                currentScenario?.id === scenario.id
                  ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                  : 'border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800'
              }
              ${isRunning ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:shadow-lg'}
            `}
            onClick={() => !isRunning && handleRunDemo(scenario)}
          >
            <div className="flex items-start gap-4">
              <div className="text-4xl">{scenario.icon}</div>
              <div className="flex-1">
                <h3 className="font-bold text-gray-800 dark:text-gray-100 mb-2">
                  {scenario.name}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  {scenario.description}
                </p>

                <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-500">
                  <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    <span>~{scenario.duration}s</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Zap className="w-3 h-3" />
                    <span>{scenario.steps.length} steps</span>
                  </div>
                </div>

                {!isRunning && (
                  <button
                    className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-colors text-sm font-medium"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRunDemo(scenario);
                    }}
                  >
                    <Play className="w-4 h-4" />
                    Run Demo
                  </button>
                )}

                {currentScenario?.id === scenario.id && (
                  <div className="mt-4 flex items-center justify-center gap-2 text-purple-600 dark:text-purple-400">
                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-ping" />
                    <span className="text-sm font-medium">Running...</span>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Instructions */}
      {!isRunning && (
        <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-300 dark:border-blue-800 rounded-lg">
          <p className="text-sm text-gray-700 dark:text-gray-300">
            <strong>How it works:</strong> Select a demo scenario to watch AI agents coordinate automatically.
            The narration panel will appear showing each step in real-time. Watch the activity feed and
            dashboards update as agents respond to the scenario.
          </p>
        </div>
      )}
    </Card>
  );
};

export default DemoControlPanel;

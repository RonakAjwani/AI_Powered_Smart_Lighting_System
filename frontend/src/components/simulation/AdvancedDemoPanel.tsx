'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Activity, Zap, AlertTriangle, Target, Settings, Sun } from 'lucide-react';
import { advancedScenarios, scenarioRunner, AdvancedScenario } from '@/utils/scenarioEngine';
import { PowerGridTopology } from '@/utils/streetLightGenerator';
import { Incident } from '@/components/map/IncidentMarkers';
import Card from '@/components/shared/Card';

interface AdvancedDemoPanelProps {
  onGridUpdate?: (grid: PowerGridTopology, incidents: Incident[]) => void;
  initialGrid?: PowerGridTopology | null;
}

const getDifficultyColor = (difficulty: AdvancedScenario['difficulty']) => {
  switch (difficulty) {
    case 'EASY':
      return 'bg-green-500/20 text-green-400 border-green-500/30';
    case 'MEDIUM':
      return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
    case 'HARD':
      return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
    case 'EXTREME':
      return 'bg-red-500/20 text-red-400 border-red-500/30';
    default:
      return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
  }
};

const getDifficultyIcon = (difficulty: AdvancedScenario['difficulty']) => {
  switch (difficulty) {
    case 'EASY':
      return <Target className="w-4 h-4" />;
    case 'MEDIUM':
      return <Activity className="w-4 h-4" />;
    case 'HARD':
      return <AlertTriangle className="w-4 h-4" />;
    case 'EXTREME':
      return <Zap className="w-4 h-4" />;
    default:
      return null;
  }
};

export const AdvancedDemoPanel: React.FC<AdvancedDemoPanelProps> = ({
  onGridUpdate,
  initialGrid,
}) => {
  const [isRunning, setIsRunning] = useState(false);
  const [currentScenario, setCurrentScenario] = useState<AdvancedScenario | null>(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (initialGrid) {
      scenarioRunner.setGrid(initialGrid);
    }

    if (onGridUpdate) {
      scenarioRunner.setOnGridUpdate(onGridUpdate);
    }
  }, [initialGrid, onGridUpdate]);

  useEffect(() => {
    // Monitor scenario runner state
    const interval = setInterval(() => {
      const running = scenarioRunner.getIsRunning();
      const scenario = scenarioRunner.getCurrentScenario();

      setIsRunning(running);
      setCurrentScenario(scenario);

      // Calculate progress based on time
      if (running && scenario) {
        const elapsed = Date.now() - (scenario as any).startTime || 0;
        const totalDuration = scenario.duration * 1000;
        setProgress(Math.min(100, (elapsed / totalDuration) * 100));
      } else {
        setProgress(0);
      }
    }, 100);

    return () => clearInterval(interval);
  }, []);

  const handleRunScenario = async (scenario: AdvancedScenario) => {
    if (isRunning || !initialGrid) {
      return;
    }

    (scenario as any).startTime = Date.now();
    await scenarioRunner.runScenario(scenario);
  };

  const handleStopScenario = () => {
    scenarioRunner.stop();
    setIsRunning(false);
    setCurrentScenario(null);
    setProgress(0);
  };

  return (
    <Card>
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100 flex items-center gap-2">
            <Zap className="w-6 h-6 text-purple-500" />
            Advanced Simulation Scenarios
          </h2>
          {isRunning && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center gap-2 px-3 py-1 bg-purple-500 rounded-full"
            >
              <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
              <span className="text-white text-sm font-medium">LIVE</span>
            </motion.div>
          )}
        </div>
        <p className="text-gray-600 dark:text-gray-400 text-sm">
          Realistic physics-based scenarios with cascading effects and multi-agent coordination
        </p>
      </div>

      {/* Current Scenario Progress */}
      {isRunning && currentScenario && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 p-5 bg-gradient-to-r from-purple-900/30 to-blue-900/30 border-2 border-purple-500/50 rounded-xl"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <span className="text-3xl">{currentScenario.icon}</span>
              <div>
                <p className="font-bold text-lg text-gray-100">
                  {currentScenario.name}
                </p>
                <p className="text-sm text-gray-400 mt-0.5">
                  {currentScenario.steps.length} steps • {currentScenario.duration}s duration
                </p>
              </div>
            </div>
            <button
              onClick={handleStopScenario}
              className="flex items-center gap-2 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors font-medium"
            >
              <Settings className="w-4 h-4" />
              Stop
            </button>
          </div>

          {/* Progress Bar */}
          <div className="mt-4">
            <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
              <span>Progress</span>
              <span>{progress.toFixed(0)}%</span>
            </div>
            <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-purple-500 to-blue-500 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>

          {/* Objectives Checklist */}
          <div className="mt-4 pt-4 border-t border-purple-500/30">
            <p className="text-xs font-semibold text-gray-400 mb-2">OBJECTIVES</p>
            <div className="space-y-1">
              {currentScenario.objectives.map((objective, index) => (
                <div
                  key={index}
                  className="flex items-center gap-2 text-xs text-gray-300"
                >
                  <div className={`w-2 h-2 rounded-full ${
                    progress > (index / currentScenario.objectives.length) * 100
                      ? 'bg-green-500'
                      : 'bg-gray-600'
                  }`} />
                  <span className={
                    progress > (index / currentScenario.objectives.length) * 100
                      ? 'text-green-400'
                      : ''
                  }>
                    {objective}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {/* Scenario Cards */}
      <div className="grid grid-cols-1 gap-5">
        {advancedScenarios.map((scenario) => (
          <motion.div
            key={scenario.id}
            whileHover={{ scale: isRunning ? 1 : 1.01 }}
            className={`
              p-6 rounded-xl border-2 transition-all
              ${
                currentScenario?.id === scenario.id
                  ? 'border-purple-500 bg-purple-900/20 shadow-lg shadow-purple-500/20'
                  : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
              }
              ${isRunning ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:shadow-xl'}
            `}
            onClick={() => !isRunning && handleRunScenario(scenario)}
          >
            <div className="flex items-start gap-4">
              {/* Icon */}
              <div className="text-5xl flex-shrink-0">
                {scenario.icon}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                {/* Header */}
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex-1">
                    <h3 className="font-bold text-xl text-gray-100 mb-1">
                      {scenario.name}
                    </h3>
                    <p className="text-sm text-gray-400 leading-relaxed">
                      {scenario.description}
                    </p>
                  </div>

                  {/* Difficulty Badge */}
                  <div className={`
                    flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-bold whitespace-nowrap
                    ${getDifficultyColor(scenario.difficulty)}
                  `}>
                    {getDifficultyIcon(scenario.difficulty)}
                    {scenario.difficulty}
                  </div>
                </div>

                {/* Metadata */}
                <div className="flex items-center gap-6 text-xs text-gray-500 mb-4">
                  <div className="flex items-center gap-1.5">
                    <Sun className="w-3.5 h-3.5" />
                    <span>~{scenario.duration}s</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Zap className="w-3.5 h-3.5" />
                    <span>{scenario.steps.length} steps</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Target className="w-3.5 h-3.5" />
                    <span>{scenario.objectives.length} objectives</span>
                  </div>
                </div>

                {/* Objectives Preview */}
                <div className="mb-4">
                  <p className="text-xs font-semibold text-gray-400 mb-2">KEY OBJECTIVES:</p>
                  <ul className="space-y-1">
                    {scenario.objectives.slice(0, 3).map((objective, index) => (
                      <li key={index} className="flex items-start gap-2 text-xs text-gray-300">
                        <span className="text-purple-400 mt-0.5">▸</span>
                        <span>{objective}</span>
                      </li>
                    ))}
                    {scenario.objectives.length > 3 && (
                      <li className="text-xs text-gray-500 ml-4">
                        +{scenario.objectives.length - 3} more...
                      </li>
                    )}
                  </ul>
                </div>

                {/* Action Button */}
                {!isRunning && (
                  <button
                    className="w-full flex items-center justify-center gap-2 px-5 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white rounded-lg transition-all text-sm font-bold shadow-lg hover:shadow-xl"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRunScenario(scenario);
                    }}
                  >
                    <Zap className="w-4 h-4" />
                    Launch Scenario
                  </button>
                )}

                {currentScenario?.id === scenario.id && (
                  <div className="mt-4 flex items-center justify-center gap-2 text-purple-400 animate-pulse">
                    <div className="w-2 h-2 bg-purple-400 rounded-full" />
                    <span className="text-sm font-semibold">RUNNING...</span>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Instructions */}
      {!isRunning && (
        <div className="mt-6 p-5 bg-blue-900/20 border border-blue-700/50 rounded-lg">
          <p className="text-sm text-gray-300 leading-relaxed">
            <strong className="text-blue-400">💡 Pro Tip:</strong> These scenarios simulate real-world events with
            cascading effects. Watch the live map, agent activity feed, and system metrics update in real-time as
            the AI agents coordinate their response. Each scenario demonstrates different aspects of multi-agent
            collaboration and decision-making.
          </p>
        </div>
      )}
    </Card>
  );
};

export default AdvancedDemoPanel;

'use client';

import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle, AlertTriangle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface ActivityItem {
  id: string;
  agent: string;
  action: string;
  status: 'running' | 'completed' | 'error';
  timestamp: Date;
}

export const AgentActivityFeed: React.FC = () => {
  const [activities, setActivities] = useState<ActivityItem[]>([]);

  // Subscribe to window events for activity updates
  useEffect(() => {
    const handleActivity = (event: CustomEvent) => {
      const newActivity: ActivityItem = {
        id: `${Date.now()}-${Math.random()}`,
        agent: event.detail.agent,
        action: event.detail.action,
        status: event.detail.status || 'running',
        timestamp: new Date(),
      };

      setActivities(prev => [newActivity, ...prev].slice(0, 10)); // Keep last 10 activities

      // Auto-complete running activities after 3 seconds
      if (newActivity.status === 'running') {
        setTimeout(() => {
          setActivities(prev =>
            prev.map(item =>
              item.id === newActivity.id ? { ...item, status: 'completed' as const } : item
            )
          );
        }, 3000);
      }
    };

    window.addEventListener('agent-activity', handleActivity as EventListener);
    return () => window.removeEventListener('agent-activity', handleActivity as EventListener);
  }, []);

  const getStatusIcon = (status: ActivityItem['status']) => {
    switch (status) {
      case 'running':
        return <Activity className="w-4 h-4 text-blue-400 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'error':
        return <AlertTriangle className="w-4 h-4 text-red-400" />;
    }
  };

  const getStatusColor = (status: ActivityItem['status']) => {
    switch (status) {
      case 'running':
        return 'border-blue-500 bg-blue-500/10';
      case 'completed':
        return 'border-green-500 bg-green-500/10';
      case 'error':
        return 'border-red-500 bg-red-500/10';
    }
  };

  return (
    <div className="bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-700 w-full">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-5 h-5 text-purple-400" />
        <h3 className="font-bold text-lg text-gray-100">Agent Activity</h3>
      </div>

      <div className="space-y-2 max-h-96 overflow-y-auto">
        <AnimatePresence>
          {activities.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              No agent activity yet. Trigger a simulation to see agents in action!
            </div>
          ) : (
            activities.map(activity => (
              <motion.div
                key={activity.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className={`p-3 rounded-lg border ${getStatusColor(activity.status)} transition-all`}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">{getStatusIcon(activity.status)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-gray-200 text-sm">{activity.agent}</div>
                    <div className="text-xs text-gray-400 mt-0.5">{activity.action}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {activity.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

// Helper function to dispatch activity events
export const logAgentActivity = (agent: string, action: string, status?: 'running' | 'completed' | 'error') => {
  window.dispatchEvent(
    new CustomEvent('agent-activity', {
      detail: { agent, action, status: status || 'running' },
    })
  );
};

export default AgentActivityFeed;

'use client'; // Needed for Zustand hook

import React from 'react';
import { useDashboardStore } from '@/store/useDashboardStore';
import LoadingSpinner from '@/components/shared/LoadingSpinner'; // Assume this exists

// Lazy load agent dashboards for better performance
const LazyCybersecurityDashboard = React.lazy(() => import('@/components/cybersecurity/CybersecurityDashboard'));
const LazyWeatherDashboard = React.lazy(() => import('@/components/weather/WeatherDashboard'));
const LazyPowerDashboard = React.lazy(() => import('@/components/power/PowerDashboard'));


const AgentViewDisplay: React.FC = () => {
  const selectedAgentView = useDashboardStore((state) => state.selectedAgentView);

  const renderAgentView = () => {
    switch (selectedAgentView) {
      case 'cybersecurity':
        return <LazyCybersecurityDashboard />;
      case 'weather':
        return <LazyWeatherDashboard />;
      case 'power':
        return <LazyPowerDashboard />;
      case 'overview': // Should ideally be handled in page.tsx, but included for completeness
         return <div>Overview Dashboard Placeholder</div>;
      default:
        return <div>Select an agent view from the sidebar.</div>;
    }
  };

  return (
     <React.Suspense fallback={<LoadingSpinner />}>
        {renderAgentView()}
     </React.Suspense>
    );
};

export default AgentViewDisplay;
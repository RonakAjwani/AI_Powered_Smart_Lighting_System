'use client';

import React from "react";
import { useDashboardStore } from '@/store/useDashboardStore';
import { CloudSun, ShieldCheck, Zap } from 'lucide-react';
import MapAndControls from '@/components/shared/MapAndControls';
import DashboardMetrics from '@/components/shared/DashboardMetrics';
import LiveClockAndWeather from '@/components/shared/LiveClockAndWeather';
import FleetAnalytics from '@/components/shared/FleetAnalytics';
import Footer from '@/components/shared/Footer';
// Weather panels
import ZoneControlPanel from '@/components/weather/ZoneControlPanel';
import LiveAnalysisPanel from '@/components/weather/LiveAnalysisPanel';
import AgentLogPanel from '@/components/weather/AgentLogPanel';
// Cybersecurity panels
import ZoneStatusPanel from '@/components/cybersecurity/ZoneStatusPanel';
import AttackSimulator from '@/components/cybersecurity/AttackSimulator';
// Blackout panels
import ZonePowerPanel from '@/components/shared/ZonePowerPanel';
import IncidentPanel from '@/components/shared/IncidentPanel';
import BlackoutSimulator from '@/components/shared/BlackoutSimulator';

const UnifiedDashboard: React.FC = () => {
  const selectedAgentView = useDashboardStore((state) => state.selectedAgentView);

  // Header icon and title
  let icon = <CloudSun className="text-yellow-400 w-8 h-8" />;
  let title = 'Weather Agent Dashboard';
  let mainPanels = null;
  let sidePanels = null;

  // Uniform main panel layout: grid for cards, fixed map size, consistent spacing
  let mainGridPanels = null;
  if (selectedAgentView === 'weather') {
    mainGridPanels = (
      <>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full">
          <LiveClockAndWeather />
          <DashboardMetrics />
        </div>
        <div className="flex flex-col md:flex-row gap-6 w-full">
          <div className="flex-1 min-w-[350px] max-w-[600px] mx-auto">
            <MapAndControls />
          </div>
          <div className="flex-1 min-w-[300px] max-w-[400px] mx-auto">
            <FleetAnalytics />
          </div>
        </div>
      </>
    );
    sidePanels = (
      <div className="flex flex-col gap-6">
        <ZoneControlPanel />
        <LiveAnalysisPanel />
        <AgentLogPanel />
      </div>
    );
  } else if (selectedAgentView === 'cybersecurity') {
    icon = <ShieldCheck className="text-blue-400 w-8 h-8" />;
    title = 'Cybersecurity Dashboard';
    mainGridPanels = (
      <>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full">
          <DashboardMetrics />
          <div />
        </div>
        <div className="flex flex-col md:flex-row gap-6 w-full">
          <div className="flex-1 min-w-[350px] max-w-[600px] mx-auto">
            <MapAndControls />
          </div>
          <div className="flex-1 min-w-[300px] max-w-[400px] mx-auto" />
        </div>
      </>
    );
    sidePanels = (
      <div className="flex flex-col gap-6">
        <ZoneStatusPanel />
        <AttackSimulator />
      </div>
    );
  } else if (selectedAgentView === 'power') {
    icon = <Zap className="text-green-400 w-8 h-8" />;
    title = 'Power Grid Dashboard';
    mainGridPanels = (
      <>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full">
          <DashboardMetrics />
          <div />
        </div>
        <div className="flex flex-col md:flex-row gap-6 w-full">
          <div className="flex-1 min-w-[350px] max-w-[600px] mx-auto">
            <MapAndControls />
          </div>
          <div className="flex-1 min-w-[300px] max-w-[400px] mx-auto">
            <FleetAnalytics />
          </div>
        </div>
      </>
    );
    sidePanels = (
      <div className="flex flex-col gap-6">
        <ZonePowerPanel />
        <IncidentPanel />
        <BlackoutSimulator />
      </div>
    );
  }

  return (
    <div className="flex flex-col lg:flex-row gap-8 w-full px-8 py-8 max-w-7xl mx-auto">
      {/* Left: Main Info & Map */}
      <div className="flex-1 flex flex-col gap-8">
        <div className="flex items-center gap-3 mb-4">
          {icon}
          <h2 className="text-3xl font-bold text-gray-800 dark:text-gray-100 tracking-tight">{title}</h2>
        </div>
        {mainGridPanels}
      </div>
      {/* Right: Side Panels */}
      <div className="w-full lg:w-[350px] flex flex-col gap-6">
        {sidePanels}
      </div>
      <Footer />
    </div>
  );
};

export default UnifiedDashboard;

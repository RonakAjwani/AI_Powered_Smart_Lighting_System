'use client';

import React from 'react';
import { useDashboardStore } from '@/store/useDashboardStore';
import MissionControlHeader from '@/components/layout/MissionControlHeader';
import WeatherLightingView from '@/components/views/WeatherLightingView';
import CyberDefenseView from '@/components/views/CyberDefenseView';
import PowerGridView from '@/components/views/PowerGridView';

export default function MainPage() {
  const selectedAgentView = useDashboardStore((s) => s.selectedAgentView);

  return (
    <div className="min-h-screen">
      <MissionControlHeader />
      {selectedAgentView === 'weather' && <WeatherLightingView />}
      {selectedAgentView === 'cybersecurity' && <CyberDefenseView />}
      {selectedAgentView === 'power' && <PowerGridView />}
      {selectedAgentView === 'overview' && <WeatherLightingView />}
    </div>
  );
}

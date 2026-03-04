'use client'; // Needed for Zustand hook and onClick handlers

import React from 'react';
import { ShieldCheck, CloudSun, Zap, LayoutDashboard } from 'lucide-react';
import { useDashboardStore, AgentView } from '@/store/useDashboardStore';



const navItems = [
  {
    key: 'weather',
    label: 'Weather Dashboard',
    icon: <CloudSun className="w-5 h-5 mr-2 text-yellow-300" />,
  },
  {
    key: 'cybersecurity',
    label: 'Cybersecurity',
    icon: <ShieldCheck className="w-5 h-5 mr-2 text-blue-300" />,
  },
  {
    key: 'power',
    label: 'Blackout Response',
    icon: <Zap className="w-5 h-5 mr-2 text-green-300" />,
  },
];

const Sidebar: React.FC = () => {
  const selected = useDashboardStore((state) => state.selectedAgentView);
  const setSelected = useDashboardStore((state) => state.setSelectedAgentView);
  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col h-full shadow-md">
      {/* Title */}
      <div className="p-6 border-b border-gray-800">
        <h1 className="text-2xl font-bold tracking-tight">Mumbai Smart City</h1>
      </div>
      {/* Navigation */}
      <nav className="flex-1 p-6 space-y-2">
        {navItems.map((item) => (
          <button
            key={item.key}
            className={`flex items-center w-full text-left px-3 py-2 rounded-lg font-medium transition-colors
              ${selected === item.key ? 'bg-gray-800 text-yellow-300 shadow-inner' : 'hover:bg-gray-800 hover:text-yellow-200 text-gray-200'}`}
            onClick={() => setSelected(item.key as AgentView)}
          >
            {item.icon}
            {item.label}
          </button>
        ))}
      </nav>
      <div className="p-4 text-xs text-gray-500 mt-auto opacity-70">© {new Date().getFullYear()} Mumbai Smart City</div>
    </aside>
  );
};

export default Sidebar;
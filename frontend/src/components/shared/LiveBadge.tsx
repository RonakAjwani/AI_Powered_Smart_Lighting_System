'use client';

import React from 'react';
import { Radio, Wifi } from 'lucide-react';

interface LiveBadgeProps {
  showNetwork?: boolean;
  variant?: 'default' | 'success' | 'warning';
}

const LiveBadge: React.FC<LiveBadgeProps> = ({
  showNetwork = false,
  variant = 'success'
}) => {
  const colors = {
    default: 'bg-gray-500/10 text-gray-400 border-gray-500/30',
    success: 'bg-green-500/10 text-green-400 border-green-500/30',
    warning: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  };

  return (
    <div className="flex items-center gap-2">
      <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border ${colors[variant]}`}>
        <div className="w-2 h-2 bg-current rounded-full animate-pulse" />
        <span className="text-xs font-medium">Live</span>
      </div>
      {showNetwork && (
        <Wifi className="w-4 h-4 text-gray-400" />
      )}
    </div>
  );
};

export default LiveBadge;

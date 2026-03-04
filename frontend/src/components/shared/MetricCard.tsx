'use client';

import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  icon: LucideIcon;
  iconColor?: string;
  label: string;
  value: string | number;
  subtitle?: string;
  bgColor?: string;
  valueColor?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({
  icon: Icon,
  iconColor = 'text-blue-400',
  label,
  value,
  subtitle,
  bgColor = 'bg-[#0d1b2e]',
  valueColor = 'text-white',
  trend,
  trendValue,
}) => {
  return (
    <div className={`${bgColor} border border-gray-800 rounded-lg p-5 hover:border-gray-700 transition-colors`}>
      <div className="flex items-start justify-between mb-3">
        <div className={`p-2 rounded-lg bg-gray-800/50`}>
          <Icon className={`w-5 h-5 ${iconColor}`} />
        </div>
        {trend && trendValue && (
          <div
            className={`text-xs px-2 py-1 rounded ${
              trend === 'up'
                ? 'bg-green-500/10 text-green-400'
                : trend === 'down'
                ? 'bg-red-500/10 text-red-400'
                : 'bg-gray-500/10 text-gray-400'
            }`}
          >
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendValue}
          </div>
        )}
      </div>

      <div className="text-gray-400 text-sm mb-2">{label}</div>

      <div className={`text-3xl font-bold ${valueColor} mb-1`}>{value}</div>

      {subtitle && <div className="text-gray-500 text-xs">{subtitle}</div>}
    </div>
  );
};

export default MetricCard;


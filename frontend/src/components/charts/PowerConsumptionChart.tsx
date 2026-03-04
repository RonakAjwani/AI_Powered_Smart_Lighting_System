'use client';

import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { usePowerData } from '@/hooks/usePowerData';
import { Activity } from 'lucide-react';

interface PowerDataPoint {
  time: string;
  consumption: number;
  forecast: number;
}

export const PowerConsumptionChart: React.FC = () => {
  const powerData = usePowerData();
  const [chartData, setChartData] = useState<PowerDataPoint[]>([]);

  useEffect(() => {
    // Generate mock historical data with realistic patterns
    // In production, this would come from the backend API
    const now = new Date();
    const data: PowerDataPoint[] = [];

    for (let i = 23; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      const hour = time.getHours();

      // Simulate realistic consumption patterns (higher during day, lower at night)
      const baseConsumption = hour >= 6 && hour <= 22 ? 850 : 450;
      const variation = Math.random() * 200 - 100;
      const consumption = Math.max(300, baseConsumption + variation);

      // Forecast is slightly ahead
      const forecast = consumption + (Math.random() * 100 - 50);

      data.push({
        time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        consumption: Math.round(consumption),
        forecast: Math.round(forecast),
      });
    }

    setChartData(data);
  }, [powerData.lastUpdated]);

  if (powerData.loading && chartData.length === 0) {
    return (
      <div className="bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-700 h-80 flex items-center justify-center">
        <Activity className="w-8 h-8 text-blue-400 animate-pulse" />
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-700">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-100">Power Consumption & Forecast</h3>
        <p className="text-sm text-gray-400">Last 24 hours</p>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="colorConsumption" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#10b981" stopOpacity={0.1}/>
            </linearGradient>
            <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="time"
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            interval="preserveStartEnd"
          />
          <YAxis
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            label={{ value: 'kW', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '0.5rem',
              color: '#f3f4f6'
            }}
          />
          <Legend
            wrapperStyle={{ color: '#9ca3af' }}
          />
          <Area
            type="monotone"
            dataKey="consumption"
            stroke="#10b981"
            fillOpacity={1}
            fill="url(#colorConsumption)"
            strokeWidth={2}
            name="Actual Consumption"
          />
          <Area
            type="monotone"
            dataKey="forecast"
            stroke="#3b82f6"
            fillOpacity={1}
            fill="url(#colorForecast)"
            strokeWidth={2}
            strokeDasharray="5 5"
            name="Forecasted"
          />
        </AreaChart>
      </ResponsiveContainer>

      <div className="mt-4 grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-xs text-gray-400">Current</p>
          <p className="text-lg font-bold text-green-400">
            {chartData[chartData.length - 1]?.consumption || 0} kW
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-400">Peak (24h)</p>
          <p className="text-lg font-bold text-yellow-400">
            {Math.max(...chartData.map(d => d.consumption))} kW
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-400">Average</p>
          <p className="text-lg font-bold text-blue-400">
            {Math.round(chartData.reduce((sum, d) => sum + d.consumption, 0) / chartData.length)} kW
          </p>
        </div>
      </div>
    </div>
  );
};

export default PowerConsumptionChart;

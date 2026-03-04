'use client';

import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useWeatherData } from '@/hooks/useWeatherData';
import { Activity, Thermometer, Droplets } from 'lucide-react';

interface WeatherDataPoint {
  time: string;
  temperature: number;
  humidity: number;
}

export const WeatherTrendsChart: React.FC = () => {
  const weatherData = useWeatherData();
  const [chartData, setChartData] = useState<WeatherDataPoint[]>([]);

  useEffect(() => {
    // Generate realistic weather trend data
    const now = new Date();
    const data: WeatherDataPoint[] = [];

    for (let i = 11; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 2 * 60 * 60 * 1000); // 2-hour intervals
      const hour = time.getHours();

      // Simulate temperature pattern (cooler at night, warmer during day)
      const baseTemp = hour >= 6 && hour <= 18
        ? 25 + (hour - 6) * 0.5  // Warming during day
        : 20 + Math.sin((hour - 18) * Math.PI / 12) * 3; // Cooling at night

      const tempVariation = Math.random() * 4 - 2;
      const temperature = Math.round((baseTemp + tempVariation) * 10) / 10;

      // Humidity inversely related to temperature
      const baseHumidity = 80 - (temperature - 20) * 2;
      const humidityVariation = Math.random() * 10 - 5;
      const humidity = Math.min(100, Math.max(30, Math.round(baseHumidity + humidityVariation)));

      data.push({
        time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        temperature,
        humidity,
      });
    }

    setChartData(data);
  }, [weatherData.lastUpdated]);

  if (weatherData.loading && chartData.length === 0) {
    return (
      <div className="bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-700 h-80 flex items-center justify-center">
        <Activity className="w-8 h-8 text-yellow-400 animate-pulse" />
      </div>
    );
  }

  const currentTemp = chartData[chartData.length - 1]?.temperature || 0;
  const currentHumidity = chartData[chartData.length - 1]?.humidity || 0;

  return (
    <div className="bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-700">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-100">Weather Trends</h3>
        <p className="text-sm text-gray-400">Temperature & Humidity - Last 24 hours</p>
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="time"
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
          />
          <YAxis
            yAxisId="left"
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            label={{ value: '°C', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            label={{ value: '%', angle: 90, position: 'insideRight', fill: '#9ca3af' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '0.5rem',
              color: '#f3f4f6'
            }}
          />
          <Legend wrapperStyle={{ color: '#9ca3af' }} />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="temperature"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={{ fill: '#f59e0b', r: 4 }}
            activeDot={{ r: 6 }}
            name="Temperature (°C)"
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="humidity"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: '#3b82f6', r: 4 }}
            activeDot={{ r: 6 }}
            name="Humidity (%)"
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="mt-4 grid grid-cols-2 gap-4">
        <div className="flex items-center gap-3 p-3 bg-gray-900 rounded-lg">
          <Thermometer className="w-6 h-6 text-orange-400" />
          <div>
            <p className="text-xs text-gray-400">Current Temp</p>
            <p className="text-xl font-bold text-orange-400">{currentTemp}°C</p>
          </div>
        </div>
        <div className="flex items-center gap-3 p-3 bg-gray-900 rounded-lg">
          <Droplets className="w-6 h-6 text-blue-400" />
          <div>
            <p className="text-xs text-gray-400">Current Humidity</p>
            <p className="text-xl font-bold text-blue-400">{currentHumidity}%</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WeatherTrendsChart;

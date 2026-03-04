'use client';

import React, { useEffect, useState } from "react";
import { useWeatherData } from '@/hooks/useWeatherData';
import { Cloud, CloudRain, Sun, Wind } from 'lucide-react';

const LiveClockAndWeather: React.FC = () => {
  const [time, setTime] = useState<string>("");
  const weatherData = useWeatherData();

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  // Extract weather info from current data
  const currentWeather = weatherData.currentData?.zones?.[0];
  const temperature = currentWeather?.temperature || '--';
  const condition = currentWeather?.weather_condition || '---';
  const humidity = currentWeather?.humidity || '--';

  const getWeatherIcon = () => {
    if (!condition || condition === '---') return <Cloud className="w-6 h-6 text-gray-400" />;
    const cond = condition.toLowerCase();
    if (cond.includes('rain')) return <CloudRain className="w-6 h-6 text-blue-400" />;
    if (cond.includes('sun') || cond.includes('clear')) return <Sun className="w-6 h-6 text-yellow-400" />;
    if (cond.includes('wind')) return <Wind className="w-6 h-6 text-gray-300" />;
    return <Cloud className="w-6 h-6 text-gray-400" />;
  };

  return (
    <div className="flex flex-col gap-2 items-center justify-center py-8 bg-gray-800 rounded-xl shadow-md border border-gray-700">
      <div className="text-4xl font-mono font-bold text-blue-400" data-testid="local-time">{time}</div>
      <div className="text-md text-gray-300">Smart Lighting System</div>

      <div className="mt-2 px-4 py-2 bg-gray-700 rounded-lg flex items-center gap-3">
        {getWeatherIcon()}
        <div className="flex flex-col">
          <div className="text-lg text-gray-200 font-semibold">
            {typeof temperature === 'number' ? `${temperature.toFixed(1)}°C` : `${temperature}°C`}
          </div>
          <div className="text-xs text-gray-400">{condition} • Humidity: {humidity}%</div>
        </div>
      </div>

      {weatherData.loading && (
        <div className="text-xs text-gray-500 animate-pulse">Updating...</div>
      )}
    </div>
  );
};

export default LiveClockAndWeather;

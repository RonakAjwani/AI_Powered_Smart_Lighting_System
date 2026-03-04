'use client';
import React, { useState, useEffect } from 'react';
import { getWeatherSystemStatus, getCurrentWeatherData, getWeatherAlerts } from '@/utils/api';

import Card from '@/components/shared/Card';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import { CloudSun, AlertTriangle, Thermometer } from 'lucide-react';
import ZoneControlPanel from './ZoneControlPanel';
import LiveAnalysisPanel from './LiveAnalysisPanel';
import AgentLogPanel from './AgentLogPanel';

const WeatherDashboard: React.FC = () => {
    const [status, setStatus] = useState<any>(null);
    const [currentWeather, setCurrentWeather] = useState<any>(null);
    const [alerts, setAlerts] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const [statusData, weatherData, alertsData] = await Promise.all([
                    getWeatherSystemStatus(),
                    getCurrentWeatherData(),
                    getWeatherAlerts()
                ]);

                if (statusData.error) throw new Error(`Status fetch failed: ${statusData.message}`);
                setStatus(statusData);

                if (weatherData.error) throw new Error(`Weather data fetch failed: ${weatherData.message}`);
                setCurrentWeather(weatherData);

                if (alertsData.error) throw new Error(`Alerts fetch failed: ${alertsData.message}`);
                setAlerts(alertsData.alerts || []); // Assuming alerts are in an 'alerts' array

            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to fetch weather data');
                console.error(err);
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();

        // Optional: Set up polling or WebSocket connection here for real-time updates
        const intervalId = setInterval(fetchData, 60000); // Refresh every 60 seconds
        return () => clearInterval(intervalId); // Cleanup interval on unmount

    }, []);


    if (isLoading) {
        return <LoadingSpinner />;
    }

    return (
        <div className="flex flex-col lg:flex-row gap-8 w-full">
            {/* Left: Main Info & Controls */}
            <div className="flex-1 flex flex-col gap-6">
                <div className="flex items-center gap-3 mb-2">
                    <CloudSun className="text-yellow-400 w-8 h-8" />
                    <h2 className="text-3xl font-bold text-gray-800 dark:text-gray-100 tracking-tight">Weather Agent Dashboard</h2>
                </div>
                {error && <Card title="Error" className="bg-red-100 border-red-400 text-red-700 dark:bg-red-900 dark:border-red-700 dark:text-red-200">{error}</Card>}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card title={<span className="flex items-center gap-2"><Thermometer className="text-blue-400 w-5 h-5" /> System Status</span>}>
                        {status ? <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(status.system_status || status.agent_statuses || status, null, 2)}</pre> : <p>No status data</p>}
                    </Card>
                    <Card title={<span className="flex items-center gap-2"><CloudSun className="text-yellow-400 w-5 h-5" /> Current Conditions</span>}>
                        {currentWeather?.success && currentWeather?.current_conditions ? (
                            <div className="flex flex-col gap-1">
                                <span className="text-2xl font-bold text-blue-400">{currentWeather.current_conditions.temp_c ?? '--'}°C</span>
                                <span className="capitalize text-gray-300">{currentWeather.current_conditions.weather_desc ?? 'Unknown'}</span>
                                <span className="text-xs text-gray-400">Humidity: {currentWeather.current_conditions.humidity ?? '--'}%</span>
                            </div>
                        ) : currentWeather ? (
                            <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(currentWeather, null, 2)}</pre>
                        ) : (
                            <p>No current weather data</p>
                        )}
                    </Card>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card title={<span className="flex items-center gap-2"><AlertTriangle className="text-red-400 w-5 h-5" /> Active Alerts</span>}>
                        {alerts.length > 0 ? (
                            <ul className='space-y-1 text-sm'>
                                {alerts.slice(0, 5).map((alert: any, index: number) => (
                                    <li key={alert.alert_id || index} className={`p-1 rounded font-semibold ${alert.severity === 'critical' || alert.severity === 'high' ? 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-200' : 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200'}`}>
                                        [{alert.severity?.toUpperCase()}] {alert.alert_type} in {alert.zone_id}
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <p className="text-sm text-gray-500 dark:text-gray-400">No active alerts.</p>
                        )}
                    </Card>
                    <ZoneControlPanel />
                </div>
            </div>
            {/* Right: Live Analysis & Logs */}
            <div className="w-full lg:w-[350px] flex flex-col gap-6">
                <LiveAnalysisPanel />
                <AgentLogPanel />
            </div>
        </div>
    );
};

export default WeatherDashboard;
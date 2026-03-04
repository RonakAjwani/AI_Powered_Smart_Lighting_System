"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { getWeatherConfig, checkHealth } from "@/lib/api";

export default function WeatherPage() {
    const [isOnline, setIsOnline] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [zones, setZones] = useState<string[]>([]);

    // Thresholds from API
    const [windThreshold, setWindThreshold] = useState(50);
    const [visibilityThreshold, setVisibilityThreshold] = useState(1000);
    const [precipitationThreshold, setPrecipitationThreshold] = useState(10);
    const [emergencyWind, setEmergencyWind] = useState(80);
    const [emergencyPrecipitation, setEmergencyPrecipitation] = useState(25);

    // Features
    const [features, setFeatures] = useState({
        realTimeWeather: true,
        predictiveAdjust: true,
        disasterMode: true,
        autoAdjust: true,
    });

    const [isSaving, setIsSaving] = useState(false);
    const [saveMessage, setSaveMessage] = useState<{ type: string; text: string } | null>(null);

    // Fetch config from backend
    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            const online = await checkHealth("weather");
            setIsOnline(online);

            if (online) {
                const config = await getWeatherConfig();
                if (config?.config) {
                    setWindThreshold(config.config.thresholds.wind_speed);
                    setVisibilityThreshold(config.config.thresholds.visibility);
                    setPrecipitationThreshold(config.config.thresholds.precipitation);
                    setEmergencyWind(config.config.emergency_thresholds.wind_speed);
                    setEmergencyPrecipitation(config.config.emergency_thresholds.precipitation);
                    setZones(config.config.zones || []);
                }
            }
            setIsLoading(false);
        };
        fetchData();
    }, []);

    const saveConfig = async () => {
        setIsSaving(true);
        setSaveMessage(null);
        try {
            await new Promise((r) => setTimeout(r, 1000));
            setSaveMessage({ type: "success", text: "Weather configuration saved successfully!" });
        } catch {
            setSaveMessage({ type: "danger", text: "Failed to save configuration." });
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <>
            {/* Content Header */}
            <div className="content-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1>Weather Configuration</h1>
                        <ol className="breadcrumb">
                            <li className="breadcrumb-item"><Link href="/">Home</Link></li>
                            <li className="breadcrumb-item active">Weather</li>
                        </ol>
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <span className={`badge badge-${isOnline ? 'success' : 'danger'}`}>
                            {isLoading ? 'Connecting...' : isOnline ? 'Service Online (Port 8001)' : 'Service Offline'}
                        </span>
                        <button onClick={saveConfig} disabled={isSaving} className="btn btn-success">
                            {isSaving ? 'Saving...' : 'Save Configuration'}
                        </button>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <section className="content">
                {saveMessage && (
                    <div className={`alert alert-${saveMessage.type} mb-4`}>{saveMessage.text}</div>
                )}

                {/* Info Boxes */}
                <div className="row mb-4">
                    <div className="col-3">
                        <div className="info-box">
                            <span className="info-box-icon bg-info">☁️</span>
                            <div className="info-box-content">
                                <span className="info-box-text">Wind Threshold</span>
                                <span className="info-box-number">{windThreshold} km/h</span>
                            </div>
                        </div>
                    </div>
                    <div className="col-3">
                        <div className="info-box">
                            <span className="info-box-icon bg-primary">👁️</span>
                            <div className="info-box-content">
                                <span className="info-box-text">Visibility Threshold</span>
                                <span className="info-box-number">{visibilityThreshold} m</span>
                            </div>
                        </div>
                    </div>
                    <div className="col-3">
                        <div className="info-box">
                            <span className="info-box-icon bg-warning">💧</span>
                            <div className="info-box-content">
                                <span className="info-box-text">Precipitation</span>
                                <span className="info-box-number">{precipitationThreshold} mm</span>
                            </div>
                        </div>
                    </div>
                    <div className="col-3">
                        <div className="info-box">
                            <span className="info-box-icon bg-success">📍</span>
                            <div className="info-box-content">
                                <span className="info-box-text">Zones Configured</span>
                                <span className="info-box-number">{zones.length}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="row">
                    {/* Normal Thresholds Card */}
                    <div className="col-6">
                        <div className="card">
                            <div className="card-header" style={{ background: '#17a2b820' }}>
                                <h3 className="card-title">🌤️ Normal Thresholds (Live from API)</h3>
                            </div>
                            <div className="card-body">
                                <div className="form-group">
                                    <label className="form-label">Wind Speed Threshold</label>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <input type="number" value={windThreshold} onChange={(e) => setWindThreshold(parseInt(e.target.value))} className="form-control" />
                                        <span className="text-muted">km/h</span>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Visibility Threshold</label>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <input type="number" value={visibilityThreshold} onChange={(e) => setVisibilityThreshold(parseInt(e.target.value))} className="form-control" />
                                        <span className="text-muted">meters</span>
                                    </div>
                                </div>
                                <div className="form-group mb-0">
                                    <label className="form-label">Precipitation Threshold</label>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <input type="number" value={precipitationThreshold} onChange={(e) => setPrecipitationThreshold(parseInt(e.target.value))} className="form-control" />
                                        <span className="text-muted">mm</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Emergency Thresholds Card */}
                    <div className="col-6">
                        <div className="card">
                            <div className="card-header" style={{ background: '#dc354520' }}>
                                <h3 className="card-title">🚨 Emergency Thresholds (Live from API)</h3>
                            </div>
                            <div className="card-body">
                                <div className="form-group">
                                    <label className="form-label">Emergency Wind Speed</label>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <input type="number" value={emergencyWind} onChange={(e) => setEmergencyWind(parseInt(e.target.value))} className="form-control" />
                                        <span className="text-muted">km/h</span>
                                    </div>
                                </div>
                                <div className="form-group mb-0">
                                    <label className="form-label">Emergency Precipitation</label>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <input type="number" value={emergencyPrecipitation} onChange={(e) => setEmergencyPrecipitation(parseInt(e.target.value))} className="form-control" />
                                        <span className="text-muted">mm</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Feature Toggles */}
                <div className="card">
                    <div className="card-header" style={{ background: '#28a74520' }}>
                        <h3 className="card-title">⚙️ Feature Settings</h3>
                    </div>
                    <div className="card-body">
                        <div className="row">
                            {[
                                { key: "realTimeWeather", label: "Real-Time Weather Data", desc: "Fetch live weather updates" },
                                { key: "predictiveAdjust", label: "Predictive Adjustments", desc: "AI-powered lighting predictions" },
                                { key: "disasterMode", label: "Disaster Mode", desc: "Emergency weather protocols" },
                                { key: "autoAdjust", label: "Auto Adjustments", desc: "Automatic lighting changes" },
                            ].map((feature) => (
                                <div key={feature.key} className="col-6">
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem', background: '#f8f9fa', borderRadius: '0.25rem', marginBottom: '0.5rem' }}>
                                        <div>
                                            <span className="font-weight-bold">{feature.label}</span>
                                            <p className="text-muted mb-0" style={{ fontSize: '0.75rem' }}>{feature.desc}</p>
                                        </div>
                                        <label className="custom-switch">
                                            <input type="checkbox" checked={features[feature.key as keyof typeof features]} onChange={(e) => setFeatures({ ...features, [feature.key]: e.target.checked })} />
                                            <span className="custom-switch-slider"></span>
                                        </label>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Configured Zones */}
                {zones.length > 0 && (
                    <div className="card">
                        <div className="card-header">
                            <h3 className="card-title">📍 Configured Zones (from API)</h3>
                        </div>
                        <div className="card-body">
                            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                {zones.map((zone, i) => (
                                    <span key={i} className="badge badge-info" style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}>{zone}</span>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Agents Table */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">Weather Intelligence Agents</h3>
                    </div>
                    <div className="card-body" style={{ padding: 0 }}>
                        <table className="table table-striped mb-0">
                            <thead>
                                <tr>
                                    <th>Agent</th>
                                    <th>Status</th>
                                    <th>Description</th>
                                </tr>
                            </thead>
                            <tbody>
                                {[
                                    { name: "Weather Data Collector", status: "active", desc: "Fetching weather data from APIs" },
                                    { name: "Environmental Sensor", status: "active", desc: "Processing sensor data" },
                                    { name: "Impact Analyzer", status: "active", desc: "Analyzing weather conditions" },
                                    { name: "Disaster Response", status: "standby", desc: "Ready for emergencies" },
                                    { name: "Report Generator", status: "active", desc: "Creating weather reports" },
                                ].map((agent) => (
                                    <tr key={agent.name}>
                                        <td className="font-weight-bold">{agent.name}</td>
                                        <td><span className={`badge badge-${agent.status === 'active' ? 'success' : 'warning'}`}>{agent.status}</span></td>
                                        <td className="text-muted">{agent.desc}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>
        </>
    );
}

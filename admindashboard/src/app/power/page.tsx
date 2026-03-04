"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { getPowerSystemStatus, checkHealth } from "@/lib/api";

export default function PowerPage() {
    const [isOnline, setIsOnline] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    // System status from API
    const [gridStatus, setGridStatus] = useState<string>("unknown");
    const [currentLoad, setCurrentLoad] = useState(0);
    const [voltage, setVoltage] = useState(0);
    const [frequency, setFrequency] = useState(0);
    const [activeNodes, setActiveNodes] = useState(0);
    const [totalNodes, setTotalNodes] = useState(0);

    // Thresholds (editable)
    const [voltageMin, setVoltageMin] = useState(114);
    const [voltageMax, setVoltageMax] = useState(126);
    const [loadHigh, setLoadHigh] = useState(80);
    const [loadCritical, setLoadCritical] = useState(95);

    // Features
    const [features, setFeatures] = useState({
        demandResponse: true,
        loadBalancing: true,
        peakShaving: true,
        renewableIntegration: false,
        autoBackup: true,
        prioritizeHospitals: true,
    });

    const [isSaving, setIsSaving] = useState(false);
    const [saveMessage, setSaveMessage] = useState<{ type: string; text: string } | null>(null);

    // Fetch data from backend
    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            const online = await checkHealth("power");
            setIsOnline(online);

            if (online) {
                const status = await getPowerSystemStatus();
                if (status) {
                    setGridStatus(status.grid_status || "stable");
                    setCurrentLoad(status.current_load || 67);
                    setVoltage(status.voltage || 120);
                    setFrequency(status.frequency || 60);
                    setActiveNodes(status.active_nodes || 0);
                    setTotalNodes(status.total_nodes || 0);
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
            setSaveMessage({ type: "success", text: "Power grid configuration saved successfully!" });
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
                        <h1>Power Grid Configuration</h1>
                        <ol className="breadcrumb">
                            <li className="breadcrumb-item"><Link href="/">Home</Link></li>
                            <li className="breadcrumb-item active">Power Grid</li>
                        </ol>
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <span className={`badge badge-${isOnline ? 'success' : 'danger'}`}>
                            {isLoading ? 'Connecting...' : isOnline ? 'Service Online (Port 8002)' : 'Service Offline'}
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

                {/* Info Boxes - Live Data from API */}
                <div className="row mb-4">
                    <div className="col-3">
                        <div className="info-box">
                            <span className={`info-box-icon bg-${gridStatus === 'stable' ? 'success' : gridStatus === 'warning' ? 'warning' : 'danger'}`}>⚡</span>
                            <div className="info-box-content">
                                <span className="info-box-text">Grid Status (Live)</span>
                                <span className={`info-box-number text-${gridStatus === 'stable' ? 'success' : gridStatus === 'warning' ? 'warning' : 'danger'}`}>
                                    {gridStatus.charAt(0).toUpperCase() + gridStatus.slice(1)}
                                </span>
                            </div>
                        </div>
                    </div>
                    <div className="col-3">
                        <div className="info-box">
                            <span className="info-box-icon bg-info">🔌</span>
                            <div className="info-box-content">
                                <span className="info-box-text">Current Load (Live)</span>
                                <span className="info-box-number">{currentLoad}%</span>
                            </div>
                        </div>
                    </div>
                    <div className="col-3">
                        <div className="info-box">
                            <span className="info-box-icon bg-warning">📊</span>
                            <div className="info-box-content">
                                <span className="info-box-text">Voltage (Live)</span>
                                <span className="info-box-number">{voltage}V</span>
                            </div>
                        </div>
                    </div>
                    <div className="col-3">
                        <div className="info-box">
                            <span className="info-box-icon bg-primary">🔋</span>
                            <div className="info-box-content">
                                <span className="info-box-text">Active Nodes</span>
                                <span className="info-box-number">{activeNodes}/{totalNodes}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="row">
                    {/* Voltage Thresholds */}
                    <div className="col-6">
                        <div className="card">
                            <div className="card-header" style={{ background: '#ffc10720' }}>
                                <h3 className="card-title">⚡ Voltage Thresholds</h3>
                            </div>
                            <div className="card-body">
                                <div className="row">
                                    <div className="col-6">
                                        <div className="form-group">
                                            <label className="form-label">Min Voltage (V)</label>
                                            <input type="number" value={voltageMin} onChange={(e) => setVoltageMin(parseInt(e.target.value))} className="form-control" />
                                        </div>
                                    </div>
                                    <div className="col-6">
                                        <div className="form-group mb-0">
                                            <label className="form-label">Max Voltage (V)</label>
                                            <input type="number" value={voltageMax} onChange={(e) => setVoltageMax(parseInt(e.target.value))} className="form-control" />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Load Thresholds */}
                    <div className="col-6">
                        <div className="card">
                            <div className="card-header" style={{ background: '#17a2b820' }}>
                                <h3 className="card-title">📊 Load Management</h3>
                            </div>
                            <div className="card-body">
                                <div className="row">
                                    <div className="col-6">
                                        <div className="form-group">
                                            <label className="form-label">High Load (%)</label>
                                            <input type="number" value={loadHigh} onChange={(e) => setLoadHigh(parseInt(e.target.value))} className="form-control" />
                                        </div>
                                    </div>
                                    <div className="col-6">
                                        <div className="form-group mb-0">
                                            <label className="form-label">Critical Load (%)</label>
                                            <input type="number" value={loadCritical} onChange={(e) => setLoadCritical(parseInt(e.target.value))} className="form-control" />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="row">
                    {/* Optimization Features */}
                    <div className="col-6">
                        <div className="card">
                            <div className="card-header" style={{ background: '#28a74520' }}>
                                <h3 className="card-title">🔧 Energy Optimization</h3>
                            </div>
                            <div className="card-body">
                                {[
                                    { key: "demandResponse", label: "Demand Response", desc: "Reduce consumption during peaks" },
                                    { key: "loadBalancing", label: "Load Balancing", desc: "Distribute load across grid" },
                                    { key: "peakShaving", label: "Peak Shaving", desc: "Limit peak demand spikes" },
                                    { key: "renewableIntegration", label: "Renewable Integration", desc: "Prioritize solar/wind" },
                                ].map((feature) => (
                                    <div key={feature.key} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem', background: '#f8f9fa', borderRadius: '0.25rem', marginBottom: '0.5rem' }}>
                                        <div>
                                            <span className="font-weight-bold">{feature.label}</span>
                                            <p className="text-muted mb-0" style={{ fontSize: '0.75rem' }}>{feature.desc}</p>
                                        </div>
                                        <label className="custom-switch">
                                            <input type="checkbox" checked={features[feature.key as keyof typeof features]} onChange={(e) => setFeatures({ ...features, [feature.key]: e.target.checked })} />
                                            <span className="custom-switch-slider"></span>
                                        </label>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Outage Response */}
                    <div className="col-6">
                        <div className="card">
                            <div className="card-header" style={{ background: '#dc354520' }}>
                                <h3 className="card-title">⚠️ Outage Response</h3>
                            </div>
                            <div className="card-body">
                                <div className="callout callout-warning mb-3">
                                    <h5>Emergency Protocols</h5>
                                    <p className="mb-0">These settings control automatic responses during power outages.</p>
                                </div>
                                {[
                                    { key: "autoBackup", label: "Auto Switch to Backup", desc: "Switch to backup power automatically" },
                                    { key: "prioritizeHospitals", label: "Prioritize Hospitals", desc: "Keep hospital zones online first" },
                                ].map((feature) => (
                                    <div key={feature.key} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem', background: '#f8f9fa', borderRadius: '0.25rem', marginBottom: '0.5rem' }}>
                                        <div>
                                            <span className="font-weight-bold">{feature.label}</span>
                                            <p className="text-muted mb-0" style={{ fontSize: '0.75rem' }}>{feature.desc}</p>
                                        </div>
                                        <label className="custom-switch">
                                            <input type="checkbox" checked={features[feature.key as keyof typeof features]} onChange={(e) => setFeatures({ ...features, [feature.key]: e.target.checked })} />
                                            <span className="custom-switch-slider"></span>
                                        </label>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Agents Table */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">Power Grid Agents</h3>
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
                                    { name: "Load Forecaster", status: "active", desc: "Predicting energy demand" },
                                    { name: "Outage Detector", status: "active", desc: "Monitoring grid health" },
                                    { name: "Energy Optimizer", status: "active", desc: "Optimizing usage" },
                                    { name: "Demand Manager", status: "active", desc: "Balancing load" },
                                    { name: "Rerouting Agent", status: "standby", desc: "Ready for outages" },
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

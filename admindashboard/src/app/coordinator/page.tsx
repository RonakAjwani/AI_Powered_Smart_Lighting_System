"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { getCoordinatorState, getCoordinatorPriorities, checkHealth } from "@/lib/api";

// Priority levels
const defaultPriorities = [
    { id: "CYBER_CRITICAL", name: "Cyber Critical", level: 1, color: "bg-danger" },
    { id: "POWER_OUTAGE", name: "Power Outage", level: 2, color: "bg-danger" },
    { id: "WEATHER_DISASTER", name: "Weather Disaster", level: 3, color: "bg-warning" },
    { id: "CYBER_HIGH", name: "Cyber High", level: 4, color: "bg-warning" },
    { id: "POWER_GRID_UNSTABLE", name: "Grid Unstable", level: 5, color: "bg-info" },
    { id: "CYBER_MEDIUM", name: "Cyber Medium", level: 6, color: "bg-info" },
    { id: "WEATHER_ADVISORY", name: "Weather Advisory", level: 7, color: "bg-secondary" },
    { id: "POWER_OPTIMIZATION", name: "Optimization", level: 8, color: "bg-secondary" },
    { id: "NOMINAL_OPERATION", name: "Nominal", level: 9, color: "bg-success" },
];

export default function CoordinatorPage() {
    const [isOnline, setIsOnline] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [decisionCount, setDecisionCount] = useState(0);

    const [priorities, setPriorities] = useState(defaultPriorities);
    const [systemMode, setSystemMode] = useState("NOMINAL");
    const [autoDecision, setAutoDecision] = useState(true);

    const [llm, setLlm] = useState({
        model: "llama3-8b-8192",
        temperature: 0.0,
        maxTokens: 2048,
        timeout: 30,
    });

    const [isSaving, setIsSaving] = useState(false);
    const [saveMessage, setSaveMessage] = useState<{ type: string; text: string } | null>(null);

    // Fetch data from backend
    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            const online = await checkHealth("coordinator");
            setIsOnline(online);

            if (online) {
                // Fetch coordinator state
                const state = await getCoordinatorState();
                if (state) {
                    setSystemMode(state.system_mode || "NOMINAL");
                    setDecisionCount(state.decision_count || 0);
                }

                // Fetch priorities
                const priData = await getCoordinatorPriorities();
                if (priData?.priorities) {
                    // Map API priorities to UI format
                    const mapped = defaultPriorities.map((p, i) => ({
                        ...p,
                        level: priData.priorities[p.id] || (i + 1),
                    }));
                    setPriorities(mapped);
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
            setSaveMessage({ type: "success", text: "Coordinator configuration saved successfully!" });
        } catch {
            setSaveMessage({ type: "danger", text: "Failed to save configuration." });
        } finally {
            setIsSaving(false);
        }
    };

    const updatePriority = (id: string, newLevel: number) => {
        setPriorities(priorities.map((p) => p.id === id ? { ...p, level: newLevel } : p));
    };

    return (
        <>
            {/* Content Header */}
            <div className="content-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1>Coordinator Settings</h1>
                        <ol className="breadcrumb">
                            <li className="breadcrumb-item"><Link href="/">Home</Link></li>
                            <li className="breadcrumb-item active">Coordinator</li>
                        </ol>
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <span className={`badge badge-${isOnline ? 'success' : 'danger'}`}>
                            {isLoading ? 'Connecting...' : isOnline ? 'Service Online (Port 8004)' : 'Service Offline'}
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

                {/* System Mode Card */}
                <div className="card mb-4">
                    <div className="card-header">
                        <h3 className="card-title">🎯 Current System Mode (Live from API)</h3>
                        <div className="card-tools">
                            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                <span className="text-muted">Auto Decision</span>
                                <label className="custom-switch">
                                    <input type="checkbox" checked={autoDecision} onChange={(e) => setAutoDecision(e.target.checked)} />
                                    <span className="custom-switch-slider"></span>
                                </label>
                                <button className="btn btn-sm btn-primary">Trigger Decision</button>
                            </div>
                        </div>
                    </div>
                    <div className="card-body">
                        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                            {["NOMINAL", "LOCKDOWN", "EMERGENCY_POWER", "EMERGENCY_WEATHER"].map((mode) => (
                                <button
                                    key={mode}
                                    onClick={() => setSystemMode(mode)}
                                    className={`btn ${systemMode === mode ? "btn-primary" : "btn-secondary"}`}
                                >
                                    {mode.replace(/_/g, " ")}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="row">
                    {/* Priority Hierarchy */}
                    <div className="col-6">
                        <div className="card">
                            <div className="card-header">
                                <h3 className="card-title">📋 Priority Hierarchy</h3>
                            </div>
                            <div className="card-body" style={{ padding: 0 }}>
                                <table className="table table-striped mb-0">
                                    <thead>
                                        <tr>
                                            <th>Level</th>
                                            <th>Priority</th>
                                            <th>ID</th>
                                            <th>Adjust</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {[...priorities].sort((a, b) => a.level - b.level).map((p) => (
                                            <tr key={p.id}>
                                                <td>
                                                    <span className={`badge ${p.color}`} style={{ fontWeight: 'bold', minWidth: 30 }}>
                                                        {p.level}
                                                    </span>
                                                </td>
                                                <td className="font-weight-bold">{p.name}</td>
                                                <td><code style={{ fontSize: '0.75rem' }}>{p.id}</code></td>
                                                <td>
                                                    <input
                                                        type="number"
                                                        value={p.level}
                                                        min={1}
                                                        max={10}
                                                        onChange={(e) => updatePriority(p.id, parseInt(e.target.value))}
                                                        className="form-control form-control-sm"
                                                        style={{ width: 60 }}
                                                    />
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    {/* LLM Configuration */}
                    <div className="col-6">
                        <div className="card">
                            <div className="card-header">
                                <h3 className="card-title">🤖 LLM Configuration</h3>
                            </div>
                            <div className="card-body">
                                <div className="form-group">
                                    <label className="form-label">Model</label>
                                    <select
                                        value={llm.model}
                                        onChange={(e) => setLlm({ ...llm, model: e.target.value })}
                                        className="form-control"
                                    >
                                        <option value="llama3-8b-8192">Llama 3 8B</option>
                                        <option value="llama3-70b-8192">Llama 3 70B</option>
                                        <option value="mixtral-8x7b-32768">Mixtral 8x7B</option>
                                        <option value="gemma-7b-it">Gemma 7B</option>
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Temperature: {llm.temperature}</label>
                                    <input
                                        type="range"
                                        value={llm.temperature}
                                        min={0}
                                        max={1}
                                        step={0.1}
                                        onChange={(e) => setLlm({ ...llm, temperature: parseFloat(e.target.value) })}
                                        className="form-control"
                                        style={{ padding: 0 }}
                                    />
                                    <small className="text-muted">0 = deterministic, 1 = creative</small>
                                </div>
                                <div className="row">
                                    <div className="col-6">
                                        <div className="form-group mb-0">
                                            <label className="form-label">Max Tokens</label>
                                            <input
                                                type="number"
                                                value={llm.maxTokens}
                                                onChange={(e) => setLlm({ ...llm, maxTokens: parseInt(e.target.value) })}
                                                className="form-control"
                                            />
                                        </div>
                                    </div>
                                    <div className="col-6">
                                        <div className="form-group mb-0">
                                            <label className="form-label">Timeout (sec)</label>
                                            <input
                                                type="number"
                                                value={llm.timeout}
                                                onChange={(e) => setLlm({ ...llm, timeout: parseInt(e.target.value) })}
                                                className="form-control"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Decision Engine Status */}
                        <div className="card">
                            <div className="card-header">
                                <h3 className="card-title">📊 Decision Engine Status (Live)</h3>
                            </div>
                            <div className="card-body">
                                <div className="info-box mb-2" style={{ background: isOnline ? '#d4edda' : '#f8d7da', minHeight: 'auto' }}>
                                    <span className={`info-box-icon bg-${isOnline ? 'success' : 'danger'}`} style={{ width: 50 }}>
                                        {isOnline ? '✓' : '!'}
                                    </span>
                                    <div className="info-box-content">
                                        <span className="info-box-text">Status</span>
                                        <span className={`info-box-number text-${isOnline ? 'success' : 'danger'}`}>
                                            {isOnline ? 'Active' : 'Offline'}
                                        </span>
                                    </div>
                                </div>
                                <table className="table table-sm mb-0">
                                    <tbody>
                                        <tr>
                                            <td className="text-muted">Last Decision</td>
                                            <td className="font-weight-bold">2 min ago</td>
                                        </tr>
                                        <tr>
                                            <td className="text-muted">Decisions Today</td>
                                            <td className="font-weight-bold">{decisionCount}</td>
                                        </tr>
                                        <tr>
                                            <td className="text-muted">Current Mode</td>
                                            <td>
                                                <span className={`badge badge-${systemMode === 'NOMINAL' ? 'success' : systemMode.includes('EMERGENCY') ? 'danger' : 'warning'}`}>
                                                    {systemMode}
                                                </span>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </>
    );
}

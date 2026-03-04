"use client";

import React, { useState } from "react";
import Link from "next/link";

// Agent type
interface Agent {
    id: string;
    name: string;
    service: "cybersecurity" | "weather" | "power" | "coordinator";
    status: "active" | "standby" | "disabled";
    description: string;
    lastRun: string;
    successRate: number;
}

// All agents
const allAgents: Agent[] = [
    { id: "ddos_detection", name: "DDoS Detection Agent", service: "cybersecurity", status: "active", description: "Detects DDoS attacks", lastRun: "2 min ago", successRate: 98.5 },
    { id: "malware_detection", name: "Malware Detection Agent", service: "cybersecurity", status: "active", description: "Identifies malware patterns", lastRun: "5 min ago", successRate: 97.2 },
    { id: "weather_collector", name: "Weather Data Collector", service: "weather", status: "active", description: "Collects weather data", lastRun: "1 min ago", successRate: 99.1 },
    { id: "impact_analyzer", name: "Weather Impact Analyzer", service: "weather", status: "active", description: "Analyzes weather impact", lastRun: "3 min ago", successRate: 96.8 },
    { id: "disaster_response", name: "Disaster Response Agent", service: "weather", status: "standby", description: "Emergency protocols", lastRun: "24h ago", successRate: 100 },
    { id: "lighting_advisor", name: "Lighting Advisor Agent", service: "weather", status: "active", description: "Lighting recommendations", lastRun: "2 min ago", successRate: 95.4 },
    { id: "weather_reporter", name: "Weather Report Generator", service: "weather", status: "active", description: "Generates reports", lastRun: "10 min ago", successRate: 99.8 },
    { id: "load_forecaster", name: "Energy Load Forecaster", service: "power", status: "active", description: "Predicts consumption", lastRun: "5 min ago", successRate: 94.2 },
    { id: "outage_detector", name: "Outage Detection Agent", service: "power", status: "active", description: "Monitors grid", lastRun: "30 sec ago", successRate: 99.5 },
    { id: "energy_optimizer", name: "Energy Optimization Agent", service: "power", status: "active", description: "Optimizes usage", lastRun: "1 min ago", successRate: 93.7 },
    { id: "demand_response", name: "Demand Response Agent", service: "power", status: "active", description: "Load balancing", lastRun: "3 min ago", successRate: 96.1 },
    { id: "rerouting_agent", name: "Power Rerouting Agent", service: "power", status: "standby", description: "Handles outages", lastRun: "48h ago", successRate: 100 },
    { id: "priority_manager", name: "Priority Manager", service: "coordinator", status: "active", description: "Determines priorities", lastRun: "10 sec ago", successRate: 99.9 },
    { id: "decision_engine", name: "Decision Engine", service: "coordinator", status: "active", description: "Makes decisions", lastRun: "10 sec ago", successRate: 98.2 },
];

const serviceBadge: Record<string, string> = {
    cybersecurity: "badge-danger",
    weather: "badge-info",
    power: "badge-warning",
    coordinator: "badge-secondary",
};

export default function AgentsPage() {
    const [agents] = useState(allAgents);
    const [filter, setFilter] = useState("all");
    const [statusFilter, setStatusFilter] = useState("all");

    const filtered = agents.filter((a) => {
        if (filter !== "all" && a.service !== filter) return false;
        if (statusFilter !== "all" && a.status !== statusFilter) return false;
        return true;
    });

    const counts = {
        total: agents.length,
        active: agents.filter((a) => a.status === "active").length,
        cybersecurity: agents.filter((a) => a.service === "cybersecurity").length,
        weather: agents.filter((a) => a.service === "weather").length,
        power: agents.filter((a) => a.service === "power").length,
        coordinator: agents.filter((a) => a.service === "coordinator").length,
    };

    return (
        <>
            {/* Content Header */}
            <div className="content-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1>AI Agents Overview</h1>
                        <ol className="breadcrumb">
                            <li className="breadcrumb-item"><Link href="/">Home</Link></li>
                            <li className="breadcrumb-item active">All Agents</li>
                        </ol>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <section className="content">
                {/* Stats Row */}
                <div className="row mb-4">
                    <div className="col-3">
                        <div className="small-box bg-info">
                            <div className="inner">
                                <h3>{counts.total}</h3>
                                <p>Total Agents</p>
                            </div>
                            <div className="icon">🤖</div>
                        </div>
                    </div>
                    <div className="col-3">
                        <div className="small-box bg-success">
                            <div className="inner">
                                <h3>{counts.active}</h3>
                                <p>Active</p>
                            </div>
                            <div className="icon">✓</div>
                        </div>
                    </div>
                    <div className="col-3">
                        <div className="small-box bg-warning">
                            <div className="inner">
                                <h3>{agents.filter((a) => a.status === "standby").length}</h3>
                                <p>Standby</p>
                            </div>
                            <div className="icon">⏸</div>
                        </div>
                    </div>
                    <div className="col-3">
                        <div className="small-box bg-danger">
                            <div className="inner">
                                <h3>{agents.filter((a) => a.status === "disabled").length}</h3>
                                <p>Disabled</p>
                            </div>
                            <div className="icon">✕</div>
                        </div>
                    </div>
                </div>

                {/* Filters */}
                <div className="card mb-4">
                    <div className="card-body" style={{ padding: '0.75rem 1.25rem' }}>
                        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
                            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                <span className="text-muted">Service:</span>
                                {["all", "cybersecurity", "weather", "power", "coordinator"].map((f) => (
                                    <button key={f} onClick={() => setFilter(f)} className={`btn btn-sm ${filter === f ? "btn-primary" : "btn-secondary"}`}>
                                        {f === "all" ? "All" : f.charAt(0).toUpperCase() + f.slice(1)}
                                    </button>
                                ))}
                            </div>
                            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                <span className="text-muted">Status:</span>
                                {["all", "active", "standby", "disabled"].map((s) => (
                                    <button key={s} onClick={() => setStatusFilter(s)} className={`btn btn-sm ${statusFilter === s ? "btn-primary" : "btn-secondary"}`}>
                                        {s === "all" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Agents Table */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">All System Agents ({filtered.length})</h3>
                    </div>
                    <div className="card-body" style={{ padding: 0 }}>
                        <table className="table table-striped table-hover mb-0">
                            <thead>
                                <tr>
                                    <th>Agent Name</th>
                                    <th>Service</th>
                                    <th>Status</th>
                                    <th>Description</th>
                                    <th>Last Run</th>
                                    <th>Success Rate</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filtered.map((agent) => (
                                    <tr key={agent.id}>
                                        <td>
                                            <span className="font-weight-bold">{agent.name}</span>
                                            <br />
                                            <code style={{ fontSize: '0.7rem' }}>{agent.id}</code>
                                        </td>
                                        <td><span className={`badge ${serviceBadge[agent.service]}`}>{agent.service}</span></td>
                                        <td><span className={`badge badge-${agent.status === 'active' ? 'success' : agent.status === 'standby' ? 'warning' : 'danger'}`}>{agent.status}</span></td>
                                        <td className="text-muted">{agent.description}</td>
                                        <td>{agent.lastRun}</td>
                                        <td>
                                            <div className="progress" style={{ height: 6, width: 80 }}>
                                                <div className="progress-bar" style={{ width: `${agent.successRate}%`, background: agent.successRate >= 95 ? 'var(--success)' : agent.successRate >= 90 ? 'var(--warning)' : 'var(--danger)' }}></div>
                                            </div>
                                            <small>{agent.successRate}%</small>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Coming Soon */}
                <div className="callout callout-info">
                    <h5>🚀 Coming Soon: Custom Agent Creation</h5>
                    <p className="mb-0">In Phase 2, you'll be able to create custom AI agents from templates without writing code. Stay tuned!</p>
                </div>
            </section>
        </>
    );
}

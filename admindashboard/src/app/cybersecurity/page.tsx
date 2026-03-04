"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import {
    getCyberDDoSConfig, getCyberMalwareConfig, getCyberAgentStatus,
    getSimulatorStatus, getSimulatorZones, getMetricsTimeline, getMetricsSummary,
    putDDoSConfig, putMalwareConfig, resetConfig,
    startSimulator, stopSimulator, triggerAttack,
    checkHealth, WS_BASE,
    type DDoSConfig, type MalwareConfig, type CyberAgentStatus,
    type SimulatorStatus, type ZoneInfo, type TimelineBucket, type MetricsSummary,
} from "@/lib/api";

// Recharts — direct import (works in client components)
import {
    AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, Legend, ResponsiveContainer,
} from "recharts";

// ═══════════════════════════════════════════════════════════════════════════
// Styles (inline module — scoped to this page)
// ═══════════════════════════════════════════════════════════════════════════
const S = {
    tabs: {
        display: "flex", gap: "0", borderBottom: "2px solid #dee2e6",
        marginBottom: "1rem", background: "#fff", borderRadius: "4px 4px 0 0",
    } as React.CSSProperties,
    tab: (active: boolean): React.CSSProperties => ({
        padding: "0.75rem 1.25rem", cursor: "pointer", fontWeight: active ? 700 : 500,
        borderBottom: active ? "3px solid #007bff" : "3px solid transparent",
        color: active ? "#007bff" : "#6c757d", background: "transparent",
        border: "none", fontSize: "0.9rem", transition: "all 0.2s",
        display: "flex", alignItems: "center", gap: "0.4rem",
    }),
    logBox: {
        background: "#1e1e2e", color: "#cdd6f4", fontFamily: "'Fira Code', monospace",
        fontSize: "0.78rem", lineHeight: "1.6", padding: "0.75rem",
        height: "500px", overflowY: "auto", borderRadius: "6px",
    } as React.CSSProperties,
    logLine: (severity: string): React.CSSProperties => ({
        padding: "2px 0", borderLeft: `3px solid ${severity === "critical" ? "#f38ba8" : severity === "high" ? "#fab387"
            : severity === "medium" ? "#f9e2af" : "#a6e3a1"
            }`, paddingLeft: "8px", marginBottom: "2px",
    }),
    statCard: (color: string): React.CSSProperties => ({
        background: `linear-gradient(135deg, ${color}22, ${color}08)`,
        border: `1px solid ${color}33`, borderRadius: "8px",
        padding: "1rem", textAlign: "center" as const,
    }),
    pulseGreen: {
        display: "inline-block", width: "8px", height: "8px", borderRadius: "50%",
        background: "#28a745", boxShadow: "0 0 8px #28a745", marginRight: "6px",
    } as React.CSSProperties,
    pulseRed: {
        display: "inline-block", width: "8px", height: "8px", borderRadius: "50%",
        background: "#dc3545", boxShadow: "0 0 8px #dc3545", marginRight: "6px",
    } as React.CSSProperties,
};

const SEVERITY_COLORS = { critical: "#f38ba8", high: "#fab387", medium: "#f9e2af", low: "#a6e3a1" };
const PIE_COLORS = ["#f38ba8", "#fab387", "#f9e2af", "#a6e3a1", "#89b4fa", "#cba6f7", "#f5c2e7"];

type Tab = "overview" | "ddos" | "malware" | "logs" | "map";

// ═══════════════════════════════════════════════════════════════════════════
// Main Page Component
// ═══════════════════════════════════════════════════════════════════════════
export default function CybersecurityPage() {
    const [tab, setTab] = useState<Tab>("overview");
    const [isOnline, setIsOnline] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    // Data
    const [agentStatus, setAgentStatus] = useState<CyberAgentStatus | null>(null);
    const [ddosConfig, setDdosConfig] = useState<DDoSConfig | null>(null);
    const [malwareConfig, setMalwareConfig] = useState<MalwareConfig | null>(null);
    const [simulatorStatus, setSimulatorStatus] = useState<SimulatorStatus | null>(null);
    const [zones, setZones] = useState<ZoneInfo[]>([]);
    const [timeline, setTimeline] = useState<TimelineBucket[]>([]);
    const [summary, setSummary] = useState<MetricsSummary | null>(null);

    // WebSocket live logs
    const [logs, setLogs] = useState<any[]>([]);
    const [wsConnected, setWsConnected] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);
    const logBoxRef = useRef<HTMLDivElement>(null);

    // Save state
    const [isSaving, setIsSaving] = useState(false);
    const [saveMsg, setSaveMsg] = useState<{ type: string; text: string } | null>(null);

    // ── Fetch all data ──
    const fetchAll = useCallback(async () => {
        setIsLoading(true);
        const online = await checkHealth("cybersecurity");
        setIsOnline(online);
        if (online) {
            const [ddos, malware, agents, sim, z, tl, sm] = await Promise.all([
                getCyberDDoSConfig(), getCyberMalwareConfig(), getCyberAgentStatus(),
                getSimulatorStatus(), getSimulatorZones(), getMetricsTimeline(),
                getMetricsSummary(),
            ]);
            if (ddos) setDdosConfig(ddos);
            if (malware) setMalwareConfig(malware);
            if (agents) setAgentStatus(agents);
            if (sim) setSimulatorStatus(sim);
            if (z) setZones(z);
            if (tl) setTimeline(tl);
            if (sm) setSummary(sm);
        }
        setIsLoading(false);
    }, []);

    useEffect(() => { fetchAll(); }, [fetchAll]);

    // ── Auto-refresh timeline & summary every 5s ──
    useEffect(() => {
        if (!isOnline) return;
        const interval = setInterval(async () => {
            const [tl, sm, sim] = await Promise.all([
                getMetricsTimeline(), getMetricsSummary(), getSimulatorStatus(),
            ]);
            if (tl) setTimeline(tl);
            if (sm) setSummary(sm);
            if (sim) setSimulatorStatus(sim);
        }, 5000);
        return () => clearInterval(interval);
    }, [isOnline]);

    // ── WebSocket connection ──
    useEffect(() => {
        if (!isOnline) return;
        const ws = new WebSocket(`${WS_BASE("cybersecurity")}/ws`);
        wsRef.current = ws;

        ws.onopen = () => setWsConnected(true);
        ws.onclose = () => setWsConnected(false);
        ws.onerror = () => setWsConnected(false);

        ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                if (msg.type === "kafka_event" || msg.type === "system_status") {
                    setLogs(prev => {
                        const updated = [...prev, msg];
                        return updated.slice(-500); // keep last 500
                    });
                }
            } catch { /* ignore */ }
        };

        // Heartbeat
        const ping = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: "ping" }));
            }
        }, 20000);

        return () => {
            clearInterval(ping);
            ws.close();
        };
    }, [isOnline]);

    // Auto-scroll logs
    useEffect(() => {
        if (logBoxRef.current) {
            logBoxRef.current.scrollTop = logBoxRef.current.scrollHeight;
        }
    }, [logs]);

    // ── Save handlers ──
    const saveDDoS = async () => {
        if (!ddosConfig) return;
        setIsSaving(true); setSaveMsg(null);
        try {
            const result = await putDDoSConfig(ddosConfig.thresholds);
            if (result) setSaveMsg({ type: "success", text: "DDoS configuration saved!" });
            else setSaveMsg({ type: "danger", text: "Failed to save DDoS config." });
        } catch { setSaveMsg({ type: "danger", text: "Failed to save." }); }
        setIsSaving(false);
    };

    const saveMalware = async () => {
        if (!malwareConfig) return;
        setIsSaving(true); setSaveMsg(null);
        try {
            const result = await putMalwareConfig(malwareConfig.thresholds);
            if (result) setSaveMsg({ type: "success", text: "Malware configuration saved!" });
            else setSaveMsg({ type: "danger", text: "Failed to save Malware config." });
        } catch { setSaveMsg({ type: "danger", text: "Failed to save." }); }
        setIsSaving(false);
    };

    const doReset = async () => {
        setIsSaving(true); setSaveMsg(null);
        try {
            const result = await resetConfig();
            if (result) {
                setSaveMsg({ type: "success", text: "All configs reset to defaults!" });
                fetchAll();
            }
        } catch { setSaveMsg({ type: "danger", text: "Reset failed." }); }
        setIsSaving(false);
    };

    // ── Attack trigger ──
    const [attackType, setAttackType] = useState("ddos_flood");
    const [attackZone, setAttackZone] = useState("SL-ZONE-A");
    const [attackIntensity, setAttackIntensity] = useState(0.8);
    const [attackDuration, setAttackDuration] = useState(30);
    const [attackMsg, setAttackMsg] = useState("");

    const doAttack = async () => {
        setAttackMsg("Triggering...");
        const result = await triggerAttack(attackType, attackZone, attackIntensity, attackDuration);
        if (result?.status === "attack_triggered") {
            setAttackMsg(`✅ ${attackType} attack launched on ${attackZone} for ${attackDuration}s`);
        } else {
            setAttackMsg(`❌ Failed: ${result?.error || "Unknown error"}`);
        }
    };

    // ── Log filters ──
    const [logFilter, setLogFilter] = useState("all");
    const [zoneFilter, setZoneFilter] = useState("all");
    const filteredLogs = logs.filter(l => {
        const data = l.data || l;
        // Zone filter
        if (zoneFilter !== "all" && data.zone_id !== zoneFilter) return false;
        // Severity / type filter
        if (logFilter === "all") return true;
        if (logFilter === "critical") return data.severity === "critical";
        if (logFilter === "suspicious") return data.suspicious === true;
        if (logFilter === "ddos") return data.event_type === "network_traffic" && data.suspicious;
        if (logFilter === "malware") return ["process_execution", "file_system_change", "device_behavior"].includes(data.event_type);
        return true;
    });

    // ═══════════════════════════════════════════════════════════════════════
    // Render
    // ═══════════════════════════════════════════════════════════════════════
    return (
        <>
            {/* Header */}
            <div className="content-header">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                        <h1>⚡ Cybersecurity Command Center</h1>
                        <ol className="breadcrumb">
                            <li className="breadcrumb-item"><Link href="/">Home</Link></li>
                            <li className="breadcrumb-item active">Cybersecurity</li>
                        </ol>
                    </div>
                    <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                        <span style={wsConnected ? S.pulseGreen : S.pulseRed} />
                        <span className={`badge badge-${isOnline ? "success" : "danger"}`}>
                            {isLoading ? "Connecting..." : isOnline ? "Live" : "Offline"}
                        </span>
                        <span className={`badge badge-${simulatorStatus?.is_running ? "info" : "secondary"}`}>
                            SIM {simulatorStatus?.is_running ? "Running" : "Stopped"}
                        </span>
                    </div>
                </div>
            </div>

            <section className="content">
                {saveMsg && (
                    <div className={`alert alert-${saveMsg.type} mb-3`} style={{ padding: "0.5rem 1rem", fontSize: "0.9rem" }}>
                        {saveMsg.text}
                        <button onClick={() => setSaveMsg(null)} style={{ float: "right", background: "none", border: "none", fontWeight: 700, cursor: "pointer" }}>×</button>
                    </div>
                )}

                {/* Tabs */}
                <div style={S.tabs}>
                    {([
                        ["overview", "📊", "Overview"],
                        ["ddos", "🚨", "DDoS Config"],
                        ["malware", "🛡️", "Malware Config"],
                        ["logs", "📜", "Live Logs"],
                        ["map", "🗺️", "Network Map"],
                    ] as [Tab, string, string][]).map(([key, icon, label]) => (
                        <button key={key} style={S.tab(tab === key)} onClick={() => setTab(key)}>
                            {icon} {label}
                        </button>
                    ))}
                </div>

                {/* ═══════ TAB: Overview ═══════ */}
                {tab === "overview" && <OverviewTab
                    summary={summary} timeline={timeline} simulatorStatus={simulatorStatus}
                    agentStatus={agentStatus} zones={zones}
                    onStartSim={async () => { await startSimulator(); fetchAll(); }}
                    onStopSim={async () => { await stopSimulator(); fetchAll(); }}
                />}

                {/* ═══════ TAB: DDoS Config ═══════ */}
                {tab === "ddos" && <DDoSConfigTab
                    config={ddosConfig} setConfig={setDdosConfig}
                    onSave={saveDDoS} onReset={doReset} isSaving={isSaving}
                />}

                {/* ═══════ TAB: Malware Config ═══════ */}
                {tab === "malware" && <MalwareConfigTab
                    config={malwareConfig} setConfig={setMalwareConfig}
                    onSave={saveMalware} onReset={doReset} isSaving={isSaving}
                />}

                {/* ═══════ TAB: Live Logs ═══════ */}
                {tab === "logs" && (
                    <div>
                        <div className="card">
                            <div className="card-header">
                                <h3 className="card-title">
                                    <span style={wsConnected ? S.pulseGreen : S.pulseRed} />
                                    Real-Time Network Event Stream
                                </h3>
                                <div className="card-tools" style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                                    <select value={zoneFilter} onChange={e => setZoneFilter(e.target.value)}
                                        className="form-control" style={{ width: "170px", height: "32px", fontSize: "0.85rem" }}>
                                        <option value="all">All Zones</option>
                                        <option value="SL-ZONE-A">Airport Zone</option>
                                        <option value="SL-ZONE-B">Port Zone</option>
                                        <option value="SL-ZONE-C">Industrial Zone</option>
                                        <option value="SL-ZONE-D">Residential Zone</option>
                                        <option value="SL-ZONE-E">Hospital Zone</option>
                                        <option value="SL-ZONE-F">Commercial Zone</option>
                                        <option value="SL-ZONE-G">Transport Hub</option>
                                    </select>
                                    <select value={logFilter} onChange={e => setLogFilter(e.target.value)}
                                        className="form-control" style={{ width: "150px", height: "32px", fontSize: "0.85rem" }}>
                                        <option value="all">All Events</option>
                                        <option value="critical">Critical Only</option>
                                        <option value="suspicious">Suspicious</option>
                                        <option value="ddos">DDoS Events</option>
                                        <option value="malware">Malware Events</option>
                                    </select>
                                    <span className="badge badge-secondary">{filteredLogs.length} events</span>
                                    <button className="btn btn-sm btn-outline-danger" onClick={() => setLogs([])}>Clear</button>
                                </div>
                            </div>
                            <div className="card-body" style={{ padding: 0 }}>
                                <div ref={logBoxRef} style={S.logBox}>
                                    {filteredLogs.length === 0 && (
                                        <div style={{ color: "#6c7086", textAlign: "center", padding: "2rem" }}>
                                            {wsConnected ? "Waiting for events..." : "WebSocket disconnected. Events will appear when connected."}
                                        </div>
                                    )}
                                    {filteredLogs.map((log, i) => {
                                        const data = log.data || log;
                                        const sev = data.severity || "low";
                                        const ts = data.timestamp ? new Date(data.timestamp).toLocaleTimeString() : "";
                                        return (
                                            <div key={i} style={S.logLine(sev)}>
                                                <span style={{ color: "#7f849c" }}>[{ts}]</span>{" "}
                                                <span style={{ color: SEVERITY_COLORS[sev as keyof typeof SEVERITY_COLORS] || "#cdd6f4", fontWeight: sev === "critical" ? 700 : 400 }}>
                                                    [{sev.toUpperCase()}]
                                                </span>{" "}
                                                <span style={{ color: "#89b4fa" }}>{data.zone_name || data.zone_id || ""}</span>{" "}
                                                <span style={{ color: "#cba6f7" }}>{data.device_id || ""}</span>{" "}
                                                <span>{data.event_type || log.type || ""}</span>{" "}
                                                {data.suspicious && <span style={{ color: "#f38ba8" }}>⚠ SUSPICIOUS</span>}
                                                {data.requests_per_second && <span style={{ color: "#fab387" }}> RPS:{data.requests_per_second}</span>}
                                                {data.source_ip && <span style={{ color: "#94e2d5" }}> src:{data.source_ip}</span>}
                                                {data.process_name && <span style={{ color: "#f38ba8" }}> proc:{data.process_name}</span>}
                                                {data.files_modified && <span style={{ color: "#fab387" }}> files:{data.files_modified}</span>}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>

                        {/* Attack Simulation Panel */}
                        <div className="card" style={{ borderLeft: "4px solid #dc3545" }}>
                            <div className="card-header" style={{ background: "#dc354510" }}>
                                <h3 className="card-title">⚔️ Attack Simulation</h3>
                            </div>
                            <div className="card-body">
                                <div className="row">
                                    <div className="col-3">
                                        <label className="form-label" style={{ fontSize: "0.85rem" }}>Attack Type</label>
                                        <select value={attackType} onChange={e => setAttackType(e.target.value)} className="form-control">
                                            <option value="ddos_flood">DDoS Flood</option>
                                            <option value="malware_infection">Malware Infection</option>
                                            <option value="firmware_tampering">Firmware Tampering</option>
                                            <option value="reconnaissance">Reconnaissance</option>
                                        </select>
                                    </div>
                                    <div className="col-3">
                                        <label className="form-label" style={{ fontSize: "0.85rem" }}>Target Zone</label>
                                        <select value={attackZone} onChange={e => setAttackZone(e.target.value)} className="form-control">
                                            {zones.map(z => <option key={z.id} value={z.id}>{z.name}</option>)}
                                        </select>
                                    </div>
                                    <div className="col-2">
                                        <label className="form-label" style={{ fontSize: "0.85rem" }}>Intensity</label>
                                        <input type="range" min="0.1" max="1" step="0.1" value={attackIntensity}
                                            onChange={e => setAttackIntensity(parseFloat(e.target.value))}
                                            style={{ width: "100%" }} />
                                        <small className="text-muted">{(attackIntensity * 100).toFixed(0)}%</small>
                                    </div>
                                    <div className="col-2">
                                        <label className="form-label" style={{ fontSize: "0.85rem" }}>Duration (s)</label>
                                        <input type="number" value={attackDuration} onChange={e => setAttackDuration(parseInt(e.target.value))}
                                            className="form-control" min={5} max={120} />
                                    </div>
                                    <div className="col-2" style={{ display: "flex", alignItems: "flex-end" }}>
                                        <button className="btn btn-danger" onClick={doAttack} style={{ width: "100%" }}>
                                            🚀 Launch Attack
                                        </button>
                                    </div>
                                </div>
                                {attackMsg && <div style={{ marginTop: "0.5rem", fontWeight: 600 }}>{attackMsg}</div>}
                            </div>
                        </div>
                    </div>
                )}

                {/* ═══════ TAB: Network Map ═══════ */}
                {tab === "map" && <NetworkMapTab zones={zones} simulatorStatus={simulatorStatus} />}
            </section>
        </>
    );
}


// ═══════════════════════════════════════════════════════════════════════════
// Overview Tab Component
// ═══════════════════════════════════════════════════════════════════════════
function OverviewTab({ summary, timeline, simulatorStatus, agentStatus, zones, onStartSim, onStopSim }: {
    summary: MetricsSummary | null;
    timeline: TimelineBucket[];
    simulatorStatus: SimulatorStatus | null;
    agentStatus: CyberAgentStatus | null;
    zones: ZoneInfo[];
    onStartSim: () => void;
    onStopSim: () => void;
}) {
    // Recharts is always available (direct import)
    const RechartsLoaded = true;

    const severityPieData = summary ? Object.entries(summary.by_severity)
        .filter(([, v]) => v > 0)
        .map(([name, value]) => ({ name, value })) : [];

    const typePieData = summary ? Object.entries(summary.by_event_type)
        .filter(([, v]) => v > 0)
        .slice(0, 7)
        .map(([name, value]) => ({ name: name.replace(/_/g, " "), value })) : [];

    return (
        <div>
            {/* Summary Cards Row */}
            <div className="row mb-3">
                {[
                    { label: "Total Events (5m)", value: summary?.total_events ?? "—", color: "#007bff" },
                    { label: "Events / sec", value: summary?.events_per_second?.toFixed(1) ?? "—", color: "#17a2b8" },
                    { label: "Suspicious", value: summary?.suspicious_events ?? "—", color: "#dc3545" },
                    {
                        label: "Threat Level", value: (summary?.threat_level || "—").toUpperCase(), color:
                            summary?.threat_level === "critical" ? "#dc3545" : summary?.threat_level === "high" ? "#fd7e14"
                                : summary?.threat_level === "medium" ? "#ffc107" : "#28a745"
                    },
                    { label: "Zones Active", value: zones.length || "—", color: "#6f42c1" },
                    { label: "Sim Events", value: simulatorStatus?.events_generated ?? "—", color: "#20c997" },
                ].map((c, i) => (
                    <div className="col-2" key={i}>
                        <div style={S.statCard(c.color)}>
                            <div style={{ fontSize: "1.8rem", fontWeight: 700, color: c.color }}>{c.value}</div>
                            <div style={{ fontSize: "0.8rem", color: "#6c757d", marginTop: "4px" }}>{c.label}</div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Simulator Controls */}
            <div className="card mb-3">
                <div className="card-header">
                    <h3 className="card-title">🎮 Simulator Control</h3>
                    <div className="card-tools">
                        <span className={`badge badge-${simulatorStatus?.is_running ? "success" : "secondary"}`}>
                            {simulatorStatus?.is_running ? "Running" : "Stopped"}
                        </span>
                    </div>
                </div>
                <div className="card-body" style={{ padding: "0.75rem 1.25rem" }}>
                    <div style={{ display: "flex", gap: "1rem", alignItems: "center", flexWrap: "wrap" }}>
                        <button className="btn btn-success btn-sm" onClick={onStartSim} disabled={simulatorStatus?.is_running}>
                            ▶ Start
                        </button>
                        <button className="btn btn-danger btn-sm" onClick={onStopSim} disabled={!simulatorStatus?.is_running}>
                            ⏹ Stop
                        </button>
                        <span className="text-muted" style={{ fontSize: "0.85rem" }}>
                            ⏱ Uptime: {simulatorStatus?.uptime_seconds?.toFixed(0) ?? 0}s
                            &nbsp;|&nbsp; 📊 {simulatorStatus?.events_generated ?? 0} events
                            &nbsp;|&nbsp; ⚡ {simulatorStatus?.events_per_second?.toFixed(1) ?? 0} ev/s
                            &nbsp;|&nbsp; 🔧 {simulatorStatus?.device_count ?? 0} devices
                        </span>
                        {(simulatorStatus?.active_attacks?.length ?? 0) > 0 && (
                            <span className="badge badge-danger">
                                {simulatorStatus!.active_attacks.length} active attack(s)
                            </span>
                        )}
                    </div>
                </div>
            </div>

            {/* Charts Row */}
            <div className="row">
                {/* Threat Timeline */}
                <div className="col-8">
                    <div className="card">
                        <div className="card-header">
                            <h3 className="card-title">📈 Threat Timeline (5 min)</h3>
                        </div>
                        <div className="card-body" style={{ padding: "0.5rem" }}>
                            {RechartsLoaded && timeline.length > 0 ? (
                                <ResponsiveContainer width="100%" height={280}>
                                    <AreaChart data={timeline}>
                                        <defs>
                                            <linearGradient id="critGrad" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#f38ba8" stopOpacity={0.4} />
                                                <stop offset="95%" stopColor="#f38ba8" stopOpacity={0} />
                                            </linearGradient>
                                            <linearGradient id="highGrad" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#fab387" stopOpacity={0.4} />
                                                <stop offset="95%" stopColor="#fab387" stopOpacity={0} />
                                            </linearGradient>
                                            <linearGradient id="normGrad" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#a6e3a1" stopOpacity={0.4} />
                                                <stop offset="95%" stopColor="#a6e3a1" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#e9ecef" />
                                        <XAxis dataKey="time" tickFormatter={(v: string) => new Date(v).toLocaleTimeString().slice(0, 5)}
                                            stroke="#adb5bd" fontSize={11} />
                                        <YAxis stroke="#adb5bd" fontSize={11} />
                                        <RTooltip contentStyle={{ background: "#fff", border: "1px solid #dee2e6", borderRadius: 6 }}
                                            labelFormatter={(v: any) => new Date(String(v)).toLocaleTimeString()} />
                                        <Area type="monotone" dataKey="critical" stroke="#f38ba8" fill="url(#critGrad)" strokeWidth={2} />
                                        <Area type="monotone" dataKey="high" stroke="#fab387" fill="url(#highGrad)" strokeWidth={2} />
                                        <Area type="monotone" dataKey="normal" stroke="#a6e3a1" fill="url(#normGrad)" strokeWidth={1.5} />
                                        <Legend />
                                    </AreaChart>
                                </ResponsiveContainer>
                            ) : (
                                <div style={{ height: 280, display: "flex", alignItems: "center", justifyContent: "center", color: "#adb5bd" }}>
                                    {timeline.length === 0 ? "No timeline data yet. Start the simulator." : "Loading charts..."}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Severity Breakdown Pie */}
                <div className="col-4">
                    <div className="card">
                        <div className="card-header">
                            <h3 className="card-title">🎯 Severity Breakdown</h3>
                        </div>
                        <div className="card-body" style={{ padding: "0.5rem" }}>
                            {RechartsLoaded && severityPieData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={280}>
                                    <PieChart>
                                        <Pie data={severityPieData} cx="50%" cy="50%" outerRadius={90}
                                            label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}
                                            dataKey="value" fontSize={11}>
                                            {severityPieData.map((_, i) => (
                                                <Cell key={i} fill={SEVERITY_COLORS[severityPieData[i].name as keyof typeof SEVERITY_COLORS] || PIE_COLORS[i]} />
                                            ))}
                                        </Pie>
                                        <RTooltip />
                                    </PieChart>
                                </ResponsiveContainer>
                            ) : (
                                <div style={{ height: 280, display: "flex", alignItems: "center", justifyContent: "center", color: "#adb5bd" }}>
                                    No severity data
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Second Charts Row */}
            <div className="row">
                {/* Event Type Distribution */}
                <div className="col-6">
                    <div className="card">
                        <div className="card-header"><h3 className="card-title">📊 Event Type Distribution</h3></div>
                        <div className="card-body" style={{ padding: "0.5rem" }}>
                            {RechartsLoaded && typePieData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={250}>
                                    <BarChart data={typePieData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#e9ecef" />
                                        <XAxis dataKey="name" fontSize={10} angle={-20} textAnchor="end" height={60} />
                                        <YAxis fontSize={11} />
                                        <RTooltip />
                                        <Bar dataKey="value" fill="#89b4fa" radius={[4, 4, 0, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <div style={{ height: 250, display: "flex", alignItems: "center", justifyContent: "center", color: "#adb5bd" }}>No data</div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Agents Status */}
                <div className="col-6">
                    <div className="card">
                        <div className="card-header"><h3 className="card-title">🤖 Security Agents</h3></div>
                        <div className="card-body" style={{ padding: 0 }}>
                            <table className="table table-striped mb-0">
                                <thead>
                                    <tr><th>Agent</th><th>Status</th><th>Capabilities</th></tr>
                                </thead>
                                <tbody>
                                    {agentStatus ? Object.entries(agentStatus.agents).map(([name, agent]) => (
                                        <tr key={name}>
                                            <td style={{ fontWeight: 600 }}>{name.replace(/_/g, " ").replace(/^\w/, c => c.toUpperCase())}</td>
                                            <td><span className={`badge badge-${agent.status === "active" ? "success" : "warning"}`}>{agent.status}</span></td>
                                            <td style={{ fontSize: "0.8rem" }}>{agent.capabilities.slice(0, 3).join(", ")}</td>
                                        </tr>
                                    )) : (
                                        <tr><td colSpan={3} className="text-muted text-center">Loading...</td></tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Zone Activity */}
                    <div className="card">
                        <div className="card-header"><h3 className="card-title">🏙️ Zone Activity</h3></div>
                        <div className="card-body" style={{ padding: 0 }}>
                            <table className="table table-sm mb-0">
                                <thead><tr><th>Zone</th><th>Type</th><th>Priority</th><th>Devices</th><th>Events</th></tr></thead>
                                <tbody>
                                    {zones.map(z => (
                                        <tr key={z.id}>
                                            <td style={{ fontWeight: 600 }}>
                                                <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: "50%", background: z.color, marginRight: 6 }} />
                                                {z.name}
                                            </td>
                                            <td>{z.type}</td>
                                            <td><span className={`badge badge-${z.priority === "critical" ? "danger" : z.priority === "high" ? "warning" : "info"}`}>{z.priority}</span></td>
                                            <td>{z.device_count}</td>
                                            <td>{summary?.by_zone?.[z.id] ?? 0}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}


// ═══════════════════════════════════════════════════════════════════════════
// DDoS Config Tab
// ═══════════════════════════════════════════════════════════════════════════
function DDoSConfigTab({ config, setConfig, onSave, onReset, isSaving }: {
    config: DDoSConfig | null;
    setConfig: (c: DDoSConfig) => void;
    onSave: () => void;
    onReset: () => void;
    isSaving: boolean;
}) {
    if (!config) return <div className="text-muted">Loading DDoS configuration...</div>;

    const updateThreshold = (key: keyof DDoSConfig["thresholds"], value: number) => {
        setConfig({ ...config, thresholds: { ...config.thresholds, [key]: value } });
    };

    const fields: [keyof DDoSConfig["thresholds"], string, string][] = [
        ["normal_rps_min", "Normal RPS (Min)", "req/s"],
        ["normal_rps_max", "Normal RPS (Max)", "req/s"],
        ["moderate_rps", "Moderate RPS", "req/s"],
        ["high_rps", "High RPS", "req/s"],
        ["critical_rps", "Critical RPS", "req/s"],
        ["syn_flood_threshold", "SYN Flood Threshold", "packets/s"],
        ["http_flood_threshold", "HTTP Flood Threshold", "req/s"],
        ["packet_size_anomaly_min", "Packet Size Min", "bytes"],
        ["packet_size_anomaly_max", "Packet Size Max", "bytes"],
        ["requests_per_ip_normal", "Requests/IP Normal", "req/min"],
        ["requests_per_ip_suspicious", "Requests/IP Suspicious", "req/min"],
        ["unique_ips_normal", "Unique IPs Normal", "IPs"],
        ["unique_ips_attack", "Unique IPs Attack", "IPs"],
        ["geo_concentration_threshold", "Geo Concentration", "ratio"],
        ["response_time_normal_ms", "Response Time Normal", "ms"],
        ["failed_request_rate", "Failed Request Rate", "ratio"],
    ];

    return (
        <div>
            <div className="card" style={{ borderLeft: "4px solid #dc3545" }}>
                <div className="card-header" style={{ background: "#dc354510" }}>
                    <h3 className="card-title">🚨 DDoS Detection Agent — Threshold Configuration</h3>
                    <div className="card-tools">
                        <button className="btn btn-sm btn-outline-secondary" onClick={onReset} disabled={isSaving}>🔄 Reset All</button>
                        <button className="btn btn-sm btn-success" onClick={onSave} disabled={isSaving}>
                            {isSaving ? "Saving..." : "💾 Save Changes"}
                        </button>
                    </div>
                </div>
                <div className="card-body">
                    <div className="row">
                        {fields.map(([key, label, unit]) => (
                            <div className="col-4 mb-3" key={key}>
                                <label className="form-label" style={{ fontSize: "0.85rem", fontWeight: 600 }}>{label}</label>
                                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                                    <input type="number" value={config.thresholds[key]}
                                        onChange={e => updateThreshold(key, key.includes("rate") || key.includes("concentration") ? parseFloat(e.target.value) : parseInt(e.target.value))}
                                        className="form-control" step={key.includes("rate") || key.includes("concentration") ? 0.01 : 1} />
                                    <span className="text-muted" style={{ fontSize: "0.8rem", whiteSpace: "nowrap" }}>{unit}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                    <div className="row mt-2">
                        <div className="col-4">
                            <label className="form-label" style={{ fontSize: "0.85rem", fontWeight: 600 }}>Detection Window</label>
                            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                                <input type="number" value={config.detection_window}
                                    onChange={e => setConfig({ ...config, detection_window: parseInt(e.target.value) })}
                                    className="form-control" />
                                <span className="text-muted" style={{ fontSize: "0.8rem" }}>seconds</span>
                            </div>
                        </div>
                        <div className="col-4">
                            <label className="form-label" style={{ fontSize: "0.85rem", fontWeight: 600 }}>Agent Timeout</label>
                            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                                <input type="number" value={config.agent_timeout}
                                    onChange={e => setConfig({ ...config, agent_timeout: parseInt(e.target.value) })}
                                    className="form-control" />
                                <span className="text-muted" style={{ fontSize: "0.8rem" }}>seconds</span>
                            </div>
                        </div>
                        <div className="col-4">
                            <label className="form-label" style={{ fontSize: "0.85rem", fontWeight: 600 }}>Attack Types Detected</label>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
                                {config.attack_types.map(t => (
                                    <span key={t} className="badge badge-danger" style={{ fontSize: "0.75rem" }}>{t}</span>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}


// ═══════════════════════════════════════════════════════════════════════════
// Malware Config Tab
// ═══════════════════════════════════════════════════════════════════════════
function MalwareConfigTab({ config, setConfig, onSave, onReset, isSaving }: {
    config: MalwareConfig | null;
    setConfig: (c: MalwareConfig) => void;
    onSave: () => void;
    onReset: () => void;
    isSaving: boolean;
}) {
    if (!config) return <div className="text-muted">Loading Malware configuration...</div>;

    const updateThreshold = (key: keyof MalwareConfig["thresholds"], value: number) => {
        setConfig({ ...config, thresholds: { ...config.thresholds, [key]: value } });
    };

    const fields: [keyof MalwareConfig["thresholds"], string, string][] = [
        ["file_encryption_rate", "File Encryption Rate", "files/min"],
        ["suspicious_process_count", "Suspicious Process Count", "processes"],
        ["cpu_usage_threshold", "CPU Usage Threshold", "%"],
        ["memory_usage_threshold", "Memory Usage Threshold", "%"],
        ["outbound_connections", "Outbound Connections", "connections"],
        ["file_modifications", "File Modifications", "files"],
        ["network_upload_mb", "Network Upload Threshold", "MB"],
    ];

    return (
        <div>
            <div className="card" style={{ borderLeft: "4px solid #17a2b8" }}>
                <div className="card-header" style={{ background: "#17a2b810" }}>
                    <h3 className="card-title">🛡️ Malware Detection Agent — Threshold Configuration</h3>
                    <div className="card-tools">
                        <button className="btn btn-sm btn-outline-secondary" onClick={onReset} disabled={isSaving}>🔄 Reset All</button>
                        <button className="btn btn-sm btn-success" onClick={onSave} disabled={isSaving}>
                            {isSaving ? "Saving..." : "💾 Save Changes"}
                        </button>
                    </div>
                </div>
                <div className="card-body">
                    <div className="row">
                        {fields.map(([key, label, unit]) => (
                            <div className="col-4 mb-3" key={key}>
                                <label className="form-label" style={{ fontSize: "0.85rem", fontWeight: 600 }}>{label}</label>
                                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                                    <input type="number" value={config.thresholds[key]}
                                        onChange={e => updateThreshold(key, parseInt(e.target.value))}
                                        className="form-control" />
                                    <span className="text-muted" style={{ fontSize: "0.8rem", whiteSpace: "nowrap" }}>{unit}</span>
                                </div>
                            </div>
                        ))}
                    </div>

                    <hr />

                    <div className="row">
                        <div className="col-4">
                            <label className="form-label" style={{ fontSize: "0.85rem", fontWeight: 600 }}>C2 Suspicious Ports</label>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
                                {config.c2_suspicious_ports.map(p => (
                                    <span key={p} className="badge badge-warning" style={{ fontSize: "0.75rem" }}>{p}</span>
                                ))}
                            </div>
                        </div>
                        <div className="col-4">
                            <label className="form-label" style={{ fontSize: "0.85rem", fontWeight: 600 }}>Suspicious Extensions</label>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
                                {config.suspicious_extensions.map(ext => (
                                    <span key={ext} className="badge badge-info" style={{ fontSize: "0.75rem" }}>{ext}</span>
                                ))}
                            </div>
                        </div>
                        <div className="col-4">
                            <label className="form-label" style={{ fontSize: "0.85rem", fontWeight: 600 }}>Known Malware Families</label>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
                                {config.known_families.map(f => (
                                    <span key={f} className="badge badge-danger" style={{ fontSize: "0.75rem" }}>{f}</span>
                                ))}
                            </div>
                        </div>
                    </div>

                    <div className="row mt-3">
                        <div className="col-6">
                            <label className="form-label" style={{ fontSize: "0.85rem", fontWeight: 600 }}>Suspicious Processes</label>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
                                {config.suspicious_processes.map(p => (
                                    <span key={p} className="badge badge-secondary" style={{ fontSize: "0.75rem" }}>{p}</span>
                                ))}
                            </div>
                        </div>
                        <div className="col-3">
                            <label className="form-label" style={{ fontSize: "0.85rem", fontWeight: 600 }}>Agent Timeout</label>
                            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                                <input type="number" value={config.agent_timeout}
                                    onChange={e => setConfig({ ...config, agent_timeout: parseInt(e.target.value) })}
                                    className="form-control" />
                                <span className="text-muted" style={{ fontSize: "0.8rem" }}>seconds</span>
                            </div>
                        </div>
                        <div className="col-3">
                            <label className="form-label" style={{ fontSize: "0.85rem", fontWeight: 600 }}>Detection Types</label>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
                                {config.detection_types.map(t => (
                                    <span key={t} className="badge badge-info" style={{ fontSize: "0.75rem" }}>{t}</span>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}


// ═══════════════════════════════════════════════════════════════════════════
// Network Map Tab (Leaflet — SSR-safe via dynamic import)
// ═══════════════════════════════════════════════════════════════════════════
const LeafletMap = dynamic<{ zones: ZoneInfo[]; simulatorStatus: SimulatorStatus | null }>(() => import("./CyberMapLeaflet"), { ssr: false });

function NetworkMapTab({ zones, simulatorStatus }: { zones: ZoneInfo[]; simulatorStatus: SimulatorStatus | null }) {
    return (
        <div>
            <div className="card">
                <div className="card-header">
                    <h3 className="card-title">🗺️ Mumbai Smart Lighting Grid — Network Map</h3>
                    <div className="card-tools">
                        <span className="badge badge-info">{zones.length} zones</span>
                        <span className="badge badge-secondary">
                            {zones.reduce((s, z) => s + z.device_count, 0)} devices
                        </span>
                    </div>
                </div>
                <div className="card-body" style={{ padding: 0, height: "550px" }}>
                    <LeafletMap zones={zones} simulatorStatus={simulatorStatus} />
                </div>
            </div>

            {/* Zone Details */}
            <div className="card">
                <div className="card-header"><h3 className="card-title">📋 Zone Details</h3></div>
                <div className="card-body" style={{ padding: 0 }}>
                    <table className="table table-striped mb-0">
                        <thead>
                            <tr>
                                <th>Zone</th><th>Area</th><th>Type</th><th>Priority</th>
                                <th>Devices</th><th>Center</th>
                            </tr>
                        </thead>
                        <tbody>
                            {zones.map(z => (
                                <tr key={z.id}>
                                    <td>
                                        <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: "50%", background: z.color, marginRight: 6 }} />
                                        <strong>{z.name}</strong>
                                    </td>
                                    <td>{z.area}</td>
                                    <td>{z.type}</td>
                                    <td>
                                        <span className={`badge badge-${z.priority === "critical" ? "danger" : z.priority === "high" ? "warning" : "info"}`}>
                                            {z.priority}
                                        </span>
                                    </td>
                                    <td>{z.device_count}</td>
                                    <td style={{ fontSize: "0.8rem" }}>{z.center[0].toFixed(4)}, {z.center[1].toFixed(4)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

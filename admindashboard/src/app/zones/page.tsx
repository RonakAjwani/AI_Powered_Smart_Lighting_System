"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
    checkHealth, getSimulatorZones,
    API_BASE, type ZoneInfo,
} from "@/lib/api";

// ── Zone type styles ──
const typeColors: Record<string, { bg: string; text: string }> = {
    airport: { bg: "#ef444422", text: "#ef4444" },
    port: { bg: "#f9731622", text: "#f97316" },
    industrial: { bg: "#eab30822", text: "#eab308" },
    residential: { bg: "#22c55e22", text: "#22c55e" },
    hospital: { bg: "#06b6d422", text: "#06b6d4" },
    commercial: { bg: "#8b5cf622", text: "#8b5cf6" },
    transport_hub: { bg: "#ec489922", text: "#ec4899" },
    custom: { bg: "#6b728022", text: "#6b7280" },
};

const priorityBadge: Record<string, { bg: string; text: string; label: string }> = {
    critical: { bg: "#ef444433", text: "#f87171", label: "Critical" },
    high: { bg: "#f9731633", text: "#fb923c", label: "High" },
    medium: { bg: "#eab30833", text: "#fbbf24", label: "Medium" },
    low: { bg: "#22c55e33", text: "#4ade80", label: "Low" },
};

export default function ZonesPage() {
    const [zones, setZones] = useState<ZoneInfo[]>([]);
    const [isOnline, setIsOnline] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [filter, setFilter] = useState<"all" | "critical" | "high">("all");

    // Fetch zones from backend
    const fetchZones = useCallback(async () => {
        setIsLoading(true);
        const online = await checkHealth("cybersecurity");
        setIsOnline(online);
        if (online) {
            const z = await getSimulatorZones();
            if (z) setZones(z);
        }
        setIsLoading(false);
    }, []);

    useEffect(() => { fetchZones(); }, [fetchZones]);

    // Filter zones
    const filteredZones = zones.filter((zone) => {
        if (filter === "critical") return zone.priority === "critical";
        if (filter === "high") return zone.priority === "high" || zone.priority === "critical";
        return true;
    });

    // Stats
    const totalDevices = zones.reduce((sum, z) => sum + z.device_count, 0);
    const criticalCount = zones.filter(z => z.priority === "critical").length;

    return (
        <>
            {/* Header */}
            <div className="content-header">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                        <h1>🗺️ Zone Configuration</h1>
                        <ol className="breadcrumb">
                            <li className="breadcrumb-item"><Link href="/">Home</Link></li>
                            <li className="breadcrumb-item active">Zones</li>
                        </ol>
                    </div>
                    <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                        <span className={`badge badge-${isOnline ? "success" : "danger"}`}>
                            {isLoading ? "Loading..." : isOnline ? "Backend Online" : "Backend Offline"}
                        </span>
                        <button className="btn btn-sm btn-outline-primary" onClick={fetchZones}>
                            🔄 Refresh
                        </button>
                    </div>
                </div>
            </div>

            <section className="content">
                {/* ── Summary Cards ── */}
                <div className="row mb-3">
                    {[
                        { icon: "🏙️", label: "TOTAL ZONES", value: zones.length, color: "#3b82f6" },
                        { icon: "📡", label: "TOTAL DEVICES", value: totalDevices, color: "#22c55e" },
                        { icon: "⚠️", label: "CRITICAL ZONES", value: criticalCount, color: "#ef4444" },
                        { icon: "🌍", label: "REGION", value: "Mumbai", color: "#8b5cf6" },
                    ].map((card, i) => (
                        <div key={i} className="col-3">
                            <div className="card" style={{
                                background: `linear-gradient(135deg, ${card.color}22, ${card.color}08)`,
                                border: `1px solid ${card.color}44`,
                            }}>
                                <div className="card-body" style={{ padding: "1rem", textAlign: "center" }}>
                                    <div style={{ fontSize: "1.5rem" }}>{card.icon}</div>
                                    <div style={{ fontSize: "0.7rem", color: "#6c757d", letterSpacing: "0.05em" }}>{card.label}</div>
                                    <div style={{ fontSize: "1.4rem", fontWeight: 700 }}>{card.value}</div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* ── Filter Buttons ── */}
                <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
                    {(["all", "critical", "high"] as const).map(f => (
                        <button
                            key={f}
                            className={`btn btn-sm ${filter === f ? "btn-primary" : "btn-outline-secondary"}`}
                            onClick={() => setFilter(f)}
                        >
                            {f === "all" ? "All" : f === "critical" ? "Critical Only" : "High + Critical"}
                        </button>
                    ))}
                </div>

                {/* ── Zones Table ── */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">Mumbai Infrastructure Zones</h3>
                        <div className="card-tools">
                            <span className="badge badge-info">{filteredZones.length} zones</span>
                        </div>
                    </div>
                    <div className="card-body" style={{ padding: 0 }}>
                        {!isOnline && !isLoading ? (
                            <div style={{ padding: "2rem", textAlign: "center", color: "#6c757d" }}>
                                <p style={{ fontSize: "1.1rem" }}>⚠️ Cybersecurity backend is offline</p>
                                <p style={{ fontSize: "0.85rem" }}>Start the backend service on port 8003 to load zones.</p>
                                <code style={{ display: "block", marginTop: "0.5rem", fontSize: "0.8rem", color: "#868e96" }}>
                                    cd backend/cybersecurity && venv\Scripts\python -m uvicorn src.main:app --port 8003
                                </code>
                            </div>
                        ) : isLoading ? (
                            <div style={{ padding: "2rem", textAlign: "center", color: "#6c757d" }}>Loading zones...</div>
                        ) : (
                            <table className="table table-hover" style={{ marginBottom: 0 }}>
                                <thead>
                                    <tr>
                                        <th style={{ width: "60px" }}>ID</th>
                                        <th>Zone Name</th>
                                        <th>Area</th>
                                        <th>Type</th>
                                        <th>Devices</th>
                                        <th>Priority</th>
                                        <th>Center</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredZones.map((zone) => {
                                        const tc = typeColors[zone.type] || typeColors.custom;
                                        const pb = priorityBadge[zone.priority] || priorityBadge.medium;
                                        return (
                                            <tr key={zone.id}>
                                                <td>
                                                    <span style={{
                                                        display: "inline-block", width: "12px", height: "12px",
                                                        borderRadius: "50%", background: zone.color,
                                                        marginRight: "6px", verticalAlign: "middle",
                                                        boxShadow: `0 0 6px ${zone.color}66`,
                                                    }} />
                                                    <code style={{ fontSize: "0.75rem" }}>{zone.id.replace("SL-", "")}</code>
                                                </td>
                                                <td style={{ fontWeight: 600 }}>{zone.name}</td>
                                                <td style={{ color: "#868e96", fontSize: "0.85rem" }}>{zone.area}</td>
                                                <td>
                                                    <span style={{
                                                        padding: "2px 8px", borderRadius: "4px", fontSize: "0.75rem",
                                                        fontWeight: 600, textTransform: "uppercase",
                                                        background: tc.bg, color: tc.text,
                                                    }}>
                                                        {zone.type.replace(/_/g, " ")}
                                                    </span>
                                                </td>
                                                <td>
                                                    <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>{zone.device_count}</span>
                                                    <span style={{ color: "#868e96", fontSize: "0.75rem", marginLeft: "4px" }}>devices</span>
                                                </td>
                                                <td>
                                                    <span style={{
                                                        padding: "2px 10px", borderRadius: "12px", fontSize: "0.75rem",
                                                        fontWeight: 600, background: pb.bg, color: pb.text,
                                                    }}>
                                                        {pb.label}
                                                    </span>
                                                </td>
                                                <td style={{ fontSize: "0.8rem", fontFamily: "monospace", color: "#868e96" }}>
                                                    {zone.center[0].toFixed(4)}, {zone.center[1].toFixed(4)}
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        )}
                    </div>
                </div>

                {/* ── Device List per Zone (expandable) ── */}
                {filteredZones.length > 0 && (
                    <div className="row mt-3">
                        {filteredZones.map(zone => (
                            <div key={zone.id} className="col-6 col-lg-4 mb-3">
                                <div className="card" style={{ borderLeft: `4px solid ${zone.color}` }}>
                                    <div className="card-header" style={{ padding: "0.6rem 1rem" }}>
                                        <h3 className="card-title" style={{ fontSize: "0.85rem", fontWeight: 600 }}>
                                            {zone.name}
                                        </h3>
                                        <div className="card-tools">
                                            <span className="badge" style={{
                                                background: zone.color + "33", color: zone.color,
                                            }}>{zone.device_count} devices</span>
                                        </div>
                                    </div>
                                    <div className="card-body" style={{ padding: "0.5rem", maxHeight: "150px", overflowY: "auto" }}>
                                        {zone.devices && zone.devices.length > 0 ? (
                                            <table style={{ width: "100%", fontSize: "0.72rem" }}>
                                                <tbody>
                                                    {zone.devices.map(d => (
                                                        <tr key={d.device_id} style={{ borderBottom: "1px solid #dee2e644" }}>
                                                            <td style={{ padding: "2px 4px" }}>
                                                                <code>{d.device_id}</code>
                                                            </td>
                                                            <td style={{ padding: "2px 4px", textAlign: "right" }}>
                                                                <span style={{
                                                                    color: d.status === "online" ? "#22c55e" : "#ef4444",
                                                                    fontWeight: 600,
                                                                }}>●</span> {d.status}
                                                            </td>
                                                            <td style={{ padding: "2px 4px", textAlign: "right", color: "#868e96" }}>
                                                                {Math.round(d.brightness)}%
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        ) : (
                                            <div style={{ color: "#868e96", fontSize: "0.75rem", textAlign: "center", padding: "0.5rem" }}>
                                                No device data
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </section>
        </>
    );
}

"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { getAllServicesHealth, getCoordinatorState, type ServiceHealth } from "@/lib/api";

export default function DashboardPage() {
  // Service health state
  const [services, setServices] = useState<ServiceHealth[]>([
    { name: "Cybersecurity", status: "offline", port: 8000 },
    { name: "Weather", status: "offline", port: 8001 },
    { name: "Power Grid", status: "offline", port: 8002 },
    { name: "Coordinator", status: "offline", port: 8004 },
  ]);

  const [coordinatorState, setCoordinatorState] = useState<{
    threatLevel?: string;
    gridStatus?: string;
    lastDecision?: string;
  }>({});

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<string>("");

  // Refresh all services from real backend
  const refreshHealth = async () => {
    setIsRefreshing(true);
    try {
      const healthData = await getAllServicesHealth();
      setServices(healthData);

      // Also fetch coordinator state
      const state = await getCoordinatorState();
      if (state) {
        setCoordinatorState({
          threatLevel: state.cybersecurity?.threat_level || "Normal",
          gridStatus: state.power?.grid_status || "Stable",
          lastDecision: state.last_decision || "N/A",
        });
      }

      setLastRefresh(new Date().toLocaleTimeString());
    } catch (error) {
      console.error("Failed to refresh health:", error);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    refreshHealth();
    const interval = setInterval(refreshHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const onlineCount = services.filter((s) => s.status === "online").length;

  return (
    <>
      {/* Content Header */}
      <div className="content-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1>Dashboard</h1>
            <ol className="breadcrumb">
              <li className="breadcrumb-item"><Link href="/">Home</Link></li>
              <li className="breadcrumb-item active">Dashboard</li>
            </ol>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {lastRefresh && <span className="text-muted" style={{ fontSize: '0.875rem' }}>Last update: {lastRefresh}</span>}
            <button onClick={refreshHealth} disabled={isRefreshing} className="btn btn-primary">
              <svg style={{ width: 16, height: 16 }} className={isRefreshing ? 'animate-spin' : ''} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <section className="content">
        {/* Small Boxes (Stat boxes) */}
        <div className="row">
          <div className="col-3">
            <div className="small-box bg-info">
              <div className="inner">
                <h3>{onlineCount}/{services.length}</h3>
                <p>Services Online</p>
              </div>
              <div className="icon">
                <svg style={{ width: 60, height: 60 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <Link href="/agents" className="small-box-footer">
                More info <span>→</span>
              </Link>
            </div>
          </div>

          <div className="col-3">
            <div className="small-box bg-success">
              <div className="inner">
                <h3>14</h3>
                <p>Active Agents</p>
              </div>
              <div className="icon">
                <svg style={{ width: 60, height: 60 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <Link href="/agents" className="small-box-footer">
                More info <span>→</span>
              </Link>
            </div>
          </div>

          <div className="col-3">
            <div className="small-box bg-warning">
              <div className="inner">
                <h3>8</h3>
                <p>Configured Zones</p>
              </div>
              <div className="icon">
                <svg style={{ width: 60, height: 60 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                </svg>
              </div>
              <Link href="/zones" className="small-box-footer">
                More info <span>→</span>
              </Link>
            </div>
          </div>

          <div className="col-3">
            <div className="small-box bg-danger">
              <div className="inner">
                <h3>0</h3>
                <p>Active Alerts</p>
              </div>
              <div className="icon">
                <svg style={{ width: 60, height: 60 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <Link href="#" className="small-box-footer">
                More info <span>→</span>
              </Link>
            </div>
          </div>
        </div>

        {/* Main row */}
        <div className="row">
          {/* Service Status Card */}
          <div className="col-6">
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">
                  <svg style={{ width: 18, height: 18, marginRight: 8 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
                  </svg>
                  Service Health (Live)
                </h3>
              </div>
              <div className="card-body" style={{ padding: 0 }}>
                <table className="table table-striped mb-0">
                  <thead>
                    <tr>
                      <th>Service</th>
                      <th>Port</th>
                      <th>Status</th>
                      <th>Latency</th>
                    </tr>
                  </thead>
                  <tbody>
                    {services.map((service) => (
                      <tr key={service.port}>
                        <td>{service.name}</td>
                        <td><code>{service.port}</code></td>
                        <td>
                          <span className={`badge badge-${service.status === 'online' ? 'success' : 'danger'}`}>
                            {service.status}
                          </span>
                        </td>
                        <td>{service.latency ? `${service.latency}ms` : '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Quick Actions Card */}
          <div className="col-6">
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">
                  <svg style={{ width: 18, height: 18, marginRight: 8 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Quick Actions
                </h3>
              </div>
              <div className="card-body">
                <div className="row">
                  <div className="col-6 mb-3">
                    <Link href="/zones" className="btn btn-info" style={{ width: '100%' }}>
                      <svg style={{ width: 16, height: 16 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                      </svg>
                      Configure Zones
                    </Link>
                  </div>
                  <div className="col-6 mb-3">
                    <Link href="/cybersecurity" className="btn btn-danger" style={{ width: '100%' }}>
                      <svg style={{ width: 16, height: 16 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                      Security Settings
                    </Link>
                  </div>
                  <div className="col-6 mb-3">
                    <Link href="/weather" className="btn btn-primary" style={{ width: '100%' }}>
                      <svg style={{ width: 16, height: 16 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
                      </svg>
                      Weather Config
                    </Link>
                  </div>
                  <div className="col-6 mb-3">
                    <Link href="/power" className="btn btn-warning" style={{ width: '100%' }}>
                      <svg style={{ width: 16, height: 16 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      Power Grid
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* System State from Coordinator */}
        <div className="row">
          <div className="col-12">
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">
                  <svg style={{ width: 18, height: 18, marginRight: 8 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  System State (from Coordinator)
                </h3>
                <div className="card-tools">
                  <Link href="/coordinator" className="btn btn-sm btn-primary">Configure</Link>
                </div>
              </div>
              <div className="card-body">
                <div style={{ display: 'flex', gap: '2rem' }}>
                  <div className="info-box" style={{ flex: 1, marginBottom: 0 }}>
                    <span className="info-box-icon bg-danger">🛡️</span>
                    <div className="info-box-content">
                      <span className="info-box-text">Threat Level</span>
                      <span className="info-box-number">{coordinatorState.threatLevel || "Loading..."}</span>
                    </div>
                  </div>
                  <div className="info-box" style={{ flex: 1, marginBottom: 0 }}>
                    <span className="info-box-icon bg-warning">⚡</span>
                    <div className="info-box-content">
                      <span className="info-box-text">Grid Status</span>
                      <span className="info-box-number">{coordinatorState.gridStatus || "Loading..."}</span>
                    </div>
                  </div>
                  <div className="info-box" style={{ flex: 1, marginBottom: 0 }}>
                    <span className="info-box-icon bg-info">🤖</span>
                    <div className="info-box-content">
                      <span className="info-box-text">Last Decision</span>
                      <span className="info-box-number" style={{ fontSize: '1rem' }}>{coordinatorState.lastDecision || "Loading..."}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Priority Hierarchy */}
        <div className="row">
          <div className="col-12">
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">
                  <svg style={{ width: 18, height: 18, marginRight: 8 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                  </svg>
                  Priority Hierarchy
                </h3>
                <div className="card-tools">
                  <Link href="/coordinator" className="btn btn-sm btn-primary">Configure</Link>
                </div>
              </div>
              <div className="card-body">
                <p className="text-muted mb-3">
                  The Coordinator uses this priority hierarchy to make decisions when multiple concerns are present.
                </p>
                <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                  {[
                    { level: 1, name: "CYBER CRITICAL", color: "bg-danger" },
                    { level: 2, name: "POWER OUTAGE", color: "bg-danger" },
                    { level: 3, name: "WEATHER DISASTER", color: "bg-warning" },
                    { level: 4, name: "CYBER HIGH", color: "bg-warning" },
                    { level: 5, name: "GRID UNSTABLE", color: "bg-info" },
                    { level: 6, name: "CYBER MEDIUM", color: "bg-info" },
                    { level: 7, name: "WEATHER ADVISORY", color: "bg-secondary" },
                    { level: 8, name: "OPTIMIZATION", color: "bg-secondary" },
                    { level: 9, name: "NOMINAL", color: "bg-success" },
                  ].map((priority) => (
                    <div
                      key={priority.level}
                      className={`${priority.color}`}
                      style={{
                        padding: '0.5rem 1rem',
                        borderRadius: '0.25rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        fontSize: '0.875rem'
                      }}
                    >
                      <span style={{
                        width: 24,
                        height: 24,
                        borderRadius: '50%',
                        background: 'rgba(255,255,255,0.3)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 700
                      }}>
                        {priority.level}
                      </span>
                      {priority.name}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

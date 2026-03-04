"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

// Navigation items matching AdminLTE structure
const navItems = [
    {
        name: "Dashboard",
        href: "/",
        icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6",
    },
    {
        name: "Zone Config",
        href: "/zones",
        icon: "M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7",
    },
    {
        name: "Cybersecurity",
        href: "/cybersecurity",
        icon: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z",
    },
    {
        name: "Weather",
        href: "/weather",
        icon: "M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z",
    },
    {
        name: "Power Grid",
        href: "/power",
        icon: "M13 10V3L4 14h7v7l9-11h-7z",
    },
    {
        name: "Coordinator",
        href: "/coordinator",
        icon: "M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4",
    },
    {
        name: "All Agents",
        href: "/agents",
        icon: "M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z",
    },
];

export default function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className="main-sidebar">
            {/* Brand Logo */}
            <Link href="/" className="brand-link">
                <div className="brand-image bg-primary" style={{
                    width: 33,
                    height: 33,
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                }}>
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                </div>
                <span className="font-weight-bold">AI Lighting</span>
            </Link>

            {/* Sidebar Navigation */}
            <nav className="mt-2" style={{ padding: '0.5rem' }}>
                <ul className="nav-sidebar" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                    {navItems.map((item) => {
                        const isActive = pathname === item.href;
                        return (
                            <li key={item.href} className="nav-item">
                                <Link
                                    href={item.href}
                                    className={`nav-link ${isActive ? "active" : ""}`}
                                >
                                    <svg className="nav-icon" style={{ width: 20, height: 20 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={item.icon} />
                                    </svg>
                                    <span>{item.name}</span>
                                </Link>
                            </li>
                        );
                    })}
                </ul>
            </nav>

            {/* Sidebar Footer - System Status */}
            <div style={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                right: 0,
                padding: '1rem',
                borderTop: '1px solid rgba(255,255,255,0.1)'
            }}>
                <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)', marginBottom: '0.5rem' }}>
                    SYSTEM STATUS
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                    {[
                        { name: 'Cyber', status: 'online' },
                        { name: 'Weather', status: 'online' },
                        { name: 'Power', status: 'online' },
                        { name: 'Coord', status: 'online' },
                    ].map((service) => (
                        <div key={service.name} style={{ display: 'flex', alignItems: 'center', fontSize: '0.75rem', color: 'rgba(255,255,255,0.8)' }}>
                            <span className={`status-dot ${service.status}`}></span>
                            {service.name}
                        </div>
                    ))}
                </div>
            </div>
        </aside>
    );
}

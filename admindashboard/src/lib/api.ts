// API configuration and utilities for connecting to backend services

// Backend ports
export const API_PORTS = {
    cybersecurity: 8000,
    weather: 8001,
    power: 8002,
    coordinator: 8004,
} as const;

export const API_BASE = (service: keyof typeof API_PORTS) =>
    `http://localhost:${API_PORTS[service]}`;

export const WS_BASE = (service: keyof typeof API_PORTS) =>
    `ws://localhost:${API_PORTS[service]}`;

// Generic fetch with error handling
async function apiFetch<T>(url: string, options?: RequestInit): Promise<T | null> {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 8000);

        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            console.error(`API error: ${response.status} ${response.statusText}`);
            return null;
        }

        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch ${url}:`, error);
        return null;
    }
}

// Health check for a service
export async function checkHealth(service: keyof typeof API_PORTS): Promise<boolean> {
    const result = await apiFetch<{ status: string }>(`${API_BASE(service)}/health`);
    return result?.status === "ok" || result?.status === "healthy";
}

// ============ Cybersecurity API ============

export interface DDoSConfig {
    thresholds: {
        normal_rps_min: number;
        normal_rps_max: number;
        moderate_rps: number;
        high_rps: number;
        critical_rps: number;
        syn_flood_threshold: number;
        http_flood_threshold: number;
        packet_size_anomaly_min: number;
        packet_size_anomaly_max: number;
        requests_per_ip_normal: number;
        requests_per_ip_suspicious: number;
        unique_ips_normal: number;
        unique_ips_attack: number;
        geo_concentration_threshold: number;
        response_time_normal_ms: number;
        failed_request_rate: number;
    };
    detection_window: number;
    agent_timeout: number;
    attack_types: string[];
}

export interface MalwareConfig {
    thresholds: {
        file_encryption_rate: number;
        suspicious_process_count: number;
        cpu_usage_threshold: number;
        memory_usage_threshold: number;
        outbound_connections: number;
        file_modifications: number;
        network_upload_mb: number;
    };
    c2_suspicious_ports: number[];
    suspicious_extensions: string[];
    suspicious_processes: string[];
    known_families: string[];
    agent_timeout: number;
    detection_types: string[];
}

export interface CyberAgentStatus {
    agents: {
        ddos_detection: { status: string; capabilities: string[] };
        malware_detection: { status: string; capabilities: string[] };
    };
    graph_status: string;
    system_mode: string;
    timestamp: string;
}

export interface SimulatorStatus {
    is_running: boolean;
    uptime_seconds: number;
    events_generated: number;
    events_per_second: number;
    active_attacks: { type: string; zone: string; remaining_seconds: number }[];
    zone_count: number;
    device_count: number;
}

export interface ZoneInfo {
    id: string;
    name: string;
    area: string;
    type: string;
    center: [number, number];
    bounds: [[number, number], [number, number]];
    device_count: number;
    priority: string;
    color: string;
    devices: {
        device_id: string;
        zone_id: string;
        zone_name: string;
        lat: number;
        lng: number;
        status: string;
        brightness: number;
    }[];
}

export interface TimelineBucket {
    time: string;
    total: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
    ddos: number;
    malware: number;
    normal: number;
}

export interface MetricsSummary {
    window_seconds: number;
    total_events: number;
    events_per_second: number;
    by_severity: Record<string, number>;
    by_event_type: Record<string, number>;
    by_zone: Record<string, number>;
    suspicious_events: number;
    threat_level: string;
    timestamp: string;
}

// ── GET endpoints ──

export async function getCyberDDoSConfig(): Promise<DDoSConfig | null> {
    return apiFetch<DDoSConfig>(`${API_BASE("cybersecurity")}/config/ddos`);
}

export async function getCyberMalwareConfig(): Promise<MalwareConfig | null> {
    return apiFetch<MalwareConfig>(`${API_BASE("cybersecurity")}/config/malware`);
}

export async function getCyberAgentStatus(): Promise<CyberAgentStatus | null> {
    return apiFetch<CyberAgentStatus>(`${API_BASE("cybersecurity")}/status/agents`);
}

export async function getSimulatorStatus(): Promise<SimulatorStatus | null> {
    return apiFetch<SimulatorStatus>(`${API_BASE("cybersecurity")}/simulator/status`);
}

export async function getSimulatorZones(): Promise<ZoneInfo[] | null> {
    return apiFetch<ZoneInfo[]>(`${API_BASE("cybersecurity")}/simulator/zones`);
}

export async function getMetricsTimeline(window = 300, bucket = 10): Promise<TimelineBucket[] | null> {
    return apiFetch<TimelineBucket[]>(`${API_BASE("cybersecurity")}/metrics/timeline?window=${window}&bucket=${bucket}`);
}

export async function getMetricsSummary(): Promise<MetricsSummary | null> {
    return apiFetch<MetricsSummary>(`${API_BASE("cybersecurity")}/metrics/summary`);
}

// ── PUT endpoints (save config) ──

export async function putDDoSConfig(data: Partial<DDoSConfig["thresholds"]> & { detection_window?: number; agent_timeout?: number }): Promise<any> {
    return apiFetch(`${API_BASE("cybersecurity")}/config/ddos`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    });
}

export async function putMalwareConfig(data: Partial<MalwareConfig["thresholds"]> & {
    c2_suspicious_ports?: number[];
    suspicious_extensions?: string[];
    suspicious_processes?: string[];
    known_families?: string[];
    agent_timeout?: number;
}): Promise<any> {
    return apiFetch(`${API_BASE("cybersecurity")}/config/malware`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    });
}

export async function resetConfig(): Promise<any> {
    return apiFetch(`${API_BASE("cybersecurity")}/config/reset`, { method: "POST" });
}

// ── Simulator control ──

export async function startSimulator(): Promise<any> {
    return apiFetch(`${API_BASE("cybersecurity")}/simulator/start`, { method: "POST" });
}

export async function stopSimulator(): Promise<any> {
    return apiFetch(`${API_BASE("cybersecurity")}/simulator/stop`, { method: "POST" });
}

export async function triggerAttack(type: string, zone: string, intensity: number, duration: number): Promise<any> {
    return apiFetch(`${API_BASE("cybersecurity")}/simulator/attack`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type, zone, intensity, duration }),
    });
}

export async function addZone(zoneData: any): Promise<any> {
    return apiFetch(`${API_BASE("cybersecurity")}/simulator/zones`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(zoneData),
    });
}

// ============ Weather API ============
export interface WeatherConfig {
    success: boolean;
    config: {
        zones: string[];
        update_intervals: Record<string, string>;
        thresholds: {
            wind_speed: number;
            visibility: number;
            precipitation: number;
        };
        emergency_thresholds: {
            wind_speed: number;
            precipitation: number;
        };
    };
    timestamp: string;
}

export interface WeatherStatus {
    status: string;
    agents: Record<string, { status: string; last_run?: string }>;
    graph_status: string;
    timestamp: string;
}

export async function getWeatherConfig(): Promise<WeatherConfig | null> {
    return apiFetch<WeatherConfig>(`${API_BASE("weather")}/weather/config`);
}

export async function getWeatherStatus(): Promise<WeatherStatus | null> {
    return apiFetch<WeatherStatus>(`${API_BASE("weather")}/weather/status`);
}

// ============ Power API ============
export interface PowerSystemStatus {
    service_info: {
        name: string;
        version: string;
        uptime: string;
        timestamp: string;
    };
    agents_status: Record<string, string>;
    workflow_status: {
        active_workflows: number;
        completed_workflows: number;
        last_execution: string | null;
    };
    system_health: {
        kafka_connected: boolean;
        agents_operational: boolean;
        memory_usage: string;
        error_rate: string;
    };
    grid_status?: string;
    current_load?: number;
    voltage?: number;
    frequency?: number;
    active_nodes?: number;
    total_nodes?: number;
}

export async function getPowerSystemStatus(): Promise<PowerSystemStatus | null> {
    return apiFetch<PowerSystemStatus>(`${API_BASE("power")}/system/status`);
}

// ============ Coordinator API ============
export interface CoordinatorState {
    cybersecurity?: {
        threat_level?: string;
        alerts?: unknown[];
    };
    weather?: {
        conditions?: Record<string, unknown>;
    };
    power?: {
        grid_status?: string;
    };
    last_decision?: string;
    lighting_state?: Record<string, unknown>;
    system_mode?: string;
    decision_count?: number;
}

export interface CoordinatorPriorities {
    priorities: Record<string, number>;
}

export async function getCoordinatorState(): Promise<CoordinatorState | null> {
    return apiFetch<CoordinatorState>(`${API_BASE("coordinator")}/state`);
}

export async function getCoordinatorPriorities(): Promise<CoordinatorPriorities | null> {
    return apiFetch<CoordinatorPriorities>(`${API_BASE("coordinator")}/priorities`);
}

// ============ All Services Health Check ============
export interface ServiceHealth {
    name: string;
    port: number;
    status: "online" | "offline";
    latency?: number;
}

export async function getAllServicesHealth(): Promise<ServiceHealth[]> {
    const services: { name: string; port: number; service: keyof typeof API_PORTS }[] = [
        { name: "Cybersecurity", port: 8000, service: "cybersecurity" },
        { name: "Weather", port: 8001, service: "weather" },
        { name: "Power Grid", port: 8002, service: "power" },
        { name: "Coordinator", port: 8004, service: "coordinator" },
    ];

    const results = await Promise.all(
        services.map(async (svc) => {
            const start = Date.now();
            const isOnline = await checkHealth(svc.service);
            const latency = Date.now() - start;

            return {
                name: svc.name,
                port: svc.port,
                status: isOnline ? "online" as const : "offline" as const,
                latency: isOnline ? latency : undefined,
            };
        })
    );

    return results;
}

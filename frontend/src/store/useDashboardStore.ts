import { create } from 'zustand';

// Views
export type AgentView = 'cybersecurity' | 'power' | 'weather' | 'overview';

// Scenarios / controls
export type WeatherScenario = 'clear' | 'heavy-rain' | 'dense-fog' | 'cyclone';
export type CyberAttackType = 'ransomware' | 'brute-force' | null;
export type BlackoutScenario = 'weather-catastrophe' | 'cyber-major' | 'equipment-minor' | null;
export type BlackoutCause = 'grid-failure' | 'cyber-attack' | 'weather-event' | 'equipment-failure';

// Active attack info received from cybersecurity WebSocket
export interface ActiveAttack {
  attackId: string;
  attackType: string;
  zoneId: string;
  zoneName: string;
  intensity: number;
  startedAt: number; // timestamp ms
  severity: string;
}

interface DashboardState {
  selectedAgentView: AgentView;
  setSelectedAgentView: (view: AgentView) => void;

  // Live/system indicator
  systemStatus: 'OPERATIONAL' | 'WARNING' | 'CRITICAL';
  setSystemStatus: (status: 'OPERATIONAL' | 'WARNING' | 'CRITICAL') => void;

  // Weather
  weatherScenario: WeatherScenario;
  setWeatherScenario: (scenario: WeatherScenario) => void;

  // Cyber
  cyberTargetZone: string | null;
  setCyberTargetZone: (zone: string | null) => void;
  cyberAttackType: CyberAttackType;
  setCyberAttackType: (type: CyberAttackType) => void;

  // Active attacks from cybersecurity WebSocket
  activeAttacks: Record<string, ActiveAttack>; // keyed by zoneId
  addAttack: (attack: ActiveAttack) => void;
  clearAttack: (zoneId: string) => void;
  clearAllAttacks: () => void;

  // Power
  blackoutScenario: BlackoutScenario;
  setBlackoutScenario: (scenario: BlackoutScenario) => void;
  blackoutCause: BlackoutCause;
  setBlackoutCause: (cause: BlackoutCause) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  selectedAgentView: 'overview',
  setSelectedAgentView: (view) => set({ selectedAgentView: view }),

  systemStatus: 'OPERATIONAL',
  setSystemStatus: (status) => set({ systemStatus: status }),

  weatherScenario: 'clear',
  setWeatherScenario: (scenario) => set({ weatherScenario: scenario }),

  cyberTargetZone: null,
  setCyberTargetZone: (zone) => set({ cyberTargetZone: zone }),
  cyberAttackType: null,
  setCyberAttackType: (type) => set({ cyberAttackType: type }),

  // Active attacks — auto-escalate system status
  activeAttacks: {},
  addAttack: (attack) => set((state) => {
    const updated = { ...state.activeAttacks, [attack.zoneId]: attack };
    return {
      activeAttacks: updated,
      systemStatus: Object.keys(updated).length > 0 ? 'CRITICAL' : state.systemStatus,
    };
  }),
  clearAttack: (zoneId) => set((state) => {
    const updated = { ...state.activeAttacks };
    delete updated[zoneId];
    return {
      activeAttacks: updated,
      systemStatus: Object.keys(updated).length === 0 ? 'OPERATIONAL' : 'WARNING',
    };
  }),
  clearAllAttacks: () => set({ activeAttacks: {}, systemStatus: 'OPERATIONAL' }),

  blackoutScenario: null,
  setBlackoutScenario: (scenario) => set({ blackoutScenario: scenario }),
  blackoutCause: 'grid-failure',
  setBlackoutCause: (cause) => set({ blackoutCause: cause }),
}));

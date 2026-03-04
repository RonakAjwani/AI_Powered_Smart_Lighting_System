/**
 * Advanced Simulation Scenario Engine
 * Creates realistic, physics-based simulation scenarios with cascading effects
 */

import { PowerGridTopology, updateGridState, getCascadingFailure } from './streetLightGenerator';
import { Incident } from '@/components/map/IncidentMarkers';
import {
  simulateWeatherEvent,
  executeWeatherWorkflow,
  simulateCyberAttack,
  runSecurityAnalysis,
  triggerIntrusionResponse,
  triggerPowerOutage,
  detectPowerOutages,
  runEnergyOptimization
} from './simulators';
import { logAgentActivity } from '@/components/shared/AgentActivityFeed';
import toast from 'react-hot-toast';

export interface ScenarioStep {
  id: string;
  time: number; // milliseconds from start
  agent: string;
  action: string;
  narration: string;
  effects: {
    type: 'GRID_UPDATE' | 'INCIDENT' | 'API_CALL' | 'UI_UPDATE';
    data: any;
  }[];
  execute: (grid: PowerGridTopology) => Promise<{
    updatedGrid: PowerGridTopology;
    incidents: Incident[];
  }>;
}

export interface AdvancedScenario {
  id: string;
  name: string;
  description: string;
  icon: string;
  difficulty: 'EASY' | 'MEDIUM' | 'HARD' | 'EXTREME';
  duration: number; // seconds
  objectives: string[];
  steps: ScenarioStep[];
  initialConditions?: {
    weatherCondition?: string;
    gridLoad?: number; // percentage
    securityLevel?: string;
  };
}

/**
 * Scenario 1: Cascading Power Failure
 * Realistic power grid failure with cascading effects
 */
export const cascadingPowerFailureScenario: AdvancedScenario = {
  id: 'cascading-power-failure',
  name: 'Cascading Power Grid Failure',
  description: 'Transformer overload triggers cascading failures across multiple zones',
  icon: '⚡',
  difficulty: 'HARD',
  duration: 45,
  objectives: [
    'Detect initial overload',
    'Isolate affected circuits',
    'Reroute power to healthy zones',
    'Restore critical infrastructure',
    'Prevent complete blackout',
  ],
  steps: [
    {
      id: 'initial-overload',
      time: 0,
      agent: 'Grid Monitor',
      action: 'Detecting transformer overload',
      narration: '⚠️ Transformer in Downtown shows dangerous overload - 115% capacity',
      effects: [
        { type: 'GRID_UPDATE', data: { zoneIndex: 0, overload: true } },
      ],
      execute: async (grid) => {
        logAgentActivity('Grid Monitor', 'Critical overload detected in Downtown substation', 'running');

        // Simulate transformer overload in Downtown zone
        const downtownZone = grid.zones.find(z => z.type === 'DOWNTOWN')!;
        const updatedGrid = updateGridState(grid, {
          zoneId: downtownZone.id,
          incident: 'EQUIPMENT_FAILURE',
        });

        await new Promise(resolve => setTimeout(resolve, 2000));
        logAgentActivity('Grid Monitor', 'Overload confirmed - immediate action required', 'error');

        return {
          updatedGrid,
          incidents: [{
            id: `overload-${Date.now()}`,
            type: 'EQUIPMENT_FAILURE' as const,
            severity: 'HIGH' as const,
            location: downtownZone.center,
            affectedRadius: 1.5,
            timestamp: new Date(),
            description: 'Transformer overload in Downtown sector',
            affectedLights: Math.floor(downtownZone.totalLights * 0.4),
            status: 'ACTIVE' as const,
          }],
        };
      },
    },
    {
      id: 'circuit-failure',
      time: 5000,
      agent: 'Protection System',
      action: 'Circuit breaker tripped',
      narration: '🔌 Circuit breaker trips to prevent damage - 120 lights offline',
      effects: [
        { type: 'API_CALL', data: { endpoint: 'triggerPowerOutage' } },
      ],
      execute: async (grid) => {
        logAgentActivity('Protection System', 'Emergency circuit breaker activation', 'running');

        const downtownZone = grid.zones.find(z => z.type === 'DOWNTOWN')!;

        // Trigger actual backend API
        try {
          await triggerPowerOutage([downtownZone.id.toLowerCase()]);
        } catch (error) {
          console.error('API call failed:', error);
        }

        // Update local grid state
        const updatedGrid = updateGridState(grid, {
          zoneId: downtownZone.id,
          incident: 'POWER_OUTAGE',
        });

        await new Promise(resolve => setTimeout(resolve, 2000));
        logAgentActivity('Protection System', 'Circuit isolated - investigating cascading risk', 'completed');

        return { updatedGrid, incidents: [] };
      },
    },
    {
      id: 'cascade-detection',
      time: 10000,
      agent: 'AI Load Predictor',
      action: 'Detecting cascade risk',
      narration: '🧠 AI predicts 60% chance of cascade to adjacent Financial District',
      effects: [],
      execute: async (grid) => {
        logAgentActivity('AI Load Predictor', 'Running cascade probability analysis', 'running');

        await new Promise(resolve => setTimeout(resolve, 3000));
        logAgentActivity('AI Load Predictor', 'HIGH RISK: Adjacent zones approaching overload', 'error');

        return { updatedGrid: grid, incidents: [] };
      },
    },
    {
      id: 'cascade-occurs',
      time: 15000,
      agent: 'System Alert',
      action: 'Cascade failure detected',
      narration: '🚨 CRITICAL: Load shifted to Financial District causes secondary failure',
      effects: [
        { type: 'GRID_UPDATE', data: { cascadeZone: 1 } },
      ],
      execute: async (grid) => {
        logAgentActivity('System Alert', 'CASCADE IN PROGRESS - Multiple zones affected', 'error');

        const financialZone = grid.zones.find(z => z.name.includes('Financial'))!;

        const updatedGrid = updateGridState(grid, {
          zoneId: financialZone.id,
          incident: 'POWER_OUTAGE',
        });

        return {
          updatedGrid,
          incidents: [{
            id: `cascade-${Date.now()}`,
            type: 'POWER_OUTAGE' as const,
            severity: 'CRITICAL' as const,
            location: financialZone.center,
            affectedRadius: 2.0,
            timestamp: new Date(),
            description: 'Cascading failure reached Financial District',
            affectedLights: Math.floor(financialZone.totalLights * 0.7),
            status: 'ACTIVE' as const,
          }],
        };
      },
    },
    {
      id: 'outage-detection',
      time: 18000,
      agent: 'Outage Detector',
      action: 'Mapping affected areas',
      narration: '🗺️ 340 lights offline across 2 zones - impact assessment in progress',
      effects: [
        { type: 'API_CALL', data: { endpoint: 'detectPowerOutages' } },
      ],
      execute: async (grid) => {
        logAgentActivity('Outage Detector', 'Scanning grid for all affected areas', 'running');

        try {
          await detectPowerOutages();
        } catch (error) {
          console.error('API call failed:', error);
        }

        await new Promise(resolve => setTimeout(resolve, 2000));
        logAgentActivity('Outage Detector', 'Outage mapping complete - initiating recovery', 'completed');

        return { updatedGrid: grid, incidents: [] };
      },
    },
    {
      id: 'emergency-reroute',
      time: 24000,
      agent: 'Energy Router',
      action: 'Emergency power rerouting',
      narration: '🔀 Activating backup substations and rerouting power to critical zones',
      effects: [],
      execute: async (grid) => {
        logAgentActivity('Energy Router', 'Calculating optimal power distribution', 'running');

        await new Promise(resolve => setTimeout(resolve, 2500));
        logAgentActivity('Energy Router', 'Emergency rerouting in progress', 'running');

        // Partially restore some lights
        const updatedGrid = { ...grid };
        const affectedZones = updatedGrid.zones.filter(z =>
          z.type === 'DOWNTOWN' || z.name.includes('Financial')
        );

        affectedZones.forEach(zone => {
          const zoneLights = updatedGrid.streetLights.filter(l => l.zoneId === zone.id);
          const criticalLights = zoneLights.filter(l => l.securityLevel === 'HIGH' || l.securityLevel === 'CRITICAL');

          // Restore critical lights
          criticalLights.forEach(light => {
            light.status = 'ONLINE';
            light.brightness = 80;
            light.voltage = 210; // Reduced voltage
          });
        });

        await new Promise(resolve => setTimeout(resolve, 2000));
        logAgentActivity('Energy Router', 'Critical infrastructure restored', 'completed');

        return { updatedGrid, incidents: [] };
      },
    },
    {
      id: 'load-optimization',
      time: 30000,
      agent: 'Load Optimizer',
      action: 'Optimizing grid load',
      narration: '⚖️ Balancing load across healthy substations to prevent further failures',
      effects: [
        { type: 'API_CALL', data: { endpoint: 'runEnergyOptimization' } },
      ],
      execute: async (grid) => {
        logAgentActivity('Load Optimizer', 'Running AI-powered load optimization', 'running');

        try {
          await runEnergyOptimization();
        } catch (error) {
          console.error('API call failed:', error);
        }

        await new Promise(resolve => setTimeout(resolve, 2500));
        logAgentActivity('Load Optimizer', 'Grid load balanced - system stabilizing', 'completed');

        return { updatedGrid: grid, incidents: [] };
      },
    },
    {
      id: 'full-restoration',
      time: 38000,
      agent: 'Recovery Coordinator',
      action: 'Full system restoration',
      narration: '✅ Repairs complete - bringing all zones back online systematically',
      effects: [],
      execute: async (grid) => {
        logAgentActivity('Recovery Coordinator', 'Initiating full system restoration', 'running');

        // Restore all lights
        const updatedGrid = { ...grid };
        updatedGrid.streetLights.forEach(light => {
          if (light.status === 'OFFLINE') {
            light.status = 'ONLINE';
            light.brightness = 75 + Math.random() * 20;
            light.voltage = 220 + (Math.random() - 0.5) * 10;
            light.current = light.powerRating / light.voltage;
          }
        });

        await new Promise(resolve => setTimeout(resolve, 3000));
        logAgentActivity('Recovery Coordinator', 'All systems operational - crisis resolved', 'completed');

        return { updatedGrid, incidents: [] };
      },
    },
  ],
};

/**
 * Scenario 2: Coordinated Cyber Attack with Propagation
 */
export const coordinatedCyberAttackScenario: AdvancedScenario = {
  id: 'coordinated-cyber-attack',
  name: 'Coordinated Multi-Vector Cyber Attack',
  description: 'Sophisticated ransomware spreads through network, targeting critical infrastructure',
  icon: '🛡️',
  difficulty: 'EXTREME',
  duration: 50,
  objectives: [
    'Detect initial intrusion',
    'Identify attack vector and malware type',
    'Isolate compromised systems',
    'Stop malware propagation',
    'Restore system integrity',
  ],
  steps: [
    {
      id: 'initial-intrusion',
      time: 0,
      agent: 'Intrusion Detection',
      action: 'Suspicious network activity detected',
      narration: '🚨 Anomalous traffic from external IP targeting controller systems',
      effects: [],
      execute: async (grid) => {
        logAgentActivity('Intrusion Detection', 'Analyzing suspicious network patterns', 'running');

        await new Promise(resolve => setTimeout(resolve, 2000));
        logAgentActivity('Intrusion Detection', 'ALERT: Intrusion attempt confirmed', 'error');

        return { updatedGrid: grid, incidents: [] };
      },
    },
    {
      id: 'malware-deployment',
      time: 5000,
      agent: 'Threat Analyzer',
      action: 'Malware signature detected',
      narration: '💻 Ransomware variant identified - targeting lighting control systems',
      effects: [
        { type: 'API_CALL', data: { endpoint: 'simulateCyberAttack' } },
      ],
      execute: async (grid) => {
        logAgentActivity('Threat Analyzer', 'Performing deep packet inspection', 'running');

        try {
          await simulateCyberAttack('malware');
        } catch (error) {
          console.error('API call failed:', error);
        }

        const downtownZone = grid.zones.find(z => z.type === 'DOWNTOWN')!;

        const updatedGrid = updateGridState(grid, {
          zoneId: downtownZone.id,
          incident: 'CYBER_ATTACK',
        });

        await new Promise(resolve => setTimeout(resolve, 2500));
        logAgentActivity('Threat Analyzer', 'Malware classified: Advanced Persistent Threat', 'error');

        return {
          updatedGrid,
          incidents: [{
            id: `cyber-initial-${Date.now()}`,
            type: 'CYBER_ATTACK' as const,
            severity: 'HIGH' as const,
            location: downtownZone.center,
            affectedRadius: 1.0,
            timestamp: new Date(),
            description: 'Ransomware detected in Downtown control systems',
            affectedLights: Math.floor(downtownZone.totalLights * 0.2),
            status: 'ACTIVE' as const,
          }],
        };
      },
    },
    {
      id: 'propagation-detected',
      time: 12000,
      agent: 'Network Monitor',
      action: 'Malware propagation detected',
      narration: '📡 Malware spreading through mesh network - 3 additional zones at risk',
      effects: [],
      execute: async (grid) => {
        logAgentActivity('Network Monitor', 'Tracking malware propagation paths', 'running');

        // Find a light in downtown to start cascading from
        const downtownLights = grid.streetLights.filter(l => l.zoneId.includes('01'));
        if (downtownLights.length === 0) {
          return { updatedGrid: grid, incidents: [] };
        }

        const originLight = downtownLights[0];
        const affectedLightIds = getCascadingFailure(grid, originLight.id, 4);

        const updatedGrid = { ...grid };
        affectedLightIds.forEach(lightId => {
          const light = updatedGrid.streetLights.find(l => l.id === lightId);
          if (light) {
            light.status = 'WARNING';
            light.brightness = Math.random() * 100; // Random brightness (malware effect)
          }
        });

        await new Promise(resolve => setTimeout(resolve, 3000));
        logAgentActivity('Network Monitor', `${affectedLightIds.length} systems compromised`, 'error');

        return { updatedGrid, incidents: [] };
      },
    },
    {
      id: 'isolation-attempt',
      time: 18000,
      agent: 'Security Response',
      action: 'Network segmentation activated',
      narration: '🔒 Isolating compromised zones from main network',
      effects: [
        { type: 'API_CALL', data: { endpoint: 'triggerIntrusionResponse' } },
      ],
      execute: async (grid) => {
        logAgentActivity('Security Response', 'Activating network isolation protocols', 'running');

        try {
          await triggerIntrusionResponse();
        } catch (error) {
          console.error('API call failed:', error);
        }

        await new Promise(resolve => setTimeout(resolve, 2500));
        logAgentActivity('Security Response', 'Compromised segments isolated', 'completed');

        return { updatedGrid: grid, incidents: [] };
      },
    },
    {
      id: 'malware-analysis',
      time: 25000,
      agent: 'Malware Lab',
      action: 'Analyzing malware behavior',
      narration: '🔬 Reverse engineering malware to develop countermeasures',
      effects: [
        { type: 'API_CALL', data: { endpoint: 'runSecurityAnalysis' } },
      ],
      execute: async (grid) => {
        logAgentActivity('Malware Lab', 'Deep analysis of malware payload', 'running');

        try {
          await runSecurityAnalysis();
        } catch (error) {
          console.error('API call failed:', error);
        }

        await new Promise(resolve => setTimeout(resolve, 4000));
        logAgentActivity('Malware Lab', 'Decryption key recovered - preparing patch', 'completed');

        return { updatedGrid: grid, incidents: [] };
      },
    },
    {
      id: 'patch-deployment',
      time: 33000,
      agent: 'Patch Manager',
      action: 'Deploying security patches',
      narration: '🛠️ Rolling out patches to all affected systems',
      effects: [],
      execute: async (grid) => {
        logAgentActivity('Patch Manager', 'Deploying countermeasures to compromised systems', 'running');

        const updatedGrid = { ...grid };

        // Fix compromised lights
        updatedGrid.streetLights
          .filter(l => l.status === 'WARNING')
          .forEach(light => {
            light.status = 'MAINTENANCE';
            light.brightness = 50;
          });

        await new Promise(resolve => setTimeout(resolve, 3000));
        logAgentActivity('Patch Manager', 'Security patches applied successfully', 'completed');

        return { updatedGrid, incidents: [] };
      },
    },
    {
      id: 'system-restoration',
      time: 40000,
      agent: 'System Recovery',
      action: 'Restoring normal operations',
      narration: '✅ All systems clean - returning to normal operation mode',
      effects: [],
      execute: async (grid) => {
        logAgentActivity('System Recovery', 'Verifying system integrity and restoring services', 'running');

        const updatedGrid = { ...grid };

        // Restore all lights to normal
        updatedGrid.streetLights.forEach(light => {
          if (light.status !== 'ONLINE') {
            light.status = 'ONLINE';
            light.brightness = 75 + Math.random() * 20;
          }
        });

        await new Promise(resolve => setTimeout(resolve, 3000));
        logAgentActivity('System Recovery', 'Threat neutralized - all systems operational', 'completed');

        return { updatedGrid, incidents: [] };
      },
    },
  ],
};

/**
 * Scenario 3: Hurricane with Multi-System Impact
 */
export const hurricaneMultiSystemScenario: AdvancedScenario = {
  id: 'hurricane-multi-system',
  name: 'Category 4 Hurricane Multi-System Impact',
  description: 'Severe hurricane affects weather, power, and security systems simultaneously',
  icon: '🌪️',
  difficulty: 'EXTREME',
  duration: 60,
  objectives: [
    'Activate pre-storm protocols',
    'Maximize visibility for emergency services',
    'Manage cascading power issues',
    'Maintain security during chaos',
    'Coordinate multi-agent response',
  ],
  initialConditions: {
    weatherCondition: 'clear',
    gridLoad: 80,
    securityLevel: 'normal',
  },
  steps: [
    {
      id: 'storm-warning',
      time: 0,
      agent: 'Weather Prediction',
      action: 'Hurricane warning issued',
      narration: '🌪️ Category 4 hurricane detected 50 miles offshore - landfall in 2 hours',
      effects: [],
      execute: async (grid) => {
        logAgentActivity('Weather Prediction', 'Hurricane tracking and impact modeling', 'running');

        await new Promise(resolve => setTimeout(resolve, 2000));
        logAgentActivity('Weather Prediction', 'HIGH RISK: Direct hit predicted for city center', 'error');

        return { updatedGrid: grid, incidents: [] };
      },
    },
    {
      id: 'pre-storm-protocol',
      time: 5000,
      agent: 'Emergency Coordinator',
      action: 'Activating pre-storm protocols',
      narration: '🚨 Emergency mode activated - all systems preparing for hurricane impact',
      effects: [
        { type: 'API_CALL', data: { endpoint: 'executeWeatherWorkflow' } },
      ],
      execute: async (grid) => {
        logAgentActivity('Emergency Coordinator', 'Coordinating all systems for hurricane response', 'running');

        try {
          await executeWeatherWorkflow('emergency');
        } catch (error) {
          console.error('API call failed:', error);
        }

        // Set all lights to maximum brightness
        const updatedGrid = { ...grid };
        updatedGrid.streetLights.forEach(light => {
          if (light.status === 'ONLINE') {
            light.brightness = 100;
          }
        });

        await new Promise(resolve => setTimeout(resolve, 2500));
        logAgentActivity('Emergency Coordinator', 'Pre-storm protocols activated', 'completed');

        return { updatedGrid, incidents: [] };
      },
    },
    // Additional steps would follow similar pattern...
    // For brevity, showing key steps only
  ],
};

export const advancedScenarios: AdvancedScenario[] = [
  cascadingPowerFailureScenario,
  coordinatedCyberAttackScenario,
  hurricaneMultiSystemScenario,
];

/**
 * Scenario Runner
 */
export class ScenarioRunner {
  private isRunning = false;
  private currentScenario: AdvancedScenario | null = null;
  private abortController: AbortController | null = null;
  private grid: PowerGridTopology | null = null;
  private onGridUpdate: ((grid: PowerGridTopology, incidents: Incident[]) => void) | null = null;

  setGrid(grid: PowerGridTopology) {
    this.grid = grid;
  }

  setOnGridUpdate(callback: (grid: PowerGridTopology, incidents: Incident[]) => void) {
    this.onGridUpdate = callback;
  }

  async runScenario(scenario: AdvancedScenario): Promise<void> {
    if (this.isRunning || !this.grid) {
      toast.error('Cannot start scenario');
      return;
    }

    this.isRunning = true;
    this.currentScenario = scenario;
    this.abortController = new AbortController();

    toast.success(`🎬 Starting: ${scenario.name}`, { duration: 3000 });

    try {
      for (const step of scenario.steps) {
        if (this.abortController.signal.aborted) break;

        // Wait for step timing
        await new Promise(resolve => setTimeout(resolve, step.time));
        if (this.abortController.signal.aborted) break;

        // Show narration
        toast(step.narration, { duration: 4000 });

        // Execute step
        try {
          const result = await step.execute(this.grid);
          this.grid = result.updatedGrid;

          if (this.onGridUpdate) {
            this.onGridUpdate(result.updatedGrid, result.incidents);
          }
        } catch (error) {
          console.error(`Step ${step.id} failed:`, error);
          logAgentActivity(step.agent, `Failed: ${step.action}`, 'error');
        }
      }

      if (!this.abortController.signal.aborted) {
        toast.success(`✅ Scenario complete: ${scenario.name}`, { duration: 4000 });
      }
    } catch (error) {
      toast.error('Scenario failed');
      console.error('Scenario error:', error);
    } finally {
      this.isRunning = false;
      this.currentScenario = null;
      this.abortController = null;
    }
  }

  stop(): void {
    if (this.abortController) {
      this.abortController.abort();
    }
  }

  getIsRunning(): boolean {
    return this.isRunning;
  }

  getCurrentScenario(): AdvancedScenario | null {
    return this.currentScenario;
  }
}

export const scenarioRunner = new ScenarioRunner();

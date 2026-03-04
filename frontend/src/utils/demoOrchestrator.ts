/**
 * Auto-Demo Orchestrator
 * Runs complete scenarios showing multi-agent coordination
 */

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

export interface DemoStep {
  id: string;
  agent: string;
  action: string;
  narration: string;
  delay: number; // milliseconds
  execute: () => Promise<any>;
}

export interface DemoScenario {
  id: string;
  name: string;
  description: string;
  icon: string;
  duration: number; // seconds
  steps: DemoStep[];
}

// Demo event emitter for UI updates
export const emitDemoEvent = (type: 'start' | 'step' | 'complete' | 'error', data?: any) => {
  window.dispatchEvent(
    new CustomEvent('demo-event', {
      detail: { type, data, timestamp: new Date() },
    })
  );
};

/**
 * Demo Scenario 1: Severe Weather Response
 * Shows how the system responds to a hurricane threat
 */
export const severeWeatherScenario: DemoScenario = {
  id: 'severe-weather',
  name: 'Severe Weather Response',
  description: 'Hurricane detected → Multi-agent coordination → Emergency protocols activated',
  icon: '🌪️',
  duration: 25,
  steps: [
    {
      id: 'weather-detect',
      agent: 'Weather Intelligence',
      action: 'Detecting severe weather conditions',
      narration: '🌡️ Weather sensors detect incoming hurricane with 120 mph winds',
      delay: 0,
      execute: async () => {
        logAgentActivity('Weather Intelligence', 'Analyzing atmospheric conditions', 'running');
        await new Promise(resolve => setTimeout(resolve, 2000));
        logAgentActivity('Weather Intelligence', 'Hurricane threat detected', 'completed');
        return { detected: true, severity: 'critical' };
      }
    },
    {
      id: 'weather-simulate',
      agent: 'Weather Agent',
      action: 'Simulating hurricane scenario',
      narration: '🌊 Activating hurricane simulation to test system response',
      delay: 3000,
      execute: async () => {
        logAgentActivity('Weather Agent', 'Simulating hurricane conditions', 'running');
        const result = await simulateWeatherEvent('hurricane');
        logAgentActivity('Weather Agent', 'Hurricane scenario active', 'completed');
        return result;
      }
    },
    {
      id: 'weather-emergency',
      agent: 'Weather Coordinator',
      action: 'Activating emergency protocols',
      narration: '🚨 Emergency weather protocols activated across all zones',
      delay: 4000,
      execute: async () => {
        logAgentActivity('Weather Coordinator', 'Executing emergency workflow', 'running');
        const result = await executeWeatherWorkflow('emergency');
        logAgentActivity('Weather Coordinator', 'Emergency protocols active', 'completed');
        return result;
      }
    },
    {
      id: 'power-prep',
      agent: 'Power Grid Agent',
      action: 'Preparing grid for high winds',
      narration: '⚡ Power grid switching to storm mode, securing critical infrastructure',
      delay: 5000,
      execute: async () => {
        logAgentActivity('Power Grid Agent', 'Optimizing grid for storm', 'running');
        const result = await runEnergyOptimization();
        logAgentActivity('Power Grid Agent', 'Grid prepared for weather event', 'completed');
        return result;
      }
    },
    {
      id: 'cyber-monitor',
      agent: 'Cybersecurity Agent',
      action: 'Increasing security monitoring',
      narration: '🛡️ Security systems on high alert during emergency conditions',
      delay: 6000,
      execute: async () => {
        logAgentActivity('Cybersecurity Agent', 'Increasing threat monitoring', 'running');
        const result = await runSecurityAnalysis();
        logAgentActivity('Cybersecurity Agent', 'Enhanced security posture active', 'completed');
        return result;
      }
    },
    {
      id: 'coordination',
      agent: 'Central Coordinator',
      action: 'Coordinating multi-agent response',
      narration: '🎯 All agents coordinated - lights adjusted, backup power ready, security monitoring active',
      delay: 8000,
      execute: async () => {
        logAgentActivity('Central Coordinator', 'Synchronizing all agents', 'running');
        await new Promise(resolve => setTimeout(resolve, 2000));
        logAgentActivity('Central Coordinator', 'Multi-agent coordination complete', 'completed');
        return { coordinated: true };
      }
    }
  ]
};

/**
 * Demo Scenario 2: Cybersecurity Breach Response
 * Shows intrusion detection and automated response
 */
export const cyberAttackScenario: DemoScenario = {
  id: 'cyber-attack',
  name: 'Cybersecurity Breach Response',
  description: 'Intrusion detected → Threat analysis → Automated countermeasures deployed',
  icon: '🔐',
  duration: 22,
  steps: [
    {
      id: 'threat-detect',
      agent: 'Cybersecurity Monitor',
      action: 'Detecting suspicious network activity',
      narration: '🚨 Anomalous traffic pattern detected from external IP',
      delay: 0,
      execute: async () => {
        logAgentActivity('Cybersecurity Monitor', 'Analyzing network traffic', 'running');
        await new Promise(resolve => setTimeout(resolve, 2000));
        logAgentActivity('Cybersecurity Monitor', 'Intrusion attempt identified', 'completed');
        return { threat: 'intrusion', source: '203.0.113.42' };
      }
    },
    {
      id: 'attack-simulate',
      agent: 'Threat Simulator',
      action: 'Simulating intrusion attempt',
      narration: '💻 Attacker attempting to access lighting control systems',
      delay: 3000,
      execute: async () => {
        logAgentActivity('Threat Simulator', 'Simulating intrusion attack', 'running');
        const result = await simulateCyberAttack('intrusion');
        logAgentActivity('Threat Simulator', 'Intrusion scenario active', 'completed');
        return result;
      }
    },
    {
      id: 'analysis',
      agent: 'Security Analyzer',
      action: 'Analyzing threat patterns',
      narration: '🔍 Deep analysis reveals coordinated attack targeting zone controllers',
      delay: 4000,
      execute: async () => {
        logAgentActivity('Security Analyzer', 'Performing threat analysis', 'running');
        const result = await runSecurityAnalysis();
        logAgentActivity('Security Analyzer', 'Threat profile completed', 'completed');
        return result;
      }
    },
    {
      id: 'response',
      agent: 'Intrusion Response',
      action: 'Deploying countermeasures',
      narration: '🛡️ Automatic firewall rules applied, attacker IP blocked',
      delay: 5000,
      execute: async () => {
        logAgentActivity('Intrusion Response', 'Executing response protocol', 'running');
        const result = await triggerIntrusionResponse();
        logAgentActivity('Intrusion Response', 'Countermeasures deployed', 'completed');
        return result;
      }
    },
    {
      id: 'isolation',
      agent: 'Network Isolation',
      action: 'Isolating affected zones',
      narration: '🔒 Compromised zones isolated from main network',
      delay: 7000,
      execute: async () => {
        logAgentActivity('Network Isolation', 'Isolating affected systems', 'running');
        await new Promise(resolve => setTimeout(resolve, 2000));
        logAgentActivity('Network Isolation', 'Isolation complete', 'completed');
        return { isolated: true };
      }
    },
    {
      id: 'verification',
      agent: 'Security Verification',
      action: 'Verifying system integrity',
      narration: '✅ All systems verified clean - threat neutralized successfully',
      delay: 9000,
      execute: async () => {
        logAgentActivity('Security Verification', 'Running integrity checks', 'running');
        await new Promise(resolve => setTimeout(resolve, 2000));
        logAgentActivity('Security Verification', 'System integrity confirmed', 'completed');
        return { clean: true };
      }
    }
  ]
};

/**
 * Demo Scenario 3: Power Grid Emergency
 * Shows blackout detection and recovery
 */
export const powerOutageScenario: DemoScenario = {
  id: 'power-outage',
  name: 'Power Grid Emergency',
  description: 'Grid failure detected → Backup systems activated → Load balancing optimized',
  icon: '⚡',
  duration: 20,
  steps: [
    {
      id: 'outage-detect',
      agent: 'Grid Monitor',
      action: 'Detecting power anomaly',
      narration: '⚠️ Grid voltage drop detected in Zone B - possible transformer failure',
      delay: 0,
      execute: async () => {
        logAgentActivity('Grid Monitor', 'Monitoring grid health', 'running');
        await new Promise(resolve => setTimeout(resolve, 2000));
        logAgentActivity('Grid Monitor', 'Outage detected in Zone B', 'error');
        return { zone: 'B', severity: 'critical' };
      }
    },
    {
      id: 'outage-trigger',
      agent: 'Emergency System',
      action: 'Triggering emergency blackout protocol',
      narration: '🔌 Emergency blackout protocol activated for affected zones',
      delay: 3000,
      execute: async () => {
        logAgentActivity('Emergency System', 'Activating blackout protocol', 'running');
        const result = await triggerPowerOutage(['zone_b', 'zone_c']);
        logAgentActivity('Emergency System', 'Blackout protocol active', 'completed');
        return result;
      }
    },
    {
      id: 'detection',
      agent: 'Outage Detection',
      action: 'Mapping affected areas',
      narration: '🗺️ Analyzing outage extent - 2 zones affected, 340 lights offline',
      delay: 4000,
      execute: async () => {
        logAgentActivity('Outage Detection', 'Detecting outage extent', 'running');
        const result = await detectPowerOutages();
        logAgentActivity('Outage Detection', 'Outage mapping complete', 'completed');
        return result;
      }
    },
    {
      id: 'backup',
      agent: 'Backup Power System',
      action: 'Activating backup generators',
      narration: '🔋 Backup generators coming online for critical infrastructure',
      delay: 6000,
      execute: async () => {
        logAgentActivity('Backup Power System', 'Starting backup generators', 'running');
        await new Promise(resolve => setTimeout(resolve, 2500));
        logAgentActivity('Backup Power System', 'Backup power online', 'completed');
        return { backup_active: true };
      }
    },
    {
      id: 'optimization',
      agent: 'Load Balancer',
      action: 'Optimizing power distribution',
      narration: '⚖️ Redistributing load to healthy zones, prioritizing critical areas',
      delay: 8000,
      execute: async () => {
        logAgentActivity('Load Balancer', 'Optimizing energy distribution', 'running');
        const result = await runEnergyOptimization();
        logAgentActivity('Load Balancer', 'Load balancing complete', 'completed');
        return result;
      }
    },
    {
      id: 'recovery',
      agent: 'Recovery Coordinator',
      action: 'Coordinating system recovery',
      narration: '✅ Grid stabilized - 95% of lights restored, repair crews dispatched',
      delay: 10000,
      execute: async () => {
        logAgentActivity('Recovery Coordinator', 'Coordinating recovery', 'running');
        await new Promise(resolve => setTimeout(resolve, 2000));
        logAgentActivity('Recovery Coordinator', 'Recovery complete', 'completed');
        return { recovered: true };
      }
    }
  ]
};

/**
 * Demo Scenario 4: Multi-Agent Coordination Showcase
 * Shows all agents working together
 */
export const fullSystemScenario: DemoScenario = {
  id: 'full-system',
  name: 'Complete System Demonstration',
  description: 'Comprehensive showcase of all agents coordinating in real-time',
  icon: '🎭',
  duration: 35,
  steps: [
    {
      id: 'init',
      agent: 'System Initializer',
      action: 'Initializing full system demo',
      narration: '🎬 Starting comprehensive multi-agent coordination demonstration',
      delay: 0,
      execute: async () => {
        logAgentActivity('System Initializer', 'Preparing all agents', 'running');
        await new Promise(resolve => setTimeout(resolve, 2000));
        logAgentActivity('System Initializer', 'All systems ready', 'completed');
        return { ready: true };
      }
    },
    // Weather phase
    {
      id: 'weather-start',
      agent: 'Weather Intelligence',
      action: 'Monitoring weather conditions',
      narration: '🌤️ Weather monitoring active - detecting atmospheric changes',
      delay: 3000,
      execute: async () => {
        logAgentActivity('Weather Intelligence', 'Weather monitoring started', 'running');
        await simulateWeatherEvent('storm');
        logAgentActivity('Weather Intelligence', 'Storm detected and processed', 'completed');
        return {};
      }
    },
    // Power phase
    {
      id: 'power-start',
      agent: 'Power Grid',
      action: 'Analyzing energy consumption',
      narration: '⚡ Power grid analyzing consumption patterns and optimizing',
      delay: 6000,
      execute: async () => {
        logAgentActivity('Power Grid', 'Energy analysis started', 'running');
        await runEnergyOptimization();
        logAgentActivity('Power Grid', 'Grid optimized', 'completed');
        return {};
      }
    },
    // Cyber phase
    {
      id: 'cyber-start',
      agent: 'Cybersecurity',
      action: 'Running security scan',
      narration: '🔐 Security systems scanning for threats across all zones',
      delay: 9000,
      execute: async () => {
        logAgentActivity('Cybersecurity', 'Security scan started', 'running');
        await runSecurityAnalysis();
        logAgentActivity('Cybersecurity', 'Scan complete - all clear', 'completed');
        return {};
      }
    },
    // Coordination phase
    {
      id: 'coordination',
      agent: 'Central Coordinator',
      action: 'Coordinating all subsystems',
      narration: '🎯 Central coordinator synchronizing weather, power, and security data',
      delay: 12000,
      execute: async () => {
        logAgentActivity('Central Coordinator', 'Multi-agent synchronization', 'running');
        await new Promise(resolve => setTimeout(resolve, 3000));
        logAgentActivity('Central Coordinator', 'All agents coordinated', 'completed');
        return {};
      }
    },
    // Crisis simulation
    {
      id: 'crisis',
      agent: 'Crisis Manager',
      action: 'Simulating multi-threat scenario',
      narration: '🚨 Complex scenario: Storm + Cyber threat + Power spike',
      delay: 16000,
      execute: async () => {
        logAgentActivity('Crisis Manager', 'Multi-threat scenario active', 'running');
        await Promise.all([
          simulateWeatherEvent('heavyrain'),
          simulateCyberAttack('ddos'),
        ]);
        logAgentActivity('Crisis Manager', 'Multiple threats detected', 'error');
        return {};
      }
    },
    // Response phase
    {
      id: 'response',
      agent: 'Emergency Response',
      action: 'Deploying coordinated response',
      narration: '🛡️ All agents responding in coordination to complex threat',
      delay: 19000,
      execute: async () => {
        logAgentActivity('Emergency Response', 'Coordinated response deployed', 'running');
        await Promise.all([
          executeWeatherWorkflow('emergency'),
          triggerIntrusionResponse(),
          runEnergyOptimization(),
        ]);
        logAgentActivity('Emergency Response', 'Threats neutralized', 'completed');
        return {};
      }
    },
    // Resolution
    {
      id: 'resolution',
      agent: 'System Manager',
      action: 'Verifying system stability',
      narration: '✅ All threats resolved - system operating at optimal capacity',
      delay: 24000,
      execute: async () => {
        logAgentActivity('System Manager', 'Running stability checks', 'running');
        await new Promise(resolve => setTimeout(resolve, 2000));
        logAgentActivity('System Manager', 'System fully operational', 'completed');
        return { stable: true };
      }
    }
  ]
};

export const demoScenarios = [
  severeWeatherScenario,
  cyberAttackScenario,
  powerOutageScenario,
  fullSystemScenario,
];

/**
 * Run a demo scenario
 */
export class DemoRunner {
  private isRunning = false;
  private currentScenario: DemoScenario | null = null;
  private abortController: AbortController | null = null;

  async runScenario(scenario: DemoScenario): Promise<void> {
    if (this.isRunning) {
      toast.error('A demo is already running');
      return;
    }

    this.isRunning = true;
    this.currentScenario = scenario;
    this.abortController = new AbortController();

    emitDemoEvent('start', { scenario });
    toast.success(`🎬 Starting demo: ${scenario.name}`, { duration: 3000 });

    try {
      for (let i = 0; i < scenario.steps.length; i++) {
        if (this.abortController.signal.aborted) {
          break;
        }

        const step = scenario.steps[i];

        // Wait for delay
        if (step.delay > 0) {
          await new Promise(resolve => setTimeout(resolve, step.delay));
        }

        if (this.abortController.signal.aborted) {
          break;
        }

        // Emit step start
        emitDemoEvent('step', { step, index: i });

        // Execute step
        try {
          await step.execute();
        } catch (error) {
          console.error(`Demo step ${step.id} failed:`, error);
          logAgentActivity(step.agent, `Failed: ${step.action}`, 'error');
        }
      }

      if (!this.abortController.signal.aborted) {
        emitDemoEvent('complete', { scenario });
        toast.success(`✅ Demo complete: ${scenario.name}`, { duration: 4000 });
      } else {
        toast('Demo stopped', { icon: '⏹️' });
      }
    } catch (error) {
      emitDemoEvent('error', { scenario, error });
      toast.error('Demo failed');
      console.error('Demo error:', error);
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

  getCurrentScenario(): DemoScenario | null {
    return this.currentScenario;
  }
}

export const demoRunner = new DemoRunner();

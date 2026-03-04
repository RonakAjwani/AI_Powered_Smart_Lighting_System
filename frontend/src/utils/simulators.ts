// Simulation utilities for triggering backend agent actions

const API_URLS = {
  weather: process.env.NEXT_PUBLIC_WEATHER_API_URL || 'http://localhost:8001',
  power: process.env.NEXT_PUBLIC_POWER_API_URL || 'http://localhost:8002',
  cyber: process.env.NEXT_PUBLIC_CYBERSECURITY_API_URL || 'http://localhost:8000',
};

// Weather Simulations
export const simulateWeatherEvent = async (eventType: 'heatwave' | 'heavyrain' | 'storm' | 'hurricane') => {
  try {
    const response = await fetch(`${API_URLS.weather}/weather/agents/disaster/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ disaster_type: eventType }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Weather simulation error:', error);
    throw error;
  }
};

export const activateWeatherEmergency = async () => {
  try {
    const response = await fetch(`${API_URLS.weather}/weather/emergency/activate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Emergency activation error:', error);
    throw error;
  }
};

export const executeWeatherWorkflow = async (mode: 'auto' | 'normal' | 'emergency' | 'maintenance' = 'auto') => {
  try {
    const response = await fetch(`${API_URLS.weather}/weather/execute?execution_mode=${mode}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Weather workflow error:', error);
    throw error;
  }
};

// Cybersecurity Simulations
export const simulateCyberAttack = async (attackType: 'ddos' | 'malware' | 'intrusion' | 'data_breach' = 'intrusion') => {
  try {
    const response = await fetch(`${API_URLS.cyber}/events/threat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        threat_type: attackType,
        severity: 'high',
        source_ip: '192.168.1.100',
        target_zone: 'zone_1',
        description: `Simulated ${attackType} attack`,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Cyber attack simulation error:', error);
    throw error;
  }
};

export const runSecurityAnalysis = async () => {
  try {
    const response = await fetch(`${API_URLS.cyber}/analyze/security`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ analysis_type: 'full' }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Security analysis error:', error);
    throw error;
  }
};

export const triggerIntrusionResponse = async () => {
  try {
    const response = await fetch(`${API_URLS.cyber}/respond/intrusion`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Intrusion response error:', error);
    throw error;
  }
};

// Power Grid Simulations
export const triggerPowerOutage = async (zones: string[] = ['zone_1']) => {
  try {
    const response = await fetch(`${API_URLS.power}/emergency/trigger`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        emergency_type: 'power_outage',
        affected_zones: zones,
        severity: 'critical',
        description: 'Simulated power outage',
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Power outage simulation error:', error);
    throw error;
  }
};

export const runPowerWorkflow = async (triggerType: string = 'manual') => {
  try {
    const response = await fetch(`${API_URLS.power}/workflow/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ trigger_type: triggerType }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Power workflow error:', error);
    throw error;
  }
};

export const runEnergyOptimization = async () => {
  try {
    const response = await fetch(`${API_URLS.power}/agents/optimize-energy`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        zones: null, // null = all zones
        savings_target: 15.0,
        priority_mode: 'balanced',
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Energy optimization error:', error);
    throw error;
  }
};

export const detectPowerOutages = async () => {
  try {
    const response = await fetch(`${API_URLS.power}/agents/detect-outages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Outage detection error:', error);
    throw error;
  }
};

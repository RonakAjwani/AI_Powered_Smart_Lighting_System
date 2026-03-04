// Zone data types for the smart lighting system

export interface LightPole {
  id: string;
  position: [number, number]; // [lat, lng]
  status: 'online' | 'offline' | 'maintenance';
  brightness: number; // 0-100
  powerConsumption: number; // watts
}

export interface SecurityZone {
  id: string;
  name: string;
  type: 'hospital' | 'commercial' | 'residential' | 'defense' | 'airport';
  position: [number, number]; // center position [lat, lng]
  radius: number; // meters
  securityState: 'SECURE' | 'YELLOW' | 'RED';
  threatLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  activeIncidents: number;
  compliance: 'COMPLIANT' | 'NON_COMPLIANT';
  criticalAssets: string[];
}

export interface PowerZone {
  id: string;
  name: string;
  position: [number, number];
  status: 'operational' | 'degraded' | 'critical';
  capacity: number; // MW
  currentLoad: number; // MW
  affectedByOutage: boolean;
  capacityLoss: number; // percentage
}

export interface LightingZone {
  id: string;
  name: string;
  type: 'residential' | 'commercial' | 'industrial';
  position: [number, number];
  poles: LightPole[];
  totalPoles: number;
  onlinePoles: number;
  avgBrightness: number;
}

// Mumbai zones data
export const MUMBAI_CENTER: [number, number] = [19.0760, 72.8777];

export const SECURITY_ZONES: SecurityZone[] = [
  {
    id: 'kem-hospital',
    name: 'KEM Hospital',
    type: 'hospital',
    position: [19.0369, 72.8569],
    radius: 800,
    securityState: 'YELLOW',
    threatLevel: 'LOW',
    activeIncidents: 2,
    compliance: 'COMPLIANT',
    criticalAssets: ['Patient Records', 'Life Support Systems', 'Pharmacy Systems']
  },
  {
    id: 'bkc-commercial',
    name: 'BKC Commercial Zone',
    type: 'commercial',
    position: [19.0645, 72.8685],
    radius: 1200,
    securityState: 'SECURE',
    threatLevel: 'LOW',
    activeIncidents: 0,
    compliance: 'COMPLIANT',
    criticalAssets: ['Financial Systems', 'Data Centers']
  },
  {
    id: 'dadar-residential',
    name: 'Dadar Residential Area',
    type: 'residential',
    position: [19.0183, 72.8478],
    radius: 1000,
    securityState: 'SECURE',
    threatLevel: 'LOW',
    activeIncidents: 0,
    compliance: 'COMPLIANT',
    criticalAssets: ['Community Centers', 'Schools']
  },
  {
    id: 'defense-zone',
    name: 'Defence Zone',
    type: 'defense',
    position: [18.9667, 72.8147],
    radius: 900,
    securityState: 'SECURE',
    threatLevel: 'LOW',
    activeIncidents: 0,
    compliance: 'COMPLIANT',
    criticalAssets: ['Military Infrastructure', 'Communications']
  },
  {
    id: 'airport-zone',
    name: 'Airport Zone',
    type: 'airport',
    position: [19.0896, 72.8656],
    radius: 1500,
    securityState: 'SECURE',
    threatLevel: 'LOW',
    activeIncidents: 0,
    compliance: 'COMPLIANT',
    criticalAssets: ['Air Traffic Control', 'Terminal Systems']
  }
];

export const POWER_ZONES: PowerZone[] = [
  {
    id: 'hospital-power',
    name: 'Hospital Zone (Bandra)',
    position: [19.0594, 72.8400],
    status: 'operational',
    capacity: 150,
    currentLoad: 130,
    affectedByOutage: false,
    capacityLoss: 0
  },
  {
    id: 'defense-power',
    name: 'Defence Zone',
    position: [18.9667, 72.8147],
    status: 'operational',
    capacity: 120,
    currentLoad: 95,
    affectedByOutage: false,
    capacityLoss: 0
  },
  {
    id: 'airport-power',
    name: 'Airport Zone',
    position: [19.0896, 72.8656],
    status: 'operational',
    capacity: 200,
    currentLoad: 180,
    affectedByOutage: false,
    capacityLoss: 0
  },
  {
    id: 'commercial-power',
    name: 'BKC Commercial Zone',
    position: [19.0645, 72.8685],
    status: 'operational',
    capacity: 140,
    currentLoad: 115,
    affectedByOutage: false,
    capacityLoss: 0
  }
];

export const LIGHTING_ZONES: LightingZone[] = [
  {
    id: 'dadar-residential',
    name: 'Dadar Residential Area',
    type: 'residential',
    position: [19.0183, 72.8478],
    poles: [],
    totalPoles: 5,
    onlinePoles: 5,
    avgBrightness: 85
  },
  {
    id: 'bkc-commercial',
    name: 'BKC Commercial',
    type: 'commercial',
    position: [19.0645, 72.8685],
    poles: [],
    totalPoles: 3,
    onlinePoles: 3,
    avgBrightness: 85
  },
  {
    id: 'bandra-west',
    name: 'Bandra West',
    type: 'residential',
    position: [19.0594, 72.8300],
    poles: [],
    totalPoles: 4,
    onlinePoles: 4,
    avgBrightness: 85
  },
  {
    id: 'worli-area',
    name: 'Worli Area',
    type: 'commercial',
    position: [18.9990, 72.8140],
    poles: [],
    totalPoles: 2,
    onlinePoles: 2,
    avgBrightness: 85
  }
];

// Generate light pole positions for each zone
LIGHTING_ZONES.forEach(zone => {
  const poles: LightPole[] = [];
  const basePosition = zone.position;

  for (let i = 0; i < zone.totalPoles; i++) {
    // Create a spread of poles around the zone center
    const angle = (i / zone.totalPoles) * Math.PI * 2;
    const distance = 0.005 + (Math.random() * 0.003); // Slight randomization
    const lat = basePosition[0] + Math.cos(angle) * distance;
    const lng = basePosition[1] + Math.sin(angle) * distance;

    poles.push({
      id: `${zone.id}-pole-${i + 1}`,
      position: [lat, lng],
      status: 'online',
      brightness: zone.avgBrightness + (Math.random() * 10 - 5), // Slight variation
      powerConsumption: 150 + Math.random() * 50
    });
  }

  zone.poles = poles;
});

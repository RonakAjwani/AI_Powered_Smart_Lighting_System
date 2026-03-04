import { useEffect, useRef, useState, useCallback } from 'react';

export interface WebSocketMessage {
  type: 'CYBER_ALERT' | 'WEATHER_ALERT' | 'POWER_ALERT' | 'COORDINATOR_COMMAND' | 'SYSTEM_UPDATE' | 'LIGHT_STATUS';
  timestamp: string;
  data: any;
  source: 'cybersecurity' | 'weather' | 'power' | 'coordinator';
}

export interface WebSocketConfig {
  url: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

export interface WebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  error: Error | null;
  reconnectAttempt: number;
  lastMessage: WebSocketMessage | null;
}

/**
 * WebSocket hook for real-time streaming from backend
 * Supports auto-reconnection and heartbeat
 */
export const useWebSocket = (config: WebSocketConfig) => {
  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    reconnectAttempt: 0,
    lastMessage: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const messageHandlersRef = useRef<Map<string, (message: WebSocketMessage) => void>>(new Map());

  const {
    url,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    heartbeatInterval = 30000,
  } = config;

  /**
   * Start heartbeat ping to keep connection alive
   */
  const startHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }

    heartbeatIntervalRef.current = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'PING' }));
      }
    }, heartbeatInterval);
  }, [heartbeatInterval]);

  /**
   * Stop heartbeat
   */
  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    setState(prev => ({ ...prev, isConnecting: true, error: null }));

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('[WebSocket] Connected to', url);
        setState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          reconnectAttempt: 0,
          error: null,
        }));

        startHeartbeat();

        // Send initial subscription message
        ws.send(JSON.stringify({
          type: 'SUBSCRIBE',
          topics: ['cyber_alerts', 'weather_alerts', 'power_alerts', 'coordinator_commands'],
        }));
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          // Ignore pong responses
          if (message.type === 'PONG' as any) {
            return;
          }

          setState(prev => ({ ...prev, lastMessage: message }));

          // Notify all registered handlers
          messageHandlersRef.current.forEach(handler => {
            handler(message);
          });
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error);
        setState(prev => ({
          ...prev,
          error: new Error('WebSocket connection error'),
          isConnecting: false,
        }));
      };

      ws.onclose = (event) => {
        console.log('[WebSocket] Disconnected:', event.code, event.reason);
        stopHeartbeat();

        setState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
        }));

        // Attempt reconnection
        if (state.reconnectAttempt < maxReconnectAttempts) {
          console.log(`[WebSocket] Reconnecting in ${reconnectInterval}ms... (attempt ${state.reconnectAttempt + 1}/${maxReconnectAttempts})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            setState(prev => ({
              ...prev,
              reconnectAttempt: prev.reconnectAttempt + 1,
            }));
            connect();
          }, reconnectInterval);
        } else {
          console.error('[WebSocket] Max reconnection attempts reached');
          setState(prev => ({
            ...prev,
            error: new Error('Failed to reconnect to WebSocket'),
          }));
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('[WebSocket] Connection failed:', error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error : new Error('Unknown error'),
        isConnecting: false,
      }));
    }
  }, [url, reconnectInterval, maxReconnectAttempts, state.reconnectAttempt, startHeartbeat, stopHeartbeat]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    stopHeartbeat();

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnecting');
      wsRef.current = null;
    }

    setState({
      isConnected: false,
      isConnecting: false,
      error: null,
      reconnectAttempt: 0,
      lastMessage: null,
    });
  }, [stopHeartbeat]);

  /**
   * Send message to WebSocket
   */
  const send = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    console.warn('[WebSocket] Cannot send message - not connected');
    return false;
  }, []);

  /**
   * Subscribe to specific message types
   */
  const subscribe = useCallback((id: string, handler: (message: WebSocketMessage) => void) => {
    messageHandlersRef.current.set(id, handler);

    // Return unsubscribe function
    return () => {
      messageHandlersRef.current.delete(id);
    };
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [url]); // Only reconnect if URL changes

  return {
    ...state,
    connect,
    disconnect,
    send,
    subscribe,
  };
};

/**
 * Hook for simulating WebSocket when backend is not available
 * This generates fake real-time events for testing
 */
export const useSimulatedWebSocket = () => {
  const [state, setState] = useState<WebSocketState>({
    isConnected: true,
    isConnecting: false,
    error: null,
    reconnectAttempt: 0,
    lastMessage: null,
  });

  const messageHandlersRef = useRef<Map<string, (message: WebSocketMessage) => void>>(new Map());
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const generateRandomMessage = useCallback((): WebSocketMessage => {
    const types: WebSocketMessage['type'][] = ['CYBER_ALERT', 'WEATHER_ALERT', 'POWER_ALERT', 'COORDINATOR_COMMAND', 'SYSTEM_UPDATE', 'LIGHT_STATUS'];
    const sources: WebSocketMessage['source'][] = ['cybersecurity', 'weather', 'power', 'coordinator'];

    const type = types[Math.floor(Math.random() * types.length)];
    const source = sources[Math.floor(Math.random() * sources.length)];

    let data = {};

    switch (type) {
      case 'CYBER_ALERT':
        data = {
          severity: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'][Math.floor(Math.random() * 4)],
          threatType: ['intrusion', 'malware', 'ddos', 'data_breach'][Math.floor(Math.random() * 4)],
          affectedZone: `ZONE-${Math.floor(Math.random() * 12) + 1}`,
          description: 'Suspicious activity detected',
        };
        break;

      case 'WEATHER_ALERT':
        data = {
          condition: ['heavy_rain', 'storm', 'fog', 'heatwave'][Math.floor(Math.random() * 4)],
          severity: ['MODERATE', 'SEVERE', 'EXTREME'][Math.floor(Math.random() * 3)],
          affectedZones: [`ZONE-${Math.floor(Math.random() * 12) + 1}`],
          description: 'Weather event in progress',
        };
        break;

      case 'POWER_ALERT':
        data = {
          alertType: ['outage', 'overload', 'voltage_fluctuation'][Math.floor(Math.random() * 3)],
          affectedSubstation: `SUB-${Math.floor(Math.random() * 12) + 1}`,
          affectedLights: Math.floor(Math.random() * 50) + 10,
          estimatedDowntime: Math.floor(Math.random() * 120),
        };
        break;

      case 'COORDINATOR_COMMAND':
        data = {
          command: ['INCREASE_BRIGHTNESS', 'EMERGENCY_MODE', 'OPTIMIZE_ENERGY', 'LOCKDOWN'][Math.floor(Math.random() * 4)],
          targetZones: [`ZONE-${Math.floor(Math.random() * 12) + 1}`],
          priority: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'][Math.floor(Math.random() * 4)],
          reason: 'Coordinator decision based on system state',
        };
        break;

      case 'LIGHT_STATUS':
        data = {
          lightId: `LIGHT-${Math.floor(Math.random() * 12)}-${Math.floor(Math.random() * 100).toString().padStart(4, '0')}`,
          status: ['ONLINE', 'OFFLINE', 'WARNING'][Math.floor(Math.random() * 3)],
          brightness: Math.floor(Math.random() * 100),
          powerConsumption: Math.floor(Math.random() * 150) + 50,
        };
        break;

      default:
        data = { message: 'System update' };
    }

    return {
      type,
      timestamp: new Date().toISOString(),
      data,
      source,
    };
  }, []);

  const subscribe = useCallback((id: string, handler: (message: WebSocketMessage) => void) => {
    messageHandlersRef.current.set(id, handler);

    return () => {
      messageHandlersRef.current.delete(id);
    };
  }, []);

  const send = useCallback((message: any) => {
    console.log('[Simulated WebSocket] Sent:', message);
    return true;
  }, []);

  useEffect(() => {
    // Generate random messages every 3-8 seconds
    const generateMessage = () => {
      const message = generateRandomMessage();
      setState(prev => ({ ...prev, lastMessage: message }));

      messageHandlersRef.current.forEach(handler => {
        handler(message);
      });

      // Schedule next message
      const delay = 3000 + Math.random() * 5000;
      intervalRef.current = setTimeout(generateMessage, delay);
    };

    // Start generating messages
    generateMessage();

    return () => {
      if (intervalRef.current) {
        clearTimeout(intervalRef.current);
      }
    };
  }, [generateRandomMessage]);

  return {
    ...state,
    connect: () => {},
    disconnect: () => {},
    send,
    subscribe,
  };
};

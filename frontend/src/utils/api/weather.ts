// Functions to interact with the Weather Agent API (localhost:8001)

const API_URL = process.env.NEXT_PUBLIC_WEATHER_API_URL || 'http://localhost:8001';

/**
 * Fetches the current status of the weather system.
 */
export const getWeatherSystemStatus = async () => {
  try {
    const response = await fetch(`${API_URL}/weather/status`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch weather system status:", error);
    return { error: true, message: error instanceof Error ? error.message : "Unknown error" };
  }
};

/**
 * Fetches the current weather data for all zones.
 */
export const getCurrentWeatherData = async () => {
    try {
      const response = await fetch(`${API_URL}/weather/data/current`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Failed to fetch current weather data:", error);
      return { error: true, message: error instanceof Error ? error.message : "Unknown error" };
    }
  };

/**
 * Fetches active weather alerts.
 */
export const getWeatherAlerts = async () => {
    try {
      const response = await fetch(`${API_URL}/weather/alerts`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Failed to fetch weather alerts:", error);
      return { error: true, message: error instanceof Error ? error.message : "Unknown error" };
    }
  };

// Add more functions as needed (e.g., getForecast, triggerAnalysis)

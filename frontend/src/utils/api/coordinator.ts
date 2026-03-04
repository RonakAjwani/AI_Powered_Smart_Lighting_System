// Functions to interact with the Coordinator Agent API (localhost:8004)

const API_URL = process.env.NEXT_PUBLIC_COORDINATOR_API_URL || 'http://localhost:8004';

/**
 * Fetches the current status of the coordinator system.
 */
export const getCoordinatorStatus = async () => {
  try {
    const response = await fetch(`${API_URL}/health`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch coordinator status:", error);
    return { error: true, message: error instanceof Error ? error.message : "Unknown error" };
  }
};

/**
 * Fetches the aggregated system state from all services.
 */
export const getSystemState = async () => {
  try {
    const response = await fetch(`${API_URL}/system/state`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch system state:", error);
    return { error: true, message: error instanceof Error ? error.message : "Unknown error" };
  }
};

/**
 * Fetches the current primary concern and final command from the coordinator.
 */
export const getCoordinatorDecision = async () => {
  try {
    const response = await fetch(`${API_URL}/coordinator/decision`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch coordinator decision:", error);
    return { error: true, message: error instanceof Error ? error.message : "Unknown error" };
  }
};

/**
 * Triggers the coordinator to run its decision workflow.
 */
export const triggerCoordinatorWorkflow = async () => {
  try {
    const response = await fetch(`${API_URL}/coordinator/execute`, {
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
    console.error("Failed to trigger coordinator workflow:", error);
    return { error: true, message: error instanceof Error ? error.message : "Unknown error" };
  }
};

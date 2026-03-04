// Functions to interact with the Power Agent API (localhost:8002)

const API_URL = process.env.NEXT_PUBLIC_POWER_API_URL || 'http://localhost:8002';

/**
 * Fetches the current status of the power grid system.
 */
export const getPowerSystemStatus = async () => {
  try {
    const response = await fetch(`${API_URL}/system/status`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch power system status:", error);
    return { error: true, message: error instanceof Error ? error.message : "Unknown error" };
  }
};

/**
 * Triggers the main power grid workflow.
 * Returns the initial response containing the workflow ID.
 */
export const triggerPowerWorkflow = async () => {
    try {
      const response = await fetch(`${API_URL}/workflow/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ trigger_type: "manual" }), // Example body
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json(); // Contains workflow_id
    } catch (error) {
      console.error("Failed to trigger power workflow:", error);
      return { error: true, message: error instanceof Error ? error.message : "Unknown error" };
    }
  };

/**
 * Fetches the status of a specific power grid workflow.
 */
export const getPowerWorkflowStatus = async (workflowId: string) => {
    if (!workflowId) {
        return { error: true, message: "Workflow ID is required." };
    }
    try {
      const response = await fetch(`${API_URL}/workflow/status/${workflowId}`);
      if (!response.ok) {
        // Handle 404 specifically if workflow not found yet
        if (response.status === 404) {
          return { status: "not_found", workflow_id: workflowId };
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Failed to fetch power workflow status for ${workflowId}:`, error);
      return { error: true, workflow_id: workflowId, message: error instanceof Error ? error.message : "Unknown error" };
    }
  };


// Add more functions as needed (e.g., getLoadForecast, getOutages)

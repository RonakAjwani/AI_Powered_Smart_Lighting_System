// Functions to interact with the Cybersecurity Agent API (localhost:8000)

const API_URL = process.env.NEXT_PUBLIC_CYBERSECURITY_API_URL || 'http://localhost:8000';

/**
 * Fetches the current status of cybersecurity agents.
 */
export const getCybersecurityAgentStatus = async () => {
  try {
    const response = await fetch(`${API_URL}/status/agents`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch cybersecurity agent status:", error);
    return { error: true, message: error instanceof Error ? error.message : "Unknown error" };
  }
};

/**
 * Triggers a full cybersecurity analysis.
 */
export const triggerCybersecurityAnalysis = async () => {
    try {
      const response = await fetch(`${API_URL}/analyze/security`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ analysis_type: "full" }), // Example body
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Failed to trigger cybersecurity analysis:", error);
      return { error: true, message: error instanceof Error ? error.message : "Unknown error" };
    }
  };


/**
 * Fetches security metrics.
 */
export const getCybersecurityMetrics = async () => {
    try {
      const response = await fetch(`${API_URL}/metrics/security`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Failed to fetch cybersecurity metrics:", error);
      return { error: true, message: error instanceof Error ? error.message : "Unknown error" };
    }
  };

// Add more functions as needed (e.g., getThreats, getIntegrityStatus)

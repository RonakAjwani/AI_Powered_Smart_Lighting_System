import logging
from typing import Dict, Any, List, Tuple

# Define priority levels
# Lower number means HIGHER priority
PRIORITY_LEVELS = {
    "CYBER_CRITICAL": 1,
    "POWER_OUTAGE": 2,
    "WEATHER_DISASTER": 3,
    "CYBER_HIGH": 4,
    "POWER_GRID_UNSTABLE": 5,
    "WEATHER_ADVISORY": 6,
    "POWER_OPTIMIZATION": 7,
    "CYBER_MEDIUM": 8,
    "NOMINAL_OPERATION": 99
}

class PriorityManager:
    """
    Analyzes the aggregated system state to determine the single most
    important concern that the Decision Engine must address.
    """

    def __init__(self):
        logging.info("PriorityManager initialized.")

    def get_primary_concern(self, system_state: Dict[str, Any]) -> Tuple[str, int]:
        """
        Evaluates the current system state and returns the top priority concern.

        Args:
            system_state: A dictionary holding the latest data from all services.

        Returns:
            A tuple (concern_key: str, priority_level: int)
        """
        priorities = []

        # --- Cybersecurity Assessment ---
        if system_state.get("cyber_alerts"):
            for alert in system_state["cyber_alerts"]:
                if alert.get("severity") == "critical":
                    priorities.append(("CYBER_CRITICAL", PRIORITY_LEVELS["CYBER_CRITICAL"]))
                elif alert.get("severity") == "high":
                    priorities.append(("CYBER_HIGH", PRIORITY_LEVELS["CYBER_HIGH"]))
                elif alert.get("severity") == "medium":
                    priorities.append(("CYBER_MEDIUM", PRIORITY_LEVELS["CYBER_MEDIUM"]))

        # --- Power Grid Assessment ---
        if system_state.get("power_alerts"):
            for alert in system_state["power_alerts"]:
                if alert.get("status") == "outage_detected":
                    priorities.append(("POWER_OUTAGE", PRIORITY_LEVELS["POWER_OUTAGE"]))
                elif alert.get("status") == "grid_unstable":
                    priorities.append(("POWER_GRID_UNSTABLE", PRIORITY_LEVELS["POWER_GRID_UNSTABLE"]))

        # --- Weather Assessment ---
        if system_state.get("weather_alerts"):
            for alert in system_state["weather_alerts"]:
                if alert.get("alert_type") == "disaster":
                    priorities.append(("WEATHER_DISASTER", PRIORITY_LEVELS["WEATHER_DISASTER"]))
                elif alert.get("alert_type") == "advisory":
                    priorities.append(("WEATHER_ADVISORY", PRIORITY_LEVELS["WEATHER_ADVISORY"]))

        # --- Optimization Requests ---
        if system_state.get("power_optimization"):
             priorities.append(("POWER_OPTIMIZATION", PRIORITY_LEVELS["POWER_OPTIMIZATION"]))

        # --- Determine Top Priority ---
        if not priorities:
            return "NOMINAL_OPERATION", PRIORITY_LEVELS["NOMINAL_OPERATION"]

        # Sort by priority level (lowest number first)
        top_priority = sorted(priorities, key=lambda x: x[1])[0]
        
        logging.info(f"Primary concern identified: {top_priority[0]} (Level: {top_priority[1]})")
        return top_priority[0], top_priority[1]

# Singleton instance
priority_manager = PriorityManager()
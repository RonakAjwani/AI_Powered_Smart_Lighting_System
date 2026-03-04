import json
import logging
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from ..config.settings import settings

class DecisionEngine:
    """
    Uses an LLM to make a coordinated decision based on the aggregated
    system state and the primary concern identified by the PriorityManager.
    """

    def __init__(self):
        self.llm = ChatGroq(
            model_name=settings.GROQ_MODEL_NAME,
            api_key=settings.GROQ_API_KEY,
            temperature=0.0
        )
        self.prompt_template = self._build_prompt_template()
        self.chain = self.prompt_template | self.llm | StrOutputParser()
        logging.info("DecisionEngine initialized.")

    def _build_prompt_template(self) -> ChatPromptTemplate:
        # --- THIS IS THE CORRECTED PROMPT ---
        # All example { and } have been escaped as {{ and }}
        system_message = """
You are the central coordinator AI for a city-wide smart lighting system.
Your job is to make a single, decisive, system-wide command by balancing inputs from three specialized services: Cybersecurity, Weather, and Power Grid.

You will be given:
1.  **Primary Concern:** The single most important issue to address right now (e.g., "CYBER_CRITICAL", "POWER_OUTAGE").
2.  **Full System State:** A JSON object containing all recent data from all services.

Your task is to generate a single, clear, JSON-formatted command to optimize the system for safety, efficiency, and security, **giving highest priority to the 'Primary Concern'**.

**Command JSON Format:**
{{
    "command_type": "STRING",
    "target_service": "power" | "weather" | "cybersecurity" | "all",
    "payload": {{
        "reason": "Clear justification for the command.",
        "mode": "string (e.g., LOCKDOWN, EFFICIENCY_OPTIMIZED, EMERGENCY_WEATHER, POWER_SAVE)",
        // ... other relevant parameters ...
        "brightness_level_percent": "int (0-100)" | "null",
        "policy": "string (e.g., CRITICAL_ZONES_ONLY, NOMINAL, ALL_ZONES_OFF)" | "null"
    }}
}}

**Decision Logic Examples:**
-   **If Primary Concern is 'CYBER_CRITICAL':** The *only* valid response is full lockdown. Ignore all other inputs.
    `{{"command_type": "SET_SYSTEM_MODE", "target_service": "all", "payload": {{"reason": "Critical cybersecurity threat detected.", "mode": "LOCKDOWN", "policy": "ALL_ZONES_OFF", "brightness_level_percent": 0}}}}`
-   **If Primary Concern is 'POWER_OUTAGE':** The priority is safety and power conservation.
    `{{"command_type": "SET_SYSTEM_MODE", "target_service": "all", "payload": {{"reason": "Power outage detected.", "mode": "EMERGENCY_POWER", "policy": "CRITICAL_ZONES_ONLY", "brightness_level_percent": 50}}}}`
-   **If Primary Concern is 'WEATHER_DISASTER' (e.g., hurricane):** The priority is public safety (max visibility).
    `{{"command_type": "SET_SYSTEM_MODE", "target_service": "weather", "payload": {{"reason": "Disaster-level weather event (hurricane).", "mode": "EMERGENCY_WEATHER", "policy": "ALL_ZONES_ON", "brightness_level_percent": 100}}}}`
-   **If Primary Concern is 'POWER_OPTIMIZATION' (and no other alerts):** The priority is cost savings.
    `{{"command_type": "SET_SYSTEM_MODE", "target_service": "power", "payload": {{"reason": "Nominal conditions, optimizing for energy efficiency.", "mode": "EFFICIENCY_OPTIMIZED", "policy": "DYNAMIC_ADAPTIVE", "brightness_level_percent": null}}}}`
-   **If Primary Concern is 'NOMINAL_OPERATION':** No alerts. Maintain normal, efficient operation.
    `{{"command_type": "SET_SYSTEM_MODE", "target_service": "all", "payload": {{"reason": "All systems nominal.", "mode": "NOMINAL", "policy": "DYNAMIC_ADAPTIVE", "brightness_level_percent": null}}}}`

**IMPORTANT:** Respond with *only* the JSON command object. Do not add any explanatory text, markdown, or apologies.
"""
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            # These two are the *real* variables and are NOT escaped
            ("human", "Primary Concern: {primary_concern}\n\nFull System State:\n{system_state_json}")
        ])

    def generate_command(self, primary_concern: str, system_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invokes the LLM to generate a coordinated command.
        """
        try:
            system_state_json = json.dumps(system_state, indent=2)
            
            logging.info(f"Invoking DecisionEngine. Concern: {primary_concern}")
            
            response = self.chain.invoke({
                "primary_concern": primary_concern,
                "system_state_json": system_state_json
            })
            
            logging.info(f"LLM Response: {response}")
            
            # Parse the JSON response
            command_json = json.loads(response)
            return command_json

        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode LLM JSON response: {e}\nResponse was: {response}")
            return {
                "command_type": "ERROR", 
                "target_service": "all", 
                "payload": {"reason": "Failed to generate valid command.", "mode": "FAIL_SAFE"}
            }
        except Exception as e:
            # Added exc_info=True for better debugging
            logging.error(f"Error in DecisionEngine: {e}", exc_info=True)
            return {
                "command_type": "ERROR", 
                "target_service": "all", 
                "payload": {"reason": f"Internal error: {str(e)}", "mode": "FAIL_SAFE"}
            }

# Singleton instance
decision_engine = DecisionEngine()

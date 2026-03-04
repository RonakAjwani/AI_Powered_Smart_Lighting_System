import json
import logging
from typing import TypedDict, Dict, Any, List

from langgraph.graph import StateGraph, END

from ..agents.priority_manager import priority_manager
from ..agents.decision_engine import decision_engine

# 1. Define the State
class CoordinatorState(TypedDict):
    """
    Represents the aggregated state of the system from all microservices.
    """
    # Inputs - Raw data from services
    cyber_alerts: List[Dict[str, Any]]
    cyber_reports: List[Dict[str, Any]]
    weather_alerts: List[Dict[str, Any]]
    weather_impact: Dict[str, Any]
    power_alerts: List[Dict[str, Any]]
    power_forecasts: Dict[str, Any]
    power_optimization: Dict[str, Any]
    
    # Processed data
    primary_concern: str
    final_command: Dict[str, Any]

# 2. Define Graph Nodes
def run_priority_manager(state: CoordinatorState) -> CoordinatorState:
    """
    Node that runs the PriorityManager to determine the top priority.
    """
    logging.info("--- (Node) Running Priority Manager ---")
    
    # Create a simple state view for the priority manager
    simple_state = {
        "cyber_alerts": state.get("cyber_alerts", []),
        "weather_alerts": state.get("weather_alerts", []),
        "power_alerts": state.get("power_alerts", []),
        "power_optimization": state.get("power_optimization", {})
    }
    
    concern, level = priority_manager.get_primary_concern(simple_state)
    
    return {"primary_concern": concern}

def run_decision_engine(state: CoordinatorState) -> CoordinatorState:
    """
    Node that runs the LLM-based DecisionEngine to get a final command.
    """
    logging.info("--- (Node) Running Decision Engine ---")
    
    primary_concern = state.get("primary_concern")
    if not primary_concern:
        logging.error("Decision Engine cannot run without a primary concern.")
        return {"final_command": {"error": "Missing primary concern"}}

    # Pass the *full* state to the decision engine
    command = decision_engine.generate_command(primary_concern, state)
    
    logging.info(f"--- (Node) Final Command Generated: {command} ---")
    return {"final_command": command}

# 3. Build the Graph
def build_graph():
    """
    Builds the LangGraph executable.
    """
    workflow = StateGraph(CoordinatorState)

    # Add nodes
    workflow.add_node("priority_manager", run_priority_manager)
    workflow.add_node("decision_engine", run_decision_engine)

    # Define edges
    workflow.set_entry_point("priority_manager")
    workflow.add_edge("priority_manager", "decision_engine")
    workflow.add_edge("decision_engine", END)

    # Compile the graph
    app = workflow.compile()
    logging.info("Coordinator graph compiled successfully.")
    return app

# Singleton instance of the compiled graph
coordinator_graph = build_graph()
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import logging
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

from ..config.settings import config
from ..kafka.kafka_producer import power_producer

# Configure logging
logger = logging.getLogger(__name__)

class EnergyReroutingState:
    """State management for Energy Rerouting Agent"""
    
    def __init__(self):
        self.outage_alerts: List[Dict[str, Any]] = []
        self.priority_map: Dict[str, int] = {}
        self.backup_sources: Dict[str, Any] = {}
        self.current_loads: Dict[str, float] = {}
        self.rerouting_plan: Dict[str, Any] = {}
        self.load_shedding_schedule: List[Dict[str, Any]] = []
        self.backup_activations: List[Dict[str, Any]] = []
        self.rerouting_commands: List[Dict[str, Any]] = []
        self.grid_capacity: Dict[str, float] = {}
        self.errors: List[str] = []
        self.status: str = "initialized"

class EnergyReroutingAgent:
    """LangGraph-based Energy Rerouting Agent"""
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=config.GROQ_API_KEY,
            model=config.GROQ_MODEL,
            temperature=config.GROQ_TEMPERATURE,
            max_tokens=config.GROQ_MAX_TOKENS
        )
        self.state = EnergyReroutingState()
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create LangGraph workflow for energy rerouting"""
        
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("assess_outages", self._assess_outages_node)
        workflow.add_node("analyze_priorities", self._analyze_priorities_node)
        workflow.add_node("evaluate_capacity", self._evaluate_capacity_node)
        workflow.add_node("plan_rerouting", self._plan_rerouting_node)
        workflow.add_node("implement_load_shedding", self._implement_load_shedding_node)
        workflow.add_node("activate_backup", self._activate_backup_node)
        workflow.add_node("execute_rerouting", self._execute_rerouting_node)
        
        # Define workflow
        workflow.set_entry_point("assess_outages")
        workflow.add_edge("assess_outages", "analyze_priorities")
        workflow.add_edge("analyze_priorities", "evaluate_capacity")
        workflow.add_edge("evaluate_capacity", "plan_rerouting")
        workflow.add_edge("plan_rerouting", "implement_load_shedding")
        workflow.add_edge("implement_load_shedding", "activate_backup")
        workflow.add_edge("activate_backup", "execute_rerouting")
        workflow.add_edge("execute_rerouting", END)
        
        return workflow.compile()
    
    def _assess_outages_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Assess incoming outage alerts and impact"""
        try:
            logger.info("Assessing outages for rerouting decisions")
            
            # Get outage data from state or simulate
            outage_alerts = state.get("outage_alerts", [])
            
            if not outage_alerts:
                # Simulate outage scenario for demonstration
                outage_alerts = [{
                    "affected_zones": ["zone_1", "zone_3"],
                    "outage_type": "distribution_failure",
                    "severity": "critical",
                    "estimated_duration": 120,  # minutes
                    "root_cause": "transformer_failure",
                    "detected_at": datetime.now().isoformat()
                }]
            
            # Calculate total impact
            all_affected_zones = []
            total_estimated_load_lost = 0
            
            for alert in outage_alerts:
                affected_zones = alert.get("affected_zones", [])
                all_affected_zones.extend(affected_zones)
                
                # Estimate load lost per zone
                for zone in affected_zones:
                    estimated_load = 50 + (hash(zone) % 30)  # 50-80 kW per zone
                    total_estimated_load_lost += estimated_load
            
            # Remove duplicates
            unique_affected_zones = list(set(all_affected_zones))
            
            # LLM analysis of outage impact
            prompt = f"""
            Analyze outage alerts for energy rerouting strategy:
            
            Outage Alerts: {json.dumps(outage_alerts, indent=2)}
            Affected Zones: {unique_affected_zones}
            Total Load Lost: {total_estimated_load_lost} kW
            
            Assess:
            1. Rerouting urgency and complexity
            2. Critical infrastructure impact
            3. Load restoration priorities
            4. Resource requirements for recovery
            
            Return assessment in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            state["outage_alerts"] = outage_alerts
            state["affected_zones"] = unique_affected_zones
            state["total_load_lost"] = total_estimated_load_lost
            state["outage_assessment"] = response.content
            state["assessment_time"] = datetime.now().isoformat()
            
            logger.info(f"Outage assessment completed - {len(unique_affected_zones)} zones affected")
            return state
            
        except Exception as e:
            logger.error(f"Error assessing outages: {e}")
            state["errors"] = state.get("errors", []) + [f"Outage assessment failed: {str(e)}"]
            return state
    
    def _analyze_priorities_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze zone priorities and create priority map"""
        try:
            logger.info("Analyzing zone priorities for rerouting")
            
            affected_zones = state.get("affected_zones", [])
            all_zones = config.DEFAULT_ZONES
            
            # Create priority mapping
            priority_map = {}
            
            # Critical infrastructure gets highest priority
            for zone in all_zones:
                if zone in config.PRIORITY_ZONES:
                    priority_map[zone] = 1  # Highest priority
                elif "hospital" in zone.lower() or "emergency" in zone.lower():
                    priority_map[zone] = 1
                elif "commercial" in zone.lower() or "business" in zone.lower():
                    priority_map[zone] = 2  # Medium priority
                else:
                    priority_map[zone] = 3  # Standard priority
            
            # Adjust priorities based on current conditions
            current_hour = datetime.now().hour
            
            # Business hours adjustment
            if 8 <= current_hour <= 18:
                for zone in all_zones:
                    if "commercial" in zone.lower():
                        priority_map[zone] = max(1, priority_map[zone] - 1)  # Increase priority
            
            # Evening hours adjustment
            elif 18 <= current_hour <= 22:
                for zone in all_zones:
                    if "residential" in zone.lower():
                        priority_map[zone] = max(1, priority_map[zone] - 1)  # Increase priority
            
            # LLM priority analysis
            prompt = f"""
            Analyze priority assignments for energy rerouting:
            
            Current Hour: {current_hour}
            Affected Zones: {affected_zones}
            Priority Map: {json.dumps(priority_map, indent=2)}
            Critical Infrastructure Zones: {config.PRIORITY_ZONES}
            
            Evaluate:
            1. Priority assignment correctness
            2. Time-based priority adjustments
            3. Emergency service requirements
            4. Load restoration sequence recommendations
            
            Return priority analysis in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            # Sort zones by priority for restoration sequence
            restoration_sequence = sorted(
                affected_zones,
                key=lambda x: (priority_map.get(x, 5), x)
            )
            
            state["priority_map"] = priority_map
            state["restoration_sequence"] = restoration_sequence
            state["priority_analysis"] = response.content
            
            logger.info(f"Priority analysis completed - Restoration sequence: {restoration_sequence}")
            return state
            
        except Exception as e:
            logger.error(f"Error analyzing priorities: {e}")
            state["errors"] = state.get("errors", []) + [f"Priority analysis failed: {str(e)}"]
            return state
    
    def _evaluate_capacity_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate available grid capacity and backup sources"""
        try:
            logger.info("Evaluating grid capacity and backup sources")
            
            affected_zones = state.get("affected_zones", [])
            total_load_lost = state.get("total_load_lost", 0)
            
            # Simulate current grid capacity
            grid_capacity = {}
            backup_sources = {}
            
            for zone in config.DEFAULT_ZONES:
                if zone not in affected_zones:
                    # Available capacity in operational zones
                    max_capacity = 100  # kW
                    current_load = 50 + (hash(zone) % 30)
                    available_capacity = max_capacity - current_load
                    
                    grid_capacity[zone] = {
                        "max_capacity": max_capacity,
                        "current_load": current_load,
                        "available_capacity": available_capacity,
                        "utilization": current_load / max_capacity,
                        "can_support_additional": available_capacity > 10
                    }
                
                # Backup power sources
                if zone in config.PRIORITY_ZONES:
                    backup_sources[zone] = {
                        "type": "generator",
                        "capacity": 75,  # kW
                        "fuel_level": 0.8,  # 80%
                        "runtime_hours": 12,
                        "activation_time": 300,  # 5 minutes
                        "status": "standby"
                    }
            
            # Calculate total available capacity
            total_available = sum(cap["available_capacity"] for cap in grid_capacity.values())
            backup_capacity = sum(src["capacity"] for src in backup_sources.values())
            
            # Capacity adequacy assessment
            capacity_adequate = (total_available + backup_capacity * 0.6) >= total_load_lost
            
            # LLM capacity analysis
            prompt = f"""
            Evaluate grid capacity for energy rerouting:
            
            Total Load Lost: {total_load_lost} kW
            Total Available Grid Capacity: {total_available} kW
            Total Backup Capacity: {backup_capacity} kW
            Capacity Adequate: {capacity_adequate}
            
            Grid Capacity Details: {json.dumps({k: v for k, v in list(grid_capacity.items())[:3]}, indent=2)}
            Backup Sources: {len(backup_sources)} generators available
            
            Assess:
            1. Rerouting feasibility and constraints
            2. Backup power activation needs
            3. Load shedding requirements
            4. Grid stability considerations
            
            Return capacity evaluation in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            state["grid_capacity"] = grid_capacity
            state["backup_sources"] = backup_sources
            state["total_available_capacity"] = total_available
            state["backup_capacity"] = backup_capacity
            state["capacity_adequate"] = capacity_adequate
            state["capacity_analysis"] = response.content
            
            logger.info(f"Capacity evaluation completed - Available: {total_available}kW, Adequate: {capacity_adequate}")
            return state
            
        except Exception as e:
            logger.error(f"Error evaluating capacity: {e}")
            state["errors"] = state.get("errors", []) + [f"Capacity evaluation failed: {str(e)}"]
            return state
    
    def _plan_rerouting_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive rerouting plan"""
        try:
            logger.info("Creating energy rerouting plan")
            
            affected_zones = state.get("affected_zones", [])
            restoration_sequence = state.get("restoration_sequence", [])
            grid_capacity = state.get("grid_capacity", {})
            backup_sources = state.get("backup_sources", {})
            capacity_adequate = state.get("capacity_adequate", False)
            
            rerouting_plan = {
                "plan_id": f"rerouting_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "created_at": datetime.now().isoformat(),
                "strategy": "prioritized_restoration",
                "phases": []
            }
            
            # Phase 1: Immediate critical infrastructure
            critical_zones = [zone for zone in restoration_sequence if state["priority_map"].get(zone) == 1]
            if critical_zones:
                rerouting_plan["phases"].append({
                    "phase": 1,
                    "name": "Critical Infrastructure Restoration",
                    "zones": critical_zones,
                    "method": "backup_power",
                    "estimated_duration": 10,  # minutes
                    "power_source": "generators"
                })
            
            # Phase 2: Grid rerouting for medium priority
            medium_zones = [zone for zone in restoration_sequence if state["priority_map"].get(zone) == 2]
            available_zones = [zone for zone, cap in grid_capacity.items() if cap["can_support_additional"]]
            
            if medium_zones and available_zones and capacity_adequate:
                rerouting_plan["phases"].append({
                    "phase": 2,
                    "name": "Grid Rerouting",
                    "zones": medium_zones[:len(available_zones)],  # Limited by available capacity
                    "method": "grid_rerouting",
                    "estimated_duration": 20,  # minutes
                    "power_source": "neighboring_zones",
                    "source_zones": available_zones
                })
            
            # Phase 3: Load shedding if necessary
            remaining_zones = [zone for zone in restoration_sequence if zone not in critical_zones + medium_zones]
            if remaining_zones and not capacity_adequate:
                rerouting_plan["phases"].append({
                    "phase": 3,
                    "name": "Managed Load Shedding",
                    "zones": remaining_zones,
                    "method": "load_shedding",
                    "estimated_duration": 60,  # minutes
                    "power_reduction": "30%"
                })
            
            # LLM plan validation
            prompt = f"""
            Review and validate energy rerouting plan:
            
            Rerouting Plan: {json.dumps(rerouting_plan, indent=2)}
            Total Affected Zones: {len(affected_zones)}
            Available Grid Capacity: Adequate={capacity_adequate}
            
            Validate:
            1. Plan feasibility and timing
            2. Resource allocation efficiency
            3. Risk mitigation adequacy
            4. Improvement recommendations
            
            Return plan validation in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            state["rerouting_plan"] = rerouting_plan
            state["plan_validation"] = response.content
            
            logger.info(f"Rerouting plan created with {len(rerouting_plan['phases'])} phases")
            return state
            
        except Exception as e:
            logger.error(f"Error planning rerouting: {e}")
            state["errors"] = state.get("errors", []) + [f"Rerouting planning failed: {str(e)}"]
            return state
    
    def _implement_load_shedding_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Implement load shedding if required"""
        try:
            logger.info("Implementing load shedding measures")
            
            rerouting_plan = state.get("rerouting_plan", {})
            load_shedding_schedule = []
            
            # Find load shedding phases
            for phase in rerouting_plan.get("phases", []):
                if phase.get("method") == "load_shedding":
                    affected_zones = phase.get("zones", [])
                    reduction_percentage = int(phase.get("power_reduction", "30%").replace("%", ""))
                    
                    for zone in affected_zones:
                        current_load = 50 + (hash(zone) % 30)  # Simulated current load
                        reduction_amount = current_load * (reduction_percentage / 100)
                        
                        load_shedding_schedule.append({
                            "zone": zone,
                            "current_load": current_load,
                            "reduction_percentage": reduction_percentage,
                            "reduction_amount": reduction_amount,
                            "new_load": current_load - reduction_amount,
                            "implementation_time": datetime.now() + timedelta(minutes=phase.get("estimated_duration", 30)),
                            "non_essential_loads": ["lighting_decorative", "hvac_comfort", "non_critical_equipment"]
                        })
            
            if load_shedding_schedule:
                # Calculate total load reduction
                total_reduction = sum(item["reduction_amount"] for item in load_shedding_schedule)
                
                logger.warning(f"Load shedding implemented - {total_reduction:.1f}kW reduction across {len(load_shedding_schedule)} zones")
            else:
                logger.info("No load shedding required")
            
            state["load_shedding_schedule"] = load_shedding_schedule
            state["load_shedding_implemented"] = len(load_shedding_schedule) > 0
            
            return state
            
        except Exception as e:
            logger.error(f"Error implementing load shedding: {e}")
            state["errors"] = state.get("errors", []) + [f"Load shedding implementation failed: {str(e)}"]
            return state
    
    def _activate_backup_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Activate backup power sources"""
        try:
            logger.info("Activating backup power sources")
            
            rerouting_plan = state.get("rerouting_plan", {})
            backup_sources = state.get("backup_sources", {})
            backup_activations = []
            
            # Find backup power phases
            for phase in rerouting_plan.get("phases", []):
                if phase.get("method") == "backup_power":
                    zones_needing_backup = phase.get("zones", [])
                    
                    for zone in zones_needing_backup:
                        if zone in backup_sources:
                            backup_info = backup_sources[zone]
                            
                            activation = {
                                "zone": zone,
                                "backup_type": backup_info["type"],
                                "capacity": backup_info["capacity"],
                                "activation_time": datetime.now() + timedelta(minutes=backup_info["activation_time"] // 60),
                                "estimated_runtime": backup_info["runtime_hours"],
                                "fuel_level": backup_info["fuel_level"],
                                "status": "activating",
                                "activation_id": f"backup_{zone}_{datetime.now().strftime('%H%M%S')}"
                            }
                            
                            backup_activations.append(activation)
            
            if backup_activations:
                total_backup_capacity = sum(act["capacity"] for act in backup_activations)
                logger.info(f"Backup power activated - {total_backup_capacity}kW across {len(backup_activations)} zones")
            else:
                logger.info("No backup power activation required")
            
            state["backup_activations"] = backup_activations
            state["backup_activated"] = len(backup_activations) > 0
            
            return state
            
        except Exception as e:
            logger.error(f"Error activating backup power: {e}")
            state["errors"] = state.get("errors", []) + [f"Backup activation failed: {str(e)}"]
            return state
    
    def _execute_rerouting_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the rerouting commands"""
        try:
            logger.info("Executing energy rerouting commands")
            
            rerouting_plan = state.get("rerouting_plan", {})
            grid_capacity = state.get("grid_capacity", {})
            rerouting_commands = []
            
            # Generate rerouting commands for grid rerouting phases
            for phase in rerouting_plan.get("phases", []):
                if phase.get("method") == "grid_rerouting":
                    target_zones = phase.get("zones", [])
                    source_zones = phase.get("source_zones", [])
                    
                    for i, target_zone in enumerate(target_zones):
                        if i < len(source_zones):
                            source_zone = source_zones[i]
                            source_capacity = grid_capacity.get(source_zone, {})
                            
                            # Calculate rerouting parameters
                            target_load = 50 + (hash(target_zone) % 30)  # Estimated load needed
                            available_capacity = source_capacity.get("available_capacity", 0)
                            rerouting_amount = min(target_load, available_capacity * 0.8)  # 80% of available
                            
                            command = {
                                "command_id": f"reroute_{datetime.now().strftime('%H%M%S')}_{i}",
                                "command_type": "grid_rerouting",
                                "source_zone": source_zone,
                                "target_zone": target_zone,
                                "rerouting_amount": rerouting_amount,
                                "priority": state["priority_map"].get(target_zone, 3),
                                "execution_time": datetime.now() + timedelta(minutes=phase.get("estimated_duration", 20)),
                                "status": "pending",
                                "estimated_completion": datetime.now() + timedelta(minutes=30)
                            }
                            
                            rerouting_commands.append(command)
            
            # Send commands to Kafka
            success_count = 0
            for command in rerouting_commands:
                success = power_producer.send_rerouting_command({
                    "command_id": command["command_id"],
                    "command_type": command["command_type"],
                    "source_zone": command["source_zone"],
                    "target_zone": command["target_zone"],
                    "rerouting_amount": command["rerouting_amount"],
                    "priority": "high" if command["priority"] <= 2 else "medium",
                    "rerouting_data": command
                })
                
                if success:
                    success_count += 1
                    command["status"] = "sent"
            
            # Update state
            state["rerouting_commands"] = rerouting_commands
            state["commands_sent"] = success_count
            state["execution_time"] = datetime.now().isoformat()
            
            if success_count == len(rerouting_commands):
                state["status"] = "rerouting_complete"
                logger.info(f"All {success_count} rerouting commands executed successfully")
            else:
                state["status"] = "rerouting_partial"
                logger.warning(f"Only {success_count}/{len(rerouting_commands)} rerouting commands succeeded")
            
            return state
            
        except Exception as e:
            logger.error(f"Error executing rerouting: {e}")
            state["errors"] = state.get("errors", []) + [f"Rerouting execution failed: {str(e)}"]
            state["status"] = "rerouting_failed"
            return state
    
    def execute_energy_rerouting(self, outage_alerts: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Execute energy rerouting workflow"""
        try:
            logger.info("Starting energy rerouting workflow")
            
            # Initialize state
            initial_state = {
                "workflow_id": f"rerouting_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "started_at": datetime.now().isoformat(),
                "outage_alerts": outage_alerts or [],
                "errors": []
            }
            
            # Execute workflow
            result = self.workflow.invoke(initial_state)
            
            logger.info(f"Energy rerouting completed - Status: {result.get('status', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Energy rerouting workflow failed: {e}")
            return {
                "status": "rerouting_failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Create singleton instance
energy_rerouting_agent = EnergyReroutingAgent()
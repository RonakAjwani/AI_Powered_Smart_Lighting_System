import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
from ..config.settings import config
from ..kafka.kafka_producer import weather_producer

logger = logging.getLogger(__name__)

class DisasterResponseState(TypedDict):
    """State class for disaster response advisor workflow"""
    emergency_conditions: Dict[str, Any]
    impact_matrix: Dict[str, Any]
    zone_priorities: Dict[str, int]
    affected_zones: List[str]
    emergency_protocols: Dict[str, Any]
    evacuation_routes: Dict[str, List[str]]
    safety_assessments: Dict[str, Any]
    response_actions: List[Dict[str, Any]]
    lighting_strategies: Dict[str, Any]
    resource_allocation: Dict[str, Any]
    processed_zones: List[str]
    critical_situations: List[str]
    errors: List[str]
    status: str

class DisasterResponseAdvisorAgent:
    """
    LangGraph-based agent for advising on lighting strategy during storms, 
    floods, and other weather emergencies for safety and emergency response
    """
    
    def __init__(self):
        self.groq_config = config.get_groq_config()
        self.llm = ChatGroq(
            groq_api_key=self.groq_config['api_key'],
            model_name=self.groq_config['model'],
            temperature=self.groq_config['temperature'],
            max_tokens=self.groq_config['max_tokens']
        )
        
        # Emergency response protocols
        self.emergency_protocols = self._initialize_emergency_protocols()
        self.evacuation_routes = self._initialize_evacuation_routes()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow for disaster response advisory"""
        workflow = StateGraph(DisasterResponseState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_response)
        workflow.add_node("assess_emergency_conditions", self._assess_emergency_conditions_node)
        workflow.add_node("identify_affected_zones", self._identify_affected_zones_node)
        workflow.add_node("prioritize_safety_zones", self._prioritize_safety_zones_node)
        workflow.add_node("develop_lighting_strategy", self._develop_lighting_strategy_node)
        workflow.add_node("plan_evacuation_support", self._plan_evacuation_support_node)
        workflow.add_node("generate_emergency_protocols", self._generate_emergency_protocols_node)
        workflow.add_node("allocate_resources", self._allocate_resources_node)
        workflow.add_node("coordinate_response", self._coordinate_response_node)
        workflow.add_node("publish_emergency_plan", self._publish_emergency_plan_node)
        workflow.add_node("finalize", self._finalize_response)
        
        # Define workflow edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "assess_emergency_conditions")
        workflow.add_edge("assess_emergency_conditions", "identify_affected_zones")
        workflow.add_edge("identify_affected_zones", "prioritize_safety_zones")
        workflow.add_edge("prioritize_safety_zones", "develop_lighting_strategy")
        workflow.add_edge("develop_lighting_strategy", "plan_evacuation_support")
        workflow.add_edge("plan_evacuation_support", "generate_emergency_protocols")
        workflow.add_edge("generate_emergency_protocols", "allocate_resources")
        workflow.add_edge("allocate_resources", "coordinate_response")
        workflow.add_edge("coordinate_response", "publish_emergency_plan")
        workflow.add_edge("publish_emergency_plan", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def advise_disaster_response(self) -> Dict[str, Any]:
        """Main method to execute disaster response advisory workflow"""
        try:
            logger.info("Starting disaster response advisory workflow")
            
            # Initialize state
            initial_state = DisasterResponseState(
                emergency_conditions={},
                impact_matrix={},
                zone_priorities={},
                affected_zones=[],
                emergency_protocols={},
                evacuation_routes=self.evacuation_routes,
                safety_assessments={},
                response_actions=[],
                lighting_strategies={},
                resource_allocation={},
                processed_zones=[],
                critical_situations=[],
                errors=[],
                status="initializing"
            )
            
            # Execute workflow
            final_state = self.workflow.invoke(initial_state)
            
            return {
                "status": final_state["status"],
                "affected_zones": len(final_state["affected_zones"]),
                "critical_situations": len(final_state["critical_situations"]),
                "emergency_protocols": final_state["emergency_protocols"],
                "lighting_strategies": final_state["lighting_strategies"],
                "response_actions": len(final_state["response_actions"]),
                "resource_allocation": final_state["resource_allocation"],
                "errors": final_state["errors"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in disaster response workflow: {e}")
            return {
                "status": "workflow_failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _initialize_response(self, state: DisasterResponseState) -> DisasterResponseState:
        """Initialize disaster response advisory"""
        logger.info("Initializing disaster response advisory")
        
        state["status"] = "assessing_emergency"
        state["emergency_protocols"] = self.emergency_protocols.copy()
        
        return state
    
    def _assess_emergency_conditions_node(self, state: DisasterResponseState) -> DisasterResponseState:
        """Assess current emergency weather conditions"""
        logger.info("Assessing emergency weather conditions")
        
        try:
            # Collect emergency weather data
            emergency_data = self._collect_emergency_weather_data()
            state["emergency_conditions"] = emergency_data
            
            # Determine emergency types
            emergency_types = self._classify_emergency_types(emergency_data)
            state["emergency_conditions"]["emergency_types"] = emergency_types
            
            # Assess overall threat level
            threat_level = self._assess_threat_level(emergency_data)
            state["emergency_conditions"]["threat_level"] = threat_level
            
            if threat_level in ["high", "critical"]:
                state["critical_situations"].append("severe_weather_emergency")
                
        except Exception as e:
            error_msg = f"Error assessing emergency conditions: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _identify_affected_zones_node(self, state: DisasterResponseState) -> DisasterResponseState:
        """Identify zones affected by emergency conditions"""
        logger.info("Identifying affected zones")
        
        try:
            emergency_conditions = state["emergency_conditions"]
            
            for zone_id in config.DEFAULT_ZONES:
                zone_impact = self._assess_zone_emergency_impact(zone_id, emergency_conditions)
                
                if zone_impact["is_affected"]:
                    state["affected_zones"].append(zone_id)
                    state["impact_matrix"][zone_id] = zone_impact
                    state["processed_zones"].append(zone_id)
                    
                    if zone_impact["severity"] in ["high", "critical"]:
                        state["critical_situations"].append(f"critical_zone_{zone_id}")
                        
        except Exception as e:
            error_msg = f"Error identifying affected zones: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _prioritize_safety_zones_node(self, state: DisasterResponseState) -> DisasterResponseState:
        """Prioritize zones based on safety requirements"""
        logger.info("Prioritizing safety zones")
        
        try:
            for zone_id in state["affected_zones"]:
                impact_data = state["impact_matrix"][zone_id]
                priority = self._calculate_safety_priority(zone_id, impact_data)
                state["zone_priorities"][zone_id] = priority
                
                # Conduct safety assessment
                safety_assessment = self._conduct_safety_assessment(zone_id, impact_data)
                state["safety_assessments"][zone_id] = safety_assessment
                
        except Exception as e:
            error_msg = f"Error prioritizing safety zones: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _develop_lighting_strategy_node(self, state: DisasterResponseState) -> DisasterResponseState:
        """Develop emergency lighting strategies"""
        logger.info("Developing emergency lighting strategies")
        
        try:
            # Generate LLM-based lighting strategy
            strategy_prompt = self._prepare_strategy_prompt(state)
            
            prompt = f"""
            Develop emergency lighting strategies for the following disaster scenario:
            
            Emergency Situation:
            {strategy_prompt}
            
            Provide specific strategies for:
            1. Emergency lighting configurations for each affected zone
            2. Evacuation route illumination priorities
            3. Safety beacon placement and patterns
            4. Power conservation during extended emergencies
            5. Communication lighting signals for emergency responders
            
            Focus on life safety, visibility, and emergency response support.
            Provide specific lighting percentages, patterns, and timings.
            """
            
            message = HumanMessage(content=prompt)
            response = self.llm.invoke([message])
            
            # Parse lighting strategies
            lighting_strategies = self._parse_lighting_strategies(response.content, state)
            state["lighting_strategies"] = lighting_strategies
            
        except Exception as e:
            error_msg = f"Error developing lighting strategy: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _plan_evacuation_support_node(self, state: DisasterResponseState) -> DisasterResponseState:
        """Plan lighting support for evacuation routes"""
        logger.info("Planning evacuation lighting support")
        
        try:
            for zone_id in state["affected_zones"]:
                if zone_id in state["evacuation_routes"]:
                    evacuation_plan = self._create_evacuation_lighting_plan(
                        zone_id, 
                        state["evacuation_routes"][zone_id],
                        state["safety_assessments"].get(zone_id, {})
                    )
                    
                    # Add evacuation support to lighting strategy
                    if "evacuation_support" not in state["lighting_strategies"]:
                        state["lighting_strategies"]["evacuation_support"] = {}
                    
                    state["lighting_strategies"]["evacuation_support"][zone_id] = evacuation_plan
                    
        except Exception as e:
            error_msg = f"Error planning evacuation support: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _generate_emergency_protocols_node(self, state: DisasterResponseState) -> DisasterResponseState:
        """Generate specific emergency protocols"""
        logger.info("Generating emergency protocols")
        
        try:
            emergency_types = state["emergency_conditions"].get("emergency_types", [])
            
            for emergency_type in emergency_types:
                protocol = self._generate_emergency_protocol(
                    emergency_type, 
                    state["affected_zones"],
                    state["lighting_strategies"]
                )
                
                if "specific_protocols" not in state["emergency_protocols"]:
                    state["emergency_protocols"]["specific_protocols"] = {}
                
                state["emergency_protocols"]["specific_protocols"][emergency_type] = protocol
                
        except Exception as e:
            error_msg = f"Error generating emergency protocols: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _allocate_resources_node(self, state: DisasterResponseState) -> DisasterResponseState:
        """Allocate emergency lighting resources"""
        logger.info("Allocating emergency resources")
        
        try:
            # Calculate resource requirements
            resource_needs = self._calculate_resource_needs(state)
            
            # Prioritize resource allocation
            resource_allocation = self._prioritize_resource_allocation(
                resource_needs, 
                state["zone_priorities"]
            )
            
            state["resource_allocation"] = resource_allocation
            
        except Exception as e:
            error_msg = f"Error allocating resources: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _coordinate_response_node(self, state: DisasterResponseState) -> DisasterResponseState:
        """Coordinate emergency response actions"""
        logger.info("Coordinating emergency response")
        
        try:
            # Generate response actions in priority order
            sorted_zones = sorted(
                state["affected_zones"], 
                key=lambda x: state["zone_priorities"].get(x, 0), 
                reverse=True
            )
            
            for zone_id in sorted_zones:
                response_action = self._create_response_action(
                    zone_id,
                    state["impact_matrix"].get(zone_id, {}),
                    state["lighting_strategies"],
                    state["resource_allocation"]
                )
                
                state["response_actions"].append(response_action)
                
        except Exception as e:
            error_msg = f"Error coordinating response: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _publish_emergency_plan_node(self, state: DisasterResponseState) -> DisasterResponseState:
        """Publish emergency plan to Kafka"""
        logger.info("Publishing emergency plan")
        
        try:
            # Publish emergency protocols
            for emergency_type, protocol in state["emergency_protocols"].get("specific_protocols", {}).items():
                weather_producer.publish_emergency_protocol(
                    emergency_type,
                    state["affected_zones"],
                    protocol
                )
            
            # Publish zone-specific emergency lighting
            for zone_id in state["affected_zones"]:
                emergency_lighting = {
                    "zone_id": zone_id,
                    "lighting_strategy": state["lighting_strategies"].get("zones", {}).get(zone_id, {}),
                    "priority": state["zone_priorities"].get(zone_id, 1),
                    "safety_assessment": state["safety_assessments"].get(zone_id, {}),
                    "response_actions": [
                        action for action in state["response_actions"] 
                        if action.get("zone_id") == zone_id
                    ]
                }
                
                weather_producer.publish_weather_alert(
                    zone_id,
                    "emergency_lighting_protocol",
                    "critical",
                    emergency_lighting
                )
                
        except Exception as e:
            error_msg = f"Error publishing emergency plan: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _finalize_response(self, state: DisasterResponseState) -> DisasterResponseState:
        """Finalize disaster response advisory workflow"""
        logger.info("Finalizing disaster response advisory")
        
        if len(state["affected_zones"]) > 0:
            state["status"] = "response_plan_complete"
        else:
            state["status"] = "no_emergency_detected"
        
        return state
    
    # Helper methods
    def _initialize_emergency_protocols(self) -> Dict[str, Any]:
        """Initialize emergency response protocols"""
        return {
            "storm": {
                "name": "Storm Emergency Protocol",
                "lighting_mode": "high_intensity",
                "flash_pattern": "slow_warning",
                "duration": "weather_dependent",
                "safety_measures": ["increase_brightness", "enable_warning_beacons"]
            },
            "flood": {
                "name": "Flood Emergency Protocol", 
                "lighting_mode": "flood_safe",
                "flash_pattern": "evacuation_signal",
                "duration": "until_safe",
                "safety_measures": ["waterproof_mode", "elevated_lighting", "route_marking"]
            },
            "extreme_wind": {
                "name": "High Wind Emergency Protocol",
                "lighting_mode": "wind_resistant",
                "flash_pattern": "danger_warning",
                "duration": "wind_dependent",
                "safety_measures": ["secure_fixtures", "backup_power", "shelter_lighting"]
            },
            "severe_weather": {
                "name": "Severe Weather Protocol",
                "lighting_mode": "emergency_maximum",
                "flash_pattern": "emergency_strobe",
                "duration": "extended",
                "safety_measures": ["full_illumination", "emergency_signals", "shelter_identification"]
            }
        }
    
    def _initialize_evacuation_routes(self) -> Dict[str, List[str]]:
        """Initialize evacuation routes for each zone"""
        return {
            "zone_1": ["route_1a", "route_1b", "emergency_exit_1"],
            "zone_2": ["route_2a", "route_2b", "emergency_exit_2"],
            "zone_3": ["route_3a", "emergency_exit_3"],
            "zone_4": ["route_4a", "route_4b", "emergency_exit_4"],
            "zone_5": ["route_5a", "emergency_exit_5"]
        }
    
    def _collect_emergency_weather_data(self) -> Dict[str, Any]:
        """Collect emergency weather data"""
        import random
        
        # Simulate emergency weather conditions
        return {
            "wind_speed": random.uniform(20, 50),  # High wind
            "precipitation": random.uniform(15, 40),  # Heavy rain
            "visibility": random.randint(100, 800),  # Poor visibility
            "temperature": random.uniform(-5, 40),
            "pressure": random.uniform(980, 1040),
            "weather_condition": random.choice(["Thunderstorm", "Tornado", "Blizzard", "Flood"]),
            "severity": random.choice(["high", "critical"]),
            "duration_estimate": random.randint(60, 360),  # minutes
            "timestamp": datetime.now().isoformat()
        }
    
    def _classify_emergency_types(self, emergency_data: Dict[str, Any]) -> List[str]:
        """Classify types of emergency based on weather data"""
        emergency_types = []
        
        wind_speed = emergency_data.get("wind_speed", 0)
        precipitation = emergency_data.get("precipitation", 0)
        visibility = emergency_data.get("visibility", 10000)
        condition = emergency_data.get("weather_condition", "")
        
        if wind_speed > config.EMERGENCY_WIND_SPEED:
            emergency_types.append("extreme_wind")
        
        if precipitation > config.FLOOD_RISK_THRESHOLD:
            emergency_types.append("flood")
        
        if condition in ["Thunderstorm", "Tornado"]:
            emergency_types.append("storm")
        
        if visibility < 500:
            emergency_types.append("low_visibility")
        
        if len(emergency_types) > 1 or condition in ["Tornado", "Blizzard"]:
            emergency_types.append("severe_weather")
        
        return emergency_types if emergency_types else ["weather_emergency"]
    
    def _assess_threat_level(self, emergency_data: Dict[str, Any]) -> str:
        """Assess overall threat level"""
        threat_score = 0
        
        # Wind threat
        wind_speed = emergency_data.get("wind_speed", 0)
        if wind_speed > config.EMERGENCY_WIND_SPEED * 1.5:
            threat_score += 4
        elif wind_speed > config.EMERGENCY_WIND_SPEED:
            threat_score += 3
        
        # Precipitation threat
        precipitation = emergency_data.get("precipitation", 0)
        if precipitation > config.FLOOD_RISK_THRESHOLD:
            threat_score += 4
        elif precipitation > config.EMERGENCY_PRECIPITATION:
            threat_score += 3
        
        # Visibility threat
        visibility = emergency_data.get("visibility", 10000)
        if visibility < 200:
            threat_score += 4
        elif visibility < 500:
            threat_score += 3
        
        # Weather condition threat
        condition = emergency_data.get("weather_condition", "")
        condition_threats = {
            "Tornado": 5, "Blizzard": 4, "Thunderstorm": 3, "Flood": 4
        }
        threat_score += condition_threats.get(condition, 1)
        
        # Determine threat level
        if threat_score >= 12:
            return "critical"
        elif threat_score >= 8:
            return "high"
        elif threat_score >= 4:
            return "medium"
        else:
            return "low"
    
    def _assess_zone_emergency_impact(self, zone_id: str, emergency_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Assess emergency impact on specific zone"""
        try:
            # Simulate zone-specific impact assessment
            base_impact = {
                "is_affected": True,
                "severity": emergency_conditions.get("severity", "medium"),
                "emergency_types": emergency_conditions.get("emergency_types", []),
                "estimated_duration": emergency_conditions.get("duration_estimate", 120),
                "safety_risk": "high",
                "evacuation_needed": False,
                "infrastructure_risk": "medium"
            }
            
            # Zone-specific factors
            threat_level = emergency_conditions.get("threat_level", "medium")
            if threat_level == "critical":
                base_impact["evacuation_needed"] = True
                base_impact["safety_risk"] = "critical"
            
            # Visibility impact
            visibility = emergency_conditions.get("visibility", 10000)
            if visibility < 300:
                base_impact["lighting_priority"] = "maximum"
            elif visibility < 1000:
                base_impact["lighting_priority"] = "high"
            else:
                base_impact["lighting_priority"] = "medium"
            
            return base_impact
            
        except Exception as e:
            logger.error(f"Error assessing zone emergency impact: {e}")
            return {"is_affected": False, "error": str(e)}
    
    def _calculate_safety_priority(self, zone_id: str, impact_data: Dict[str, Any]) -> int:
        """Calculate safety priority for zone"""
        try:
            priority = 1  # Base priority
            
            # Severity-based priority
            severity = impact_data.get("severity", "low")
            severity_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}
            priority += severity_scores.get(severity, 1)
            
            # Safety risk priority
            safety_risk = impact_data.get("safety_risk", "low")
            priority += severity_scores.get(safety_risk, 1)
            
            # Evacuation priority
            if impact_data.get("evacuation_needed", False):
                priority += 3
            
            # Zone importance (could be enhanced with real data)
            zone_importance = {"zone_1": 2, "zone_2": 1, "zone_3": 3, "zone_4": 1, "zone_5": 2}
            priority += zone_importance.get(zone_id, 1)
            
            return min(priority, 10)  # Cap at 10
            
        except Exception as e:
            logger.error(f"Error calculating safety priority: {e}")
            return 1
    
    def _conduct_safety_assessment(self, zone_id: str, impact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct comprehensive safety assessment"""
        return {
            "zone_id": zone_id,
            "overall_safety": impact_data.get("safety_risk", "medium"),
            "evacuation_status": "required" if impact_data.get("evacuation_needed") else "standby",
            "lighting_requirements": {
                "minimum_brightness": 80,  # percentage
                "recommended_brightness": 100,
                "backup_power": "required",
                "emergency_patterns": "enabled"
            },
            "access_routes": {
                "primary": "accessible",
                "secondary": "check_required",
                "emergency": "priority_clear"
            },
            "communication_needs": ["emergency_beacons", "status_indicators"],
            "monitoring_frequency": "continuous",
            "assessment_timestamp": datetime.now().isoformat()
        }
    
    def _prepare_strategy_prompt(self, state: DisasterResponseState) -> str:
        """Prepare strategy prompt for LLM"""
        emergency_conditions = state["emergency_conditions"]
        affected_zones = state["affected_zones"]
        
        prompt_parts = [
            f"Emergency Type: {', '.join(emergency_conditions.get('emergency_types', []))}",
            f"Threat Level: {emergency_conditions.get('threat_level', 'unknown')}",
            f"Affected Zones: {len(affected_zones)} zones",
            f"Wind Speed: {emergency_conditions.get('wind_speed', 'N/A')} m/s",
            f"Visibility: {emergency_conditions.get('visibility', 'N/A')} meters",
            f"Precipitation: {emergency_conditions.get('precipitation', 'N/A')} mm/h"
        ]
        
        # Add zone-specific details
        for zone_id in affected_zones[:3]:  # Limit to first 3 zones for prompt length
            impact = state["impact_matrix"].get(zone_id, {})
            prompt_parts.append(
                f"Zone {zone_id}: {impact.get('severity', 'unknown')} severity, "
                f"evacuation {'needed' if impact.get('evacuation_needed') else 'standby'}"
            )
        
        return "\n".join(prompt_parts)
    
    def _parse_lighting_strategies(self, llm_response: str, state: DisasterResponseState) -> Dict[str, Any]:
        """Parse LLM response into lighting strategies"""
        try:
            strategies = {
                "overall_approach": "emergency_response",
                "zones": {},
                "evacuation_support": {},
                "emergency_beacons": {},
                "power_management": "priority_zones_first",
                "llm_analysis": llm_response,
                "generated_at": datetime.now().isoformat()
            }
            
            # Generate zone-specific strategies
            for zone_id in state["affected_zones"]:
                impact_data = state["impact_matrix"].get(zone_id, {})
                priority = state["zone_priorities"].get(zone_id, 1)
                
                strategies["zones"][zone_id] = {
                    "brightness_level": 100 if priority >= 7 else 80,
                    "flash_pattern": "emergency_strobe" if priority >= 8 else "slow_warning",
                    "color_mode": "high_visibility_white",
                    "backup_power": "enabled",
                    "duration": "continuous"
                }
            
            return strategies
            
        except Exception as e:
            logger.error(f"Error parsing lighting strategies: {e}")
            return {"error": str(e), "raw_response": llm_response}
    
    def _create_evacuation_lighting_plan(self, zone_id: str, evacuation_routes: List[str], 
                                       safety_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Create evacuation lighting plan for zone"""
        return {
            "zone_id": zone_id,
            "evacuation_routes": evacuation_routes,
            "route_lighting": {
                route: {
                    "brightness": 100,
                    "pattern": "directional_flow",
                    "color": "evacuation_blue",
                    "priority": "critical"
                } for route in evacuation_routes
            },
            "assembly_points": {
                "lighting_mode": "beacon_strobe",
                "visibility_range": "maximum",
                "identification_signals": "enabled"
            },
            "backup_systems": "redundant_power",
            "communication_lights": "emergency_status_display"
        }
    
    def _generate_emergency_protocol(self, emergency_type: str, affected_zones: List[str], 
                                   lighting_strategies: Dict[str, Any]) -> Dict[str, Any]:
        """Generate specific emergency protocol"""
        base_protocol = self.emergency_protocols.get(emergency_type, {})
        
        return {
            **base_protocol,
            "affected_zones": affected_zones,
            "activation_time": datetime.now().isoformat(),
            "estimated_duration": "weather_dependent",
            "lighting_configuration": lighting_strategies.get("zones", {}),
            "emergency_contacts": ["emergency_services", "facility_management"],
            "status_monitoring": "real_time",
            "escalation_criteria": {
                "condition_worsening": "immediate_escalation",
                "system_failure": "backup_activation",
                "evacuation_ordered": "maximum_response"
            }
        }
    
    def _calculate_resource_needs(self, state: DisasterResponseState) -> Dict[str, Any]:
        """Calculate emergency resource requirements"""
        return {
            "power_requirements": {
                "emergency_power": len(state["affected_zones"]) * 1000,  # Watts
                "backup_duration": 240,  # minutes
                "priority_zones": state["critical_situations"]
            },
            "equipment_needs": {
                "emergency_beacons": len(state["affected_zones"]) * 2,
                "backup_controllers": len(state["affected_zones"]),
                "communication_devices": len(state["affected_zones"])
            },
            "personnel_requirements": {
                "emergency_responders": max(2, len(state["affected_zones"]) // 2),
                "technical_support": 1,
                "coordination_team": 1
            }
        }
    
    def _prioritize_resource_allocation(self, resource_needs: Dict[str, Any], 
                                      zone_priorities: Dict[str, int]) -> Dict[str, Any]:
        """Prioritize resource allocation based on zone priorities"""
        # Sort zones by priority
        sorted_zones = sorted(zone_priorities.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "allocation_order": [zone_id for zone_id, _ in sorted_zones],
            "power_distribution": {
                zone_id: priority * 100 for zone_id, priority in sorted_zones  # Watts per priority
            },
            "equipment_priority": {
                zone_id: "critical" if priority >= 8 else "high" if priority >= 5 else "normal"
                for zone_id, priority in sorted_zones
            },
            "response_timeline": {
                "immediate": [z for z, p in sorted_zones if p >= 8],
                "urgent": [z for z, p in sorted_zones if 5 <= p < 8],
                "standard": [z for z, p in sorted_zones if p < 5]
            }
        }
    
    def _create_response_action(self, zone_id: str, impact_data: Dict[str, Any], 
                              lighting_strategies: Dict[str, Any], 
                              resource_allocation: Dict[str, Any]) -> Dict[str, Any]:
        """Create specific response action for zone"""
        return {
            "action_id": f"emergency_response_{zone_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "zone_id": zone_id,
            "action_type": "emergency_lighting_activation",
            "priority": resource_allocation.get("equipment_priority", {}).get(zone_id, "normal"),
            "lighting_configuration": lighting_strategies.get("zones", {}).get(zone_id, {}),
            "safety_measures": impact_data.get("emergency_types", []),
            "estimated_duration": impact_data.get("estimated_duration", 120),
            "success_criteria": {
                "lighting_operational": True,
                "visibility_adequate": True,
                "safety_maintained": True
            },
            "monitoring_requirements": "continuous",
            "created_at": datetime.now().isoformat()
        }

# Create agent instance
disaster_response_advisor_agent = DisasterResponseAdvisorAgent()
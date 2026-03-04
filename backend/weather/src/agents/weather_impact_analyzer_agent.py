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

class WeatherImpactState(TypedDict):
    """State class for weather impact analysis workflow"""
    weather_data: Dict[str, Any]
    sensor_data: Dict[str, Any]
    zone_map: Dict[str, Any]
    severity_matrix: Dict[str, Any]
    lighting_recommendations: Dict[str, Any]
    zone_priorities: Dict[str, int]
    impact_assessments: Dict[str, Any]
    processed_zones: List[str]
    critical_zones: List[str]
    errors: List[str]
    status: str

class WeatherImpactAnalyzerAgent:
    """
    LangGraph-based agent for analyzing weather impact on lighting systems
    and determining zone-level lighting adjustments
    """
    
    def __init__(self):
        self.groq_config = config.get_groq_config()
        self.llm = ChatGroq(
            groq_api_key=self.groq_config['api_key'],
            model_name=self.groq_config['model'],
            temperature=self.groq_config['temperature'],
            max_tokens=self.groq_config['max_tokens']
        )
        
        # Zone mapping data (GeoJSON style)
        self.zone_map = self._initialize_zone_map()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow for weather impact analysis"""
        workflow = StateGraph(WeatherImpactState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_analysis)
        workflow.add_node("collect_weather_data", self._collect_weather_data_node)
        workflow.add_node("collect_sensor_data", self._collect_sensor_data_node)
        workflow.add_node("calculate_severity_matrix", self._calculate_severity_matrix_node)
        workflow.add_node("assess_zone_impact", self._assess_zone_impact_node)
        workflow.add_node("prioritize_zones", self._prioritize_zones_node)
        workflow.add_node("generate_recommendations", self._generate_recommendations_node)
        workflow.add_node("analyze_critical_zones", self._analyze_critical_zones_node)
        workflow.add_node("publish_analysis", self._publish_analysis_node)
        workflow.add_node("finalize", self._finalize_analysis)
        
        # Define workflow edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "collect_weather_data")
        workflow.add_edge("collect_weather_data", "collect_sensor_data")
        workflow.add_edge("collect_sensor_data", "calculate_severity_matrix")
        workflow.add_edge("calculate_severity_matrix", "assess_zone_impact")
        workflow.add_edge("assess_zone_impact", "prioritize_zones")
        workflow.add_edge("prioritize_zones", "generate_recommendations")
        workflow.add_edge("generate_recommendations", "analyze_critical_zones")
        workflow.add_edge("analyze_critical_zones", "publish_analysis")
        workflow.add_edge("publish_analysis", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def analyze_weather_impact(self) -> Dict[str, Any]:
        """Main method to execute weather impact analysis workflow"""
        try:
            logger.info("Starting weather impact analysis workflow")
            
            # Initialize state
            initial_state = WeatherImpactState(
                weather_data={},
                sensor_data={},
                zone_map=self.zone_map,
                severity_matrix={},
                lighting_recommendations={},
                zone_priorities={},
                impact_assessments={},
                processed_zones=[],
                critical_zones=[],
                errors=[],
                status="initializing"
            )
            
            # Execute workflow
            final_state = self.workflow.invoke(initial_state)
            
            return {
                "status": final_state["status"],
                "processed_zones": len(final_state["processed_zones"]),
                "critical_zones": len(final_state["critical_zones"]),
                "severity_matrix": final_state["severity_matrix"],
                "lighting_recommendations": final_state["lighting_recommendations"],
                "impact_assessments": final_state["impact_assessments"],
                "errors": final_state["errors"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in weather impact analysis workflow: {e}")
            return {
                "status": "workflow_failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _initialize_analysis(self, state: WeatherImpactState) -> WeatherImpactState:
        """Initialize weather impact analysis"""
        logger.info("Initializing weather impact analysis")
        
        state["status"] = "collecting_data"
        
        # Initialize zone priorities (default values)
        for zone_id in config.DEFAULT_ZONES:
            state["zone_priorities"][zone_id] = 1  # Default priority
        
        return state
    
    def _collect_weather_data_node(self, state: WeatherImpactState) -> WeatherImpactState:
        """Collect current weather data and forecasts"""
        logger.info("Collecting weather data for impact analysis")
        
        try:
            # Simulate collecting weather data from W1/W2 agents
            # In real implementation, this would fetch from Kafka or database
            for zone_id in config.DEFAULT_ZONES:
                weather_data = self._simulate_weather_data(zone_id)
                if weather_data:
                    state["weather_data"][zone_id] = weather_data
                else:
                    state["errors"].append(f"Failed to collect weather data for {zone_id}")
                    
        except Exception as e:
            error_msg = f"Error collecting weather data: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _collect_sensor_data_node(self, state: WeatherImpactState) -> WeatherImpactState:
        """Collect real-time sensor data"""
        logger.info("Collecting sensor data for impact analysis")
        
        try:
            # Simulate collecting sensor data from environmental sensors
            for zone_id in config.DEFAULT_ZONES:
                sensor_data = self._simulate_sensor_data(zone_id)
                if sensor_data:
                    state["sensor_data"][zone_id] = sensor_data
                else:
                    state["errors"].append(f"Failed to collect sensor data for {zone_id}")
                    
        except Exception as e:
            error_msg = f"Error collecting sensor data: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _calculate_severity_matrix_node(self, state: WeatherImpactState) -> WeatherImpactState:
        """Calculate weather severity matrix for each zone"""
        logger.info("Calculating weather severity matrix")
        
        for zone_id in config.DEFAULT_ZONES:
            try:
                weather_data = state["weather_data"].get(zone_id, {})
                sensor_data = state["sensor_data"].get(zone_id, {})
                
                if weather_data or sensor_data:
                    severity_data = self._calculate_zone_severity(weather_data, sensor_data)
                    state["severity_matrix"][zone_id] = severity_data
                    state["processed_zones"].append(zone_id)
                else:
                    state["errors"].append(f"No data available for severity calculation in {zone_id}")
                    
            except Exception as e:
                error_msg = f"Error calculating severity for {zone_id}: {str(e)}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
        
        return state
    
    def _assess_zone_impact_node(self, state: WeatherImpactState) -> WeatherImpactState:
        """Assess weather impact on each zone's lighting needs"""
        logger.info("Assessing zone-level weather impact")
        
        for zone_id in state["processed_zones"]:
            try:
                severity_data = state["severity_matrix"][zone_id]
                zone_config = config.get_zone_config(zone_id)
                
                impact_assessment = self._assess_lighting_impact(severity_data, zone_config)
                state["impact_assessments"][zone_id] = impact_assessment
                
                # Identify critical zones
                if impact_assessment.get("risk_level") in ["high", "critical"]:
                    state["critical_zones"].append(zone_id)
                    
            except Exception as e:
                error_msg = f"Error assessing impact for {zone_id}: {str(e)}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
        
        return state
    
    def _prioritize_zones_node(self, state: WeatherImpactState) -> WeatherImpactState:
        """Prioritize zones based on impact severity and importance"""
        logger.info("Prioritizing zones for lighting adjustments")
        
        try:
            # Calculate priorities based on severity and zone importance
            for zone_id in state["processed_zones"]:
                severity_data = state["severity_matrix"].get(zone_id, {})
                impact_data = state["impact_assessments"].get(zone_id, {})
                
                priority_score = self._calculate_zone_priority(severity_data, impact_data, zone_id)
                state["zone_priorities"][zone_id] = priority_score
                
        except Exception as e:
            error_msg = f"Error prioritizing zones: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _generate_recommendations_node(self, state: WeatherImpactState) -> WeatherImpactState:
        """Generate lighting recommendations using LLM analysis"""
        logger.info("Generating lighting recommendations")
        
        try:
            # Prepare analysis summary for LLM
            analysis_summary = self._prepare_analysis_summary(state)
            
            prompt = f"""
            Analyze the following weather impact data and provide lighting adjustment recommendations:
            
            Weather Impact Analysis:
            {analysis_summary}
            
            Provide specific recommendations for:
            1. Lighting intensity adjustments per zone (percentage increase/decrease)
            2. Safety considerations for each critical zone
            3. Energy efficiency optimizations
            4. Priority order for implementing changes
            5. Emergency lighting protocols if needed
            
            Focus on visibility enhancement, safety, and energy conservation.
            Respond in structured format with specific percentages and actions.
            """
            
            message = HumanMessage(content=prompt)
            response = self.llm.invoke([message])
            
            # Parse recommendations
            recommendations = self._parse_lighting_recommendations(response.content, state)
            state["lighting_recommendations"] = recommendations
            
        except Exception as e:
            error_msg = f"Error generating recommendations: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _analyze_critical_zones_node(self, state: WeatherImpactState) -> WeatherImpactState:
        """Perform detailed analysis of critical zones"""
        logger.info("Analyzing critical zones in detail")
        
        for zone_id in state["critical_zones"]:
            try:
                severity_data = state["severity_matrix"][zone_id]
                impact_data = state["impact_assessments"][zone_id]
                
                critical_analysis = self._perform_critical_zone_analysis(
                    zone_id, severity_data, impact_data
                )
                
                # Update impact assessment with critical analysis
                state["impact_assessments"][zone_id]["critical_analysis"] = critical_analysis
                
            except Exception as e:
                error_msg = f"Error analyzing critical zone {zone_id}: {str(e)}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
        
        return state
    
    def _publish_analysis_node(self, state: WeatherImpactState) -> WeatherImpactState:
        """Publish weather impact analysis to Kafka"""
        logger.info("Publishing weather impact analysis")
        
        try:
            # Publish zone-level impact analysis
            for zone_id in state["processed_zones"]:
                impact_data = {
                    "zone_id": zone_id,
                    "severity_matrix": state["severity_matrix"].get(zone_id, {}),
                    "impact_assessment": state["impact_assessments"].get(zone_id, {}),
                    "priority": state["zone_priorities"].get(zone_id, 1),
                    "recommendations": state["lighting_recommendations"].get(zone_id, {}),
                    "timestamp": datetime.now().isoformat()
                }
                
                weather_producer.publish_impact_analysis(
                    zone_id, 
                    impact_data["severity_matrix"], 
                    impact_data["recommendations"]
                )
            
            # Publish critical zone alerts
            for zone_id in state["critical_zones"]:
                weather_producer.publish_weather_alert(
                    zone_id,
                    "critical_weather_impact",
                    "high",
                    state["impact_assessments"][zone_id]
                )
            
        except Exception as e:
            error_msg = f"Error publishing analysis: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _finalize_analysis(self, state: WeatherImpactState) -> WeatherImpactState:
        """Finalize weather impact analysis workflow"""
        logger.info("Finalizing weather impact analysis")
        
        if len(state["processed_zones"]) > 0:
            state["status"] = "analysis_complete"
        else:
            state["status"] = "analysis_failed"
        
        return state
    
    # Helper methods
    def _initialize_zone_map(self) -> Dict[str, Any]:
        """Initialize GeoJSON-style zone mapping"""
        zone_map = {
            "type": "FeatureCollection",
            "features": []
        }
        
        for zone_id in config.DEFAULT_ZONES:
            zone_config = config.get_zone_config(zone_id)
            coordinates = zone_config["coordinates"]
            
            feature = {
                "type": "Feature",
                "properties": {
                    "zone_id": zone_id,
                    "name": f"Lighting Zone {zone_id}",
                    "importance": "medium",  # high, medium, low
                    "lighting_type": "street",  # street, park, commercial
                    "pedestrian_traffic": "medium"
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [coordinates["lon"], coordinates["lat"]]
                }
            }
            zone_map["features"].append(feature)
        
        return zone_map
    
    def _simulate_weather_data(self, zone_id: str) -> Optional[Dict[str, Any]]:
        """Simulate weather data (replace with actual data fetching)"""
        import random
        
        try:
            return {
                "temperature": round(random.uniform(10, 30), 1),
                "humidity": round(random.uniform(40, 80), 1),
                "wind_speed": round(random.uniform(0, 20), 1),
                "visibility": random.randint(500, 10000),
                "precipitation": round(random.uniform(0, 10), 2),
                "weather_condition": random.choice(["Clear", "Cloudy", "Rain", "Fog", "Storm"]),
                "cloudiness": random.randint(0, 100),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error simulating weather data: {e}")
            return None
    
    def _simulate_sensor_data(self, zone_id: str) -> Optional[Dict[str, Any]]:
        """Simulate sensor data (replace with actual data fetching)"""
        import random
        
        try:
            return {
                "light_level": random.randint(50, 500),  # Lux
                "motion_detected": random.choice([True, False]),
                "air_quality": random.randint(50, 200),
                "noise_level": round(random.uniform(30, 80), 1),  # dB
                "device_status": "active",
                "battery_level": random.randint(70, 100),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error simulating sensor data: {e}")
            return None
    
    def _calculate_zone_severity(self, weather_data: Dict[str, Any], 
                               sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate weather severity matrix for a zone"""
        try:
            severity_score = 1  # Base severity
            
            # Weather-based severity factors
            visibility = weather_data.get("visibility", 10000)
            wind_speed = weather_data.get("wind_speed", 0)
            precipitation = weather_data.get("precipitation", 0)
            weather_condition = weather_data.get("weather_condition", "Clear")
            
            # Visibility impact
            if visibility < 1000:
                severity_score += 3
            elif visibility < 3000:
                severity_score += 2
            elif visibility < 5000:
                severity_score += 1
            
            # Wind impact
            if wind_speed > config.EMERGENCY_WIND_SPEED:
                severity_score += 3
            elif wind_speed > config.WIND_SPEED_THRESHOLD:
                severity_score += 2
            
            # Precipitation impact
            if precipitation > config.EMERGENCY_PRECIPITATION:
                severity_score += 3
            elif precipitation > config.PRECIPITATION_THRESHOLD:
                severity_score += 2
            
            # Weather condition impact
            condition_scores = {
                "Clear": 0, "Cloudy": 1, "Rain": 2, 
                "Fog": 3, "Storm": 4, "Thunderstorm": 5
            }
            severity_score += condition_scores.get(weather_condition, 1)
            
            # Sensor-based adjustments
            light_level = sensor_data.get("light_level", 300)
            if light_level < config.LOW_LIGHT_THRESHOLD:
                severity_score += 1
            
            # Calculate lighting adjustment factor
            lighting_adjustment = min(severity_score * 0.15, 1.5)  # Max 150% boost
            
            return {
                "severity_score": min(severity_score, 10),  # Cap at 10
                "visibility_factor": visibility,
                "wind_factor": wind_speed,
                "precipitation_factor": precipitation,
                "lighting_adjustment": lighting_adjustment,
                "risk_level": self._determine_risk_level(severity_score),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating zone severity: {e}")
            return {"severity_score": 1, "error": str(e)}
    
    def _determine_risk_level(self, severity_score: int) -> str:
        """Determine risk level based on severity score"""
        if severity_score >= 8:
            return "critical"
        elif severity_score >= 6:
            return "high"
        elif severity_score >= 4:
            return "medium"
        else:
            return "low"
    
    def _assess_lighting_impact(self, severity_data: Dict[str, Any], 
                              zone_config: Dict[str, Any]) -> Dict[str, Any]:
        """Assess lighting impact for a specific zone"""
        try:
            severity_score = severity_data.get("severity_score", 1)
            risk_level = severity_data.get("risk_level", "low")
            
            # Base lighting recommendations
            lighting_impact = {
                "brightness_adjustment": severity_data.get("lighting_adjustment", 1.0),
                "color_temperature_adjustment": 1.0,  # Warmer light in bad weather
                "flash_pattern": None,
                "emergency_mode": False
            }
            
            # Adjust based on risk level
            if risk_level == "critical":
                lighting_impact["emergency_mode"] = True
                lighting_impact["flash_pattern"] = "slow_flash"
                lighting_impact["color_temperature_adjustment"] = 0.8  # Warmer
            elif risk_level == "high":
                lighting_impact["brightness_adjustment"] *= 1.3
                lighting_impact["color_temperature_adjustment"] = 0.9
            
            # Zone-specific adjustments
            zone_thresholds = zone_config.get("thresholds", {})
            if severity_data.get("visibility_factor", 10000) < zone_thresholds.get("visibility", 1000):
                lighting_impact["brightness_adjustment"] *= 1.2
            
            return {
                "lighting_impact": lighting_impact,
                "risk_level": risk_level,
                "safety_priority": "high" if risk_level in ["high", "critical"] else "medium",
                "estimated_duration": "unknown",  # Would be enhanced with forecast data
                "recommended_actions": self._get_recommended_actions(risk_level),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error assessing lighting impact: {e}")
            return {"error": str(e)}
    
    def _get_recommended_actions(self, risk_level: str) -> List[str]:
        """Get recommended actions based on risk level"""
        actions = {
            "low": ["Monitor conditions", "Standard lighting operation"],
            "medium": ["Increase brightness by 20%", "Monitor for changes"],
            "high": ["Increase brightness by 50%", "Enable safety warnings", "Increase monitoring frequency"],
            "critical": ["Enable emergency lighting", "Activate warning systems", "Consider area restrictions"]
        }
        return actions.get(risk_level, ["Monitor conditions"])
    
    def _calculate_zone_priority(self, severity_data: Dict[str, Any], 
                               impact_data: Dict[str, Any], zone_id: str) -> int:
        """Calculate priority score for zone lighting adjustments"""
        try:
            base_priority = 1
            severity_score = severity_data.get("severity_score", 1)
            risk_level = impact_data.get("risk_level", "low")
            
            # Risk-based priority
            risk_priorities = {"low": 1, "medium": 2, "high": 3, "critical": 4}
            priority = risk_priorities.get(risk_level, 1)
            
            # Severity-based adjustment
            if severity_score >= 8:
                priority += 2
            elif severity_score >= 6:
                priority += 1
            
            # Zone importance (could be enhanced with real zone data)
            zone_importance = {"zone_1": 3, "zone_2": 2, "zone_3": 3, "zone_4": 1, "zone_5": 2}
            priority += zone_importance.get(zone_id, 1)
            
            return min(priority, 10)  # Cap at 10
            
        except Exception as e:
            logger.error(f"Error calculating zone priority: {e}")
            return 1
    
    def _prepare_analysis_summary(self, state: WeatherImpactState) -> str:
        """Prepare analysis summary for LLM processing"""
        summary_parts = []
        
        # Overall summary
        summary_parts.append(f"Weather Impact Analysis Summary:")
        summary_parts.append(f"- Total zones analyzed: {len(state['processed_zones'])}")
        summary_parts.append(f"- Critical zones identified: {len(state['critical_zones'])}")
        
        # Zone-specific details
        for zone_id in state["processed_zones"]:
            severity_data = state["severity_matrix"].get(zone_id, {})
            impact_data = state["impact_assessments"].get(zone_id, {})
            priority = state["zone_priorities"].get(zone_id, 1)
            
            zone_summary = f"""
            Zone {zone_id}:
            - Severity Score: {severity_data.get('severity_score', 'N/A')}
            - Risk Level: {impact_data.get('risk_level', 'unknown')}
            - Priority: {priority}
            - Visibility: {severity_data.get('visibility_factor', 'N/A')}m
            - Current Adjustment: {severity_data.get('lighting_adjustment', 'N/A')}x
            """
            summary_parts.append(zone_summary)
        
        return "\n".join(summary_parts)
    
    def _parse_lighting_recommendations(self, llm_response: str, 
                                      state: WeatherImpactState) -> Dict[str, Any]:
        """Parse LLM response into structured lighting recommendations"""
        try:
            # Basic parsing - would be enhanced with better NLP
            recommendations = {
                "overall_strategy": "adaptive_lighting",
                "zones": {},
                "emergency_protocols": [],
                "energy_considerations": "maintain_efficiency",
                "implementation_order": state["critical_zones"] + [
                    z for z in state["processed_zones"] if z not in state["critical_zones"]
                ],
                "llm_analysis": llm_response,
                "generated_at": datetime.now().isoformat()
            }
            
            # Zone-specific recommendations based on severity
            for zone_id in state["processed_zones"]:
                severity_data = state["severity_matrix"].get(zone_id, {})
                adjustment = severity_data.get("lighting_adjustment", 1.0)
                
                recommendations["zones"][zone_id] = {
                    "brightness_percentage": int(adjustment * 100),
                    "adjustment_factor": adjustment,
                    "priority": state["zone_priorities"].get(zone_id, 1),
                    "estimated_duration": "weather_dependent"
                }
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error parsing recommendations: {e}")
            return {
                "error": str(e),
                "raw_response": llm_response,
                "fallback_used": True
            }
    
    def _perform_critical_zone_analysis(self, zone_id: str, severity_data: Dict[str, Any], 
                                      impact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform detailed analysis for critical zones"""
        try:
            critical_analysis = {
                "zone_id": zone_id,
                "critical_factors": [],
                "immediate_actions": [],
                "monitoring_requirements": [],
                "escalation_triggers": {}
            }
            
            # Identify critical factors
            if severity_data.get("visibility_factor", 10000) < 500:
                critical_analysis["critical_factors"].append("extreme_low_visibility")
                critical_analysis["immediate_actions"].append("enable_maximum_brightness")
            
            if severity_data.get("wind_factor", 0) > config.EMERGENCY_WIND_SPEED:
                critical_analysis["critical_factors"].append("dangerous_wind_conditions")
                critical_analysis["immediate_actions"].append("activate_wind_warning_lights")
            
            if severity_data.get("precipitation_factor", 0) > config.EMERGENCY_PRECIPITATION:
                critical_analysis["critical_factors"].append("heavy_precipitation")
                critical_analysis["immediate_actions"].append("enable_flood_lighting_mode")
            
            # Monitoring requirements
            critical_analysis["monitoring_requirements"] = [
                "continuous_weather_monitoring",
                "real_time_sensor_validation",
                "emergency_response_readiness"
            ]
            
            # Escalation triggers
            critical_analysis["escalation_triggers"] = {
                "visibility_threshold": 200,  # meters
                "wind_threshold": config.EMERGENCY_WIND_SPEED * 1.5,
                "duration_threshold": 120  # minutes
            }
            
            return critical_analysis
            
        except Exception as e:
            logger.error(f"Error in critical zone analysis: {e}")
            return {"error": str(e)}

# Create agent instance
weather_impact_analyzer_agent = WeatherImpactAnalyzerAgent()
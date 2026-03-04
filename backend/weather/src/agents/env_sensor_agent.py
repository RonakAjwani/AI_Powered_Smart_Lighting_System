import logging
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
from ..config.settings import config
from ..kafka.kafka_producer import weather_producer

logger = logging.getLogger(__name__)

class EnvironmentalSensorState(TypedDict):
    """State class for environmental sensor agent workflow"""
    zones_to_monitor: List[str]
    sensor_readings: Dict[str, Any]
    historical_data: Dict[str, List[Dict[str, Any]]]
    deviation_analysis: Dict[str, Any]
    data_quality_scores: Dict[str, float]
    real_time_alerts: List[Dict[str, Any]]
    forecast_comparisons: Dict[str, Any]
    processed_zones: List[str]
    errors: List[str]
    status: str

class EnvironmentalSensorAgent:
    """
    LangGraph-based agent for collecting real-time environmental sensor data
    and analyzing deviations from weather forecasts
    """
    
    def __init__(self):
        self.groq_config = config.get_groq_config()
        self.llm = ChatGroq(
            groq_api_key=self.groq_config['api_key'],
            model_name=self.groq_config['model'],
            temperature=self.groq_config['temperature'],
            max_tokens=self.groq_config['max_tokens']
        )
        
        # Simulated sensor endpoints (in real implementation, these would be IoT device endpoints)
        self.sensor_endpoints = {
            zone_id: f"http://sensor-{zone_id}.local/api/readings"
            for zone_id in config.DEFAULT_ZONES
        }
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow for environmental sensor monitoring"""
        workflow = StateGraph(EnvironmentalSensorState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_monitoring)
        workflow.add_node("collect_sensor_data", self._collect_sensor_data_node)
        workflow.add_node("validate_data_quality", self._validate_data_quality_node)
        workflow.add_node("analyze_deviations", self._analyze_deviations_node)
        workflow.add_node("compare_forecasts", self._compare_forecasts_node)
        workflow.add_node("generate_insights", self._generate_insights_node)
        workflow.add_node("detect_anomalies", self._detect_anomalies_node)
        workflow.add_node("publish_readings", self._publish_readings_node)
        workflow.add_node("finalize", self._finalize_monitoring)
        
        # Define workflow edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "collect_sensor_data")
        workflow.add_edge("collect_sensor_data", "validate_data_quality")
        workflow.add_edge("validate_data_quality", "analyze_deviations")
        workflow.add_edge("analyze_deviations", "compare_forecasts")
        workflow.add_edge("compare_forecasts", "generate_insights")
        workflow.add_edge("generate_insights", "detect_anomalies")
        workflow.add_edge("detect_anomalies", "publish_readings")
        workflow.add_edge("publish_readings", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def collect_environmental_data(self) -> Dict[str, Any]:
        """Main method to execute environmental sensor monitoring workflow"""
        try:
            logger.info("Starting environmental sensor monitoring workflow")
            
            # Initialize state
            initial_state = EnvironmentalSensorState(
                zones_to_monitor=config.DEFAULT_ZONES.copy(),
                sensor_readings={},
                historical_data={},
                deviation_analysis={},
                data_quality_scores={},
                real_time_alerts=[],
                forecast_comparisons={},
                processed_zones=[],
                errors=[],
                status="initializing"
            )
            
            # Execute workflow
            final_state = self.workflow.invoke(initial_state)
            
            return {
                "status": final_state["status"],
                "processed_zones": len(final_state["processed_zones"]),
                "total_zones": len(config.DEFAULT_ZONES),
                "average_data_quality": (
                    sum(final_state["data_quality_scores"].values()) / 
                    len(final_state["data_quality_scores"]) 
                    if final_state["data_quality_scores"] else 0
                ),
                "alerts_generated": len(final_state["real_time_alerts"]),
                "deviation_analysis": final_state["deviation_analysis"],
                "errors": final_state["errors"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in environmental sensor workflow: {e}")
            return {
                "status": "workflow_failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _initialize_monitoring(self, state: EnvironmentalSensorState) -> EnvironmentalSensorState:
        """Initialize environmental sensor monitoring"""
        logger.info("Initializing environmental sensor monitoring")
        
        state["status"] = "collecting_sensor_data"
        state["zones_to_monitor"] = config.DEFAULT_ZONES.copy()
        
        # Initialize historical data storage
        for zone_id in state["zones_to_monitor"]:
            state["historical_data"][zone_id] = []
        
        return state
    
    def _collect_sensor_data_node(self, state: EnvironmentalSensorState) -> EnvironmentalSensorState:
        """Collect real-time sensor data from all zones"""
        logger.info("Collecting real-time sensor data")
        
        for zone_id in state["zones_to_monitor"]:
            try:
                # Simulate sensor data collection (replace with actual IoT integration)
                sensor_data = self._simulate_sensor_readings(zone_id)
                
                if sensor_data:
                    state["sensor_readings"][zone_id] = sensor_data
                    
                    # Store in historical data
                    state["historical_data"][zone_id].append({
                        **sensor_data,
                        "collected_at": datetime.now().isoformat()
                    })
                    
                    # Keep only last 24 hours of data
                    cutoff_time = datetime.now() - timedelta(hours=24)
                    state["historical_data"][zone_id] = [
                        reading for reading in state["historical_data"][zone_id]
                        if datetime.fromisoformat(reading["collected_at"]) > cutoff_time
                    ]
                    
                else:
                    state["errors"].append(f"Failed to collect sensor data for {zone_id}")
                    
            except Exception as e:
                error_msg = f"Error collecting sensor data for {zone_id}: {str(e)}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
        
        return state
    
    def _validate_data_quality_node(self, state: EnvironmentalSensorState) -> EnvironmentalSensorState:
        """Validate quality of collected sensor data"""
        logger.info("Validating sensor data quality")
        
        for zone_id, sensor_data in state["sensor_readings"].items():
            try:
                quality_score = self._calculate_data_quality(sensor_data)
                state["data_quality_scores"][zone_id] = quality_score
                
                if quality_score >= 0.7:  # Good quality threshold
                    state["processed_zones"].append(zone_id)
                else:
                    logger.warning(f"Low data quality for {zone_id}: {quality_score:.2f}")
                    
            except Exception as e:
                error_msg = f"Error validating data quality for {zone_id}: {str(e)}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
        
        return state
    
    def _analyze_deviations_node(self, state: EnvironmentalSensorState) -> EnvironmentalSensorState:
        """Analyze deviations in sensor readings"""
        logger.info("Analyzing sensor data deviations")
        
        for zone_id in state["processed_zones"]:
            try:
                current_readings = state["sensor_readings"][zone_id]
                historical_readings = state["historical_data"][zone_id]
                
                deviations = self._calculate_deviations(current_readings, historical_readings)
                state["deviation_analysis"][zone_id] = deviations
                
            except Exception as e:
                error_msg = f"Error analyzing deviations for {zone_id}: {str(e)}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
        
        return state
    
    def _compare_forecasts_node(self, state: EnvironmentalSensorState) -> EnvironmentalSensorState:
        """Compare sensor readings with weather forecasts"""
        logger.info("Comparing sensor data with forecasts")
        
        for zone_id in state["processed_zones"]:
            try:
                sensor_data = state["sensor_readings"][zone_id]
                forecast_comparison = self._compare_with_forecast(zone_id, sensor_data)
                state["forecast_comparisons"][zone_id] = forecast_comparison
                
            except Exception as e:
                error_msg = f"Error comparing forecasts for {zone_id}: {str(e)}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
        
        return state
    
    def _generate_insights_node(self, state: EnvironmentalSensorState) -> EnvironmentalSensorState:
        """Generate insights using LLM analysis"""
        logger.info("Generating environmental insights")
        
        try:
            # Prepare sensor data summary
            sensor_summary = self._prepare_sensor_summary(state)
            
            prompt = f"""
            Analyze the following environmental sensor data for smart lighting system:
            
            Sensor Data Summary:
            {sensor_summary}
            
            Provide analysis for:
            1. Current environmental conditions impact on lighting needs
            2. Deviation patterns from normal readings
            3. Forecast accuracy assessment
            4. Lighting adjustment recommendations
            5. Risk assessment for each zone
            
            Focus on visibility, safety, and energy efficiency factors.
            Respond in structured format.
            """
            
            message = HumanMessage(content=prompt)
            response = self.llm.invoke([message])
            
            # Store insights in deviation analysis
            state["deviation_analysis"]["llm_insights"] = {
                "analysis": response.content,
                "generated_at": datetime.now().isoformat(),
                "zones_analyzed": len(state["processed_zones"])
            }
            
        except Exception as e:
            error_msg = f"Error generating environmental insights: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _detect_anomalies_node(self, state: EnvironmentalSensorState) -> EnvironmentalSensorState:
        """Detect anomalies and generate real-time alerts"""
        logger.info("Detecting environmental anomalies")
        
        for zone_id in state["processed_zones"]:
            try:
                sensor_data = state["sensor_readings"][zone_id]
                deviations = state["deviation_analysis"].get(zone_id, {})
                
                anomalies = self._detect_sensor_anomalies(sensor_data, deviations)
                
                for anomaly in anomalies:
                    alert = {
                        "zone_id": zone_id,
                        "anomaly_type": anomaly["type"],
                        "severity": anomaly["severity"],
                        "sensor_data": sensor_data,
                        "deviation_details": anomaly["details"],
                        "timestamp": datetime.now().isoformat()
                    }
                    state["real_time_alerts"].append(alert)
                    
            except Exception as e:
                error_msg = f"Error detecting anomalies for {zone_id}: {str(e)}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
        
        return state
    
    def _publish_readings_node(self, state: EnvironmentalSensorState) -> EnvironmentalSensorState:
        """Publish sensor readings and alerts to Kafka"""
        logger.info("Publishing sensor readings to Kafka")
        
        published_count = 0
        
        # Publish sensor readings
        for zone_id in state["processed_zones"]:
            try:
                sensor_data = state["sensor_readings"][zone_id]
                data_quality = state["data_quality_scores"].get(zone_id, 0.5)
                
                # Add metadata to sensor data
                enhanced_data = {
                    **sensor_data,
                    "data_quality_score": data_quality,
                    "collection_timestamp": datetime.now().isoformat(),
                    "source": "environmental_sensor_agent"
                }
                
                weather_producer.publish_sensor_data(zone_id, enhanced_data)
                published_count += 1
                
            except Exception as e:
                error_msg = f"Error publishing sensor data for {zone_id}: {str(e)}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
        
        # Publish real-time alerts
        for alert in state["real_time_alerts"]:
            try:
                weather_producer.publish_weather_alert(
                    alert["zone_id"],
                    alert["anomaly_type"],
                    alert["severity"],
                    alert["deviation_details"]
                )
                published_count += 1
                
            except Exception as e:
                error_msg = f"Error publishing alert: {str(e)}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
        
        logger.info(f"Published {published_count} sensor readings and alerts to Kafka")
        return state
    
    def _finalize_monitoring(self, state: EnvironmentalSensorState) -> EnvironmentalSensorState:
        """Finalize environmental sensor monitoring workflow"""
        logger.info("Finalizing environmental sensor monitoring")
        
        if len(state["processed_zones"]) > 0:
            state["status"] = "monitoring_complete"
        else:
            state["status"] = "monitoring_failed"
        
        return state
    
    # Helper methods
    def _simulate_sensor_readings(self, zone_id: str) -> Optional[Dict[str, Any]]:
        """Simulate sensor readings (replace with actual IoT integration)"""
        try:
            import random
            from datetime import datetime
            
            # Simulate realistic sensor values with some variation
            base_temp = 20 + random.gauss(0, 5)  # Temperature around 20°C
            base_humidity = 60 + random.gauss(0, 15)  # Humidity around 60%
            
            sensor_data = {
                "temperature": round(base_temp, 1),
                "humidity": max(0, min(100, round(base_humidity, 1))),
                "pressure": round(1013.25 + random.gauss(0, 10), 1),
                "wind_speed": max(0, round(random.gauss(5, 3), 1)),
                "wind_direction": random.randint(0, 360),
                "light_level": max(0, round(random.gauss(300, 100), 0)),  # Lux
                "visibility": max(100, round(random.gauss(8000, 2000), 0)),  # Meters
                "precipitation": max(0, round(random.expovariate(1 / 0.1), 2)),  # mm/h
                "air_quality_index": random.randint(20, 150),
                "timestamp": datetime.now().isoformat(),
                "zone_id": zone_id,
                "sensor_status": "active"
            }
            
            logger.debug(f"Simulated sensor data for {zone_id}: {sensor_data['temperature']}°C, {sensor_data['humidity']}% humidity")
            return sensor_data
            
        except Exception as e:
            logger.error(f"Error simulating sensor readings for {zone_id}: {e}")
            return None
    
    def _calculate_data_quality(self, sensor_data: Dict[str, Any]) -> float:
        """Calculate data quality score for sensor readings"""
        try:
            quality_score = 1.0
            
            # Check for missing or invalid values
            required_fields = ['temperature', 'humidity', 'wind_speed', 'visibility']
            missing_fields = [field for field in required_fields if field not in sensor_data or sensor_data[field] is None]
            
            if missing_fields:
                quality_score -= 0.2 * len(missing_fields)
            
            # Check for realistic value ranges
            if sensor_data.get('temperature', 0) < -50 or sensor_data.get('temperature', 0) > 60:
                quality_score -= 0.3
            
            if sensor_data.get('humidity', 0) < 0 or sensor_data.get('humidity', 0) > 100:
                quality_score -= 0.3
            
            if sensor_data.get('wind_speed', 0) < 0 or sensor_data.get('wind_speed', 0) > 100:
                quality_score -= 0.2
            
            # Check sensor status
            if sensor_data.get('sensor_status') != 'active':
                quality_score -= 0.4
            
            return max(0.0, min(1.0, quality_score))
            
        except Exception as e:
            logger.error(f"Error calculating data quality: {e}")
            return 0.0
    
    def _calculate_deviations(self, current_readings: Dict[str, Any], 
                            historical_readings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate deviations from historical patterns"""
        try:
            if not historical_readings:
                return {"status": "insufficient_historical_data"}
            
            # Calculate averages from last 6 hours
            recent_readings = [
                reading for reading in historical_readings
                if datetime.fromisoformat(reading["collected_at"]) > 
                datetime.now() - timedelta(hours=6)
            ]
            
            if not recent_readings:
                return {"status": "no_recent_data"}
            
            deviations = {}
            
            # Temperature deviation
            avg_temp = sum(r.get('temperature', 0) for r in recent_readings) / len(recent_readings)
            current_temp = current_readings.get('temperature', avg_temp)
            deviations['temperature_deviation'] = abs(current_temp - avg_temp)
            
            # Humidity deviation
            avg_humidity = sum(r.get('humidity', 0) for r in recent_readings) / len(recent_readings)
            current_humidity = current_readings.get('humidity', avg_humidity)
            deviations['humidity_deviation'] = abs(current_humidity - avg_humidity)
            
            # Wind speed deviation
            avg_wind = sum(r.get('wind_speed', 0) for r in recent_readings) / len(recent_readings)
            current_wind = current_readings.get('wind_speed', avg_wind)
            deviations['wind_speed_deviation'] = abs(current_wind - avg_wind)
            
            # Overall deviation score
            deviations['overall_deviation_score'] = (
                deviations['temperature_deviation'] / 10 +  # Normalize to 0-1 scale
                deviations['humidity_deviation'] / 50 +
                deviations['wind_speed_deviation'] / 20
            ) / 3
            
            return deviations
            
        except Exception as e:
            logger.error(f"Error calculating deviations: {e}")
            return {"status": "calculation_error", "error": str(e)}
    
    def _compare_with_forecast(self, zone_id: str, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare sensor readings with weather forecast predictions"""
        try:
            # This would fetch actual forecast data from Kafka or storage
            # For now, simulate forecast comparison
            
            forecast_temp = sensor_data.get('temperature', 20) + random.uniform(-3, 3)
            forecast_humidity = sensor_data.get('humidity', 60) + random.uniform(-10, 10)
            
            comparison = {
                "temperature_difference": abs(sensor_data.get('temperature', 20) - forecast_temp),
                "humidity_difference": abs(sensor_data.get('humidity', 60) - forecast_humidity),
                "forecast_accuracy": "good" if abs(sensor_data.get('temperature', 20) - forecast_temp) < 2 else "poor",
                "comparison_timestamp": datetime.now().isoformat()
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing with forecast: {e}")
            return {"status": "comparison_error", "error": str(e)}
    
    def _prepare_sensor_summary(self, state: EnvironmentalSensorState) -> str:
        """Prepare sensor data summary for LLM analysis"""
        summary_parts = []
        
        for zone_id in state["processed_zones"]:
            sensor_data = state["sensor_readings"].get(zone_id, {})
            quality_score = state["data_quality_scores"].get(zone_id, 0.0)
            deviations = state["deviation_analysis"].get(zone_id, {})
            
            zone_summary = f"""
            Zone {zone_id}:
            - Temperature: {sensor_data.get('temperature', 'N/A')}°C
            - Humidity: {sensor_data.get('humidity', 'N/A')}%
            - Wind Speed: {sensor_data.get('wind_speed', 'N/A')}m/s
            - Visibility: {sensor_data.get('visibility', 'N/A')}m
            - Light Level: {sensor_data.get('light_level', 'N/A')} lux
            - Data Quality: {quality_score:.2f}
            - Overall Deviation: {deviations.get('overall_deviation_score', 'N/A')}
            """
            summary_parts.append(zone_summary)
        
        return "\n".join(summary_parts)
    
    def _detect_sensor_anomalies(self, sensor_data: Dict[str, Any], 
                                deviations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in sensor readings"""
        anomalies = []
        
        try:
            # Temperature anomaly
            if deviations.get('temperature_deviation', 0) > 10:
                anomalies.append({
                    "type": "temperature_anomaly",
                    "severity": "high" if deviations['temperature_deviation'] > 15 else "medium",
                    "details": {"deviation": deviations['temperature_deviation']}
                })
            
            # Visibility anomaly
            visibility = sensor_data.get('visibility', 10000)
            if visibility < config.VISIBILITY_THRESHOLD:
                anomalies.append({
                    "type": "low_visibility",
                    "severity": "critical" if visibility < 500 else "high",
                    "details": {"visibility": visibility}
                })
            
            # Wind speed anomaly
            wind_speed = sensor_data.get('wind_speed', 0)
            if wind_speed > config.WIND_SPEED_THRESHOLD:
                anomalies.append({
                    "type": "high_wind",
                    "severity": "critical" if wind_speed > config.EMERGENCY_WIND_SPEED else "high",
                    "details": {"wind_speed": wind_speed}
                })
            
            # Overall deviation anomaly
            if deviations.get('overall_deviation_score', 0) > 0.7:
                anomalies.append({
                    "type": "overall_deviation",
                    "severity": "medium",
                    "details": {"deviation_score": deviations['overall_deviation_score']}
                })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting sensor anomalies: {e}")
            return []

# Create agent instance
environmental_sensor_agent = EnvironmentalSensorAgent()
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

class EnergyLoadForecasterState:
    """State management for Energy Load Forecaster Agent"""
    
    def __init__(self):
        self.smart_meter_data: Dict[str, Any] = {}
        self.zone_occupancy: Dict[str, Any] = {}
        self.weather_data: Dict[str, Any] = {}
        self.historical_data: List[Dict[str, Any]] = []
        self.forecasts: Dict[str, Any] = {}
        self.confidence_scores: Dict[str, float] = {}
        self.peak_predictions: Dict[str, Any] = {}
        self.alerts: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.status: str = "initialized"

class EnergyLoadForecasterAgent:
    """LangGraph-based Energy Load Forecaster Agent"""
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=config.GROQ_API_KEY,
            model=config.GROQ_MODEL,
            temperature=config.GROQ_TEMPERATURE,
            max_tokens=config.GROQ_MAX_TOKENS
        )
        self.state = EnergyLoadForecasterState()
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create LangGraph workflow for energy load forecasting"""
        
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("collect_meter_data", self._collect_meter_data_node)
        workflow.add_node("analyze_occupancy", self._analyze_occupancy_node)
        workflow.add_node("process_weather", self._process_weather_node)
        workflow.add_node("generate_forecast", self._generate_forecast_node)
        workflow.add_node("calculate_peaks", self._calculate_peaks_node)
        workflow.add_node("validate_forecast", self._validate_forecast_node)
        workflow.add_node("publish_results", self._publish_results_node)
        
        # Define workflow
        workflow.set_entry_point("collect_meter_data")
        workflow.add_edge("collect_meter_data", "analyze_occupancy")
        workflow.add_edge("analyze_occupancy", "process_weather")
        workflow.add_edge("process_weather", "generate_forecast")
        workflow.add_edge("generate_forecast", "calculate_peaks")
        workflow.add_edge("calculate_peaks", "validate_forecast")
        workflow.add_edge("validate_forecast", "publish_results")
        workflow.add_edge("publish_results", END)
        
        return workflow.compile()
    
    def _collect_meter_data_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Collect smart meter data from all zones"""
        try:
            logger.info("Collecting smart meter data for forecasting")
            
            # Simulate smart meter data collection
            current_time = datetime.now()
            zones = config.DEFAULT_ZONES
            
            meter_data = {}
            for zone in zones:
                # Simulate realistic meter readings
                base_load = 50 + (hash(zone) % 30)  # 50-80 kW base load
                time_factor = 1.0 + 0.3 * abs((current_time.hour - 12) / 12)  # Peak around noon
                
                meter_data[zone] = {
                    "current_load": base_load * time_factor,
                    "voltage": 240.0 + (hash(zone) % 10 - 5),  # 235-245V
                    "frequency": 50.0 + (hash(zone) % 2 - 1) * 0.1,  # 49.9-50.1 Hz
                    "power_factor": 0.85 + (hash(zone) % 15) * 0.01,  # 0.85-1.0
                    "timestamp": current_time.isoformat(),
                    "daily_consumption": base_load * 24 * 0.8  # kWh
                }
            
            # Analyze data with LLM
            prompt = f"""
            Analyze the following smart meter data for energy load forecasting:
            
            Meter Data: {json.dumps(meter_data, indent=2)}
            
            Provide insights on:
            1. Current load patterns across zones
            2. Power quality indicators
            3. Consumption trends
            4. Any anomalies detected
            
            Return analysis in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            state["smart_meter_data"] = meter_data
            state["meter_analysis"] = response.content
            state["collection_time"] = current_time.isoformat()
            
            logger.info(f"Collected meter data for {len(meter_data)} zones")
            return state
            
        except Exception as e:
            logger.error(f"Error collecting meter data: {e}")
            state["errors"] = state.get("errors", []) + [f"Meter data collection failed: {str(e)}"]
            return state
    
    def _analyze_occupancy_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze zone occupancy patterns"""
        try:
            logger.info("Analyzing zone occupancy patterns")
            
            current_hour = datetime.now().hour
            current_day = datetime.now().strftime("%A")
            
            # Simulate occupancy data
            occupancy_data = {}
            for zone in config.DEFAULT_ZONES:
                # Business hours pattern
                if 8 <= current_hour <= 18 and current_day not in ["Saturday", "Sunday"]:
                    occupancy_rate = 0.6 + (hash(zone) % 30) * 0.01  # 60-90% during business hours
                else:
                    occupancy_rate = 0.1 + (hash(zone) % 20) * 0.01  # 10-30% off hours
                
                occupancy_data[zone] = {
                    "occupancy_rate": occupancy_rate,
                    "people_count": int(occupancy_rate * 100),  # Assume max 100 people per zone
                    "activity_level": "high" if occupancy_rate > 0.5 else "low",
                    "is_business_hours": 8 <= current_hour <= 18,
                    "day_type": "weekday" if current_day not in ["Saturday", "Sunday"] else "weekend"
                }
            
            # LLM analysis of occupancy impact
            prompt = f"""
            Analyze occupancy patterns for energy load forecasting:
            
            Current Time: {current_hour}:00 on {current_day}
            Occupancy Data: {json.dumps(occupancy_data, indent=2)}
            
            Provide insights on:
            1. Expected load correlation with occupancy
            2. Peak demand timing predictions
            3. Weekend vs weekday patterns
            4. Occupancy-based load adjustments needed
            
            Return analysis in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            state["zone_occupancy"] = occupancy_data
            state["occupancy_analysis"] = response.content
            
            logger.info("Occupancy analysis completed")
            return state
            
        except Exception as e:
            logger.error(f"Error analyzing occupancy: {e}")
            state["errors"] = state.get("errors", []) + [f"Occupancy analysis failed: {str(e)}"]
            return state
    
    def _process_weather_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process weather data impact on energy demand"""
        try:
            logger.info("Processing weather data for load forecasting")
            
            # Simulate weather data (would normally come from weather service)
            weather_data = {
                "temperature": 22.0,  # Celsius
                "humidity": 65.0,
                "weather_condition": "Clear",
                "visibility": 10000,
                "wind_speed": 5.2,
                "timestamp": datetime.now().isoformat()
            }
            
            # LLM analysis of weather impact
            prompt = f"""
            Analyze weather impact on energy load forecasting:
            
            Weather Conditions: {json.dumps(weather_data, indent=2)}
            Current Season: {datetime.now().strftime("%B")}
            
            Consider:
            1. Temperature impact on HVAC loads
            2. Lighting requirements based on weather conditions
            3. Seasonal patterns and adjustments
            4. Weather-driven load variations
            
            Provide load adjustment factors for different weather scenarios.
            Return analysis in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            state["weather_data"] = weather_data
            state["weather_analysis"] = response.content
            
            logger.info("Weather data processed for forecasting")
            return state
            
        except Exception as e:
            logger.error(f"Error processing weather data: {e}")
            state["errors"] = state.get("errors", []) + [f"Weather processing failed: {str(e)}"]
            return state
    
    def _generate_forecast_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate energy load forecasts"""
        try:
            logger.info("Generating energy load forecasts")
            
            meter_data = state.get("smart_meter_data", {})
            occupancy_data = state.get("zone_occupancy", {})
            weather_data = state.get("weather_data", {})
            
            # Generate hourly forecasts for next 24 hours
            forecasts = {}
            current_time = datetime.now()
            
            for zone in config.DEFAULT_ZONES:
                zone_forecasts = []
                current_load = meter_data.get(zone, {}).get("current_load", 50.0)
                occupancy_rate = occupancy_data.get(zone, {}).get("occupancy_rate", 0.5)
                
                for hour in range(config.FORECAST_HORIZON_HOURS):
                    forecast_time = current_time + timedelta(hours=hour)
                    
                    # Simple forecast model (would be more sophisticated in production)
                    base_load = current_load
                    time_factor = 1.0 + 0.3 * abs((forecast_time.hour - 12) / 12)
                    occupancy_factor = 0.5 + occupancy_rate * 0.5
                    weather_factor = 1.0  # Simplified weather impact
                    
                    predicted_load = base_load * time_factor * occupancy_factor * weather_factor
                    
                    zone_forecasts.append({
                        "hour": hour,
                        "timestamp": forecast_time.isoformat(),
                        "predicted_load": round(predicted_load, 2),
                        "confidence": 0.85 + (hash(str(hour)) % 15) * 0.01  # 85-100%
                    })
                
                forecasts[zone] = zone_forecasts
            
            # LLM validation and insights
            prompt = f"""
            Review and validate energy load forecasts:
            
            Sample Forecast Data: {json.dumps({k: v[:6] for k, v in list(forecasts.items())[:2]}, indent=2)}
            Total Zones: {len(forecasts)}
            Forecast Horizon: {config.FORECAST_HORIZON_HOURS} hours
            
            Provide:
            1. Forecast validation and accuracy assessment
            2. Potential issues or concerns
            3. Confidence level evaluation
            4. Recommended adjustments
            
            Return validation results in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            state["forecasts"] = forecasts
            state["forecast_validation"] = response.content
            state["forecast_generated_at"] = current_time.isoformat()
            
            logger.info(f"Generated forecasts for {len(forecasts)} zones")
            return state
            
        except Exception as e:
            logger.error(f"Error generating forecasts: {e}")
            state["errors"] = state.get("errors", []) + [f"Forecast generation failed: {str(e)}"]
            return state
    
    def _calculate_peaks_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate peak demand predictions"""
        try:
            logger.info("Calculating peak demand predictions")
            
            forecasts = state.get("forecasts", {})
            peak_predictions = {}
            
            for zone, zone_forecasts in forecasts.items():
                if not zone_forecasts:
                    continue
                
                # Find peak load in forecast
                max_load = max(f["predicted_load"] for f in zone_forecasts)
                peak_hour = next(f for f in zone_forecasts if f["predicted_load"] == max_load)
                
                # Calculate if peak exceeds threshold
                threshold_exceeded = max_load > (config.PEAK_DEMAND_THRESHOLD / 100) * 100  # Assume 100kW capacity
                
                peak_predictions[zone] = {
                    "peak_load": max_load,
                    "peak_time": peak_hour["timestamp"],
                    "peak_hour": peak_hour["hour"],
                    "threshold_exceeded": threshold_exceeded,
                    "load_factor": max_load / (sum(f["predicted_load"] for f in zone_forecasts) / len(zone_forecasts)),
                    "confidence": peak_hour["confidence"]
                }
            
            state["peak_predictions"] = peak_predictions
            
            # Generate alerts for high peaks
            alerts = []
            for zone, prediction in peak_predictions.items():
                if prediction["threshold_exceeded"]:
                    alerts.append({
                        "zone": zone,
                        "alert_type": "peak_demand_warning",
                        "predicted_peak": prediction["peak_load"],
                        "peak_time": prediction["peak_time"],
                        "severity": "high" if prediction["load_factor"] > 1.5 else "medium"
                    })
            
            state["alerts"] = alerts
            
            logger.info(f"Calculated peak predictions for {len(peak_predictions)} zones")
            if alerts:
                logger.warning(f"Generated {len(alerts)} peak demand alerts")
            
            return state
            
        except Exception as e:
            logger.error(f"Error calculating peaks: {e}")
            state["errors"] = state.get("errors", []) + [f"Peak calculation failed: {str(e)}"]
            return state
    
    def _validate_forecast_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate forecast accuracy and reliability"""
        try:
            logger.info("Validating forecast accuracy")
            
            forecasts = state.get("forecasts", {})
            
            # Calculate overall confidence scores
            confidence_scores = {}
            for zone, zone_forecasts in forecasts.items():
                if zone_forecasts:
                    avg_confidence = sum(f["confidence"] for f in zone_forecasts) / len(zone_forecasts)
                    confidence_scores[zone] = round(avg_confidence, 3)
            
            overall_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0
            
            # Determine forecast quality
            if overall_confidence >= 0.9:
                forecast_quality = "excellent"
            elif overall_confidence >= 0.8:
                forecast_quality = "good"
            elif overall_confidence >= 0.7:
                forecast_quality = "acceptable"
            else:
                forecast_quality = "poor"
            
            state["confidence_scores"] = confidence_scores
            state["overall_confidence"] = overall_confidence
            state["forecast_quality"] = forecast_quality
            state["validation_time"] = datetime.now().isoformat()
            
            logger.info(f"Forecast validation completed - Quality: {forecast_quality}")
            return state
            
        except Exception as e:
            logger.error(f"Error validating forecast: {e}")
            state["errors"] = state.get("errors", []) + [f"Forecast validation failed: {str(e)}"]
            return state
    
    def _publish_results_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Publish forecast results to Kafka"""
        try:
            logger.info("Publishing forecast results")
            
            # Prepare forecast data for publishing
            forecast_data = {
                "forecasts": state.get("forecasts", {}),
                "peak_predictions": state.get("peak_predictions", {}),
                "confidence_scores": state.get("confidence_scores", {}),
                "overall_confidence": state.get("overall_confidence", 0),
                "forecast_quality": state.get("forecast_quality", "unknown"),
                "horizon_hours": config.FORECAST_HORIZON_HOURS,
                "generated_at": state.get("forecast_generated_at"),
                "validated_at": state.get("validation_time")
            }
            
            # Send to Kafka
            success = power_producer.send_forecast_data({
                "zone_id": "all_zones",
                "forecast_data": forecast_data,
                "horizon_hours": config.FORECAST_HORIZON_HOURS
            })
            
            if success:
                state["status"] = "forecast_complete"
                state["published_at"] = datetime.now().isoformat()
                logger.info("Forecast results published successfully")
            else:
                state["status"] = "forecast_failed"
                state["errors"] = state.get("errors", []) + ["Failed to publish forecast results"]
            
            # Publish alerts if any
            alerts = state.get("alerts", [])
            for alert in alerts:
                power_producer.send_grid_alert({
                    "alert_type": alert["alert_type"],
                    "zone_id": alert["zone"],
                    "severity": alert["severity"],
                    "message": f"Peak demand warning: {alert['predicted_peak']}kW at {alert['peak_time']}",
                    "data": alert
                })
            
            return state
            
        except Exception as e:
            logger.error(f"Error publishing results: {e}")
            state["errors"] = state.get("errors", []) + [f"Publishing failed: {str(e)}"]
            state["status"] = "forecast_failed"
            return state
    
    def forecast_energy_load(self, initial_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute energy load forecasting workflow"""
        try:
            logger.info("Starting energy load forecasting workflow")
            
            # Initialize state
            if initial_state is None:
                initial_state = {
                    "workflow_id": f"forecast_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "started_at": datetime.now().isoformat(),
                    "errors": []
                }
            
            # Execute workflow
            result = self.workflow.invoke(initial_state)
            
            logger.info(f"Energy load forecasting completed - Status: {result.get('status', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Energy load forecasting workflow failed: {e}")
            return {
                "status": "forecast_failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Create singleton instance
energy_load_forecaster_agent = EnergyLoadForecasterAgent()
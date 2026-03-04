import logging
import httpx
import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
from ..config.settings import config
from ..kafka.kafka_producer import weather_producer

logger = logging.getLogger(__name__)

class WeatherCollectionState(TypedDict):
    """State class for weather collection and forecast workflow"""
    zones_to_process: List[str]
    current_weather: Dict[str, Any]
    forecast_data: Dict[str, Any]
    api_responses: List[Dict[str, Any]]
    confidence_scores: Dict[str, float]
    processed_zones: List[str]
    ml_predictions: Dict[str, Any]
    alerts_generated: List[Dict[str, Any]]
    errors: List[str]
    status: str

class WeatherCollectionForecastAgent:
    """
    LangGraph-based agent for collecting weather data and generating forecasts
    using TheWeatherAPI and ML-based predictions
    """
    
    def __init__(self):
        self.weatherapi_config = config.get_weatherapi_config()
        self.groq_config = config.get_groq_config()
        self.timeout = config.AGENT_TIMEOUT
        self.llm = ChatGroq(
            groq_api_key=self.groq_config['api_key'],
            model_name=self.groq_config['model'],
            temperature=self.groq_config['temperature'],
            max_tokens=self.groq_config['max_tokens']
        )
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow for weather collection"""
        workflow = StateGraph(WeatherCollectionState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_collection)
        workflow.add_node("fetch_current_weather", self._fetch_current_weather_node)
        workflow.add_node("fetch_forecasts", self._fetch_forecasts_node)
        workflow.add_node("calculate_confidence", self._calculate_confidence_node)
        workflow.add_node("generate_ml_predictions", self._generate_ml_predictions_node)
        workflow.add_node("generate_alerts", self._generate_alerts_node)
        workflow.add_node("publish_data", self._publish_data_node)
        workflow.add_node("finalize", self._finalize_collection)
        
        # Define workflow edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "fetch_current_weather")
        workflow.add_edge("fetch_current_weather", "fetch_forecasts")
        workflow.add_edge("fetch_forecasts", "calculate_confidence")
        workflow.add_edge("calculate_confidence", "generate_ml_predictions")
        workflow.add_edge("generate_ml_predictions", "generate_alerts")
        workflow.add_edge("generate_alerts", "publish_data")
        workflow.add_edge("publish_data", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def collect_weather_data(self) -> Dict[str, Any]:
        """Main method to execute weather collection workflow"""
        try:
            logger.info("Starting weather data collection workflow")
            
            # Initialize state
            initial_state = WeatherCollectionState(
                zones_to_process=config.DEFAULT_ZONES.copy(),
                current_weather={},
                forecast_data={},
                api_responses=[],
                confidence_scores={},
                processed_zones=[],
                ml_predictions={},
                alerts_generated=[],
                errors=[],
                status="initializing"
            )
            
            # Execute workflow
            final_state = self.workflow.invoke(initial_state)
            
            return {
                "status": final_state["status"],
                "processed_zones": len(final_state["processed_zones"]),
                "total_zones": len(config.DEFAULT_ZONES),
                "average_confidence": (
                    sum(final_state["confidence_scores"].values()) / 
                    len(final_state["confidence_scores"]) 
                    if final_state["confidence_scores"] else 0
                ),
                "ml_predictions": final_state["ml_predictions"],
                "alerts_generated": len(final_state["alerts_generated"]),
                "errors": final_state["errors"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in weather collection workflow: {e}")
            return {
                "status": "workflow_failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _initialize_collection(self, state: WeatherCollectionState) -> WeatherCollectionState:
        """Initialize weather data collection"""
        logger.info("Initializing weather data collection")
        
        state["status"] = "collecting_data"
        state["zones_to_process"] = config.DEFAULT_ZONES.copy()
        
        return state
    
    def _fetch_current_weather_node(self, state: WeatherCollectionState) -> WeatherCollectionState:
        """Fetch current weather data for all zones"""
        logger.info("Fetching current weather data")
        
        try:
            results = []
            for zone_id in state["zones_to_process"]:
                try:
                    zone_config = config.get_zone_config(zone_id)
                    coordinates = zone_config['coordinates']
                    # Call the synchronous function directly
                    result = self._fetch_current_weather(zone_id, coordinates)
                    results.append(result)
                except Exception as e:
                    results.append(e) # Append the exception to be processed below

            # Process results
            for i, result in enumerate(results):
                zone_id = state["zones_to_process"][i]
                if isinstance(result, Exception):
                    error_msg = f"Error fetching current weather for {zone_id}: {str(result)}"
                    logger.error(error_msg)
                    state["errors"].append(error_msg)
                elif result and not result.get("error"):
                    state["current_weather"][zone_id] = result
                    state["api_responses"].append({
                        "zone_id": zone_id,
                        "type": "current_weather",
                        "success": True,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    state["errors"].append(f"Failed to fetch current weather for {zone_id}")

        except Exception as e:
            error_msg = f"Error in weather fetching workflow: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _fetch_forecasts_node(self, state: WeatherCollectionState) -> WeatherCollectionState:
        """Fetch forecast data for all zones"""
        logger.info("Fetching forecast data")
        
        try:
            results = []
            for zone_id in state["zones_to_process"]:
                try:
                    zone_config = config.get_zone_config(zone_id)
                    coordinates = zone_config['coordinates']
                    # Call the synchronous function directly
                    result = self._fetch_forecast_data(zone_id, coordinates)
                    results.append(result)
                except Exception as e:
                    results.append(e) # Append the exception to be processed below

            # Process results
            for i, result in enumerate(results):
                zone_id = state["zones_to_process"][i]
                if isinstance(result, Exception):
                    error_msg = f"Error fetching forecast for {zone_id}: {str(result)}"
                    logger.error(error_msg)
                    state["errors"].append(error_msg)
                elif result and len(result) > 0:
                    state["forecast_data"][zone_id] = result
                    state["api_responses"].append({
                        "zone_id": zone_id,
                        "type": "forecast_data",
                        "success": True,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    state["errors"].append(f"Failed to fetch forecast for {zone_id}")

        except Exception as e:
            error_msg = f"Error in forecast fetching workflow: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _calculate_confidence_node(self, state: WeatherCollectionState) -> WeatherCollectionState:
        """Calculate confidence scores for all zones"""
        logger.info("Calculating confidence scores")
        
        for zone_id in state["zones_to_process"]:
            try:
                current_weather = state["current_weather"].get(zone_id)
                forecast_data = state["forecast_data"].get(zone_id)
                
                confidence = self._calculate_confidence_score(current_weather, forecast_data)
                state["confidence_scores"][zone_id] = confidence
                
                if current_weather or forecast_data:
                    state["processed_zones"].append(zone_id)
                    
            except Exception as e:
                error_msg = f"Error calculating confidence for {zone_id}: {str(e)}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
        
        return state
    
    def _generate_ml_predictions_node(self, state: WeatherCollectionState) -> WeatherCollectionState:
        """Generate ML-enhanced predictions using LLM"""
        logger.info("Generating ML-enhanced predictions")
        
        try:
            # Prepare weather summary
            weather_summary = self._prepare_weather_summary(state)
            
            prompt = f"""
            Analyze the following weather data and provide enhanced predictions for smart lighting system:
            
            Weather Data Summary:
            {weather_summary}
            
            Provide analysis for:
            1. Short-term predictions (next 6 hours) for each zone
            2. Lighting impact assessment (visibility, safety concerns)
            3. Risk level assessment (low, medium, high, critical)
            4. Recommended lighting adjustments
            5. Confidence level for predictions (0-100%)
            
            Focus on conditions affecting outdoor lighting: fog, storms, visibility, precipitation.
            Respond in structured format.
            """
            
            message = HumanMessage(content=prompt)
            response = self.llm.invoke([message])
            
            state["ml_predictions"] = {
                "analysis": response.content,
                "generated_at": datetime.now().isoformat(),
                "zones_analyzed": len(state["processed_zones"]),
                "confidence": "ml_enhanced"
            }
            
        except Exception as e:
            error_msg = f"Error in ML prediction generation: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            state["ml_predictions"] = {"error": error_msg}
        
        return state
    
    def _generate_alerts_node(self, state: WeatherCollectionState) -> WeatherCollectionState:
        """Generate weather alerts based on conditions"""
        logger.info("Generating weather alerts")
        
        for zone_id in state["processed_zones"]:
            try:
                current_weather = state["current_weather"].get(zone_id)
                
                if current_weather and self._requires_weather_alert(current_weather):
                    alert_type, severity = self._determine_alert_details(current_weather)
                    
                    alert = {
                        "zone_id": zone_id,
                        "alert_type": alert_type,
                        "severity": severity,
                        "conditions": current_weather,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    state["alerts_generated"].append(alert)
                    
            except Exception as e:
                error_msg = f"Error generating alert for {zone_id}: {str(e)}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
        
        return state
    
    def _publish_data_node(self, state: WeatherCollectionState) -> WeatherCollectionState:
        """Publish collected data to Kafka"""
        logger.info("Publishing weather data to Kafka")
        
        published_count = 0
        
        for zone_id in state["processed_zones"]:
            try:
                current_weather = state["current_weather"].get(zone_id)
                forecast_data = state["forecast_data"].get(zone_id)
                confidence = state["confidence_scores"].get(zone_id, 0.5)
                
                # Publish current weather
                if current_weather:
                    weather_producer.publish_sensor_data(zone_id, current_weather)
                    published_count += 1
                
                # Publish forecast
                if forecast_data:
                    weather_producer.publish_weather_forecast(zone_id, forecast_data, confidence)
                    published_count += 1
                
            except Exception as e:
                error_msg = f"Error publishing data for {zone_id}: {str(e)}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
        
        # Publish alerts
        for alert in state["alerts_generated"]:
            try:
                weather_producer.publish_weather_alert(
                    alert["zone_id"],
                    alert["alert_type"],
                    alert["severity"],
                    alert["conditions"]
                )
                published_count += 1
                
            except Exception as e:
                error_msg = f"Error publishing alert: {str(e)}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
        
        logger.info(f"Published {published_count} weather data items to Kafka")
        return state
    
    def _finalize_collection(self, state: WeatherCollectionState) -> WeatherCollectionState:
        """Finalize weather data collection workflow"""
        logger.info("Finalizing weather data collection")
        
        if len(state["processed_zones"]) > 0:
            state["status"] = "collection_complete"
        else:
            state["status"] = "collection_failed"
        
        return state
    
    # Helper methods (same as before but adapted for LangGraph)
    def _fetch_current_weather(self, zone_id: str, coordinates: Dict[str, float]) -> Dict[str, Any]:
        """Fetch current weather data for a specific zone using WeatherAPI."""
        location = f"{coordinates['lat']},{coordinates['lon']}"
        api_key = self.weatherapi_config["api_key"]
        base_url = self.weatherapi_config["base_url"]
        endpoint = f"{base_url}/current.json" # Use current.json for current weather

        params = {
            "key": api_key,
            "q": location,
            "aqi": "no" # Air Quality Index (optional, set to 'yes' if needed)
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(endpoint, params=params)
                response.raise_for_status() # Raise exception for bad status codes
                data = response.json()
                logger.info(f"Successfully fetched current weather for {zone_id} from WeatherAPI")
                # --- PARSE WeatherAPI RESPONSE ---
                # Example parsing (adjust based on actual needs)
                return {
                    "timestamp": data.get("location", {}).get("localtime_epoch"),
                    "temperature": data.get("current", {}).get("temp_c"),
                    "humidity": data.get("current", {}).get("humidity"),
                    "wind_speed": data.get("current", {}).get("wind_kph") * 1000 / 3600, # Convert kph to m/s
                    "condition": data.get("current", {}).get("condition", {}).get("text"),
                    "pressure": data.get("current", {}).get("pressure_mb"),
                    "visibility": data.get("current", {}).get("vis_km") * 1000, # Convert km to meters
                    "precipitation": data.get("current", {}).get("precip_mm"), # Precipitation in mm (might need conversion if API gives rate)
                    "cloud_cover": data.get("current", {}).get("cloud"),
                    "uv_index": data.get("current", {}).get("uv"),
                    "zone_id": zone_id,
                    "raw_data": data # Store raw data if needed later
                }
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching current weather for {zone_id}: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Network error fetching current weather for {zone_id}: {e}")
        except Exception as e:
            logger.error(f"Error processing current weather for {zone_id}: {e}", exc_info=True)
        return {"zone_id": zone_id, "error": True} # Indicate failure
    
    def _fetch_forecast_data(self, zone_id: str, coordinates: Dict[str, float]) -> List[Dict[str, Any]]:
        """Fetch forecast data for a specific zone using WeatherAPI."""
        location = f"{coordinates['lat']},{coordinates['lon']}"
        api_key = self.weatherapi_config["api_key"]
        base_url = self.weatherapi_config["base_url"]
        endpoint = f"{base_url}/forecast.json" # Use forecast.json for forecast

        # Calculate forecast days needed based on FORECAST_HOURS (WeatherAPI max is usually 10-14 days)
        days_needed = (config.FORECAST_HOURS + 23) // 24 # Round up to nearest day
        days_to_fetch = min(days_needed, 10) # Limit to WeatherAPI's typical max (e.g., 10 days)

        params = {
            "key": api_key,
            "q": location,
            "days": days_to_fetch,
            "aqi": "no",
            "alerts": "yes" # Include weather alerts
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(endpoint, params=params)
                response.raise_for_status()
                data = response.json()
                logger.info(f"Successfully fetched forecast data for {zone_id} from WeatherAPI")

                # --- PARSE WeatherAPI FORECAST RESPONSE ---
                forecast_list = []
                forecast_days = data.get("forecast", {}).get("forecastday", [])

                for day in forecast_days:
                    for hour_data in day.get("hour", []):
                        # Only include hours within the desired FORECAST_HOURS range
                        timestamp = hour_data.get("time_epoch")
                        if timestamp and timestamp <= time.time() + config.FORECAST_HOURS * 3600:
                            forecast_list.append({
                                "timestamp": timestamp,
                                "temperature": hour_data.get("temp_c"),
                                "humidity": hour_data.get("humidity"),
                                "wind_speed": hour_data.get("wind_kph") * 1000 / 3600, # kph to m/s
                                "condition": hour_data.get("condition", {}).get("text"),
                                "pressure": hour_data.get("pressure_mb"),
                                "visibility": hour_data.get("vis_km") * 1000, # km to meters
                                "precipitation": hour_data.get("precip_mm"), # mm
                                "cloud_cover": hour_data.get("cloud"),
                                "uv_index": hour_data.get("uv"),
                                "chance_of_rain": hour_data.get("chance_of_rain"), # Percentage
                                "chance_of_snow": hour_data.get("chance_of_snow"), # Percentage
                                "zone_id": zone_id,
                            })
                # --- PARSE ALERTS ---
                alerts = []
                for alert in data.get("alerts", {}).get("alert", []):
                     alerts.append({
                        "headline": alert.get("headline"),
                        "event": alert.get("event"),
                        "description": alert.get("desc"),
                        "effective": alert.get("effective"),
                        "expires": alert.get("expires"),
                        "severity": alert.get("severity"),
                        "urgency": alert.get("urgency"),
                    })
                # Add alerts to the state or handle them appropriately
                # For now, just logging them
                if alerts:
                     logger.warning(f"Weather alerts received for {zone_id}: {alerts}")


                return forecast_list

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching forecast for {zone_id}: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Network error fetching forecast for {zone_id}: {e}")
        except Exception as e:
            logger.error(f"Error processing forecast for {zone_id}: {e}", exc_info=True)
        return [] # Return empty list on failure
    
    def _calculate_confidence_score(self, current_weather: Optional[Dict[str, Any]], 
                                  forecast_data: Optional[List[Dict[str, Any]]]) -> float:
        """Calculate confidence score for weather predictions"""
        base_confidence = 0.5
        
        if current_weather and not current_weather.get("error"):
            base_confidence += 0.2
            if current_weather.get('condition') in ['Clear', 'Sunny', 'Partly cloudy']:
                base_confidence += 0.1
        
        if forecast_data and len(forecast_data) > 0:
            base_confidence += 0.2
            if len(forecast_data) >= 8:
                base_confidence += 0.1
        
        return min(max(base_confidence, 0.0), 1.0)
    
    def _prepare_weather_summary(self, state: WeatherCollectionState) -> str:
        """Prepare weather data summary for LLM analysis"""
        summary_parts = []
        
        for zone_id in state["processed_zones"]:
            current = state["current_weather"].get(zone_id, {})
            confidence = state["confidence_scores"].get(zone_id, 0.5)
            
            zone_summary = f"""
            Zone {zone_id}:
            - Current: {current.get('condition', 'Unknown')} ({current.get('temperature', 'N/A')}°C)
            - Visibility: {current.get('visibility', 'Unknown')}m
            - Wind: {current.get('wind_speed', 'Unknown')}m/s
            - Precipitation: {current.get('precipitation', 0)}mm/h
            - Confidence: {confidence:.2f}
            """
            summary_parts.append(zone_summary)
        
        return "\n".join(summary_parts)
    
    def _requires_weather_alert(self, weather_data: Dict[str, Any]) -> bool:
        """Check if current weather conditions require an alert"""
        visibility = weather_data.get('visibility', 10000)
        wind_speed = weather_data.get('wind_speed', 0)
        precipitation = weather_data.get('precipitation', 0)
        condition = weather_data.get('condition', '')
        
        return (
            visibility < config.VISIBILITY_THRESHOLD or
            wind_speed > config.WIND_SPEED_THRESHOLD or
            precipitation > config.PRECIPITATION_THRESHOLD or
            condition in ['Thunderstorm', 'Tornado', 'Fog', 'Heavy rain', 'Storm']
        )
    
    def _determine_alert_details(self, weather_data: Dict[str, Any]) -> tuple:
        """Determine alert type and severity based on conditions"""
        visibility = weather_data.get('visibility', 10000)
        wind_speed = weather_data.get('wind_speed', 0)
        precipitation = weather_data.get('precipitation', 0)
        condition = weather_data.get('condition', '')
        
        # Determine alert type
        if visibility < config.VISIBILITY_THRESHOLD:
            alert_type = "low_visibility"
        elif condition == 'Fog':
            alert_type = "fog"
        elif condition in ['Thunderstorm', 'Tornado', 'Storm']:
            alert_type = "storm"
        else:
            alert_type = "weather_change"
        
        # Determine severity
        if (wind_speed > config.EMERGENCY_WIND_SPEED or 
            precipitation > config.EMERGENCY_PRECIPITATION):
            severity = "critical"
        elif visibility < config.VISIBILITY_THRESHOLD / 2:
            severity = "high"
        else:
            severity = "medium"
        
        return alert_type, severity

# Create agent instance
weather_collection_forecast_agent = WeatherCollectionForecastAgent()
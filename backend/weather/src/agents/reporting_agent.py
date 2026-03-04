import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
import json
import pandas as pd
from ..config.settings import config
from ..kafka.kafka_producer import weather_producer

logger = logging.getLogger(__name__)

class ReportingState(TypedDict):
    """State class for weather reporting workflow"""
    data_sources: Dict[str, Any]
    weather_analytics: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    forecast_accuracy: Dict[str, Any]
    zone_summaries: Dict[str, Any]
    trend_analysis: Dict[str, Any]
    recommendations: Dict[str, Any]
    report_data: Dict[str, Any]
    visualization_data: Dict[str, Any]
    processed_zones: List[str]
    report_types: List[str]
    errors: List[str]
    status: str

class WeatherReportingAgent:
    """
    LangGraph-based agent for generating comprehensive weather reports,
    accuracy assessments, and performance analytics for the lighting system
    """
    
    def __init__(self):
        self.groq_config = config.get_groq_config()
        self.llm = ChatGroq(
            groq_api_key=self.groq_config['api_key'],
            model_name=self.groq_config['model'],
            temperature=self.groq_config['temperature'],
            max_tokens=self.groq_config['max_tokens']
        )
        
        # Report configuration
        self.report_config = self._initialize_report_config()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow for weather reporting"""
        workflow = StateGraph(ReportingState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_reporting)
        workflow.add_node("collect_data_sources", self._collect_data_sources_node)
        workflow.add_node("analyze_weather_patterns", self._analyze_weather_patterns_node)
        workflow.add_node("assess_forecast_accuracy", self._assess_forecast_accuracy_node)
        workflow.add_node("calculate_performance_metrics", self._calculate_performance_metrics_node)
        workflow.add_node("analyze_zone_performance", self._analyze_zone_performance_node)
        workflow.add_node("identify_trends", self._identify_trends_node)
        workflow.add_node("generate_insights", self._generate_insights_node)
        workflow.add_node("create_visualizations", self._create_visualizations_node)
        workflow.add_node("compile_reports", self._compile_reports_node)
        workflow.add_node("publish_reports", self._publish_reports_node)
        workflow.add_node("finalize", self._finalize_reporting)
        
        # Define workflow edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "collect_data_sources")
        workflow.add_edge("collect_data_sources", "analyze_weather_patterns")
        workflow.add_edge("analyze_weather_patterns", "assess_forecast_accuracy")
        workflow.add_edge("assess_forecast_accuracy", "calculate_performance_metrics")
        workflow.add_edge("calculate_performance_metrics", "analyze_zone_performance")
        workflow.add_edge("analyze_zone_performance", "identify_trends")
        workflow.add_edge("identify_trends", "generate_insights")
        workflow.add_edge("generate_insights", "create_visualizations")
        workflow.add_edge("create_visualizations", "compile_reports")
        workflow.add_edge("compile_reports", "publish_reports")
        workflow.add_edge("publish_reports", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def generate_weather_reports(self, report_types: List[str] = None) -> Dict[str, Any]:
        """Main method to execute weather reporting workflow"""
        try:
            logger.info("Starting weather reporting workflow")
            
            # Default report types if none specified
            if report_types is None:
                report_types = ["daily_summary", "forecast_accuracy", "performance_analysis"]
            
            # Initialize state
            initial_state = ReportingState(
                data_sources={},
                weather_analytics={},
                performance_metrics={},
                forecast_accuracy={},
                zone_summaries={},
                trend_analysis={},
                recommendations={},
                report_data={},
                visualization_data={},
                processed_zones=[],
                report_types=report_types,
                errors=[],
                status="initializing"
            )
            
            # Execute workflow
            final_state = self.workflow.invoke(initial_state)
            
            return {
                "status": final_state["status"],
                "report_types": final_state["report_types"],
                "processed_zones": len(final_state["processed_zones"]),
                "reports_generated": len(final_state["report_data"]),
                "performance_metrics": final_state["performance_metrics"],
                "forecast_accuracy": final_state["forecast_accuracy"],
                "recommendations": final_state["recommendations"],
                "errors": final_state["errors"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in weather reporting workflow: {e}")
            return {
                "status": "workflow_failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _initialize_reporting(self, state: ReportingState) -> ReportingState:
        """Initialize weather reporting"""
        logger.info("Initializing weather reporting")
        
        state["status"] = "collecting_data"
        
        # Set reporting time range (last 24 hours by default)
        state["data_sources"]["time_range"] = {
            "start": (datetime.now() - timedelta(hours=24)).isoformat(),
            "end": datetime.now().isoformat()
        }
        
        return state
    
    def _collect_data_sources_node(self, state: ReportingState) -> ReportingState:
        """Collect data from all weather intelligence sources"""
        logger.info("Collecting weather data sources")
        
        try:
            # Collect weather data
            weather_data = self._collect_weather_data(state["data_sources"]["time_range"])
            state["data_sources"]["weather_data"] = weather_data
            
            # Collect sensor data
            sensor_data = self._collect_sensor_data(state["data_sources"]["time_range"])
            state["data_sources"]["sensor_data"] = sensor_data
            
            # Collect forecast data
            forecast_data = self._collect_forecast_data(state["data_sources"]["time_range"])
            state["data_sources"]["forecast_data"] = forecast_data
            
            # Collect lighting system data
            lighting_data = self._collect_lighting_data(state["data_sources"]["time_range"])
            state["data_sources"]["lighting_data"] = lighting_data
            
            # Collect alert data
            alert_data = self._collect_alert_data(state["data_sources"]["time_range"])
            state["data_sources"]["alert_data"] = alert_data
            
            # Update processed zones
            state["processed_zones"] = list(set(
                list(weather_data.keys()) + 
                list(sensor_data.keys()) + 
                list(forecast_data.keys())
            ))
            
        except Exception as e:
            error_msg = f"Error collecting data sources: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _analyze_weather_patterns_node(self, state: ReportingState) -> ReportingState:
        """Analyze weather patterns and trends"""
        logger.info("Analyzing weather patterns")
        
        try:
            weather_data = state["data_sources"]["weather_data"]
            
            for zone_id in state["processed_zones"]:
                zone_weather = weather_data.get(zone_id, [])
                
                if zone_weather:
                    pattern_analysis = self._analyze_zone_weather_patterns(zone_id, zone_weather)
                    state["weather_analytics"][zone_id] = pattern_analysis
                    
        except Exception as e:
            error_msg = f"Error analyzing weather patterns: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _assess_forecast_accuracy_node(self, state: ReportingState) -> ReportingState:
        """Assess forecast accuracy against actual conditions"""
        logger.info("Assessing forecast accuracy")
        
        try:
            forecast_data = state["data_sources"]["forecast_data"]
            weather_data = state["data_sources"]["weather_data"]
            
            overall_accuracy = {}
            
            for zone_id in state["processed_zones"]:
                zone_forecasts = forecast_data.get(zone_id, [])
                zone_actuals = weather_data.get(zone_id, [])
                
                if zone_forecasts and zone_actuals:
                    accuracy_metrics = self._calculate_forecast_accuracy(zone_forecasts, zone_actuals)
                    overall_accuracy[zone_id] = accuracy_metrics
            
            state["forecast_accuracy"] = overall_accuracy
            
        except Exception as e:
            error_msg = f"Error assessing forecast accuracy: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _calculate_performance_metrics_node(self, state: ReportingState) -> ReportingState:
        """Calculate system performance metrics"""
        logger.info("Calculating performance metrics")
        
        try:
            lighting_data = state["data_sources"]["lighting_data"]
            weather_data = state["data_sources"]["weather_data"]
            alert_data = state["data_sources"]["alert_data"]
            
            # Overall system metrics
            system_metrics = self._calculate_system_metrics(lighting_data, weather_data, alert_data)
            state["performance_metrics"]["system"] = system_metrics
            
            # Zone-specific metrics
            zone_metrics = {}
            for zone_id in state["processed_zones"]:
                zone_lighting = lighting_data.get(zone_id, [])
                zone_weather = weather_data.get(zone_id, [])
                zone_alerts = [a for a in alert_data if a.get("zone_id") == zone_id]
                
                metrics = self._calculate_zone_metrics(zone_id, zone_lighting, zone_weather, zone_alerts)
                zone_metrics[zone_id] = metrics
            
            state["performance_metrics"]["zones"] = zone_metrics
            
        except Exception as e:
            error_msg = f"Error calculating performance metrics: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _analyze_zone_performance_node(self, state: ReportingState) -> ReportingState:
        """Analyze performance for each zone"""
        logger.info("Analyzing zone performance")
        
        try:
            for zone_id in state["processed_zones"]:
                weather_analytics = state["weather_analytics"].get(zone_id, {})
                performance_metrics = state["performance_metrics"]["zones"].get(zone_id, {})
                forecast_accuracy = state["forecast_accuracy"].get(zone_id, {})
                
                zone_summary = self._create_zone_summary(
                    zone_id, weather_analytics, performance_metrics, forecast_accuracy
                )
                state["zone_summaries"][zone_id] = zone_summary
                
        except Exception as e:
            error_msg = f"Error analyzing zone performance: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _identify_trends_node(self, state: ReportingState) -> ReportingState:
        """Identify trends and patterns across all data"""
        logger.info("Identifying trends and patterns")
        
        try:
            # Cross-zone trend analysis
            trend_analysis = self._perform_trend_analysis(
                state["weather_analytics"],
                state["performance_metrics"],
                state["forecast_accuracy"]
            )
            state["trend_analysis"] = trend_analysis
            
        except Exception as e:
            error_msg = f"Error identifying trends: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _generate_insights_node(self, state: ReportingState) -> ReportingState:
        """Generate insights and recommendations using LLM"""
        logger.info("Generating insights and recommendations")
        
        try:
            # Prepare comprehensive data summary for LLM
            data_summary = self._prepare_insights_summary(state)
            
            prompt = f"""
            Analyze the following comprehensive weather intelligence system data and provide insights:
            
            System Performance Data:
            {data_summary}
            
            Provide analysis and recommendations for:
            1. Overall system performance assessment
            2. Weather prediction accuracy improvements
            3. Zone-specific optimization opportunities
            4. Energy efficiency recommendations
            5. Safety and emergency response enhancements
            6. Predictive maintenance suggestions
            7. System configuration optimizations
            
            Focus on actionable insights that can improve lighting system performance,
            energy efficiency, and safety outcomes.
            """
            
            message = HumanMessage(content=prompt)
            response = self.llm.invoke([message])
            
            # Parse insights and recommendations
            insights = self._parse_insights_response(response.content)
            state["recommendations"] = insights
            
        except Exception as e:
            error_msg = f"Error generating insights: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _create_visualizations_node(self, state: ReportingState) -> ReportingState:
        """Create visualization data for reports"""
        logger.info("Creating visualization data")
        
        try:
            # Weather pattern visualizations
            weather_viz = self._create_weather_visualizations(state["weather_analytics"])
            state["visualization_data"]["weather_patterns"] = weather_viz
            
            # Performance metric visualizations
            performance_viz = self._create_performance_visualizations(state["performance_metrics"])
            state["visualization_data"]["performance_metrics"] = performance_viz
            
            # Forecast accuracy visualizations
            accuracy_viz = self._create_accuracy_visualizations(state["forecast_accuracy"])
            state["visualization_data"]["forecast_accuracy"] = accuracy_viz
            
            # Trend visualizations
            trend_viz = self._create_trend_visualizations(state["trend_analysis"])
            state["visualization_data"]["trends"] = trend_viz
            
        except Exception as e:
            error_msg = f"Error creating visualizations: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _compile_reports_node(self, state: ReportingState) -> ReportingState:
        """Compile different types of reports"""
        logger.info("Compiling weather reports")
        
        try:
            for report_type in state["report_types"]:
                report = self._generate_specific_report(report_type, state)
                state["report_data"][report_type] = report
                
        except Exception as e:
            error_msg = f"Error compiling reports: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _publish_reports_node(self, state: ReportingState) -> ReportingState:
        """Publish reports to Kafka and storage"""
        logger.info("Publishing weather reports")
        
        try:
            for report_type, report_data in state["report_data"].items():
                # Publish to Kafka
                weather_producer.publish_weather_report(report_type, report_data)
                
                # Save to file (optional)
                self._save_report_to_file(report_type, report_data)
                
        except Exception as e:
            error_msg = f"Error publishing reports: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _finalize_reporting(self, state: ReportingState) -> ReportingState:
        """Finalize weather reporting workflow"""
        logger.info("Finalizing weather reporting")
        
        if len(state["report_data"]) > 0:
            state["status"] = "reporting_complete"
        else:
            state["status"] = "reporting_failed"
        
        return state
    
    # Helper methods
    def _initialize_report_config(self) -> Dict[str, Any]:
        """Initialize reporting configuration"""
        return {
            "daily_summary": {
                "name": "Daily Weather Summary",
                "frequency": "daily",
                "includes": ["weather_patterns", "alerts", "performance"],
                "format": "comprehensive"
            },
            "forecast_accuracy": {
                "name": "Forecast Accuracy Report",
                "frequency": "weekly",
                "includes": ["accuracy_metrics", "deviation_analysis", "improvements"],
                "format": "analytical"
            },
            "performance_analysis": {
                "name": "System Performance Analysis",
                "frequency": "monthly",
                "includes": ["efficiency_metrics", "energy_usage", "optimization"],
                "format": "executive"
            },
            "emergency_response": {
                "name": "Emergency Response Report",
                "frequency": "as_needed",
                "includes": ["emergency_events", "response_times", "effectiveness"],
                "format": "detailed"
            }
        }
    
    def _collect_weather_data(self, time_range: Dict[str, str]) -> Dict[str, List[Dict[str, Any]]]:
        """Collect weather data for reporting period"""
        # Simulate weather data collection
        weather_data = {}
        
        for zone_id in config.DEFAULT_ZONES:
            # Generate simulated hourly weather data for the time range
            zone_data = []
            start_time = datetime.fromisoformat(time_range["start"])
            end_time = datetime.fromisoformat(time_range["end"])
            current_time = start_time
            
            while current_time < end_time:
                import random
                data_point = {
                    "timestamp": current_time.isoformat(),
                    "temperature": round(random.uniform(15, 25), 1),
                    "humidity": round(random.uniform(50, 80), 1),
                    "wind_speed": round(random.uniform(0, 15), 1),
                    "visibility": random.randint(2000, 10000),
                    "precipitation": round(random.uniform(0, 5), 2),
                    "weather_condition": random.choice(["Clear", "Cloudy", "Rain", "Fog"])
                }
                zone_data.append(data_point)
                current_time += timedelta(hours=1)
            
            weather_data[zone_id] = zone_data
        
        return weather_data
    
    def _collect_sensor_data(self, time_range: Dict[str, str]) -> Dict[str, List[Dict[str, Any]]]:
        """Collect sensor data for reporting period"""
        # Simulate sensor data collection
        sensor_data = {}
        
        for zone_id in config.DEFAULT_ZONES:
            zone_data = []
            start_time = datetime.fromisoformat(time_range["start"])
            end_time = datetime.fromisoformat(time_range["end"])
            current_time = start_time
            
            while current_time < end_time:
                import random
                data_point = {
                    "timestamp": current_time.isoformat(),
                    "light_level": random.randint(100, 800),
                    "motion_detected": random.choice([True, False]),
                    "air_quality": random.randint(50, 150),
                    "device_status": "active",
                    "data_quality": random.uniform(0.7, 1.0)
                }
                zone_data.append(data_point)
                current_time += timedelta(minutes=15)  # 15-minute intervals
            
            sensor_data[zone_id] = zone_data
        
        return sensor_data
    
    def _collect_forecast_data(self, time_range: Dict[str, str]) -> Dict[str, List[Dict[str, Any]]]:
        """Collect forecast data for reporting period"""
        # Simulate forecast data collection
        forecast_data = {}
        
        for zone_id in config.DEFAULT_ZONES:
            zone_data = []
            start_time = datetime.fromisoformat(time_range["start"])
            
            # Generate 6-hour forecast intervals
            current_time = start_time
            for i in range(4):  # 4 forecasts for 24 hours
                import random
                forecast_point = {
                    "forecast_timestamp": current_time.isoformat(),
                    "forecast_for": (current_time + timedelta(hours=6)).isoformat(),
                    "predicted_temperature": round(random.uniform(15, 25), 1),
                    "predicted_precipitation": round(random.uniform(0, 3), 2),
                    "predicted_wind_speed": round(random.uniform(0, 12), 1),
                    "confidence": random.uniform(0.6, 0.9)
                }
                zone_data.append(forecast_point)
                current_time += timedelta(hours=6)
            
            forecast_data[zone_id] = zone_data
        
        return forecast_data
    
    def _collect_lighting_data(self, time_range: Dict[str, str]) -> Dict[str, List[Dict[str, Any]]]:
        """Collect lighting system data for reporting period"""
        # Simulate lighting data collection
        lighting_data = {}
        
        for zone_id in config.DEFAULT_ZONES:
            zone_data = []
            start_time = datetime.fromisoformat(time_range["start"])
            end_time = datetime.fromisoformat(time_range["end"])
            current_time = start_time
            
            while current_time < end_time:
                import random
                data_point = {
                    "timestamp": current_time.isoformat(),
                    "brightness_level": random.randint(60, 100),
                    "power_consumption": round(random.uniform(80, 150), 1),
                    "adjustment_factor": round(random.uniform(0.8, 1.5), 2),
                    "mode": random.choice(["normal", "weather_adjusted", "emergency"]),
                    "efficiency": random.uniform(0.85, 0.95)
                }
                zone_data.append(data_point)
                current_time += timedelta(minutes=30)
            
            lighting_data[zone_id] = zone_data
        
        return lighting_data
    
    def _collect_alert_data(self, time_range: Dict[str, str]) -> List[Dict[str, Any]]:
        """Collect alert data for reporting period"""
        # Simulate alert data collection
        alerts = []
        
        import random
        num_alerts = random.randint(5, 15)
        
        for i in range(num_alerts):
            alert = {
                "alert_id": f"alert_{i+1}",
                "timestamp": (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat(),
                "zone_id": random.choice(config.DEFAULT_ZONES),
                "alert_type": random.choice(["low_visibility", "high_wind", "storm", "fog"]),
                "severity": random.choice(["low", "medium", "high", "critical"]),
                "duration": random.randint(15, 180),  # minutes
                "resolved": random.choice([True, False])
            }
            alerts.append(alert)
        
        return alerts
    
    def _analyze_zone_weather_patterns(self, zone_id: str, weather_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze weather patterns for a specific zone"""
        try:
            if not weather_data:
                return {"error": "no_data"}
            
            # Calculate averages and extremes
            temperatures = [d["temperature"] for d in weather_data]
            humidities = [d["humidity"] for d in weather_data]
            wind_speeds = [d["wind_speed"] for d in weather_data]
            visibilities = [d["visibility"] for d in weather_data]
            precipitations = [d["precipitation"] for d in weather_data]
            
            # Weather condition distribution
            conditions = [d["weather_condition"] for d in weather_data]
            condition_counts = {}
            for condition in conditions:
                condition_counts[condition] = condition_counts.get(condition, 0) + 1
            
            return {
                "zone_id": zone_id,
                "data_points": len(weather_data),
                "temperature": {
                    "average": round(sum(temperatures) / len(temperatures), 1),
                    "min": min(temperatures),
                    "max": max(temperatures),
                    "variance": round(sum((t - sum(temperatures)/len(temperatures))**2 for t in temperatures) / len(temperatures), 2)
                },
                "humidity": {
                    "average": round(sum(humidities) / len(humidities), 1),
                    "min": min(humidities),
                    "max": max(humidities)
                },
                "wind": {
                    "average_speed": round(sum(wind_speeds) / len(wind_speeds), 1),
                    "max_speed": max(wind_speeds),
                    "high_wind_events": len([w for w in wind_speeds if w > config.WIND_SPEED_THRESHOLD])
                },
                "visibility": {
                    "average": round(sum(visibilities) / len(visibilities), 0),
                    "min": min(visibilities),
                    "low_visibility_events": len([v for v in visibilities if v < config.VISIBILITY_THRESHOLD])
                },
                "precipitation": {
                    "total": round(sum(precipitations), 2),
                    "max_hourly": max(precipitations),
                    "rain_events": len([p for p in precipitations if p > 0])
                },
                "weather_conditions": condition_counts,
                "dominant_condition": max(condition_counts, key=condition_counts.get) if condition_counts else "unknown"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing weather patterns for {zone_id}: {e}")
            return {"error": str(e)}
    
    def _calculate_forecast_accuracy(self, forecasts: List[Dict[str, Any]], 
                                   actuals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate forecast accuracy metrics"""
        try:
            if not forecasts or not actuals:
                return {"error": "insufficient_data"}
            
            # Temperature accuracy
            temp_errors = []
            precipitation_errors = []
            
            for forecast in forecasts:
                forecast_time = datetime.fromisoformat(forecast["forecast_for"])
                
                # Find closest actual reading
                closest_actual = min(
                    actuals,
                    key=lambda x: abs(datetime.fromisoformat(x["timestamp"]) - forecast_time),
                    default=None
                )
                
                if closest_actual:
                    temp_error = abs(forecast["predicted_temperature"] - closest_actual["temperature"])
                    temp_errors.append(temp_error)
                    
                    precip_error = abs(forecast["predicted_precipitation"] - closest_actual["precipitation"])
                    precipitation_errors.append(precip_error)
            
            # Calculate accuracy metrics
            if temp_errors:
                avg_temp_error = sum(temp_errors) / len(temp_errors)
                temp_accuracy = max(0, 100 - (avg_temp_error / 2 * 100))  # Rough accuracy percentage
            else:
                avg_temp_error = 0
                temp_accuracy = 0
            
            if precipitation_errors:
                avg_precip_error = sum(precipitation_errors) / len(precipitation_errors)
                precip_accuracy = max(0, 100 - (avg_precip_error * 20))  # Rough accuracy percentage
            else:
                avg_precip_error = 0
                precip_accuracy = 0
            
            return {
                "temperature_accuracy": round(temp_accuracy, 1),
                "precipitation_accuracy": round(precip_accuracy, 1),
                "average_temperature_error": round(avg_temp_error, 1),
                "average_precipitation_error": round(avg_precip_error, 2),
                "forecasts_evaluated": len(temp_errors),
                "overall_accuracy": round((temp_accuracy + precip_accuracy) / 2, 1)
            }
            
        except Exception as e:
            logger.error(f"Error calculating forecast accuracy: {e}")
            return {"error": str(e)}
    
    def _calculate_system_metrics(self, lighting_data: Dict[str, List], 
                                weather_data: Dict[str, List], 
                                alert_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall system performance metrics"""
        try:
            # System uptime
            total_data_points = sum(len(zone_data) for zone_data in lighting_data.values())
            active_data_points = sum(
                len([d for d in zone_data if d.get("mode") != "offline"])
                for zone_data in lighting_data.values()
            )
            uptime_percentage = (active_data_points / total_data_points * 100) if total_data_points > 0 else 0
            
            # Energy efficiency
            all_efficiency = []
            all_power = []
            for zone_data in lighting_data.values():
                all_efficiency.extend([d.get("efficiency", 0) for d in zone_data])
                all_power.extend([d.get("power_consumption", 0) for d in zone_data])
            
            avg_efficiency = sum(all_efficiency) / len(all_efficiency) if all_efficiency else 0
            avg_power = sum(all_power) / len(all_power) if all_power else 0
            
            # Alert response metrics
            total_alerts = len(alert_data)
            resolved_alerts = len([a for a in alert_data if a.get("resolved", False)])
            alert_resolution_rate = (resolved_alerts / total_alerts * 100) if total_alerts > 0 else 100
            
            # Critical event response
            critical_alerts = [a for a in alert_data if a.get("severity") == "critical"]
            avg_response_time = sum(a.get("duration", 0) for a in critical_alerts) / len(critical_alerts) if critical_alerts else 0
            
            return {
                "system_uptime": round(uptime_percentage, 2),
                "average_efficiency": round(avg_efficiency * 100, 1),
                "average_power_consumption": round(avg_power, 1),
                "total_alerts": total_alerts,
                "alert_resolution_rate": round(alert_resolution_rate, 1),
                "critical_alerts": len(critical_alerts),
                "average_response_time": round(avg_response_time, 1),
                "zones_monitored": len(lighting_data),
                "data_quality": "good" if uptime_percentage > 95 else "needs_attention"
            }
            
        except Exception as e:
            logger.error(f"Error calculating system metrics: {e}")
            return {"error": str(e)}
    
    def _calculate_zone_metrics(self, zone_id: str, lighting_data: List, 
                              weather_data: List, alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance metrics for a specific zone"""
        try:
            # Lighting performance
            if lighting_data:
                brightness_levels = [d.get("brightness_level", 0) for d in lighting_data]
                power_consumption = [d.get("power_consumption", 0) for d in lighting_data]
                adjustments = [d.get("adjustment_factor", 1.0) for d in lighting_data]
                
                avg_brightness = sum(brightness_levels) / len(brightness_levels)
                avg_power = sum(power_consumption) / len(power_consumption)
                avg_adjustment = sum(adjustments) / len(adjustments)
                
                # Weather responsiveness
                weather_adjusted_count = len([d for d in lighting_data if d.get("mode") == "weather_adjusted"])
                responsiveness = (weather_adjusted_count / len(lighting_data) * 100) if lighting_data else 0
            else:
                avg_brightness = avg_power = avg_adjustment = responsiveness = 0
            
            # Zone-specific alerts
            zone_alerts = len(alerts)
            critical_zone_alerts = len([a for a in alerts if a.get("severity") == "critical"])
            
            return {
                "zone_id": zone_id,
                "average_brightness": round(avg_brightness, 1),
                "average_power_consumption": round(avg_power, 1),
                "average_adjustment_factor": round(avg_adjustment, 2),
                "weather_responsiveness": round(responsiveness, 1),
                "total_alerts": zone_alerts,
                "critical_alerts": critical_zone_alerts,
                "data_points": len(lighting_data),
                "performance_score": round((avg_brightness + responsiveness) / 2, 1)
            }
            
        except Exception as e:
            logger.error(f"Error calculating zone metrics for {zone_id}: {e}")
            return {"error": str(e)}
    
    def _create_zone_summary(self, zone_id: str, weather_analytics: Dict[str, Any], 
                           performance_metrics: Dict[str, Any], 
                           forecast_accuracy: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive zone summary"""
        return {
            "zone_id": zone_id,
            "weather_summary": {
                "dominant_condition": weather_analytics.get("dominant_condition", "unknown"),
                "average_temperature": weather_analytics.get("temperature", {}).get("average", 0),
                "weather_events": weather_analytics.get("weather_conditions", {}),
                "stability": "stable" if weather_analytics.get("temperature", {}).get("variance", 0) < 5 else "variable"
            },
            "performance_summary": {
                "overall_score": performance_metrics.get("performance_score", 0),
                "efficiency": performance_metrics.get("weather_responsiveness", 0),
                "reliability": "high" if performance_metrics.get("total_alerts", 0) < 5 else "medium"
            },
            "forecast_summary": {
                "accuracy": forecast_accuracy.get("overall_accuracy", 0),
                "reliability": "good" if forecast_accuracy.get("overall_accuracy", 0) > 80 else "needs_improvement"
            },
            "recommendations": self._generate_zone_recommendations(weather_analytics, performance_metrics, forecast_accuracy),
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_zone_recommendations(self, weather_analytics: Dict[str, Any], 
                                     performance_metrics: Dict[str, Any], 
                                     forecast_accuracy: Dict[str, Any]) -> List[str]:
        """Generate zone-specific recommendations"""
        recommendations = []
        
        # Weather-based recommendations
        if weather_analytics.get("wind", {}).get("high_wind_events", 0) > 5:
            recommendations.append("Consider wind-resistant lighting fixtures")
        
        if weather_analytics.get("visibility", {}).get("low_visibility_events", 0) > 3:
            recommendations.append("Increase base lighting levels during low visibility periods")
        
        # Performance-based recommendations
        if performance_metrics.get("weather_responsiveness", 0) < 70:
            recommendations.append("Improve weather response sensitivity")
        
        if performance_metrics.get("total_alerts", 0) > 10:
            recommendations.append("Review alert thresholds and response protocols")
        
        # Forecast accuracy recommendations
        if forecast_accuracy.get("overall_accuracy", 0) < 75:
            recommendations.append("Enhance forecast data sources and algorithms")
        
        return recommendations if recommendations else ["Continue current operation - performance is optimal"]
    
    def _perform_trend_analysis(self, weather_analytics: Dict[str, Any], 
                              performance_metrics: Dict[str, Any], 
                              forecast_accuracy: Dict[str, Any]) -> Dict[str, Any]:
        """Perform cross-zone trend analysis"""
        try:
            # Weather trends across zones
            all_temps = []
            all_wind_events = []
            all_visibility_events = []
            
            for zone_data in weather_analytics.values():
                if isinstance(zone_data, dict) and "temperature" in zone_data:
                    all_temps.append(zone_data["temperature"].get("average", 0))
                    all_wind_events.append(zone_data.get("wind", {}).get("high_wind_events", 0))
                    all_visibility_events.append(zone_data.get("visibility", {}).get("low_visibility_events", 0))
            
            # Performance trends
            all_scores = []
            all_responsiveness = []
            
            for zone_data in performance_metrics.get("zones", {}).values():
                if isinstance(zone_data, dict):
                    all_scores.append(zone_data.get("performance_score", 0))
                    all_responsiveness.append(zone_data.get("weather_responsiveness", 0))
            
            # Accuracy trends
            all_accuracy = []
            for zone_data in forecast_accuracy.values():
                if isinstance(zone_data, dict):
                    all_accuracy.append(zone_data.get("overall_accuracy", 0))
            
            return {
                "weather_trends": {
                    "average_temperature": round(sum(all_temps) / len(all_temps), 1) if all_temps else 0,
                    "total_wind_events": sum(all_wind_events),
                    "total_visibility_events": sum(all_visibility_events),
                    "most_affected_zones": len([x for x in all_wind_events if x > 3])
                },
                "performance_trends": {
                    "average_performance_score": round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
                    "average_responsiveness": round(sum(all_responsiveness) / len(all_responsiveness), 1) if all_responsiveness else 0,
                    "high_performing_zones": len([x for x in all_scores if x > 80]),
                    "zones_needing_attention": len([x for x in all_scores if x < 60])
                },
                "forecast_trends": {
                    "average_accuracy": round(sum(all_accuracy) / len(all_accuracy), 1) if all_accuracy else 0,
                    "accurate_zones": len([x for x in all_accuracy if x > 85]),
                    "improvement_needed": len([x for x in all_accuracy if x < 70])
                },
                "system_health": "good" if (sum(all_scores) / len(all_scores) if all_scores else 0) > 75 else "needs_attention"
            }
            
        except Exception as e:
            logger.error(f"Error performing trend analysis: {e}")
            return {"error": str(e)}
    
    def _prepare_insights_summary(self, state: ReportingState) -> str:
        """Prepare comprehensive summary for LLM insights"""
        summary_parts = []
        
        # System overview
        system_metrics = state["performance_metrics"].get("system", {})
        summary_parts.append(f"System Overview:")
        summary_parts.append(f"- Uptime: {system_metrics.get('system_uptime', 0)}%")
        summary_parts.append(f"- Average Efficiency: {system_metrics.get('average_efficiency', 0)}%")
        summary_parts.append(f"- Total Alerts: {system_metrics.get('total_alerts', 0)}")
        summary_parts.append(f"- Alert Resolution Rate: {system_metrics.get('alert_resolution_rate', 0)}%")
        
        # Zone performance summary
        summary_parts.append(f"\nZone Performance:")
        for zone_id, zone_summary in state["zone_summaries"].items():
            performance = zone_summary.get("performance_summary", {})
            weather = zone_summary.get("weather_summary", {})
            summary_parts.append(
                f"- {zone_id}: Score {performance.get('overall_score', 0)}, "
                f"Condition: {weather.get('dominant_condition', 'unknown')}, "
                f"Efficiency: {performance.get('efficiency', 0)}%"
            )
        
        # Trend analysis
        trends = state["trend_analysis"]
        summary_parts.append(f"\nSystem Trends:")
        summary_parts.append(f"- Average Performance: {trends.get('performance_trends', {}).get('average_performance_score', 0)}")
        summary_parts.append(f"- Forecast Accuracy: {trends.get('forecast_trends', {}).get('average_accuracy', 0)}%")
        summary_parts.append(f"- System Health: {trends.get('system_health', 'unknown')}")
        
        return "\n".join(summary_parts)
    
    def _parse_insights_response(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM insights response"""
        return {
            "insights": llm_response,
            "generated_at": datetime.now().isoformat(),
            "recommendations": {
                "immediate_actions": ["Review system performance metrics", "Address high-alert zones"],
                "short_term": ["Optimize weather response algorithms", "Improve forecast accuracy"],
                "long_term": ["Consider system upgrades", "Enhance predictive capabilities"]
            },
            "priority_areas": ["forecast_accuracy", "energy_efficiency", "emergency_response"],
            "confidence_level": "high"
        }
    
    def _create_weather_visualizations(self, weather_analytics: Dict[str, Any]) -> Dict[str, Any]:
        """Create weather pattern visualization data"""
        return {
            "temperature_trends": {
                "type": "line_chart",
                "data": [
                    {"zone": zone_id, "avg_temp": data.get("temperature", {}).get("average", 0)}
                    for zone_id, data in weather_analytics.items()
                    if isinstance(data, dict)
                ]
            },
            "weather_distribution": {
                "type": "pie_chart",
                "data": {}  # Would be populated with actual weather condition distributions
            },
            "wind_events": {
                "type": "bar_chart",
                "data": [
                    {"zone": zone_id, "events": data.get("wind", {}).get("high_wind_events", 0)}
                    for zone_id, data in weather_analytics.items()
                    if isinstance(data, dict)
                ]
            }
        }
    
    def _create_performance_visualizations(self, performance_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Create performance visualization data"""
        return {
            "zone_performance": {
                "type": "radar_chart",
                "data": [
                    {"zone": zone_id, "score": data.get("performance_score", 0)}
                    for zone_id, data in performance_metrics.get("zones", {}).items()
                    if isinstance(data, dict)
                ]
            },
            "efficiency_trends": {
                "type": "line_chart",
                "data": []  # Would be populated with time-series efficiency data
            }
        }
    
    def _create_accuracy_visualizations(self, forecast_accuracy: Dict[str, Any]) -> Dict[str, Any]:
        """Create forecast accuracy visualization data"""
        return {
            "accuracy_by_zone": {
                "type": "bar_chart",
                "data": [
                    {"zone": zone_id, "accuracy": data.get("overall_accuracy", 0)}
                    for zone_id, data in forecast_accuracy.items()
                    if isinstance(data, dict)
                ]
            }
        }
    
    def _create_trend_visualizations(self, trend_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create trend visualization data"""
        return {
            "system_health_trend": {
                "type": "gauge_chart",
                "data": {"health_score": 85}  # Would be calculated from actual trends
            }
        }
    
    def _generate_specific_report(self, report_type: str, state: ReportingState) -> Dict[str, Any]:
        """Generate specific type of report"""
        report_config = self.report_config.get(report_type, {})
        
        base_report = {
            "report_type": report_type,
            "report_name": report_config.get("name", f"{report_type} Report"),
            "generated_at": datetime.now().isoformat(),
            "time_period": state["data_sources"]["time_range"],
            "zones_analyzed": len(state["processed_zones"]),
            "data_quality": "good"
        }
        
        if report_type == "daily_summary":
            base_report.update({
                "weather_summary": state["weather_analytics"],
                "performance_summary": state["performance_metrics"],
                "alerts_summary": state["data_sources"].get("alert_data", []),
                "key_insights": state["recommendations"].get("insights", "")
            })
        
        elif report_type == "forecast_accuracy":
            base_report.update({
                "accuracy_metrics": state["forecast_accuracy"],
                "improvement_areas": state["recommendations"].get("recommendations", {}),
                "trend_analysis": state["trend_analysis"].get("forecast_trends", {})
            })
        
        elif report_type == "performance_analysis":
            base_report.update({
                "system_metrics": state["performance_metrics"],
                "zone_performance": state["zone_summaries"],
                "trends": state["trend_analysis"],
                "optimization_recommendations": state["recommendations"]
            })
        
        return base_report
    
    def _save_report_to_file(self, report_type: str, report_data: Dict[str, Any]):
        """Save report to file (optional functionality)"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"weather_report_{report_type}_{timestamp}.json"
            
            # In a real implementation, this would save to a proper file system
            logger.info(f"Report {report_type} would be saved as {filename}")
            
        except Exception as e:
            logger.error(f"Error saving report to file: {e}")

# Create agent instance
weather_reporting_agent = WeatherReportingAgent()
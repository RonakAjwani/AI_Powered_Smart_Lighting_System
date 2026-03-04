from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import logging
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
import math 

from ..config.settings import config
from ..kafka.kafka_producer import power_producer

# Configure logging
logger = logging.getLogger(__name__)

class EnergyOptimizationState:
    """State management for Energy Optimization Agent"""
    
    def __init__(self):
        self.power_budget: Dict[str, float] = {}
        self.weather_brightness: Dict[str, Any] = {}
        self.occupancy_data: Dict[str, Any] = {}
        self.current_brightness: Dict[str, float] = {}
        self.energy_costs: Dict[str, Any] = {}
        self.optimization_targets: Dict[str, float] = {}
        self.dimming_schedules: Dict[str, Any] = {}
        self.energy_savings: Dict[str, float] = {}
        self.optimization_commands: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.status: str = "initialized"

class EnergyOptimizationAgent:
    """LangGraph-based Energy Optimization Agent"""
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=config.GROQ_API_KEY,
            model=config.GROQ_MODEL,
            temperature=config.GROQ_TEMPERATURE,
            max_tokens=config.GROQ_MAX_TOKENS
        )
        self.state = EnergyOptimizationState()
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create LangGraph workflow for energy optimization"""
        
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("analyze_budget", self._analyze_budget_node)
        workflow.add_node("assess_weather", self._assess_weather_node)
        workflow.add_node("evaluate_occupancy", self._evaluate_occupancy_node)
        workflow.add_node("calculate_targets", self._calculate_targets_node)
        workflow.add_node("optimize_brightness", self._optimize_brightness_node)
        workflow.add_node("create_schedules", self._create_schedules_node)
        workflow.add_node("implement_optimization", self._implement_optimization_node)
        
        # Define workflow
        workflow.set_entry_point("analyze_budget")
        workflow.add_edge("analyze_budget", "assess_weather")
        workflow.add_edge("assess_weather", "evaluate_occupancy")
        workflow.add_edge("evaluate_occupancy", "calculate_targets")
        workflow.add_edge("calculate_targets", "optimize_brightness")
        workflow.add_edge("optimize_brightness", "create_schedules")
        workflow.add_edge("create_schedules", "implement_optimization")
        workflow.add_edge("implement_optimization", END)
        
        return workflow.compile()
    
    def _analyze_budget_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze power budget constraints"""
        try:
            logger.info("Analyzing power budget constraints")
            
            current_time = datetime.now()
            current_hour = current_time.hour
            
            # Simulate power budget data
            power_budget = {}
            energy_costs = {}
            
            # Time-of-use pricing simulation
            if 17 <= current_hour <= 21:  # Peak hours
                rate_multiplier = 1.5
                budget_pressure = "high"
            elif 22 <= current_hour <= 6:  # Off-peak hours
                rate_multiplier = 0.7
                budget_pressure = "low"
            else:  # Standard hours
                rate_multiplier = 1.0
                budget_pressure = "medium"
            
            # Calculate budget per zone
            base_budget = 10.0  # kW base allocation per zone
            for zone in config.DEFAULT_ZONES:
                zone_hash = hash(zone) % 100
                
                # Priority zones get higher budget
                if zone in config.PRIORITY_ZONES:
                    budget_allocation = base_budget * 1.5
                    priority_factor = 1.0
                else:
                    budget_allocation = base_budget * (0.8 + (zone_hash % 40) * 0.01)  # 80-120% of base
                    priority_factor = 0.8
                
                power_budget[zone] = {
                    "allocated_budget": budget_allocation,
                    "current_usage": budget_allocation * (0.6 + (zone_hash % 30) * 0.01),  # 60-90% usage
                    "available_budget": budget_allocation * (0.1 + (zone_hash % 20) * 0.01),  # 10-30% available
                    "priority_factor": priority_factor,
                    "budget_utilization": (budget_allocation * (0.6 + (zone_hash % 30) * 0.01)) / budget_allocation
                }
                
                energy_costs[zone] = {
                    "rate_per_kwh": 0.12 * rate_multiplier,  # $/kWh
                    "demand_charge": 15.0,  # $/kW
                    "current_cost": power_budget[zone]["current_usage"] * 0.12 * rate_multiplier,
                    "budget_pressure": budget_pressure
                }
            
            # Calculate system-wide metrics
            total_allocated = sum(b["allocated_budget"] for b in power_budget.values())
            total_used = sum(b["current_usage"] for b in power_budget.values())
            overall_utilization = total_used / total_allocated if total_allocated > 0 else 0
            
            # LLM budget analysis
            prompt = f"""
            Analyze power budget constraints for energy optimization:
            
            Current Hour: {current_hour}
            Rate Multiplier: {rate_multiplier}x (Budget Pressure: {budget_pressure})
            Total Allocated Budget: {total_allocated:.1f} kW
            Total Current Usage: {total_used:.1f} kW
            Overall Utilization: {overall_utilization:.1%}
            
            Sample Zone Data: {json.dumps({k: v for k, v in list(power_budget.items())[:3]}, indent=2)}
            
            Assess:
            1. Budget optimization opportunities
            2. Cost reduction strategies
            3. Peak demand management needs
            4. Priority reallocation recommendations
            
            Return budget analysis in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            state["power_budget"] = power_budget
            state["energy_costs"] = energy_costs
            state["overall_utilization"] = overall_utilization
            state["budget_pressure"] = budget_pressure
            state["rate_multiplier"] = rate_multiplier
            state["budget_analysis"] = response.content
            
            logger.info(f"Budget analysis completed - Utilization: {overall_utilization:.1%}, Pressure: {budget_pressure}")
            return state
            
        except Exception as e:
            logger.error(f"Error analyzing budget: {e}")
            state["errors"] = state.get("errors", []) + [f"Budget analysis failed: {str(e)}"]
            return state
    
    def _assess_weather_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Assess weather brightness data impact"""
        try:
            logger.info("Assessing weather brightness data")
            
            current_time = datetime.now()
            current_hour = current_time.hour
            
            # Simulate weather brightness data
            weather_brightness = {
                "ambient_light_level": max(0, 100 * abs(math.cos((current_hour - 12) * math.pi / 12))),  # 0-100 lux
                "cloud_cover": 0.3,  # 30% cloud cover
                "weather_condition": "Partly Cloudy",
                "sunrise": "06:30",
                "sunset": "18:45",
                "natural_light_availability": 0.7,  # 70% of optimal
                "lighting_adjustment_factor": 1.3,  # Need 30% more artificial lighting
                "timestamp": current_time.isoformat()
            }
            
            # Calculate zone-specific brightness requirements
            zone_brightness_needs = {}
            for zone in config.DEFAULT_ZONES:
                zone_hash = hash(zone) % 100
                
                # Base lighting requirement
                if 6 <= current_hour <= 18:  # Daylight hours
                    base_requirement = 0.4 + (zone_hash % 30) * 0.01  # 40-70% artificial lighting
                else:  # Night hours
                    base_requirement = 0.8 + (zone_hash % 20) * 0.01  # 80-100% artificial lighting
                
                # Adjust for weather
                weather_adjusted = base_requirement * weather_brightness["lighting_adjustment_factor"]
                weather_adjusted = min(1.0, weather_adjusted)  # Cap at 100%
                
                zone_brightness_needs[zone] = {
                    "base_requirement": base_requirement,
                    "weather_adjusted": weather_adjusted,
                    "natural_light_contribution": weather_brightness["natural_light_availability"] * (1 - base_requirement),
                    "energy_impact": weather_adjusted - base_requirement,
                    "zone_type": "indoor" if zone_hash % 2 == 0 else "outdoor"
                }
            
            # LLM weather impact analysis
            prompt = f"""
            Analyze weather impact on lighting energy optimization:
            
            Current Time: {current_hour}:00
            Weather Data: {json.dumps(weather_brightness, indent=2)}
            
            Zone Brightness Analysis: {json.dumps({k: v for k, v in list(zone_brightness_needs.items())[:3]}, indent=2)}
            
            Evaluate:
            1. Natural light utilization opportunities
            2. Weather-based dimming strategies
            3. Energy savings potential from daylight harvesting
            4. Adaptive lighting recommendations
            
            Return weather impact assessment in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            state["weather_brightness"] = weather_brightness
            state["zone_brightness_needs"] = zone_brightness_needs
            state["weather_analysis"] = response.content
            
            avg_adjustment = sum(z["weather_adjusted"] for z in zone_brightness_needs.values()) / len(zone_brightness_needs)
            logger.info(f"Weather assessment completed - Avg brightness need: {avg_adjustment:.1%}")
            return state
            
        except Exception as e:
            logger.error(f"Error assessing weather: {e}")
            state["errors"] = state.get("errors", []) + [f"Weather assessment failed: {str(e)}"]
            return state
    
    def _evaluate_occupancy_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate occupancy sensor data"""
        try:
            logger.info("Evaluating occupancy sensor data")
            
            current_time = datetime.now()
            current_hour = current_time.hour
            current_day = current_time.strftime("%A")
            
            # Simulate occupancy data
            occupancy_data = {}
            
            for zone in config.DEFAULT_ZONES:
                zone_hash = hash(zone) % 100
                
                # Time-based occupancy patterns
                if current_day in ["Saturday", "Sunday"]:
                    # Weekend patterns
                    if 10 <= current_hour <= 16:
                        base_occupancy = 0.3 + (zone_hash % 30) * 0.01  # 30-60%
                    else:
                        base_occupancy = 0.1 + (zone_hash % 20) * 0.01  # 10-30%
                else:
                    # Weekday patterns
                    if 8 <= current_hour <= 18:
                        base_occupancy = 0.6 + (zone_hash % 35) * 0.01  # 60-95%
                    elif 18 <= current_hour <= 22:
                        base_occupancy = 0.4 + (zone_hash % 25) * 0.01  # 40-65%
                    else:
                        base_occupancy = 0.05 + (zone_hash % 15) * 0.01  # 5-20%
                
                # Zone type adjustments
                if zone in config.PRIORITY_ZONES:
                    occupancy_factor = min(1.0, base_occupancy * 1.2)  # Higher occupancy in priority zones
                else:
                    occupancy_factor = base_occupancy
                
                people_count = int(occupancy_factor * 50)  # Assume max 50 people per zone
                
                occupancy_data[zone] = {
                    "occupancy_rate": occupancy_factor,
                    "people_count": people_count,
                    "activity_level": "high" if occupancy_factor > 0.7 else "medium" if occupancy_factor > 0.3 else "low",
                    "lighting_demand": occupancy_factor * (0.8 + (zone_hash % 20) * 0.01),  # 80-100% of occupancy
                    "energy_scaling_factor": 0.3 + occupancy_factor * 0.7,  # 30-100% energy scaling
                    "motion_detected": occupancy_factor > 0.1,
                    "last_activity": current_time - timedelta(minutes=int((1 - occupancy_factor) * 60))
                }
            
            # Calculate optimization opportunities
            total_zones = len(occupancy_data)
            low_occupancy_zones = len([z for z in occupancy_data.values() if z["occupancy_rate"] < 0.2])
            high_occupancy_zones = len([z for z in occupancy_data.values() if z["occupancy_rate"] > 0.8])
            
            # LLM occupancy analysis
            prompt = f"""
            Analyze occupancy patterns for energy optimization:
            
            Current Time: {current_hour}:00 on {current_day}
            Total Zones: {total_zones}
            Low Occupancy Zones: {low_occupancy_zones} (<20% occupied)
            High Occupancy Zones: {high_occupancy_zones} (>80% occupied)
            
            Sample Occupancy Data: {json.dumps({k: v for k, v in list(occupancy_data.items())[:3]}, indent=2)}
            
            Identify:
            1. Energy saving opportunities in low occupancy areas
            2. Comfort requirements in high occupancy areas
            3. Motion-based dimming strategies
            4. Adaptive lighting schedule recommendations
            
            Return occupancy analysis in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            state["occupancy_data"] = occupancy_data
            state["low_occupancy_zones"] = low_occupancy_zones
            state["high_occupancy_zones"] = high_occupancy_zones
            state["occupancy_analysis"] = response.content
            
            logger.info(f"Occupancy evaluation completed - Low: {low_occupancy_zones}, High: {high_occupancy_zones}")
            return state
            
        except Exception as e:
            logger.error(f"Error evaluating occupancy: {e}")
            state["errors"] = state.get("errors", []) + [f"Occupancy evaluation failed: {str(e)}"]
            return state
    
    def _calculate_targets_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimization targets"""
        try:
            logger.info("Calculating optimization targets")
            
            power_budget = state.get("power_budget", {})
            zone_brightness_needs = state.get("zone_brightness_needs", {})
            occupancy_data = state.get("occupancy_data", {})
            
            optimization_targets = {}
            
            for zone in config.DEFAULT_ZONES:
                budget_info = power_budget.get(zone, {})
                brightness_need = zone_brightness_needs.get(zone, {})
                occupancy_info = occupancy_data.get(zone, {})
                
                # Calculate target brightness
                weather_requirement = brightness_need.get("weather_adjusted", 0.8)
                occupancy_scaling = occupancy_info.get("energy_scaling_factor", 1.0)
                budget_constraint = budget_info.get("budget_utilization", 1.0)
                
                # Target brightness balances all factors
                target_brightness = weather_requirement * occupancy_scaling
                
                # Apply budget constraints
                if budget_constraint > 0.9:  # High budget pressure
                    target_brightness *= 0.85  # Reduce by 15%
                elif budget_constraint < 0.6:  # Low budget pressure
                    target_brightness *= 1.1  # Increase by 10%
                
                # Ensure within acceptable limits
                target_brightness = max(config.MIN_DIMMING_LEVEL / 100.0, target_brightness)
                target_brightness = min(config.MAX_BRIGHTNESS_LEVEL / 100.0, target_brightness)
                
                # Calculate energy targets
                current_usage = budget_info.get("current_usage", 0)
                target_usage = current_usage * target_brightness / 0.8  # Assume current at 80% brightness
                energy_savings = max(0, current_usage - target_usage)
                
                optimization_targets[zone] = {
                    "target_brightness": target_brightness,
                    "target_brightness_percent": target_brightness * 100,
                    "current_usage": current_usage,
                    "target_usage": target_usage,
                    "energy_savings": energy_savings,
                    "savings_percent": (energy_savings / current_usage * 100) if current_usage > 0 else 0,
                    "comfort_priority": "high" if zone in config.PRIORITY_ZONES else "medium",
                    "optimization_potential": "high" if energy_savings > current_usage * 0.1 else "low"
                }
            
            # Calculate system-wide targets
            total_current_usage = sum(t["current_usage"] for t in optimization_targets.values())
            total_target_usage = sum(t["target_usage"] for t in optimization_targets.values())
            total_savings = total_current_usage - total_target_usage
            overall_savings_percent = (total_savings / total_current_usage * 100) if total_current_usage > 0 else 0
            
            # LLM target validation
            prompt = f"""
            Review optimization targets calculation:
            
            System-wide Metrics:
            - Total Current Usage: {total_current_usage:.1f} kW
            - Total Target Usage: {total_target_usage:.1f} kW
            - Total Energy Savings: {total_savings:.1f} kW ({overall_savings_percent:.1f}%)
            - Savings Target: {config.ENERGY_SAVINGS_TARGET}%
            
            Sample Zone Targets: {json.dumps({k: v for k, v in list(optimization_targets.items())[:3]}, indent=2)}
            
            Validate:
            1. Target achievability and comfort impact
            2. Energy savings vs comfort balance
            3. Budget constraint satisfaction
            4. Optimization priority recommendations
            
            Return target validation in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            state["optimization_targets"] = optimization_targets
            state["total_savings"] = total_savings
            state["overall_savings_percent"] = overall_savings_percent
            state["target_validation"] = response.content
            state["targets_meet_goal"] = overall_savings_percent >= config.ENERGY_SAVINGS_TARGET
            
            logger.info(f"Optimization targets calculated - {overall_savings_percent:.1f}% energy savings")
            return state
            
        except Exception as e:
            logger.error(f"Error calculating targets: {e}")
            state["errors"] = state.get("errors", []) + [f"Target calculation failed: {str(e)}"]
            return state
    
    def _optimize_brightness_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize brightness levels per zone"""
        try:
            logger.info("Optimizing brightness levels")
            
            optimization_targets = state.get("optimization_targets", {})
            occupancy_data = state.get("occupancy_data", {})
            
            current_brightness = {}
            optimized_brightness = {}
            
            for zone in config.DEFAULT_ZONES:
                target_info = optimization_targets.get(zone, {})
                occupancy_info = occupancy_data.get(zone, {})
                
                # Current brightness simulation
                zone_hash = hash(zone) % 100
                current_level = 70 + (zone_hash % 30)  # 70-100% current brightness
                
                # Target brightness from optimization
                target_level = target_info.get("target_brightness_percent", 80.0)
                
                # Fine-tune based on real-time occupancy
                occupancy_rate = occupancy_info.get("occupancy_rate", 0.5)
                if occupancy_rate < 0.1:  # Very low occupancy
                    final_brightness = max(config.MIN_DIMMING_LEVEL, target_level * 0.6)  # Dim to 60% of target
                elif occupancy_rate > 0.9:  # Very high occupancy
                    final_brightness = min(config.MAX_BRIGHTNESS_LEVEL, target_level * 1.1)  # Boost to 110% of target
                else:
                    final_brightness = target_level
                
                # Ensure within limits
                final_brightness = max(config.MIN_DIMMING_LEVEL, final_brightness)
                final_brightness = min(config.MAX_BRIGHTNESS_LEVEL, final_brightness)
                
                current_brightness[zone] = current_level
                optimized_brightness[zone] = {
                    "current_brightness": current_level,
                    "target_brightness": target_level,
                    "final_brightness": final_brightness,
                    "brightness_change": final_brightness - current_level,
                    "change_percent": ((final_brightness - current_level) / current_level * 100) if current_level > 0 else 0,
                    "dimming_applied": final_brightness < current_level,
                    "energy_impact": target_info.get("energy_savings", 0)
                }
            
            # Calculate optimization summary
            zones_dimmed = len([z for z in optimized_brightness.values() if z["dimming_applied"]])
            avg_brightness_change = sum(z["change_percent"] for z in optimized_brightness.values()) / len(optimized_brightness)
            
            state["current_brightness"] = current_brightness
            state["optimized_brightness"] = optimized_brightness
            state["zones_dimmed"] = zones_dimmed
            state["avg_brightness_change"] = avg_brightness_change
            
            logger.info(f"Brightness optimization completed - {zones_dimmed} zones dimmed, avg change: {avg_brightness_change:.1f}%")
            return state
            
        except Exception as e:
            logger.error(f"Error optimizing brightness: {e}")
            state["errors"] = state.get("errors", []) + [f"Brightness optimization failed: {str(e)}"]
            return state
    
    def _create_schedules_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create dimming schedules and profiles"""
        try:
            logger.info("Creating dimming schedules")
            
            optimized_brightness = state.get("optimized_brightness", {})
            occupancy_data = state.get("occupancy_data", {})
            
            dimming_schedules = {}
            current_time = datetime.now()
            
            for zone in config.DEFAULT_ZONES:
                brightness_info = optimized_brightness.get(zone, {})
                occupancy_info = occupancy_data.get(zone, {})
                
                # Create hourly schedule for next 24 hours
                hourly_schedule = []
                
                for hour_offset in range(24):
                    schedule_time = current_time + timedelta(hours=hour_offset)
                    hour = schedule_time.hour
                    
                    # Base brightness from optimization
                    base_brightness = brightness_info.get("final_brightness", 80.0)
                    
                    # Time-of-day adjustments
                    if 22 <= hour or hour <= 6:  # Night hours
                        time_factor = 0.6  # Dim to 60%
                    elif 7 <= hour <= 9 or 17 <= hour <= 19:  # Transition hours
                        time_factor = 0.8  # Dim to 80%
                    else:  # Normal hours
                        time_factor = 1.0
                    
                    scheduled_brightness = base_brightness * time_factor
                    scheduled_brightness = max(config.MIN_DIMMING_LEVEL, scheduled_brightness)
                    
                    hourly_schedule.append({
                        "hour": hour,
                        "timestamp": schedule_time.isoformat(),
                        "brightness_percent": scheduled_brightness,
                        "time_factor": time_factor,
                        "estimated_energy": scheduled_brightness * 0.01 * 10  # kW estimation
                    })
                
                # Create schedule metadata
                dimming_schedules[zone] = {
                    "zone": zone,
                    "schedule_created": current_time.isoformat(),
                    "schedule_type": "adaptive_24hour",
                    "hourly_schedule": hourly_schedule,
                    "min_brightness": min(h["brightness_percent"] for h in hourly_schedule),
                    "max_brightness": max(h["brightness_percent"] for h in hourly_schedule),
                    "avg_brightness": sum(h["brightness_percent"] for h in hourly_schedule) / 24,
                    "total_daily_energy": sum(h["estimated_energy"] for h in hourly_schedule),
                    "energy_savings_daily": (brightness_info.get("energy_impact", 0) * 24)
                }
            
            # Calculate system-wide schedule metrics
            total_daily_energy = sum(s["total_daily_energy"] for s in dimming_schedules.values())
            total_daily_savings = sum(s["energy_savings_daily"] for s in dimming_schedules.values())
            
            state["dimming_schedules"] = dimming_schedules
            state["total_daily_energy"] = total_daily_energy
            state["total_daily_savings"] = total_daily_savings
            state["schedule_created_at"] = current_time.isoformat()
            
            logger.info(f"Dimming schedules created - Daily energy: {total_daily_energy:.1f}kWh, Savings: {total_daily_savings:.1f}kWh")
            return state
            
        except Exception as e:
            logger.error(f"Error creating schedules: {e}")
            state["errors"] = state.get("errors", []) + [f"Schedule creation failed: {str(e)}"]
            return state
    
    def _implement_optimization_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Implement optimization commands"""
        try:
            logger.info("Implementing energy optimization commands")
            
            optimized_brightness = state.get("optimized_brightness", {})
            dimming_schedules = state.get("dimming_schedules", {})
            
            optimization_commands = []
            
            for zone in config.DEFAULT_ZONES:
                brightness_info = optimized_brightness.get(zone, {})
                schedule_info = dimming_schedules.get(zone, {})
                
                # Create immediate optimization command
                if brightness_info.get("brightness_change", 0) != 0:
                    command = {
                        "command_id": f"optimize_{zone}_{datetime.now().strftime('%H%M%S')}",
                        "zone": zone,
                        "command_type": "brightness_optimization",
                        "current_brightness": brightness_info.get("current_brightness", 80),
                        "target_brightness": brightness_info.get("final_brightness", 80),
                        "brightness_change": brightness_info.get("brightness_change", 0),
                        "energy_savings": brightness_info.get("energy_impact", 0),
                        "implementation_time": datetime.now().isoformat(),
                        "schedule_attached": True,
                        "priority": "high" if zone in config.PRIORITY_ZONES else "medium"
                    }
                    
                    optimization_commands.append(command)
            
            # Send optimization results to Kafka
            optimization_data = {
                "optimization_id": f"energy_opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "total_zones_optimized": len(optimization_commands),
                "total_energy_savings": state.get("total_savings", 0),
                "overall_savings_percent": state.get("overall_savings_percent", 0),
                "optimization_commands": optimization_commands,
                "dimming_schedules": dimming_schedules,
                "implemented_at": datetime.now().isoformat()
            }
            
            # Send to Kafka
            success = power_producer.send_optimization_result({
                "zone_id": "system_wide",
                "optimization_data": optimization_data,
                "energy_savings": state.get("overall_savings_percent", 0)
            })
            
            if success:
                state["status"] = "optimization_complete"
                state["commands_sent"] = len(optimization_commands)
                logger.info(f"Energy optimization implemented - {len(optimization_commands)} commands sent")
            else:
                state["status"] = "optimization_failed"
                state["errors"] = state.get("errors", []) + ["Failed to send optimization commands"]
            
            state["optimization_commands"] = optimization_commands
            state["implementation_time"] = datetime.now().isoformat()
            
            return state
            
        except Exception as e:
            logger.error(f"Error implementing optimization: {e}")
            state["errors"] = state.get("errors", []) + [f"Optimization implementation failed: {str(e)}"]
            state["status"] = "optimization_failed"
            return state
    
    def optimize_energy_usage(self, initial_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute energy optimization workflow"""
        try:
            logger.info("Starting energy optimization workflow")
            
            # Initialize state
            if initial_state is None:
                initial_state = {
                    "workflow_id": f"energy_opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "started_at": datetime.now().isoformat(),
                    "errors": []
                }
            
            # Execute workflow
            result = self.workflow.invoke(initial_state)
            
            logger.info(f"Energy optimization completed - Status: {result.get('status', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Energy optimization workflow failed: {e}")
            return {
                "status": "optimization_failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Create singleton instance
energy_optimization_agent = EnergyOptimizationAgent()
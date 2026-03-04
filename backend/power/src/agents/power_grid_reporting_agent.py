from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import logging
import math
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

from ..config.settings import config
from ..kafka.kafka_producer import power_producer

# Configure logging
logger = logging.getLogger(__name__)

class PowerGridReportingState:
    """State management for Power Grid Reporting Agent"""
    
    def __init__(self):
        self.performance_metrics: Dict[str, Any] = {}
        self.energy_consumption: Dict[str, Any] = {}
        self.outage_history: List[Dict[str, Any]] = []
        self.optimization_results: Dict[str, Any] = {}
        self.cost_analysis: Dict[str, Any] = {}
        self.reliability_metrics: Dict[str, Any] = {}
        self.trend_analysis: Dict[str, Any] = {}
        self.generated_reports: Dict[str, Any] = {}
        self.report_summaries: List[Dict[str, Any]] = []
        self.recommendations: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.status: str = "initialized"

class PowerGridReportingAgent:
    """LangGraph-based Power Grid Reporting Agent"""
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=config.GROQ_API_KEY,
            model=config.GROQ_MODEL,
            temperature=config.GROQ_TEMPERATURE,
            max_tokens=config.GROQ_MAX_TOKENS
        )
        self.state = PowerGridReportingState()
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create LangGraph workflow for power grid reporting"""
        
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("collect_metrics", self._collect_metrics_node)
        workflow.add_node("analyze_consumption", self._analyze_consumption_node)
        workflow.add_node("assess_reliability", self._assess_reliability_node)
        workflow.add_node("evaluate_costs", self._evaluate_costs_node)
        workflow.add_node("identify_trends", self._identify_trends_node)
        workflow.add_node("generate_reports", self._generate_reports_node)
        workflow.add_node("create_recommendations", self._create_recommendations_node)
        
        # Define workflow
        workflow.set_entry_point("collect_metrics")
        workflow.add_edge("collect_metrics", "analyze_consumption")
        workflow.add_edge("analyze_consumption", "assess_reliability")
        workflow.add_edge("assess_reliability", "evaluate_costs")
        workflow.add_edge("evaluate_costs", "identify_trends")
        workflow.add_edge("identify_trends", "generate_reports")
        workflow.add_edge("generate_reports", "create_recommendations")
        workflow.add_edge("create_recommendations", END)
        
        return workflow.compile()
    
    def _collect_metrics_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Collect performance metrics from all zones"""
        try:
            logger.info("Collecting power grid performance metrics")
            
            current_time = datetime.now()
            performance_metrics = {}
            
            # Simulate comprehensive metrics collection
            for zone in config.DEFAULT_ZONES:
                zone_hash = hash(zone) % 100
                
                # Electrical metrics
                voltage_stability = 0.92 + (zone_hash % 8) * 0.01  # 92-99%
                frequency_stability = 0.95 + (zone_hash % 5) * 0.01  # 95-99%
                power_factor = 0.85 + (zone_hash % 15) * 0.01  # 85-100%
                
                # Load metrics
                peak_load = 70 + (zone_hash % 30)  # 70-100 kW
                average_load = peak_load * (0.6 + (zone_hash % 25) * 0.01)  # 60-85% of peak
                load_factor = average_load / peak_load
                
                # Efficiency metrics
                transmission_efficiency = 0.94 + (zone_hash % 6) * 0.01  # 94-99%
                distribution_losses = 2 + (zone_hash % 8) * 0.5  # 2-6%
                overall_efficiency = transmission_efficiency * (1 - distribution_losses / 100)
                
                # Reliability metrics
                uptime_percentage = 99.5 + (zone_hash % 5) * 0.1  # 99.5-100%
                mtbf_hours = 8760 - (zone_hash % 100)  # Mean Time Between Failures
                mttr_hours = 2 + (zone_hash % 6) * 0.5  # Mean Time To Repair: 2-5 hours
                
                performance_metrics[zone] = {
                    "voltage_stability": voltage_stability,
                    "frequency_stability": frequency_stability,
                    "power_factor": power_factor,
                    "peak_load": peak_load,
                    "average_load": average_load,
                    "load_factor": load_factor,
                    "transmission_efficiency": transmission_efficiency,
                    "distribution_losses": distribution_losses,
                    "overall_efficiency": overall_efficiency,
                    "uptime_percentage": uptime_percentage,
                    "mtbf_hours": mtbf_hours,
                    "mttr_hours": mttr_hours,
                    "last_updated": current_time.isoformat()
                }
            
            # Calculate system-wide KPIs
            system_kpis = {
                "total_zones": len(performance_metrics),
                "avg_uptime": sum(m["uptime_percentage"] for m in performance_metrics.values()) / len(performance_metrics),
                "avg_efficiency": sum(m["overall_efficiency"] for m in performance_metrics.values()) / len(performance_metrics),
                "total_peak_load": sum(m["peak_load"] for m in performance_metrics.values()),
                "total_average_load": sum(m["average_load"] for m in performance_metrics.values()),
                "system_load_factor": sum(m["average_load"] for m in performance_metrics.values()) / sum(m["peak_load"] for m in performance_metrics.values()),
                "avg_power_factor": sum(m["power_factor"] for m in performance_metrics.values()) / len(performance_metrics)
            }
            
            # LLM metrics analysis
            prompt = f"""
            Analyze collected power grid performance metrics:
            
            System KPIs: {json.dumps(system_kpis, indent=2)}
            Sample Zone Metrics: {json.dumps({k: v for k, v in list(performance_metrics.items())[:3]}, indent=2)}
            
            Performance Benchmarks:
            - Target Uptime: {config.RELIABILITY_TARGET}%
            - Target Efficiency: {config.EFFICIENCY_BASELINE}%
            - Min Power Factor: {config.POWER_FACTOR_MIN}
            
            Evaluate:
            1. Overall system performance vs targets
            2. Zone-level performance variations
            3. Critical performance indicators
            4. Areas requiring attention
            
            Return performance analysis in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            state["performance_metrics"] = performance_metrics
            state["system_kpis"] = system_kpis
            state["metrics_analysis"] = response.content
            state["collection_time"] = current_time.isoformat()
            
            logger.info(f"Metrics collected - Avg uptime: {system_kpis['avg_uptime']:.2f}%, Avg efficiency: {system_kpis['avg_efficiency']:.2f}")
            return state
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            state["errors"] = state.get("errors", []) + [f"Metrics collection failed: {str(e)}"]
            return state
    
    def _analyze_consumption_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze energy consumption patterns"""
        try:
            logger.info("Analyzing energy consumption patterns")
            
            performance_metrics = state.get("performance_metrics", {})
            current_time = datetime.now()
            
            # Generate consumption analysis for different time periods
            consumption_analysis = {
                "hourly": {},
                "daily": {},
                "weekly": {},
                "monthly": {}
            }
            
            # Hourly consumption (last 24 hours)
            hourly_data = []
            for hour in range(24):
                hour_time = current_time - timedelta(hours=23-hour)
                
                # Simulate hourly consumption pattern
                hour_of_day = hour_time.hour
                base_consumption = 500  # kWh base
                
                # Time-of-day pattern
                if 6 <= hour_of_day <= 9 or 17 <= hour_of_day <= 21:  # Peak hours
                    time_factor = 1.4
                elif 22 <= hour_of_day <= 6:  # Off-peak
                    time_factor = 0.6
                else:  # Standard hours
                    time_factor = 1.0
                
                hourly_consumption = base_consumption * time_factor * (0.9 + (hour % 10) * 0.02)
                
                hourly_data.append({
                    "hour": hour_of_day,
                    "timestamp": hour_time.isoformat(),
                    "consumption_kwh": hourly_consumption,
                    "demand_kw": hourly_consumption * 1.2,
                    "time_period": "peak" if time_factor > 1.2 else "off_peak" if time_factor < 0.8 else "standard"
                })
            
            consumption_analysis["hourly"] = {
                "data": hourly_data,
                "total_consumption": sum(h["consumption_kwh"] for h in hourly_data),
                "peak_hour": max(hourly_data, key=lambda x: x["consumption_kwh"]),
                "min_hour": min(hourly_data, key=lambda x: x["consumption_kwh"]),
                "load_factor": sum(h["consumption_kwh"] for h in hourly_data) / (24 * max(h["consumption_kwh"] for h in hourly_data))
            }
            
            # Daily consumption (last 7 days)
            daily_data = []
            for day in range(7):
                day_time = current_time - timedelta(days=6-day)
                day_name = day_time.strftime("%A")
                
                # Weekend vs weekday pattern
                if day_name in ["Saturday", "Sunday"]:
                    daily_factor = 0.7  # Lower weekend consumption
                else:
                    daily_factor = 1.0
                
                daily_consumption = 12000 * daily_factor * (0.95 + (day % 10) * 0.01)  # kWh per day
                
                daily_data.append({
                    "date": day_time.strftime("%Y-%m-%d"),
                    "day_name": day_name,
                    "consumption_kwh": daily_consumption,
                    "day_type": "weekend" if day_name in ["Saturday", "Sunday"] else "weekday"
                })
            
            consumption_analysis["daily"] = {
                "data": daily_data,
                "total_consumption": sum(d["consumption_kwh"] for d in daily_data),
                "avg_weekday": sum(d["consumption_kwh"] for d in daily_data if d["day_type"] == "weekday") / len([d for d in daily_data if d["day_type"] == "weekday"]),
                "avg_weekend": sum(d["consumption_kwh"] for d in daily_data if d["day_type"] == "weekend") / len([d for d in daily_data if d["day_type"] == "weekend"])
            }
            
            # Zone-wise consumption breakdown
            zone_consumption = {}
            total_system_consumption = consumption_analysis["daily"]["total_consumption"]
            
            for zone in config.DEFAULT_ZONES:
                zone_hash = hash(zone) % 100
                zone_share = 0.8 + (zone_hash % 40) * 0.01  # 80-120% of average share
                zone_consumption_kwh = (total_system_consumption / len(config.DEFAULT_ZONES)) * zone_share
                
                zone_consumption[zone] = {
                    "daily_consumption": zone_consumption_kwh,
                    "consumption_share": (zone_consumption_kwh / total_system_consumption) * 100,
                    "efficiency_rating": performance_metrics.get(zone, {}).get("overall_efficiency", 0.95),
                    "cost_per_kwh": 0.12 + (zone_hash % 5) * 0.01  # $0.12-0.16 per kWh
                }
            
            # LLM consumption analysis
            prompt = f"""
            Analyze energy consumption patterns:
            
            Hourly Analysis:
            - Total 24h Consumption: {consumption_analysis['hourly']['total_consumption']:.0f} kWh
            - Peak Hour: {consumption_analysis['hourly']['peak_hour']['hour']}:00 ({consumption_analysis['hourly']['peak_hour']['consumption_kwh']:.0f} kWh)
            - Load Factor: {consumption_analysis['hourly']['load_factor']:.2f}
            
            Daily Analysis:
            - 7-day Total: {consumption_analysis['daily']['total_consumption']:.0f} kWh
            - Avg Weekday: {consumption_analysis['daily']['avg_weekday']:.0f} kWh
            - Avg Weekend: {consumption_analysis['daily']['avg_weekend']:.0f} kWh
            
            Top 3 Zone Consumption: {json.dumps(dict(sorted(zone_consumption.items(), key=lambda x: x[1]['daily_consumption'], reverse=True)[:3]), indent=2)}
            
            Identify:
            1. Consumption patterns and trends
            2. Peak demand management opportunities
            3. Zone-level efficiency variations
            4. Cost optimization potential
            
            Return consumption analysis in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            state["energy_consumption"] = consumption_analysis
            state["zone_consumption"] = zone_consumption
            state["consumption_analysis"] = response.content
            
            logger.info(f"Consumption analysis completed - Daily total: {consumption_analysis['daily']['total_consumption']:.0f} kWh")
            return state
            
        except Exception as e:
            logger.error(f"Error analyzing consumption: {e}")
            state["errors"] = state.get("errors", []) + [f"Consumption analysis failed: {str(e)}"]
            return state
    
    def _assess_reliability_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Assess system reliability and outage history"""
        try:
            logger.info("Assessing system reliability metrics")
            
            performance_metrics = state.get("performance_metrics", {})
            current_time = datetime.now()
            
            # Generate outage history (last 30 days)
            outage_history = []
            reliability_metrics = {}
            
            # Simulate outage events
            for day in range(30):
                event_date = current_time - timedelta(days=29-day)
                
                # Random outage probability (lower for recent dates to show improvement)
                outage_probability = 0.1 - (day * 0.002)  # Decreasing probability
                
                if (hash(str(day)) % 100) < (outage_probability * 100):
                    affected_zones = [f"zone_{(hash(str(day)) % len(config.DEFAULT_ZONES)) + 1}"]
                    if (hash(str(day)) % 10) < 2:  # 20% chance of multi-zone outage
                        affected_zones.append(f"zone_{((hash(str(day)) + 1) % len(config.DEFAULT_ZONES)) + 1}")
                    
                    outage_duration = 30 + (hash(str(day)) % 180)  # 30-210 minutes
                    
                    outage_history.append({
                        "date": event_date.strftime("%Y-%m-%d"),
                        "start_time": event_date.replace(hour=hash(str(day)) % 24, minute=hash(str(day*2)) % 60).isoformat(),
                        "duration_minutes": outage_duration,
                        "affected_zones": affected_zones,
                        "cause": ["equipment_failure", "weather", "maintenance", "grid_overload"][hash(str(day)) % 4],
                        "customers_affected": len(affected_zones) * (100 + (hash(str(day)) % 200)),
                        "restored_time": (event_date + timedelta(minutes=outage_duration)).isoformat()
                    })
            
            # Calculate reliability metrics
            total_outages = len(outage_history)
            total_outage_minutes = sum(o["duration_minutes"] for o in outage_history)
            total_customers_affected = sum(o["customers_affected"] for o in outage_history)
            
            # System Average Interruption Duration Index (SAIDI)
            total_customers = len(config.DEFAULT_ZONES) * 300  # Assume 300 customers per zone
            saidi = total_outage_minutes / total_customers if total_customers > 0 else 0
            
            # System Average Interruption Frequency Index (SAIFI)
            saifi = total_customers_affected / total_customers if total_customers > 0 else 0
            
            # Customer Average Interruption Duration Index (CAIDI)
            caidi = total_outage_minutes / total_outages if total_outages > 0 else 0
            
            # Overall system availability
            total_minutes_in_period = 30 * 24 * 60  # 30 days
            system_availability = ((total_minutes_in_period - total_outage_minutes) / total_minutes_in_period) * 100
            
            reliability_metrics = {
                "reporting_period_days": 30,
                "total_outages": total_outages,
                "total_outage_duration_minutes": total_outage_minutes,
                "total_customers_affected": total_customers_affected,
                "saidi_minutes": saidi,
                "saifi_interruptions": saifi,
                "caidi_minutes": caidi,
                "system_availability_percent": system_availability,
                "mtbf_system_hours": (30 * 24) / total_outages if total_outages > 0 else float('inf'),
                "reliability_target_met": system_availability >= config.RELIABILITY_TARGET
            }
            
            # Outage cause analysis
            cause_breakdown = {}
            for outage in outage_history:
                cause = outage["cause"]
                if cause not in cause_breakdown:
                    cause_breakdown[cause] = {"count": 0, "total_duration": 0, "customers_affected": 0}
                cause_breakdown[cause]["count"] += 1
                cause_breakdown[cause]["total_duration"] += outage["duration_minutes"]
                cause_breakdown[cause]["customers_affected"] += outage["customers_affected"]
            
            # LLM reliability analysis
            prompt = f"""
            Assess power grid reliability performance:
            
            Reliability Metrics (30-day period):
            - Total Outages: {total_outages}
            - System Availability: {system_availability:.2f}%
            - SAIDI: {saidi:.2f} minutes per customer
            - SAIFI: {saifi:.2f} interruptions per customer
            - Target Reliability: {config.RELIABILITY_TARGET}%
            - Target Met: {reliability_metrics['reliability_target_met']}
            
            Outage Causes: {json.dumps(cause_breakdown, indent=2)}
            Recent Outages: {json.dumps(outage_history[-5:], indent=2)}
            
            Evaluate:
            1. Reliability performance vs industry standards
            2. Outage pattern analysis and root causes
            3. Improvement trends and areas of concern
            4. Preventive maintenance recommendations
            
            Return reliability assessment in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            state["outage_history"] = outage_history
            state["reliability_metrics"] = reliability_metrics
            state["cause_breakdown"] = cause_breakdown
            state["reliability_analysis"] = response.content
            
            logger.info(f"Reliability assessment completed - Availability: {system_availability:.2f}%, {total_outages} outages in 30 days")
            return state
            
        except Exception as e:
            logger.error(f"Error assessing reliability: {e}")
            state["errors"] = state.get("errors", []) + [f"Reliability assessment failed: {str(e)}"]
            return state
    
    def _evaluate_costs_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate energy costs and financial performance"""
        try:
            logger.info("Evaluating energy costs and financial metrics")
            
            energy_consumption = state.get("energy_consumption", {})
            zone_consumption = state.get("zone_consumption", {})
            outage_history = state.get("outage_history", [])
            
            # Calculate comprehensive cost analysis
            cost_analysis = {}
            
            # Energy costs
            daily_consumption = energy_consumption.get("daily", {}).get("total_consumption", 0)
            monthly_consumption = daily_consumption * 30  # Approximate monthly
            
            # Time-of-use rates
            peak_rate = 0.18  # $/kWh
            standard_rate = 0.12  # $/kWh  
            off_peak_rate = 0.08  # $/kWh
            
            # Estimate consumption by rate period (simplified)
            peak_consumption = monthly_consumption * 0.25  # 25% peak
            standard_consumption = monthly_consumption * 0.50  # 50% standard
            off_peak_consumption = monthly_consumption * 0.25  # 25% off-peak
            
            energy_costs = {
                "peak_consumption_kwh": peak_consumption,
                "standard_consumption_kwh": standard_consumption,
                "off_peak_consumption_kwh": off_peak_consumption,
                "peak_cost": peak_consumption * peak_rate,
                "standard_cost": standard_consumption * standard_rate,
                "off_peak_cost": off_peak_consumption * off_peak_rate,
                "total_energy_cost": (peak_consumption * peak_rate + 
                                    standard_consumption * standard_rate + 
                                    off_peak_consumption * off_peak_rate)
            }
            
            # Demand charges
            system_kpis = state.get("system_kpis", {})
            peak_demand_kw = system_kpis.get("total_peak_load", 1000)
            demand_charge_rate = 15.0  # $/kW
            demand_charges = peak_demand_kw * demand_charge_rate
            
            # Infrastructure costs (monthly estimates)
            infrastructure_costs = {
                "maintenance": 5000,  # Monthly maintenance
                "operations": 8000,   # Operations staff
                "upgrades": 3000,     # Equipment upgrades
                "insurance": 2000,    # Insurance premiums
                "regulatory": 1500    # Regulatory compliance
            }
            
            # Outage costs (lost revenue and restoration)
            outage_costs = 0
            for outage in outage_history:
                # Estimate cost per outage
                duration_hours = outage["duration_minutes"] / 60
                customers_affected = outage["customers_affected"]
                
                # Lost revenue (customers not paying during outage)
                lost_revenue = customers_affected * 0.5 * duration_hours  # $0.5/hour per customer
                
                # Restoration costs
                restoration_cost = 1000 + (duration_hours * 500)  # Base + hourly rate
                
                outage_costs += lost_revenue + restoration_cost
            
            # Total cost summary
            total_monthly_costs = (energy_costs["total_energy_cost"] + 
                                 demand_charges + 
                                 sum(infrastructure_costs.values()) + 
                                 outage_costs)
            
            # Cost per kWh and efficiency metrics
            cost_per_kwh = total_monthly_costs / monthly_consumption if monthly_consumption > 0 else 0
            
            # Zone-level cost analysis
            zone_costs = {}
            for zone, consumption_data in zone_consumption.items():
                zone_monthly_kwh = consumption_data["daily_consumption"] * 30
                zone_share = consumption_data["consumption_share"] / 100
                
                zone_costs[zone] = {
                    "monthly_consumption_kwh": zone_monthly_kwh,
                    "energy_cost": zone_share * energy_costs["total_energy_cost"],
                    "demand_cost": zone_share * demand_charges,
                    "infrastructure_cost": zone_share * sum(infrastructure_costs.values()),
                    "total_cost": zone_share * total_monthly_costs,
                    "cost_per_kwh": zone_share * cost_per_kwh,
                    "efficiency_rating": consumption_data["efficiency_rating"]
                }
            
            cost_analysis = {
                "energy_costs": energy_costs,
                "demand_charges": demand_charges,
                "infrastructure_costs": infrastructure_costs,
                "outage_costs": outage_costs,
                "total_monthly_costs": total_monthly_costs,
                "cost_per_kwh": cost_per_kwh,
                "zone_costs": zone_costs,
                "cost_breakdown_percent": {
                    "energy": (energy_costs["total_energy_cost"] / total_monthly_costs) * 100,
                    "demand": (demand_charges / total_monthly_costs) * 100,
                    "infrastructure": (sum(infrastructure_costs.values()) / total_monthly_costs) * 100,
                    "outages": (outage_costs / total_monthly_costs) * 100
                }
            }
            
            # LLM cost analysis
            prompt = f"""
            Analyze energy costs and financial performance:
            
            Monthly Cost Summary:
            - Total Energy Cost: ${energy_costs['total_energy_cost']:,.2f}
            - Demand Charges: ${demand_charges:,.2f}
            - Infrastructure Costs: ${sum(infrastructure_costs.values()):,.2f}
            - Outage Costs: ${outage_costs:,.2f}
            - Total Monthly Cost: ${total_monthly_costs:,.2f}
            - Cost per kWh: ${cost_per_kwh:.3f}
            
            Cost Breakdown: {json.dumps(cost_analysis['cost_breakdown_percent'], indent=2)}
            
            Budget Settings:
            - Monthly Budget: ${config.MONTHLY_ENERGY_BUDGET * cost_per_kwh:,.2f}
            - Budget Alert Threshold: {config.BUDGET_ALERT_THRESHOLD}%
            
            Evaluate:
            1. Cost efficiency vs industry benchmarks
            2. Budget variance and trend analysis
            3. Cost optimization opportunities
            4. Financial risk assessment
            
            Return cost analysis in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            state["cost_analysis"] = cost_analysis
            state["cost_evaluation"] = response.content
            
            logger.info(f"Cost evaluation completed - Monthly total: ${total_monthly_costs:,.2f}, Cost/kWh: ${cost_per_kwh:.3f}")
            return state
            
        except Exception as e:
            logger.error(f"Error evaluating costs: {e}")
            state["errors"] = state.get("errors", []) + [f"Cost evaluation failed: {str(e)}"]
            return state
    
    def _identify_trends_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Identify trends and patterns in grid performance"""
        try:
            logger.info("Identifying performance trends and patterns")
            
            performance_metrics = state.get("performance_metrics", {})
            energy_consumption = state.get("energy_consumption", {})
            reliability_metrics = state.get("reliability_metrics", {})
            cost_analysis = state.get("cost_analysis", {})
            
            # Generate trend analysis
            trend_analysis = {}
            
            # Performance trends (simulated historical comparison)
            current_efficiency = state.get("system_kpis", {}).get("avg_efficiency", 0.95)
            historical_efficiency = current_efficiency - 0.02  # Assume 2% improvement
            
            current_uptime = state.get("system_kpis", {}).get("avg_uptime", 99.5)
            historical_uptime = current_uptime - 0.3  # Assume 0.3% improvement
            
            performance_trends = {
                "efficiency": {
                    "current": current_efficiency,
                    "previous_period": historical_efficiency,
                    "change_percent": ((current_efficiency - historical_efficiency) / historical_efficiency) * 100,
                    "trend": "improving" if current_efficiency > historical_efficiency else "declining"
                },
                "uptime": {
                    "current": current_uptime,
                    "previous_period": historical_uptime,
                    "change_percent": ((current_uptime - historical_uptime) / historical_uptime) * 100,
                    "trend": "improving" if current_uptime > historical_uptime else "declining"
                }
            }
            
            # Consumption trends
            daily_data = energy_consumption.get("daily", {}).get("data", [])
            if len(daily_data) >= 7:
                recent_avg = sum(d["consumption_kwh"] for d in daily_data[-3:]) / 3  # Last 3 days
                earlier_avg = sum(d["consumption_kwh"] for d in daily_data[:3]) / 3   # First 3 days
                
                consumption_trends = {
                    "recent_average": recent_avg,
                    "earlier_average": earlier_avg,
                    "change_percent": ((recent_avg - earlier_avg) / earlier_avg) * 100 if earlier_avg > 0 else 0,
                    "trend": "increasing" if recent_avg > earlier_avg else "decreasing"
                }
            else:
                consumption_trends = {"trend": "insufficient_data"}
            
            # Cost trends
            current_cost_per_kwh = cost_analysis.get("cost_per_kwh", 0.12)
            historical_cost_per_kwh = current_cost_per_kwh * 0.95  # Assume 5% increase
            
            cost_trends = {
                "cost_per_kwh": {
                    "current": current_cost_per_kwh,
                    "previous_period": historical_cost_per_kwh,
                    "change_percent": ((current_cost_per_kwh - historical_cost_per_kwh) / historical_cost_per_kwh) * 100,
                    "trend": "increasing" if current_cost_per_kwh > historical_cost_per_kwh else "decreasing"
                }
            }
            
            # Seasonal patterns (simulated)
            current_month = datetime.now().month
            seasonal_patterns = {
                "peak_season": "summer" if 6 <= current_month <= 8 else "winter" if current_month in [12, 1, 2] else "shoulder",
                "seasonal_load_factor": 1.2 if 6 <= current_month <= 8 else 1.1 if current_month in [12, 1, 2] else 1.0,
                "weather_impact": "high_cooling" if 6 <= current_month <= 8 else "high_heating" if current_month in [12, 1, 2] else "moderate"
            }
            
            # Predictive insights
            predicted_next_month = {
                "consumption_forecast": consumption_trends.get("recent_average", 12000) * 1.05,  # 5% increase
                "cost_forecast": cost_analysis.get("total_monthly_costs", 50000) * 1.03,  # 3% increase
                "reliability_forecast": "stable" if reliability_metrics.get("system_availability_percent", 99) > 99 else "at_risk"
            }
            
            trend_analysis = {
                "performance_trends": performance_trends,
                "consumption_trends": consumption_trends,
                "cost_trends": cost_trends,
                "seasonal_patterns": seasonal_patterns,
                "predicted_next_month": predicted_next_month,
                "analysis_period": "30_days",
                "confidence_level": 0.85
            }
            
            # LLM trend analysis
            prompt = f"""
            Analyze trends and patterns in power grid performance:
            
            Performance Trends: {json.dumps(performance_trends, indent=2)}
            Consumption Trends: {json.dumps(consumption_trends, indent=2)}
            Cost Trends: {json.dumps(cost_trends, indent=2)}
            Seasonal Context: {json.dumps(seasonal_patterns, indent=2)}
            
            Predictions: {json.dumps(predicted_next_month, indent=2)}
            
            Identify:
            1. Key performance trend drivers
            2. Seasonal impact patterns
            3. Cost trend sustainability
            4. Predictive maintenance needs
            5. Strategic improvement opportunities
            
            Return trend analysis insights in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            state["trend_analysis"] = trend_analysis
            state["trend_insights"] = response.content
            
            logger.info("Trend analysis completed - Performance improving, costs increasing")
            return state
            
        except Exception as e:
            logger.error(f"Error identifying trends: {e}")
            state["errors"] = state.get("errors", []) + [f"Trend analysis failed: {str(e)}"]
            return state
    
    def _generate_reports_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive reports"""
        try:
            logger.info("Generating comprehensive power grid reports")
            
            current_time = datetime.now()
            report_id = f"power_grid_report_{current_time.strftime('%Y%m%d_%H%M%S')}"
            
            # Executive Summary Report
            executive_summary = {
                "report_id": report_id,
                "report_type": "executive_summary",
                "generated_at": current_time.isoformat(),
                "reporting_period": "30_days",
                "key_metrics": {
                    "system_availability": state.get("reliability_metrics", {}).get("system_availability_percent", 99.5),
                    "total_consumption": state.get("energy_consumption", {}).get("daily", {}).get("total_consumption", 0) * 30,
                    "total_cost": state.get("cost_analysis", {}).get("total_monthly_costs", 50000),
                    "efficiency": state.get("system_kpis", {}).get("avg_efficiency", 0.95),
                    "outage_count": len(state.get("outage_history", []))
                },
                "performance_status": "good" if state.get("reliability_metrics", {}).get("reliability_target_met", False) else "needs_attention"
            }
            
            # Detailed Performance Report
            performance_report = {
                "report_id": f"{report_id}_performance",
                "report_type": "detailed_performance",
                "generated_at": current_time.isoformat(),
                "system_kpis": state.get("system_kpis", {}),
                "performance_metrics": state.get("performance_metrics", {}),
                "reliability_metrics": state.get("reliability_metrics", {}),
                "zone_performance": {
                    zone: metrics for zone, metrics in state.get("performance_metrics", {}).items()
                }
            }
            
            # Financial Report
            financial_report = {
                "report_id": f"{report_id}_financial",
                "report_type": "financial_analysis",
                "generated_at": current_time.isoformat(),
                "cost_analysis": state.get("cost_analysis", {}),
                "budget_performance": {
                    "monthly_budget": config.MONTHLY_ENERGY_BUDGET * state.get("cost_analysis", {}).get("cost_per_kwh", 0.12),
                    "actual_cost": state.get("cost_analysis", {}).get("total_monthly_costs", 50000),
                    "variance_percent": 0,  # Calculate based on budget vs actual
                    "budget_status": "within_budget"
                }
            }
            
            # Operational Report
            operational_report = {
                "report_id": f"{report_id}_operational",
                "report_type": "operational_analysis",
                "generated_at": current_time.isoformat(),
                "energy_consumption": state.get("energy_consumption", {}),
                "outage_analysis": {
                    "outage_history": state.get("outage_history", []),
                    "cause_breakdown": state.get("cause_breakdown", {}),
                    "reliability_metrics": state.get("reliability_metrics", {})
                },
                "optimization_opportunities": []
            }
            
            # Trend Analysis Report
            trend_report = {
                "report_id": f"{report_id}_trends",
                "report_type": "trend_analysis",
                "generated_at": current_time.isoformat(),
                "trend_analysis": state.get("trend_analysis", {}),
                "predictions": state.get("trend_analysis", {}).get("predicted_next_month", {}),
                "seasonal_insights": state.get("trend_analysis", {}).get("seasonal_patterns", {})
            }
            
            # Compile all reports
            generated_reports = {
                "executive_summary": executive_summary,
                "performance_report": performance_report,
                "financial_report": financial_report,
                "operational_report": operational_report,
                "trend_report": trend_report
            }
            
            # Create report summaries for easy consumption
            report_summaries = []
            for report_type, report_data in generated_reports.items():
                summary = {
                    "report_type": report_type,
                    "report_id": report_data["report_id"],
                    "generated_at": report_data["generated_at"],
                    "key_findings": self._extract_key_findings(report_type, report_data),
                    "urgency": self._assess_report_urgency(report_type, report_data)
                }
                report_summaries.append(summary)
            
            state["generated_reports"] = generated_reports
            state["report_summaries"] = report_summaries
            state["main_report_id"] = report_id
            
            logger.info(f"Reports generated - {len(generated_reports)} reports created with ID: {report_id}")
            return state
            
        except Exception as e:
            logger.error(f"Error generating reports: {e}")
            state["errors"] = state.get("errors", []) + [f"Report generation failed: {str(e)}"]
            return state
    
    def _create_recommendations_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create actionable recommendations"""
        try:
            logger.info("Creating actionable recommendations")
            
            recommendations = []
            current_time = datetime.now()
            
            # Performance-based recommendations
            system_kpis = state.get("system_kpis", {})
            if system_kpis.get("avg_efficiency", 0.95) < config.EFFICIENCY_BASELINE:
                recommendations.append({
                    "id": f"rec_eff_{current_time.strftime('%H%M%S')}",
                    "category": "efficiency",
                    "priority": "high",
                    "title": "Improve System Efficiency",
                    "description": f"System efficiency ({system_kpis.get('avg_efficiency', 0.95):.1%}) is below baseline ({config.EFFICIENCY_BASELINE}%)",
                    "recommended_actions": [
                        "Conduct equipment maintenance on low-efficiency zones",
                        "Upgrade aging transformers and distribution equipment",
                        "Implement power factor correction measures"
                    ],
                    "expected_impact": "2-5% efficiency improvement",
                    "estimated_cost": "$15,000 - $50,000",
                    "timeline": "3-6 months"
                })
            
            # Reliability-based recommendations
            reliability_metrics = state.get("reliability_metrics", {})
            if not reliability_metrics.get("reliability_target_met", True):
                recommendations.append({
                    "id": f"rec_rel_{current_time.strftime('%H%M%S')}",
                    "category": "reliability",
                    "priority": "critical",
                    "title": "Improve System Reliability",
                    "description": f"System availability ({reliability_metrics.get('system_availability_percent', 99.5):.2f}%) below target ({config.RELIABILITY_TARGET}%)",
                    "recommended_actions": [
                        "Implement predictive maintenance program",
                        "Upgrade critical infrastructure components",
                        "Enhance outage detection and response procedures"
                    ],
                    "expected_impact": f"Increase availability to {config.RELIABILITY_TARGET}%+",
                    "estimated_cost": "$25,000 - $100,000",
                    "timeline": "6-12 months"
                })
            
            # Cost optimization recommendations
            cost_analysis = state.get("cost_analysis", {})
            if cost_analysis.get("cost_per_kwh", 0.12) > 0.15:  # High cost threshold
                recommendations.append({
                    "id": f"rec_cost_{current_time.strftime('%H%M%S')}",
                    "category": "cost_optimization",
                    "priority": "medium",
                    "title": "Reduce Energy Costs",
                    "description": f"Energy cost per kWh (${cost_analysis.get('cost_per_kwh', 0.12):.3f}) is above optimal range",
                    "recommended_actions": [
                        "Implement demand response programs",
                        "Optimize peak demand management",
                        "Negotiate better utility rates",
                        "Consider energy storage solutions"
                    ],
                    "expected_impact": "10-20% cost reduction",
                    "estimated_cost": "$10,000 - $75,000",
                    "timeline": "2-8 months"
                })
            
            # Outage reduction recommendations
            outage_history = state.get("outage_history", [])
            if len(outage_history) > 5:  # Too many outages
                cause_breakdown = state.get("cause_breakdown", {})
                top_cause = max(cause_breakdown.keys(), key=lambda x: cause_breakdown[x]["count"]) if cause_breakdown else "equipment_failure"
                
                recommendations.append({
                    "id": f"rec_outage_{current_time.strftime('%H%M%S')}",
                    "category": "outage_reduction",
                    "priority": "high",
                    "title": f"Address {top_cause.replace('_', ' ').title()} Issues",
                    "description": f"{len(outage_history)} outages in 30 days, primarily due to {top_cause.replace('_', ' ')}",
                    "recommended_actions": [
                        f"Focus maintenance on {top_cause.replace('_', ' ')} prevention",
                        "Implement condition-based monitoring",
                        "Upgrade vulnerable equipment",
                        "Enhance emergency response procedures"
                    ],
                    "expected_impact": "50% reduction in outages",
                    "estimated_cost": "$20,000 - $80,000",
                    "timeline": "4-10 months"
                })
            
            # Energy optimization recommendations
            trend_analysis = state.get("trend_analysis", {})
            consumption_trend = trend_analysis.get("consumption_trends", {}).get("trend", "stable")
            if consumption_trend == "increasing":
                recommendations.append({
                    "id": f"rec_opt_{current_time.strftime('%H%M%S')}",
                    "category": "energy_optimization",
                    "priority": "medium",
                    "title": "Implement Energy Conservation Measures",
                    "description": "Energy consumption is trending upward, optimization needed",
                    "recommended_actions": [
                        "Deploy advanced energy optimization algorithms",
                        "Implement smart dimming schedules",
                        "Upgrade to more efficient lighting technologies",
                        "Enhance occupancy-based controls"
                    ],
                    "expected_impact": f"{config.ENERGY_SAVINGS_TARGET}% energy savings",
                    "estimated_cost": "$5,000 - $30,000",
                    "timeline": "1-4 months"
                })
            
            # LLM-enhanced recommendations
            prompt = f"""
            Review and enhance power grid improvement recommendations:
            
            Current Recommendations: {json.dumps(recommendations, indent=2)}
            
            System Context:
            - Efficiency: {system_kpis.get('avg_efficiency', 0.95):.1%}
            - Reliability: {reliability_metrics.get('system_availability_percent', 99.5):.2f}%
            - Cost/kWh: ${cost_analysis.get('cost_per_kwh', 0.12):.3f}
            - Outages (30d): {len(outage_history)}
            
            Enhance recommendations with:
            1. Risk assessment for each recommendation
            2. Implementation complexity scoring
            3. ROI estimates and payback periods
            4. Alternative solution options
            5. Interdependency analysis
            
            Return enhanced recommendations in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            # Send reports to Kafka
            for report_type, report_data in state.get("generated_reports", {}).items():
                power_producer.send_power_report({
                    "report_id": report_data["report_id"],
                    "report_type": report_type,
                    "report_data": report_data
                })
            
            state["recommendations"] = recommendations
            state["recommendation_enhancement"] = response.content
            state["status"] = "reporting_complete"
            state["completed_at"] = current_time.isoformat()
            
            logger.info(f"Recommendations created - {len(recommendations)} actionable items identified")
            return state
            
        except Exception as e:
            logger.error(f"Error creating recommendations: {e}")
            state["errors"] = state.get("errors", []) + [f"Recommendation creation failed: {str(e)}"]
            state["status"] = "reporting_failed"
            return state
    
    def _extract_key_findings(self, report_type: str, report_data: Dict[str, Any]) -> List[str]:
        """Extract key findings from report data"""
        findings = []
        
        if report_type == "executive_summary":
            metrics = report_data.get("key_metrics", {})
            findings.append(f"System availability: {metrics.get('system_availability', 99.5):.1f}%")
            findings.append(f"Monthly consumption: {metrics.get('total_consumption', 0):,.0f} kWh")
            findings.append(f"Total outages: {metrics.get('outage_count', 0)}")
        
        elif report_type == "financial_report":
            cost_data = report_data.get("cost_analysis", {})
            findings.append(f"Monthly cost: ${cost_data.get('total_monthly_costs', 0):,.2f}")
            findings.append(f"Cost per kWh: ${cost_data.get('cost_per_kwh', 0):.3f}")
        
        return findings[:3]  # Limit to top 3 findings
    
    def _assess_report_urgency(self, report_type: str, report_data: Dict[str, Any]) -> str:
        """Assess urgency level of report"""
        if report_type == "executive_summary":
            status = report_data.get("performance_status", "good")
            return "high" if status == "needs_attention" else "medium"
        
        elif report_type == "operational_analysis":
            outages = len(report_data.get("outage_analysis", {}).get("outage_history", []))
            return "high" if outages > 5 else "medium" if outages > 2 else "low"
        
        return "medium"  # Default
    
    def generate_power_grid_reports(self, report_type: str = "comprehensive") -> Dict[str, Any]:
        """Execute power grid reporting workflow"""
        try:
            logger.info(f"Starting power grid reporting workflow - Type: {report_type}")
            
            # Initialize state
            initial_state = {
                "workflow_id": f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "started_at": datetime.now().isoformat(),
                "report_type": report_type,
                "errors": []
            }
            
            # Execute workflow
            result = self.workflow.invoke(initial_state)
            
            logger.info(f"Power grid reporting completed - Status: {result.get('status', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Power grid reporting workflow failed: {e}")
            return {
                "status": "reporting_failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Create singleton instance
power_grid_reporting_agent = PowerGridReportingAgent()
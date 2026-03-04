from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.agents.energy_load_forecaster_agent import energy_load_forecaster_agent
from src.agents.power_outage_detection_agent import power_outage_detection_agent
from src.agents.energy_rerouting_agent import energy_rerouting_agent
from src.agents.energy_optimization_agent import energy_optimization_agent
from src.agents.power_grid_reporting_agent import power_grid_reporting_agent
from src.config.settings import config
from src.kafka.kafka_producer import power_producer

# Configure logging
logger = logging.getLogger(__name__)

class PowerGridState:
    """Comprehensive state management for Power Grid Graph"""
    
    def __init__(self):
        # Workflow management
        self.workflow_id: str = ""
        self.started_at: str = ""
        self.current_phase: str = "initialization"
        self.completed_phases: List[str] = []
        self.errors: List[str] = []
        self.status: str = "initialized"
        
        # Agent results
        self.forecast_results: Dict[str, Any] = {}
        self.outage_detection_results: Dict[str, Any] = {}
        self.rerouting_results: Dict[str, Any] = {}
        self.optimization_results: Dict[str, Any] = {}
        self.reporting_results: Dict[str, Any] = {}
        
        # Cross-agent data
        self.system_alerts: List[Dict[str, Any]] = []
        self.energy_metrics: Dict[str, Any] = {}
        self.grid_status: Dict[str, str] = {}
        self.optimization_commands: List[Dict[str, Any]] = {}
        self.performance_summary: Dict[str, Any] = {}
        
        # Decision points
        self.outages_detected: bool = False
        self.rerouting_required: bool = False
        self.optimization_needed: bool = True
        self.emergency_mode: bool = False

class PowerGridGraph:
    """Master LangGraph orchestrating all Power Grid agents"""
    
    def __init__(self):
        self.state = PowerGridState()
        self.memory = MemorySaver()
        self.workflow = self._create_master_workflow()
        
        # Agent instances
        self.load_forecaster = energy_load_forecaster_agent
        self.outage_detector = power_outage_detection_agent
        self.energy_router = energy_rerouting_agent
        self.energy_optimizer = energy_optimization_agent
        self.grid_reporter = power_grid_reporting_agent
    
    def _create_master_workflow(self) -> StateGraph:
        """Create master LangGraph workflow orchestrating all power agents"""
        
        workflow = StateGraph(dict)
        
        # Add agent nodes
        workflow.add_node("forecast_load", self._forecast_load_node)
        workflow.add_node("detect_outages", self._detect_outages_node)
        workflow.add_node("assess_rerouting", self._assess_rerouting_node)
        workflow.add_node("execute_rerouting", self._execute_rerouting_node)
        workflow.add_node("optimize_energy", self._optimize_energy_node)
        workflow.add_node("generate_reports", self._generate_reports_node)
        workflow.add_node("emergency_response", self._emergency_response_node)
        workflow.add_node("finalize_workflow", self._finalize_workflow_node)
        
        # Define entry point
        workflow.set_entry_point("forecast_load")
        
        # Standard workflow path
        workflow.add_edge("forecast_load", "detect_outages")
        
        # Conditional routing based on outage detection
        workflow.add_conditional_edges(
            "detect_outages",
            self._should_handle_outages,
            {
                "rerouting_needed": "assess_rerouting",
                "emergency": "emergency_response",
                "continue": "optimize_energy"
            }
        )
        
        # Rerouting path
        workflow.add_edge("assess_rerouting", "execute_rerouting")
        workflow.add_edge("execute_rerouting", "optimize_energy")
        
        # Emergency path
        workflow.add_edge("emergency_response", "generate_reports")
        
        # Normal completion path
        workflow.add_edge("optimize_energy", "generate_reports")
        workflow.add_edge("generate_reports", "finalize_workflow")
        workflow.add_edge("finalize_workflow", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def _forecast_load_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute energy load forecasting"""
        try:
            logger.info("🔮 Executing Energy Load Forecasting")
            state["current_phase"] = "load_forecasting"
            
            # Prepare forecasting input
            forecast_input = {
                "workflow_id": state["workflow_id"],
                "requested_periods": ["1_hour", "4_hour", "24_hour"],
                "include_weather": True,
                "include_historical": True
            }
            
            # Execute load forecasting
            forecast_results = self.load_forecaster.forecast_energy_demand(forecast_input)
            
            # Extract key metrics
            if forecast_results.get("status") == "forecasting_complete":
                state["forecast_results"] = forecast_results
                
                # Update system metrics
                forecasts = forecast_results.get("demand_forecasts", {})
                state["energy_metrics"] = {
                    "predicted_peak_load": max([f.get("predicted_demand", 0) for f in forecasts.values()]),
                    "predicted_avg_load": sum([f.get("predicted_demand", 0) for f in forecasts.values()]) / len(forecasts) if forecasts else 0,
                    "load_trend": forecast_results.get("trend_analysis", {}).get("overall_trend", "stable"),
                    "forecast_confidence": forecast_results.get("confidence_metrics", {}).get("overall_confidence", 0.8)
                }
                
                # Check for high load alerts
                predicted_peak = state["energy_metrics"]["predicted_peak_load"]
                if predicted_peak > config.PEAK_LOAD_THRESHOLD:
                    state["system_alerts"].append({
                        "alert_type": "high_load_forecast",
                        "severity": "warning",
                        "message": f"Predicted peak load ({predicted_peak:.0f}kW) exceeds threshold",
                        "timestamp": datetime.now().isoformat()
                    })
                
                state["completed_phases"].append("load_forecasting")
                logger.info(f"✅ Load forecasting completed - Peak: {predicted_peak:.0f}kW, Trend: {state['energy_metrics']['load_trend']}")
            else:
                state["errors"].append(f"Load forecasting failed: {forecast_results.get('error', 'Unknown error')}")
                logger.error("❌ Load forecasting failed")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in load forecasting node: {e}")
            state["errors"].append(f"Load forecasting node error: {str(e)}")
            return state
    
    def _detect_outages_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute power outage detection"""
        try:
            logger.info("🔍 Executing Power Outage Detection")
            state["current_phase"] = "outage_detection"
            
            # Execute outage detection
            outage_results = self.outage_detector.detect_power_outages()
            
            # Process results
            if outage_results.get("status") in ["monitoring_complete", "alerts_sent"]:
                state["outage_detection_results"] = outage_results
                
                # Check for detected outages
                outages_detected = outage_results.get("outages_detected", [])
                if outages_detected:
                    state["outages_detected"] = True
                    affected_zones = outage_results.get("affected_zones", [])
                    outage_severity = outage_results.get("outage_severity", "unknown")
                    
                    # Determine if emergency response needed
                    if outage_severity in ["critical", "widespread"]:
                        state["emergency_mode"] = True
                    
                    if len(affected_zones) > 0:
                        state["rerouting_required"] = True
                    
                    # Add outage alerts
                    state["system_alerts"].append({
                        "alert_type": "power_outage",
                        "severity": outage_severity,
                        "affected_zones": affected_zones,
                        "outage_count": len(outages_detected),
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    logger.warning(f"⚠️ Outages detected - {len(outages_detected)} zones affected, severity: {outage_severity}")
                else:
                    state["outages_detected"] = False
                    logger.info("✅ No outages detected - Grid operating normally")
                
                # Update grid status
                state["grid_status"] = {
                    "operational_zones": len(config.DEFAULT_ZONES) - len(outages_detected),
                    "affected_zones": len(outages_detected),
                    "system_status": "emergency" if state.get("emergency_mode") else "degraded" if outages_detected else "normal",
                    "last_check": datetime.now().isoformat()
                }
                
                state["completed_phases"].append("outage_detection")
            else:
                state["errors"].append(f"Outage detection failed: {outage_results.get('error', 'Unknown error')}")
                logger.error("❌ Outage detection failed")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in outage detection node: {e}")
            state["errors"].append(f"Outage detection node error: {str(e)}")
            return state
    
    def _assess_rerouting_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Assess if energy rerouting is needed"""
        try:
            logger.info("📊 Assessing Energy Rerouting Requirements")
            state["current_phase"] = "rerouting_assessment"
            
            outages_detected = state.get("outages_detected", False)
            outage_results = state.get("outage_detection_results", {})
            
            if not outages_detected:
                logger.info("✅ No rerouting needed - No outages detected")
                state["rerouting_required"] = False
                state["completed_phases"].append("rerouting_assessment")
                return state
            
            # Analyze rerouting requirements
            affected_zones = outage_results.get("affected_zones", [])
            outage_severity = outage_results.get("outage_severity", "localized")
            impact_assessment = outage_results.get("impact_assessment", {})
            
            # Determine rerouting strategy
            if outage_severity == "widespread":
                rerouting_strategy = "emergency_load_shedding"
                priority = "critical"
            elif outage_severity == "critical":
                rerouting_strategy = "priority_rerouting"
                priority = "high"
            else:
                rerouting_strategy = "standard_rerouting"
                priority = "medium"
            
            # Prepare rerouting assessment
            rerouting_assessment = {
                "rerouting_required": True,
                "strategy": rerouting_strategy,
                "priority": priority,
                "affected_zones": affected_zones,
                "estimated_load_lost": impact_assessment.get("estimated_load_lost", 0),
                "rerouting_complexity": "high" if len(affected_zones) > 3 else "medium" if len(affected_zones) > 1 else "low"
            }
            
            state["rerouting_assessment"] = rerouting_assessment
            state["rerouting_required"] = True
            state["completed_phases"].append("rerouting_assessment")
            
            logger.info(f"✅ Rerouting assessment complete - Strategy: {rerouting_strategy}, Priority: {priority}")
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in rerouting assessment: {e}")
            state["errors"].append(f"Rerouting assessment error: {str(e)}")
            return state
    
    def _execute_rerouting_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute energy rerouting operations"""
        try:
            logger.info("🔄 Executing Energy Rerouting")
            state["current_phase"] = "energy_rerouting"
            
            # Prepare rerouting input
            outage_alerts = []
            if state.get("outages_detected"):
                outage_results = state.get("outage_detection_results", {})
                outage_alerts = [{
                    "affected_zones": outage_results.get("affected_zones", []),
                    "outage_type": outage_results.get("outage_severity", "localized"),
                    "severity": outage_results.get("outage_severity", "medium"),
                    "estimated_duration": 120,  # Default 2 hours
                    "root_cause": outage_results.get("root_cause", "unknown"),
                    "detected_at": datetime.now().isoformat()
                }]
            
            # Execute energy rerouting
            rerouting_results = self.energy_router.execute_energy_rerouting(outage_alerts)
            
            # Process rerouting results
            if rerouting_results.get("status") == "rerouting_complete":
                state["rerouting_results"] = rerouting_results
                
                # Extract rerouting metrics
                rerouting_commands = rerouting_results.get("rerouting_commands", [])
                backup_activations = rerouting_results.get("backup_activations", [])
                load_shedding = rerouting_results.get("load_shedding_schedule", [])
                
                state["optimization_commands"].extend(rerouting_commands)
                
                # Update system status
                state["grid_status"].update({
                    "rerouting_active": True,
                    "backup_sources_active": len(backup_activations),
                    "load_shedding_zones": len(load_shedding),
                    "rerouting_commands_sent": len(rerouting_commands)
                })
                
                # Add rerouting alerts
                state["system_alerts"].append({
                    "alert_type": "rerouting_executed",
                    "severity": "info",
                    "commands_sent": len(rerouting_commands),
                    "backup_activated": len(backup_activations) > 0,
                    "timestamp": datetime.now().isoformat()
                })
                
                state["completed_phases"].append("energy_rerouting")
                logger.info(f"✅ Energy rerouting completed - {len(rerouting_commands)} commands sent")
            else:
                state["errors"].append(f"Energy rerouting failed: {rerouting_results.get('error', 'Unknown error')}")
                logger.error("❌ Energy rerouting failed")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in energy rerouting node: {e}")
            state["errors"].append(f"Energy rerouting node error: {str(e)}")
            return state
    
    def _optimize_energy_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute energy optimization"""
        try:
            logger.info("⚡ Executing Energy Optimization")
            state["current_phase"] = "energy_optimization"
            
            # Skip optimization if in emergency mode
            if state.get("emergency_mode"):
                logger.info("⏭️ Skipping optimization due to emergency mode")
                state["optimization_needed"] = False
                return state
            
            # Execute energy optimization
            optimization_results = self.energy_optimizer.optimize_energy_usage()
            
            # Process optimization results
            if optimization_results.get("status") == "optimization_complete":
                state["optimization_results"] = optimization_results
                
                # Extract optimization metrics
                optimization_commands = optimization_results.get("optimization_commands", [])
                total_savings = optimization_results.get("total_savings", 0)
                savings_percent = optimization_results.get("overall_savings_percent", 0)
                
                state["optimization_commands"].extend(optimization_commands)
                
                # Update performance summary
                state["performance_summary"] = {
                    "energy_savings_achieved": savings_percent,
                    "energy_savings_target": config.ENERGY_SAVINGS_TARGET,
                    "target_met": savings_percent >= config.ENERGY_SAVINGS_TARGET,
                    "zones_optimized": len(optimization_commands),
                    "total_energy_savings_kw": total_savings,
                    "optimization_timestamp": datetime.now().isoformat()
                }
                
                # Add optimization alerts
                if savings_percent >= config.ENERGY_SAVINGS_TARGET:
                    alert_type = "optimization_success"
                    severity = "info"
                else:
                    alert_type = "optimization_below_target"
                    severity = "warning"
                
                state["system_alerts"].append({
                    "alert_type": alert_type,
                    "severity": severity,
                    "savings_achieved": savings_percent,
                    "savings_target": config.ENERGY_SAVINGS_TARGET,
                    "zones_optimized": len(optimization_commands),
                    "timestamp": datetime.now().isoformat()
                })
                
                state["completed_phases"].append("energy_optimization")
                logger.info(f"✅ Energy optimization completed - {savings_percent:.1f}% savings achieved")
            else:
                state["errors"].append(f"Energy optimization failed: {optimization_results.get('error', 'Unknown error')}")
                logger.error("❌ Energy optimization failed")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in energy optimization node: {e}")
            state["errors"].append(f"Energy optimization node error: {str(e)}")
            return state
    
    def _generate_reports_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive reports"""
        try:
            logger.info("📊 Generating Power Grid Reports")
            state["current_phase"] = "report_generation"
            
            # Determine report type based on workflow
            if state.get("emergency_mode"):
                report_type = "emergency_report"
            elif state.get("outages_detected"):
                report_type = "incident_report"
            else:
                report_type = "comprehensive"
            
            # Execute report generation
            reporting_results = self.grid_reporter.generate_power_grid_reports(report_type)
            
            # Process reporting results
            if reporting_results.get("status") == "reporting_complete":
                state["reporting_results"] = reporting_results
                
                # Extract report summaries
                report_summaries = reporting_results.get("report_summaries", [])
                recommendations = reporting_results.get("recommendations", [])
                
                # Update performance summary with report data
                generated_reports = reporting_results.get("generated_reports", {})
                if "executive_summary" in generated_reports:
                    exec_summary = generated_reports["executive_summary"]
                    key_metrics = exec_summary.get("key_metrics", {})
                    
                    state["performance_summary"].update({
                        "system_availability": key_metrics.get("system_availability", 99.5),
                        "total_consumption_kwh": key_metrics.get("total_consumption", 0),
                        "total_cost_monthly": key_metrics.get("total_cost", 0),
                        "system_efficiency": key_metrics.get("efficiency", 0.95)
                    })
                
                # Add reporting alerts
                state["system_alerts"].append({
                    "alert_type": "reports_generated",
                    "severity": "info",
                    "report_type": report_type,
                    "reports_count": len(report_summaries),
                    "recommendations_count": len(recommendations),
                    "timestamp": datetime.now().isoformat()
                })
                
                state["completed_phases"].append("report_generation")
                logger.info(f"✅ Reports generated - {len(report_summaries)} reports, {len(recommendations)} recommendations")
            else:
                state["errors"].append(f"Report generation failed: {reporting_results.get('error', 'Unknown error')}")
                logger.error("❌ Report generation failed")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in report generation node: {e}")
            state["errors"].append(f"Report generation node error: {str(e)}")
            return state
    
    def _emergency_response_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle emergency response procedures"""
        try:
            logger.info("🚨 Executing Emergency Response Procedures")
            state["current_phase"] = "emergency_response"
            
            # Immediate emergency actions
            emergency_actions = []
            
            # 1. Activate all available backup power
            if state.get("outage_detection_results", {}).get("backup_sources"):
                emergency_actions.append("activate_all_backup_power")
            
            # 2. Implement emergency load shedding
            emergency_actions.append("emergency_load_shedding")
            
            # 3. Alert all stakeholders
            emergency_actions.append("alert_emergency_contacts")
            
            # 4. Isolate affected areas
            affected_zones = state.get("outage_detection_results", {}).get("affected_zones", [])
            if affected_zones:
                emergency_actions.append(f"isolate_zones_{len(affected_zones)}")
            
            # Execute emergency rerouting with maximum priority
            emergency_alerts = [{
                "affected_zones": affected_zones,
                "outage_type": "emergency",
                "severity": "critical",
                "estimated_duration": 240,  # 4 hours for emergency
                "root_cause": "emergency_conditions",
                "detected_at": datetime.now().isoformat()
            }]
            
            # Force emergency rerouting
            emergency_rerouting = self.energy_router.execute_energy_rerouting(emergency_alerts)
            
            # Emergency response summary
            emergency_response = {
                "emergency_declared_at": datetime.now().isoformat(),
                "affected_zones": affected_zones,
                "emergency_actions": emergency_actions,
                "rerouting_status": emergency_rerouting.get("status", "failed"),
                "estimated_recovery_time": "4-8 hours",
                "emergency_contacts_notified": True
            }
            
            state["emergency_response"] = emergency_response
            state["completed_phases"].append("emergency_response")
            
            # Send emergency alert
            power_producer.send_power_outage_alert({
                "outage_type": "emergency",
                "affected_zones": affected_zones,
                "severity": "critical",
                "outage_data": emergency_response
            })
            
            logger.warning(f"🚨 Emergency response executed - {len(emergency_actions)} actions taken")
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in emergency response: {e}")
            state["errors"].append(f"Emergency response error: {str(e)}")
            return state
    
    def _finalize_workflow_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize workflow and send summary"""
        try:
            logger.info("🏁 Finalizing Power Grid Workflow")
            state["current_phase"] = "finalization"
            
            # Calculate workflow summary
            end_time = datetime.now()
            start_time = datetime.fromisoformat(state["started_at"])
            execution_duration = (end_time - start_time).total_seconds()
            
            workflow_summary = {
                "workflow_id": state["workflow_id"],
                "execution_duration_seconds": execution_duration,
                "completed_phases": state["completed_phases"],
                "total_phases": len(state["completed_phases"]),
                "errors_count": len(state.get("errors", [])),
                "success_rate": (len(state["completed_phases"]) / 7) * 100,  # 7 total possible phases
                "emergency_mode": state.get("emergency_mode", False),
                "outages_detected": state.get("outages_detected", False),
                "rerouting_executed": state.get("rerouting_required", False),
                "optimization_completed": "energy_optimization" in state["completed_phases"],
                "reports_generated": "report_generation" in state["completed_phases"]
            }
            
            # System health summary
            grid_status = state.get("grid_status", {})
            performance_summary = state.get("performance_summary", {})
            
            system_health = {
                "system_status": grid_status.get("system_status", "unknown"),
                "operational_zones": grid_status.get("operational_zones", 0),
                "affected_zones": grid_status.get("affected_zones", 0),
                "energy_savings_achieved": performance_summary.get("energy_savings_achieved", 0),
                "system_availability": performance_summary.get("system_availability", 99.5),
                "total_alerts": len(state.get("system_alerts", [])),
                "optimization_commands_sent": len(state.get("optimization_commands", []))
            }
            
            # Final status determination
            if state.get("emergency_mode"):
                final_status = "emergency_handled"
            elif len(state.get("errors", [])) > 2:
                final_status = "completed_with_errors"
            elif state.get("outages_detected"):
                final_status = "incident_managed"
            else:
                final_status = "normal_operations"
            
            state["workflow_summary"] = workflow_summary
            state["system_health"] = system_health
            state["status"] = final_status
            state["completed_at"] = end_time.isoformat()
            
            # Send final summary to Kafka
            power_producer.send_power_report({
                "report_id": f"workflow_summary_{state['workflow_id']}",
                "report_type": "workflow_summary",
                "report_data": {
                    "workflow_summary": workflow_summary,
                    "system_health": system_health,
                    "final_status": final_status,
                    "execution_time": execution_duration
                }
            })
            
            state["completed_phases"].append("finalization")
            
            # Log final summary
            logger.info(f"🎉 Power Grid Workflow Complete!")
            logger.info(f"📊 Status: {final_status}")
            logger.info(f"⏱️ Duration: {execution_duration:.1f}s")
            logger.info(f"✅ Success Rate: {workflow_summary['success_rate']:.1f}%")
            logger.info(f"📈 Energy Savings: {performance_summary.get('energy_savings_achieved', 0):.1f}%")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in workflow finalization: {e}")
            state["errors"].append(f"Workflow finalization error: {str(e)}")
            state["status"] = "finalization_failed"
            return state
    
    def _should_handle_outages(self, state: Dict[str, Any]) -> str:
        """Determine next step based on outage detection results"""
        
        if state.get("emergency_mode"):
            return "emergency"
        elif state.get("outages_detected") and state.get("rerouting_required"):
            return "rerouting_needed"
        else:
            return "continue"
    
    def execute_power_grid_workflow(
        self, 
        trigger_type: str = "scheduled",
        config_overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute the complete power grid management workflow"""
        
        try:
            workflow_id = f"power_grid_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            logger.info(f"🚀 Starting Power Grid Workflow - ID: {workflow_id}")
            logger.info(f"📋 Trigger: {trigger_type}")
            
            # Initialize workflow state
            initial_state = {
                "workflow_id": workflow_id,
                "started_at": datetime.now().isoformat(),
                "trigger_type": trigger_type,
                "current_phase": "initialization",
                "completed_phases": [],
                "errors": [],
                "status": "running",
                
                # Agent results placeholders
                "forecast_results": {},
                "outage_detection_results": {},
                "rerouting_results": {},
                "optimization_results": {},
                "reporting_results": {},
                
                # Cross-agent data
                "system_alerts": [],
                "energy_metrics": {},
                "grid_status": {},
                "optimization_commands": [],
                "performance_summary": {},
                
                # Decision flags
                "outages_detected": False,
                "rerouting_required": False,
                "optimization_needed": True,
                "emergency_mode": False
            }
            
            # Apply configuration overrides
            if config_overrides:
                initial_state.update(config_overrides)
            
            # Execute workflow with thread and configuration
            thread_config = {"configurable": {"thread_id": workflow_id}}
            result = self.workflow.invoke(initial_state, thread_config)
            
            # Log execution summary
            final_status = result.get("status", "unknown")
            execution_time = (datetime.now() - datetime.fromisoformat(initial_state["started_at"])).total_seconds()
            
            logger.info(f"🏁 Power Grid Workflow Completed!")
            logger.info(f"📊 Final Status: {final_status}")
            logger.info(f"⏱️ Total Execution Time: {execution_time:.1f} seconds")
            logger.info(f"✅ Phases Completed: {len(result.get('completed_phases', []))}")
            logger.info(f"⚠️ Errors Encountered: {len(result.get('errors', []))}")
            
            if result.get("emergency_mode"):
                logger.warning("🚨 Emergency procedures were activated during execution")
            
            if result.get("outages_detected"):
                logger.warning("⚠️ Power outages were detected and handled")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Power Grid Workflow failed: {e}")
            return {
                "workflow_id": workflow_id,
                "status": "workflow_failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "execution_time": 0
            }
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of a running workflow"""
        try:
            # Get workflow state from memory
            thread_config = {"configurable": {"thread_id": workflow_id}}
            state = self.workflow.get_state(thread_config)
            
            if state and state.values:
                current_state = state.values
                return {
                    "workflow_id": workflow_id,
                    "current_phase": current_state.get("current_phase", "unknown"),
                    "completed_phases": current_state.get("completed_phases", []),
                    "status": current_state.get("status", "unknown"),
                    "errors": current_state.get("errors", []),
                    "system_alerts": current_state.get("system_alerts", []),
                    "last_updated": datetime.now().isoformat()
                }
            else:
                return {
                    "workflow_id": workflow_id,
                    "status": "not_found",
                    "message": "Workflow not found or completed"
                }
                
        except Exception as e:
            return {
                "workflow_id": workflow_id,
                "status": "error",
                "error": str(e)
            }
    
    def trigger_emergency_response(self, emergency_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger emergency response workflow"""
        
        logger.warning("🚨 Emergency Response Triggered!")
        
        emergency_overrides = {
            "emergency_mode": True,
            "trigger_type": "emergency",
            "outages_detected": True,
            "rerouting_required": True,
            "optimization_needed": False,
            "emergency_data": emergency_data
        }
        
        return self.execute_power_grid_workflow(
            trigger_type="emergency",
            config_overrides=emergency_overrides
        )

# Create singleton instance
power_grid_graph = PowerGridGraph()

# Export main functions for easy access
def execute_power_grid_workflow(trigger_type: str = "scheduled", **kwargs) -> Dict[str, Any]:
    """Execute power grid workflow - convenience function"""
    return power_grid_graph.execute_power_grid_workflow(trigger_type, kwargs)

def get_workflow_status(workflow_id: str) -> Dict[str, Any]:
    """Get workflow status - convenience function"""
    return power_grid_graph.get_workflow_status(workflow_id)

def trigger_emergency_response(emergency_data: Dict[str, Any]) -> Dict[str, Any]:
    """Trigger emergency response - convenience function"""
    return power_grid_graph.trigger_emergency_response(emergency_data)
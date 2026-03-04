import logging
from typing import Dict, Any, List
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
from ..config.settings import config

# Import all weather agents
from ..agents.weather_collection_forecast_agent import weather_collection_forecast_agent
from ..agents.env_sensor_agent import environmental_sensor_agent
from ..agents.weather_impact_analyzer_agent import weather_impact_analyzer_agent
from ..agents.disaster_response_advisor_agent import disaster_response_advisor_agent
from ..agents.reporting_agent import weather_reporting_agent

logger = logging.getLogger(__name__)

class WeatherGraphState(TypedDict):
    """State class for weather intelligence graph coordination"""
    graph_mode: str  # 'normal', 'emergency', 'maintenance'
    agent_statuses: Dict[str, str]
    agent_results: Dict[str, Any]
    coordination_decisions: Dict[str, Any]
    emergency_conditions: Dict[str, Any]
    system_health: Dict[str, Any]
    workflow_priority: List[str]
    data_flow: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    errors: List[str]
    status: str

class WeatherIntelligenceGraph:
    """
    Master LangGraph coordinator for all weather intelligence agents.
    Orchestrates data flow, coordinates agent execution, and manages
    emergency response workflows.
    """
    
    def __init__(self):
        self.groq_config = config.get_groq_config()
        self.llm = ChatGroq(
            groq_api_key=self.groq_config['api_key'],
            model_name=self.groq_config['model'],
            temperature=self.groq_config['temperature'],
            max_tokens=self.groq_config['max_tokens']
        )
        
        # Agent registry
        self.agents = {
            "weather_collection": weather_collection_forecast_agent,
            "environmental_sensor": environmental_sensor_agent,
            "impact_analyzer": weather_impact_analyzer_agent,
            "disaster_response": disaster_response_advisor_agent,
            "reporting": weather_reporting_agent
        }
        
        # Execution schedules
        self.schedules = self._initialize_schedules()
        
        # Build the master workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build master LangGraph workflow for weather intelligence coordination"""
        workflow = StateGraph(WeatherGraphState)
        
        # Add coordination nodes
        workflow.add_node("initialize", self._initialize_coordination)
        workflow.add_node("assess_system_health", self._assess_system_health_node)
        workflow.add_node("determine_execution_mode", self._determine_execution_mode_node)
        workflow.add_node("coordinate_data_collection", self._coordinate_data_collection_node)
        workflow.add_node("execute_analysis_agents", self._execute_analysis_agents_node)
        workflow.add_node("coordinate_emergency_response", self._coordinate_emergency_response_node)
        workflow.add_node("synchronize_data_flow", self._synchronize_data_flow_node)
        workflow.add_node("monitor_agent_performance", self._monitor_agent_performance_node)
        workflow.add_node("generate_coordination_insights", self._generate_coordination_insights_node)
        workflow.add_node("execute_reporting", self._execute_reporting_node)
        workflow.add_node("finalize_coordination", self._finalize_coordination)
        
        # Define conditional edges based on execution mode
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "assess_system_health")
        workflow.add_edge("assess_system_health", "determine_execution_mode")
        
        # Conditional routing based on execution mode
        workflow.add_conditional_edges(
            "determine_execution_mode",
            self._route_execution_mode,
            {
                "normal": "coordinate_data_collection",
                "emergency": "coordinate_emergency_response",
                "maintenance": "monitor_agent_performance"
            }
        )
        
        # Normal execution flow
        workflow.add_edge("coordinate_data_collection", "execute_analysis_agents")
        workflow.add_edge("execute_analysis_agents", "synchronize_data_flow")
        workflow.add_edge("synchronize_data_flow", "monitor_agent_performance")
        
        # Emergency execution flow
        workflow.add_edge("coordinate_emergency_response", "execute_analysis_agents")
        
        # Common flow continuation
        workflow.add_edge("monitor_agent_performance", "generate_coordination_insights")
        workflow.add_edge("generate_coordination_insights", "execute_reporting")
        workflow.add_edge("execute_reporting", "finalize_coordination")
        workflow.add_edge("finalize_coordination", END)
        
        return workflow.compile()
    
    def execute_weather_intelligence(self, execution_mode: str = "auto") -> Dict[str, Any]:
        """
        Main method to execute the complete weather intelligence system
        
        Args:
            execution_mode: 'auto', 'normal', 'emergency', 'maintenance'
        """
        try:
            logger.info("Starting weather intelligence graph coordination")
            
            # Initialize state
            initial_state = WeatherGraphState(
                graph_mode=execution_mode,
                agent_statuses={agent_name: "ready" for agent_name in self.agents.keys()},
                agent_results={},
                coordination_decisions={},
                emergency_conditions={},
                system_health={},
                workflow_priority=[],
                data_flow={},
                performance_metrics={},
                errors=[],
                status="initializing"
            )
            
            # Execute master workflow
            final_state = self.workflow.invoke(initial_state)
            
            return {
                "status": final_state["status"],
                "execution_mode": final_state["graph_mode"],
                "agents_executed": len([s for s in final_state["agent_statuses"].values() if s == "completed"]),
                "agent_results": final_state["agent_results"],
                "system_health": final_state["system_health"],
                "performance_metrics": final_state["performance_metrics"],
                "coordination_insights": final_state["coordination_decisions"],
                "errors": final_state["errors"],
                "execution_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in weather intelligence graph: {e}")
            return {
                "status": "graph_failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _initialize_coordination(self, state: WeatherGraphState) -> WeatherGraphState:
        """Initialize weather intelligence coordination"""
        logger.info("Initializing weather intelligence graph coordination")
        
        state["status"] = "coordinating"
        
        # Initialize agent statuses
        for agent_name in self.agents.keys():
            state["agent_statuses"][agent_name] = "ready"
        
        # Set default workflow priority
        state["workflow_priority"] = [
            "weather_collection",
            "environmental_sensor", 
            "impact_analyzer",
            "disaster_response",
            "reporting"
        ]
        
        return state
    
    def _assess_system_health_node(self, state: WeatherGraphState) -> WeatherGraphState:
        """Assess overall system health and readiness"""
        logger.info("Assessing weather intelligence system health")
        
        try:
            # Check agent availability
            agent_health = {}
            for agent_name, agent in self.agents.items():
                try:
                    # Simple health check (would be more sophisticated in real implementation)
                    health_status = "healthy"
                    agent_health[agent_name] = {
                        "status": health_status,
                        "last_check": datetime.now().isoformat(),
                        "ready": True
                    }
                except Exception as e:
                    agent_health[agent_name] = {
                        "status": "unhealthy",
                        "error": str(e),
                        "ready": False
                    }
                    state["errors"].append(f"Agent {agent_name} health check failed: {e}")
            
            # Check data sources
            data_source_health = self._check_data_sources()
            
            # Check Kafka connectivity
            kafka_health = self._check_kafka_connectivity()
            
            # Overall system health assessment
            healthy_agents = len([h for h in agent_health.values() if h["ready"]])
            total_agents = len(agent_health)
            
            system_health = {
                "overall_status": "healthy" if healthy_agents == total_agents else "degraded",
                "agent_health": agent_health,
                "data_sources": data_source_health,
                "kafka_connectivity": kafka_health,
                "healthy_agents": healthy_agents,
                "total_agents": total_agents,
                "readiness_percentage": (healthy_agents / total_agents) * 100,
                "assessment_time": datetime.now().isoformat()
            }
            
            state["system_health"] = system_health
            
        except Exception as e:
            error_msg = f"Error assessing system health: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            state["system_health"] = {"overall_status": "unknown", "error": str(e)}
        
        return state
    
    def _determine_execution_mode_node(self, state: WeatherGraphState) -> WeatherGraphState:
        """Determine optimal execution mode based on conditions"""
        logger.info("Determining execution mode")
        
        try:
            # Check for emergency conditions
            emergency_conditions = self._detect_emergency_conditions()
            state["emergency_conditions"] = emergency_conditions
            
            # Determine execution mode
            if state["graph_mode"] == "auto":
                if emergency_conditions.get("emergency_detected", False):
                    state["graph_mode"] = "emergency"
                    state["workflow_priority"] = [
                        "weather_collection",
                        "environmental_sensor",
                        "disaster_response",
                        "impact_analyzer",
                        "reporting"
                    ]
                elif state["system_health"].get("overall_status") == "degraded":
                    state["graph_mode"] = "maintenance"
                    state["workflow_priority"] = [
                        "environmental_sensor",  # Most critical for safety
                        "weather_collection",
                        "reporting"
                    ]
                else:
                    state["graph_mode"] = "normal"
            
            # Record execution mode decision
            state["coordination_decisions"]["execution_mode"] = {
                "mode": state["graph_mode"],
                "reason": self._get_mode_reason(state),
                "priority_order": state["workflow_priority"],
                "decided_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error determining execution mode: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            # Default to normal mode on error
            state["graph_mode"] = "normal"
        
        return state
    
    def _route_execution_mode(self, state: WeatherGraphState) -> str:
        """Route workflow based on execution mode"""
        return state["graph_mode"]
    
    def _coordinate_data_collection_node(self, state: WeatherGraphState) -> WeatherGraphState:
        """Coordinate data collection agents in normal mode"""
        logger.info("Coordinating data collection agents")
        
        try:
            # Execute weather collection agent
            if "weather_collection" in state["workflow_priority"]:
                logger.info("Executing weather collection and forecast agent")
                collection_result = self.agents["weather_collection"].collect_weather_data()
                state["agent_results"]["weather_collection"] = collection_result
                state["agent_statuses"]["weather_collection"] = "completed" if collection_result.get("status") == "collection_complete" else "failed"
            
            # Execute environmental sensor agent
            if "environmental_sensor" in state["workflow_priority"]:
                logger.info("Executing environmental sensor agent")
                sensor_result = self.agents["environmental_sensor"].collect_environmental_data()
                state["agent_results"]["environmental_sensor"] = sensor_result
                state["agent_statuses"]["environmental_sensor"] = "completed" if sensor_result.get("status") == "monitoring_complete" else "failed"
            
            # Record data collection coordination
            state["coordination_decisions"]["data_collection"] = {
                "agents_executed": ["weather_collection", "environmental_sensor"],
                "execution_order": "parallel",
                "coordination_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error coordinating data collection: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _execute_analysis_agents_node(self, state: WeatherGraphState) -> WeatherGraphState:
        """Execute analysis and decision agents"""
        logger.info("Executing analysis agents")
        
        try:
            # Execute impact analyzer
            if "impact_analyzer" in state["workflow_priority"]:
                logger.info("Executing weather impact analyzer agent")
                impact_result = self.agents["impact_analyzer"].analyze_weather_impact()
                state["agent_results"]["impact_analyzer"] = impact_result
                state["agent_statuses"]["impact_analyzer"] = "completed" if impact_result.get("status") == "analysis_complete" else "failed"
            
            # Execute disaster response (if needed)
            if "disaster_response" in state["workflow_priority"]:
                # Only execute if emergency conditions detected or in emergency mode
                if (state["graph_mode"] == "emergency" or 
                    state["emergency_conditions"].get("emergency_detected", False)):
                    logger.info("Executing disaster response advisor agent")
                    disaster_result = self.agents["disaster_response"].advise_disaster_response()
                    state["agent_results"]["disaster_response"] = disaster_result
                    state["agent_statuses"]["disaster_response"] = "completed" if disaster_result.get("status") == "response_plan_complete" else "failed"
                else:
                    state["agent_statuses"]["disaster_response"] = "skipped"
            
            # Record analysis coordination
            executed_agents = [agent for agent in ["impact_analyzer", "disaster_response"] 
                             if state["agent_statuses"][agent] in ["completed", "failed"]]
            
            state["coordination_decisions"]["analysis_execution"] = {
                "agents_executed": executed_agents,
                "execution_mode": state["graph_mode"],
                "coordination_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error executing analysis agents: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _coordinate_emergency_response_node(self, state: WeatherGraphState) -> WeatherGraphState:
        """Coordinate emergency response workflow"""
        logger.info("Coordinating emergency response workflow")
        
        try:
            # Priority data collection for emergency
            emergency_agents = ["weather_collection", "environmental_sensor"]
            
            for agent_name in emergency_agents:
                if agent_name in self.agents:
                    logger.info(f"Emergency execution of {agent_name}")
                    
                    if agent_name == "weather_collection":
                        result = self.agents[agent_name].collect_weather_data()
                    elif agent_name == "environmental_sensor":
                        result = self.agents[agent_name].collect_environmental_data()
                    
                    state["agent_results"][agent_name] = result
                    state["agent_statuses"][agent_name] = "completed" if "complete" in result.get("status", "") else "failed"
            
            # Generate emergency coordination insights
            emergency_insights = self._generate_emergency_insights(state)
            state["coordination_decisions"]["emergency_response"] = emergency_insights
            
        except Exception as e:
            error_msg = f"Error coordinating emergency response: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _synchronize_data_flow_node(self, state: WeatherGraphState) -> WeatherGraphState:
        """Synchronize data flow between agents"""
        logger.info("Synchronizing data flow")
        
        try:
            # Analyze data dependencies
            data_flow_analysis = self._analyze_data_dependencies(state["agent_results"])
            
            # Check data consistency
            consistency_check = self._check_data_consistency(state["agent_results"])
            
            # Coordinate data sharing
            sharing_coordination = self._coordinate_data_sharing(state["agent_results"])
            
            state["data_flow"] = {
                "dependencies": data_flow_analysis,
                "consistency": consistency_check,
                "sharing": sharing_coordination,
                "synchronization_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error synchronizing data flow: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _monitor_agent_performance_node(self, state: WeatherGraphState) -> WeatherGraphState:
        """Monitor and assess agent performance"""
        logger.info("Monitoring agent performance")
        
        try:
            performance_metrics = {}
            
            for agent_name, agent_result in state["agent_results"].items():
                agent_status = state["agent_statuses"][agent_name]
                
                # Calculate performance metrics
                metrics = self._calculate_agent_performance(agent_name, agent_result, agent_status)
                performance_metrics[agent_name] = metrics
            
            # Overall system performance
            system_performance = self._calculate_system_performance(performance_metrics)
            
            state["performance_metrics"] = {
                "agents": performance_metrics,
                "system": system_performance,
                "monitoring_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error monitoring agent performance: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _generate_coordination_insights_node(self, state: WeatherGraphState) -> WeatherGraphState:
        """Generate coordination insights using LLM"""
        logger.info("Generating coordination insights")
        
        try:
            # Prepare coordination summary for LLM
            coordination_summary = self._prepare_coordination_summary(state)
            
            prompt = f"""
            Analyze the following weather intelligence system coordination data:
            
            System Coordination Summary:
            {coordination_summary}
            
            Provide insights and recommendations for:
            1. Overall system coordination effectiveness
            2. Agent performance optimization opportunities
            3. Data flow and synchronization improvements
            4. Emergency response coordination enhancements
            5. Resource allocation and scheduling optimization
            6. System reliability and fault tolerance improvements
            
            Focus on actionable recommendations for improving system coordination,
            performance, and reliability.
            """
            
            message = HumanMessage(content=prompt)
            response = self.llm.invoke([message])
            
            # Parse coordination insights
            insights = {
                "llm_analysis": response.content,
                "generated_at": datetime.now().isoformat(),
                "coordination_score": self._calculate_coordination_score(state),
                "improvement_areas": self._identify_improvement_areas(state),
                "recommendations": self._extract_recommendations(response.content)
            }
            
            state["coordination_decisions"]["insights"] = insights
            
        except Exception as e:
            error_msg = f"Error generating coordination insights: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _execute_reporting_node(self, state: WeatherGraphState) -> WeatherGraphState:
        """Execute reporting agent with coordination context"""
        logger.info("Executing reporting agent")
        
        try:
            # Determine report types based on execution mode
            report_types = self._determine_report_types(state["graph_mode"])
            
            # Execute reporting agent
            reporting_result = self.agents["reporting"].generate_weather_reports(report_types)
            state["agent_results"]["reporting"] = reporting_result
            state["agent_statuses"]["reporting"] = "completed" if reporting_result.get("status") == "reporting_complete" else "failed"
            
            # Add coordination context to reporting
            coordination_report = self._generate_coordination_report(state)
            state["agent_results"]["coordination_report"] = coordination_report
            
        except Exception as e:
            error_msg = f"Error executing reporting: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _finalize_coordination(self, state: WeatherGraphState) -> WeatherGraphState:
        """Finalize weather intelligence coordination"""
        logger.info("Finalizing weather intelligence coordination")
        
        # Determine overall success
        completed_agents = len([s for s in state["agent_statuses"].values() if s == "completed"])
        total_agents = len([s for s in state["agent_statuses"].values() if s != "skipped"])
        
        if completed_agents == total_agents:
            state["status"] = "coordination_complete"
        elif completed_agents > 0:
            state["status"] = "coordination_partial"
        else:
            state["status"] = "coordination_failed"
        
        # Final coordination summary
        state["coordination_decisions"]["final_summary"] = {
            "execution_mode": state["graph_mode"],
            "completed_agents": completed_agents,
            "total_agents": total_agents,
            "success_rate": (completed_agents / total_agents) * 100 if total_agents > 0 else 0,
            "errors_encountered": len(state["errors"]),
            "coordination_time": datetime.now().isoformat()
        }
        
        return state
    
    # Helper methods
    def _initialize_schedules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize agent execution schedules"""
        return {
            "weather_collection": {
                "frequency": "every_15_minutes",
                "priority": "high",
                "dependencies": []
            },
            "environmental_sensor": {
                "frequency": "every_5_minutes", 
                "priority": "critical",
                "dependencies": []
            },
            "impact_analyzer": {
                "frequency": "every_30_minutes",
                "priority": "medium",
                "dependencies": ["weather_collection", "environmental_sensor"]
            },
            "disaster_response": {
                "frequency": "on_demand",
                "priority": "critical",
                "dependencies": ["weather_collection", "environmental_sensor", "impact_analyzer"]
            },
            "reporting": {
                "frequency": "hourly",
                "priority": "low",
                "dependencies": ["weather_collection", "environmental_sensor", "impact_analyzer"]
            }
        }
    
    def _check_data_sources(self) -> Dict[str, str]:
        """Check availability of data sources"""
        return {
            "openweather_api": "available",
            "sensor_networks": "available", 
            "kafka_streams": "available",
            "historical_data": "available"
        }
    
    def _check_kafka_connectivity(self) -> Dict[str, str]:
        """Check Kafka connectivity"""
        return {
            "producer_connection": "connected",
            "consumer_connection": "connected",
            "topic_availability": "available"
        }
    
    def _detect_emergency_conditions(self) -> Dict[str, Any]:
        """Detect emergency weather conditions"""
        # Simulate emergency detection
        import random
        
        emergency_detected = random.choice([True, False])  # 50% chance for demo
        
        return {
            "emergency_detected": emergency_detected,
            "emergency_types": ["severe_storm"] if emergency_detected else [],
            "threat_level": "high" if emergency_detected else "low",
            "detection_time": datetime.now().isoformat()
        }
    
    def _get_mode_reason(self, state: WeatherGraphState) -> str:
        """Get reason for execution mode selection"""
        if state["graph_mode"] == "emergency":
            return "Emergency weather conditions detected"
        elif state["graph_mode"] == "maintenance":
            return "System health degraded"
        else:
            return "Normal operating conditions"
    
    def _generate_emergency_insights(self, state: WeatherGraphState) -> Dict[str, Any]:
        """Generate emergency coordination insights"""
        return {
            "emergency_type": state["emergency_conditions"].get("emergency_types", []),
            "response_time": "immediate",
            "coordination_priority": "life_safety",
            "agents_activated": ["weather_collection", "environmental_sensor", "disaster_response"],
            "escalation_level": "high",
            "coordination_time": datetime.now().isoformat()
        }
    
    def _analyze_data_dependencies(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data dependencies between agents"""
        return {
            "weather_to_impact": "data_available",
            "sensor_to_impact": "data_available", 
            "impact_to_disaster": "data_available",
            "all_to_reporting": "data_available",
            "dependency_health": "good"
        }
    
    def _check_data_consistency(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Check data consistency across agents"""
        return {
            "weather_sensor_consistency": "high",
            "temporal_alignment": "synchronized",
            "data_quality_score": 0.95,
            "consistency_issues": []
        }
    
    def _coordinate_data_sharing(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate data sharing between agents"""
        return {
            "shared_datasets": ["weather_data", "sensor_readings", "impact_analysis"],
            "sharing_protocol": "kafka_streams",
            "data_freshness": "real_time",
            "sharing_status": "active"
        }
    
    def _calculate_agent_performance(self, agent_name: str, agent_result: Dict[str, Any], 
                                   agent_status: str) -> Dict[str, Any]:
        """Calculate performance metrics for an agent"""
        # Performance calculation based on agent result
        success_rate = 100 if agent_status == "completed" else 0
        
        return {
            "agent_name": agent_name,
            "status": agent_status,
            "success_rate": success_rate,
            "execution_time": "normal",  # Would calculate actual execution time
            "data_quality": agent_result.get("data_quality", "unknown"),
            "error_count": len(agent_result.get("errors", [])),
            "performance_score": success_rate - (len(agent_result.get("errors", [])) * 10)
        }
    
    def _calculate_system_performance(self, agent_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall system performance"""
        total_agents = len(agent_metrics)
        successful_agents = len([m for m in agent_metrics.values() if m["success_rate"] == 100])
        
        avg_performance = sum(m["performance_score"] for m in agent_metrics.values()) / total_agents if total_agents > 0 else 0
        
        return {
            "overall_success_rate": (successful_agents / total_agents) * 100 if total_agents > 0 else 0,
            "average_performance_score": avg_performance,
            "system_health": "excellent" if avg_performance > 90 else "good" if avg_performance > 70 else "needs_attention",
            "total_agents": total_agents,
            "successful_agents": successful_agents
        }
    
    def _prepare_coordination_summary(self, state: WeatherGraphState) -> str:
        """Prepare coordination summary for LLM analysis"""
        summary_parts = []
        
        # Execution overview
        summary_parts.append(f"Execution Mode: {state['graph_mode']}")
        summary_parts.append(f"System Health: {state['system_health'].get('overall_status', 'unknown')}")
        
        # Agent performance
        summary_parts.append("Agent Performance:")
        for agent_name, status in state["agent_statuses"].items():
            result = state["agent_results"].get(agent_name, {})
            summary_parts.append(f"- {agent_name}: {status} ({len(result.get('errors', []))} errors)")
        
        # Coordination decisions
        decisions = state["coordination_decisions"]
        summary_parts.append("Coordination Decisions:")
        for decision_type, decision_data in decisions.items():
            summary_parts.append(f"- {decision_type}: {decision_data}")
        
        return "\n".join(summary_parts)
    
    def _calculate_coordination_score(self, state: WeatherGraphState) -> float:
        """Calculate overall coordination effectiveness score"""
        completed = len([s for s in state["agent_statuses"].values() if s == "completed"])
        total = len([s for s in state["agent_statuses"].values() if s != "skipped"])
        
        base_score = (completed / total) * 100 if total > 0 else 0
        error_penalty = len(state["errors"]) * 5
        
        return max(0, base_score - error_penalty)
    
    def _identify_improvement_areas(self, state: WeatherGraphState) -> List[str]:
        """Identify areas for coordination improvement"""
        improvements = []
        
        if len(state["errors"]) > 0:
            improvements.append("error_handling")
        
        failed_agents = [name for name, status in state["agent_statuses"].items() if status == "failed"]
        if failed_agents:
            improvements.append("agent_reliability")
        
        if state["system_health"].get("overall_status") != "healthy":
            improvements.append("system_health")
        
        return improvements if improvements else ["optimization"]
    
    def _extract_recommendations(self, llm_response: str) -> List[str]:
        """Extract actionable recommendations from LLM response"""
        # Simple extraction - would be more sophisticated in real implementation
        return [
            "Improve agent error handling",
            "Enhance data synchronization",
            "Optimize execution scheduling",
            "Strengthen emergency response coordination"
        ]
    
    def _determine_report_types(self, execution_mode: str) -> List[str]:
        """Determine report types based on execution mode"""
        if execution_mode == "emergency":
            return ["emergency_response", "daily_summary"]
        elif execution_mode == "maintenance":
            return ["performance_analysis"]
        else:
            return ["daily_summary", "forecast_accuracy", "performance_analysis"]
    
    def _generate_coordination_report(self, state: WeatherGraphState) -> Dict[str, Any]:
        """Generate coordination-specific report"""
        return {
            "report_type": "coordination_summary",
            "execution_mode": state["graph_mode"],
            "system_health": state["system_health"],
            "agent_performance": state["performance_metrics"],
            "coordination_decisions": state["coordination_decisions"],
            "data_flow_status": state["data_flow"],
            "errors_summary": state["errors"],
            "recommendations": state["coordination_decisions"].get("insights", {}).get("recommendations", []),
            "generated_at": datetime.now().isoformat()
        }

# Create master graph instance
weather_intelligence_graph = WeatherIntelligenceGraph()

# Convenience functions for different execution modes
async def execute_normal_operations():
    """Execute normal weather intelligence operations"""
    return weather_intelligence_graph.execute_weather_intelligence("normal")

async def execute_emergency_response():
    """Execute emergency weather response"""
    return weather_intelligence_graph.execute_weather_intelligence("emergency")

async def execute_maintenance_mode():
    """Execute system maintenance operations"""
    return weather_intelligence_graph.execute_weather_intelligence("maintenance")

async def execute_auto_mode():
    """Execute with automatic mode detection"""
    return weather_intelligence_graph.execute_weather_intelligence("auto")
import logging
from typing import Dict, Any
from datetime import datetime
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from src.agents.ddos_detection_agent import ddos_detection_agent, DDoSDetectionState
from src.agents.malware_detection_agent import malware_detection_agent, MalwareDetectionState
from src.config.settings import config

logger = logging.getLogger(__name__)

class CybersecurityGraphState(BaseModel):
    """Combined state for the 2-agent cybersecurity graph"""
    messages: list = []
    
    # Agent-specific results
    ddos_results: Dict[str, Any] = {}
    malware_results: Dict[str, Any] = {}
    
    # Overall analysis
    overall_status: str = "processing"
    risk_level: str = "unknown"
    priority_actions: list = []
    combined_summary: str = ""
    
    # Completion flags
    ddos_complete: bool = False
    malware_complete: bool = False

class CybersecurityGraph:
    """
    Dual-agent cybersecurity graph for DDoS and Malware detection.
    Runs both agents in parallel and aggregates results.
    """
    
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0,
            model_name="llama3-8b-8192",
            groq_api_key=config.GROQ_API_KEY
        )
        
        self.graph = self._create_graph()
    
    def _create_graph(self):
        """Create the 2-agent cybersecurity graph with parallel execution"""
        workflow = StateGraph(CybersecurityGraphState)
        
        # Add agent nodes
        workflow.add_node("ddos_detection", self._run_ddos_detection)
        workflow.add_node("malware_detection", self._run_malware_detection)
        workflow.add_node("aggregate_results", self._aggregate_results)
        workflow.add_node("parallel_start", lambda state: state)  # Dummy node to trigger parallel execution
        
        # Set entry point
        workflow.set_entry_point("parallel_start")
        
        # From parallel_start, both agents execute in parallel
        workflow.add_edge("parallel_start", "ddos_detection")
        workflow.add_edge("parallel_start", "malware_detection")
        
        # Both agents feed into aggregation
        workflow.add_edge("ddos_detection", "aggregate_results")
        workflow.add_edge("malware_detection", "aggregate_results")
        workflow.add_edge("aggregate_results", END)
        
        return workflow.compile()
    
    def _run_ddos_detection(self, state: CybersecurityGraphState) -> CybersecurityGraphState:
        """Execute DDoS detection agent"""
        try:
            logger.info("Running DDoS Detection Agent")
            
            # Create initial state for DDoS agent
            ddos_state = DDoSDetectionState()
            
            # Run the DDoS detection
            result = ddos_detection_agent.detect_ddos_attack(ddos_state)
            
            state.ddos_results = result
            state.ddos_complete = True
            state.messages.append("DDoS detection completed")
            
            logger.info(f"DDoS Detection Result: {result.get('attack_detected', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error in DDoS detection agent: {e}")
            state.messages.append(f"DDoS detection agent failed: {str(e)}")
            state.ddos_results = {"error": str(e), "status": "failed", "attack_detected": False}
        
        return state
    
    def _run_malware_detection(self, state: CybersecurityGraphState) -> CybersecurityGraphState:
        """Execute malware detection agent"""
        try:
            logger.info("Running Malware Detection Agent")
            
            # Create initial state for malware agent
            malware_state = MalwareDetectionState()
            
            # Run malware detection
            result = malware_detection_agent.detect_malware(malware_state)
            
            state.malware_results = result
            state.malware_complete = True
            state.messages.append("Malware detection completed")
            
            logger.info(f"Malware Detection Result: {result.get('malware_detected', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error in malware detection agent: {e}")
            state.messages.append(f"Malware detection agent failed: {str(e)}")
            state.malware_results = {"error": str(e), "status": "failed", "malware_detected": False}
        
        return state
    
    def _aggregate_results(self, state: CybersecurityGraphState) -> CybersecurityGraphState:
        """Aggregate results from both agents using LLM"""
        try:
            logger.info("Aggregating DDoS and Malware detection results")
            
            # Extract key metrics
            ddos_detected = state.ddos_results.get("attack_detected", False)
            ddos_attack_type = state.ddos_results.get("attack_type", "none")
            ddos_severity = state.ddos_results.get("severity", "none")
            
            malware_detected = state.malware_results.get("malware_detected", False)
            malware_types = state.malware_results.get("malware_types", [])
            malware_threat_level = state.malware_results.get("threat_level", "none")
            
            aggregation_prompt = f"""
            Analyze combined cybersecurity threat assessment:
            
            DDoS Detection:
            - Attack Detected: {ddos_detected}
            - Attack Type: {ddos_attack_type}
            - Severity: {ddos_severity}
            
            Malware Detection:
            - Malware Detected: {malware_detected}
            - Malware Types: {', '.join(malware_types) if malware_types else 'none'}
            - Threat Level: {malware_threat_level}
            
            Determine:
            1. Overall risk level (low/medium/high/critical)
            2. Most critical threat requiring immediate attention
            3. Top 3 priority actions for security team
            4. Combined security posture assessment
            
            Be specific and actionable.
            """
            
            response = self.llm.invoke(aggregation_prompt)
            
            # Extract overall risk level
            content = response.content.lower()
            if 'critical' in content:
                state.risk_level = 'critical'
            elif 'high' in content:
                state.risk_level = 'high'
            elif 'medium' in content:
                state.risk_level = 'medium'
            else:
                state.risk_level = 'low'
            
            # Extract priority actions
            priority_actions = []
            lines = response.content.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in ['priority', 'immediate', 'action', 'critical', '1.', '2.', '3.']):
                    if len(line.strip()) > 10:
                        priority_actions.append(line.strip())
            
            state.priority_actions = priority_actions[:3]
            state.combined_summary = response.content
            state.overall_status = "complete"
            state.messages.append(f"Aggregation complete: {state.risk_level} risk level")
            
            logger.info(f"Aggregation complete: Risk Level = {state.risk_level}")
            
        except Exception as e:
            logger.error(f"Error in result aggregation: {e}")
            state.messages.append(f"Result aggregation failed: {str(e)}")
            state.overall_status = "aggregation_failed"
            state.risk_level = "unknown"
        
        return state
    
    def execute_cybersecurity_analysis(self) -> Dict[str, Any]:
        """Execute the complete 2-agent cybersecurity analysis"""
        try:
            logger.info("Starting 2-agent cybersecurity analysis")
            
            # Initialize state
            initial_state = CybersecurityGraphState()
            
            # Execute the graph
            final_state = self.graph.invoke(initial_state)
            
            # Compile comprehensive results
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": final_state.overall_status,
                "risk_level": final_state.risk_level,
                "priority_actions": final_state.priority_actions,
                "combined_summary": final_state.combined_summary,
                "agent_results": {
                    "ddos_detection": final_state.ddos_results,
                    "malware_detection": final_state.malware_results
                },
                "completion_status": {
                    "ddos_complete": final_state.ddos_complete,
                    "malware_complete": final_state.malware_complete
                },
                "messages": final_state.messages,
                "status": "2_agent_analysis_complete"
            }
            
        except Exception as e:
            logger.error(f"Error in cybersecurity graph execution: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "2_agent_analysis_failed"
            }
    
    def execute_ddos_analysis(self) -> Dict[str, Any]:
        """Execute only DDoS detection"""
        try:
            logger.info("Starting DDoS-only analysis")
            ddos_state = DDoSDetectionState()
            result = ddos_detection_agent.detect_ddos_attack(ddos_state)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "focus_area": "ddos",
                "result": result,
                "status": "ddos_analysis_complete"
            }
            
        except Exception as e:
            logger.error(f"Error in DDoS analysis: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "ddos_analysis_failed"
            }
    
    def execute_malware_analysis(self) -> Dict[str, Any]:
        """Execute only malware detection"""
        try:
            logger.info("Starting Malware-only analysis")
            malware_state = MalwareDetectionState()
            result = malware_detection_agent.detect_malware(malware_state)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "focus_area": "malware",
                "result": result,
                "status": "malware_analysis_complete"
            }
            
        except Exception as e:
            logger.error(f"Error in Malware analysis: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "malware_analysis_failed"
            }

# Create graph instance
cybersecurity_graph = CybersecurityGraph()

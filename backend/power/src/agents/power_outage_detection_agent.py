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

class PowerOutageDetectionState:
    """State management for Power Outage Detection Agent"""
    
    def __init__(self):
        self.voltage_data: Dict[str, Any] = {}
        self.current_data: Dict[str, Any] = {}
        self.device_status: Dict[str, Any] = {}
        self.connectivity_logs: List[Dict[str, Any]] = []
        self.outages_detected: List[Dict[str, Any]] = []
        self.affected_zones: List[str] = []
        self.outage_severity: str = "none"
        self.root_cause: Optional[str] = None
        self.recovery_estimate: Optional[int] = None
        self.errors: List[str] = []
        self.status: str = "initialized"

class PowerOutageDetectionAgent:
    """LangGraph-based Power Outage Detection Agent"""
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=config.GROQ_API_KEY,
            model=config.GROQ_MODEL,
            temperature=config.GROQ_TEMPERATURE,
            max_tokens=config.GROQ_MAX_TOKENS
        )
        self.state = PowerOutageDetectionState()
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create LangGraph workflow for power outage detection"""
        
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("monitor_voltage", self._monitor_voltage_node)
        workflow.add_node("check_connectivity", self._check_connectivity_node)
        workflow.add_node("analyze_power_quality", self._analyze_power_quality_node)
        workflow.add_node("detect_outages", self._detect_outages_node)
        workflow.add_node("assess_impact", self._assess_impact_node)
        workflow.add_node("determine_cause", self._determine_cause_node)
        workflow.add_node("alert_stakeholders", self._alert_stakeholders_node)
        
        # Define workflow
        workflow.set_entry_point("monitor_voltage")
        workflow.add_edge("monitor_voltage", "check_connectivity")
        workflow.add_edge("check_connectivity", "analyze_power_quality")
        workflow.add_edge("analyze_power_quality", "detect_outages")
        workflow.add_edge("detect_outages", "assess_impact")
        workflow.add_edge("assess_impact", "determine_cause")
        workflow.add_edge("determine_cause", "alert_stakeholders")
        workflow.add_edge("alert_stakeholders", END)
        
        return workflow.compile()
    
    def _monitor_voltage_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor voltage levels across all zones"""
        try:
            logger.info("Monitoring voltage levels for outage detection")
            
            current_time = datetime.now()
            voltage_data = {}
            
            # Simulate real-time voltage monitoring
            for zone in config.DEFAULT_ZONES:
                base_voltage = 240.0  # Standard voltage
                
                # Simulate various voltage conditions
                zone_hash = hash(zone) % 100
                
                if zone_hash < 5:  # 5% chance of low voltage
                    voltage = base_voltage * (0.7 + (zone_hash % 3) * 0.1)  # 70-90% of nominal
                    status = "low_voltage"
                elif zone_hash > 95:  # 5% chance of high voltage
                    voltage = base_voltage * (1.1 + (zone_hash % 3) * 0.02)  # 110-116% of nominal
                    status = "high_voltage"
                elif zone_hash == 50:  # 1% chance of complete outage
                    voltage = 0.0
                    status = "outage"
                else:
                    voltage = base_voltage + (zone_hash % 10 - 5)  # Normal variation
                    status = "normal"
                
                voltage_data[zone] = {
                    "voltage": voltage,
                    "voltage_pu": voltage / 240.0,  # Per unit value
                    "status": status,
                    "timestamp": current_time.isoformat(),
                    "frequency": 50.0 + (zone_hash % 4 - 2) * 0.05,  # 49.9-50.1 Hz
                    "phase_angles": [0, 120, 240],  # Three-phase system
                    "quality_index": 0.95 + (zone_hash % 10) * 0.005  # 95-100%
                }
            
            # LLM analysis of voltage patterns
            prompt = f"""
            Analyze voltage monitoring data for power outage detection:
            
            Voltage Data: {json.dumps({k: v for k, v in list(voltage_data.items())[:5]}, indent=2)}
            Total Zones Monitored: {len(voltage_data)}
            Voltage Thresholds: Low={config.LOW_VOLTAGE_THRESHOLD}, High={config.HIGH_VOLTAGE_THRESHOLD}
            
            Identify:
            1. Voltage anomalies and deviations
            2. Potential outage indicators
            3. Power quality issues
            4. Patterns suggesting grid problems
            
            Return analysis in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            state["voltage_data"] = voltage_data
            state["voltage_analysis"] = response.content
            state["monitoring_time"] = current_time.isoformat()
            
            # Count anomalies
            anomalies = sum(1 for v in voltage_data.values() if v["status"] != "normal")
            logger.info(f"Voltage monitoring completed - {anomalies} anomalies detected")
            
            return state
            
        except Exception as e:
            logger.error(f"Error monitoring voltage: {e}")
            state["errors"] = state.get("errors", []) + [f"Voltage monitoring failed: {str(e)}"]
            return state
    
    def _check_connectivity_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Check device connectivity and communication logs"""
        try:
            logger.info("Checking device connectivity status")
            
            current_time = datetime.now()
            device_status = {}
            connectivity_logs = []
            
            # Simulate device connectivity checks
            for zone in config.DEFAULT_ZONES:
                zone_hash = hash(zone) % 100
                
                # Determine connectivity status
                if zone_hash < 3:  # 3% chance of communication failure
                    connected = False
                    last_response = current_time - timedelta(minutes=zone_hash * 5 + 10)
                    status = "disconnected"
                elif zone_hash < 8:  # 5% chance of intermittent issues
                    connected = True
                    last_response = current_time - timedelta(seconds=zone_hash * 30)
                    status = "intermittent"
                else:
                    connected = True
                    last_response = current_time - timedelta(seconds=zone_hash % 10)
                    status = "connected"
                
                device_status[zone] = {
                    "connected": connected,
                    "status": status,
                    "last_response": last_response.isoformat(),
                    "response_time": (zone_hash % 10) * 10 + 50,  # 50-140ms
                    "packet_loss": 0 if connected else (zone_hash % 5 + 1) * 10,  # 0-50%
                    "signal_strength": 100 - (zone_hash % 20) if connected else 0  # 80-100% or 0%
                }
                
                # Generate connectivity log entry
                connectivity_logs.append({
                    "zone": zone,
                    "timestamp": current_time.isoformat(),
                    "event": "connectivity_check",
                    "result": status,
                    "details": f"Response time: {device_status[zone]['response_time']}ms"
                })
            
            # LLM analysis of connectivity issues
            disconnected_devices = [z for z, d in device_status.items() if not d["connected"]]
            
            prompt = f"""
            Analyze device connectivity for outage detection:
            
            Total Devices: {len(device_status)}
            Disconnected Devices: {len(disconnected_devices)}
            Disconnected Zones: {disconnected_devices}
            
            Sample Device Status: {json.dumps({k: v for k, v in list(device_status.items())[:3]}, indent=2)}
            
            Assess:
            1. Communication failure patterns
            2. Potential infrastructure issues
            3. Network vs power outage correlation
            4. Device health indicators
            
            Return assessment in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            state["device_status"] = device_status
            state["connectivity_logs"] = connectivity_logs
            state["connectivity_analysis"] = response.content
            state["disconnected_count"] = len(disconnected_devices)
            
            logger.info(f"Connectivity check completed - {len(disconnected_devices)} devices disconnected")
            
            return state
            
        except Exception as e:
            logger.error(f"Error checking connectivity: {e}")
            state["errors"] = state.get("errors", []) + [f"Connectivity check failed: {str(e)}"]
            return state
    
    def _analyze_power_quality_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze power quality indicators"""
        try:
            logger.info("Analyzing power quality indicators")
            
            voltage_data = state.get("voltage_data", {})
            power_quality_issues = []
            
            for zone, data in voltage_data.items():
                voltage_pu = data.get("voltage_pu", 1.0)
                frequency = data.get("frequency", 50.0)
                quality_index = data.get("quality_index", 1.0)
                
                issues = []
                
                # Check voltage limits
                if voltage_pu < config.LOW_VOLTAGE_THRESHOLD:
                    issues.append("undervoltage")
                elif voltage_pu > config.HIGH_VOLTAGE_THRESHOLD:
                    issues.append("overvoltage")
                
                # Check frequency limits
                if frequency < config.FREQUENCY_MIN or frequency > config.FREQUENCY_MAX:
                    issues.append("frequency_deviation")
                
                # Check quality index
                if quality_index < 0.9:
                    issues.append("poor_power_quality")
                
                if issues:
                    power_quality_issues.append({
                        "zone": zone,
                        "issues": issues,
                        "voltage_pu": voltage_pu,
                        "frequency": frequency,
                        "quality_index": quality_index,
                        "severity": "critical" if "undervoltage" in issues or voltage_pu < 0.8 else "warning"
                    })
            
            # LLM analysis of power quality
            prompt = f"""
            Analyze power quality data for grid stability assessment:
            
            Power Quality Issues: {json.dumps(power_quality_issues, indent=2)}
            Total Zones with Issues: {len(power_quality_issues)}
            
            Quality Thresholds:
            - Voltage Range: {config.LOW_VOLTAGE_THRESHOLD} - {config.HIGH_VOLTAGE_THRESHOLD} pu
            - Frequency Range: {config.FREQUENCY_MIN} - {config.FREQUENCY_MAX} Hz
            - Min Quality Index: 0.9
            
            Evaluate:
            1. Grid stability indicators
            2. Cascading failure risks
            3. Power quality trend analysis
            4. Immediate intervention needs
            
            Return evaluation in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            state["power_quality_issues"] = power_quality_issues
            state["quality_analysis"] = response.content
            
            critical_issues = len([issue for issue in power_quality_issues if issue["severity"] == "critical"])
            logger.info(f"Power quality analysis completed - {critical_issues} critical issues found")
            
            return state
            
        except Exception as e:
            logger.error(f"Error analyzing power quality: {e}")
            state["errors"] = state.get("errors", []) + [f"Power quality analysis failed: {str(e)}"]
            return state
    
    def _detect_outages_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Detect actual power outages"""
        try:
            logger.info("Detecting power outages")
            
            voltage_data = state.get("voltage_data", {})
            device_status = state.get("device_status", {})
            power_quality_issues = state.get("power_quality_issues", [])
            
            outages_detected = []
            affected_zones = []
            
            # Detect outages based on multiple criteria
            for zone in config.DEFAULT_ZONES:
                voltage_info = voltage_data.get(zone, {})
                device_info = device_status.get(zone, {})
                
                voltage_pu = voltage_info.get("voltage_pu", 1.0)
                is_connected = device_info.get("connected", True)
                
                outage_detected = False
                outage_type = None
                confidence = 0.0
                
                # Complete outage detection
                if voltage_pu < config.OUTAGE_DETECTION_THRESHOLD:
                    outage_detected = True
                    outage_type = "complete_outage"
                    confidence = 0.95 if voltage_pu == 0 else 0.8
                
                # Communication-based detection
                elif not is_connected and device_info.get("packet_loss", 0) > 90:
                    outage_detected = True
                    outage_type = "communication_outage"
                    confidence = 0.7
                
                # Brownout detection
                elif voltage_pu < config.LOW_VOLTAGE_THRESHOLD:
                    outage_detected = True
                    outage_type = "brownout"
                    confidence = 0.6
                
                if outage_detected:
                    outage_data = {
                        "zone": zone,
                        "outage_type": outage_type,
                        "confidence": confidence,
                        "voltage_pu": voltage_pu,
                        "detected_at": datetime.now().isoformat(),
                        "estimated_duration": self._estimate_outage_duration(outage_type),
                        "priority": "critical" if outage_type == "complete_outage" else "high"
                    }
                    
                    outages_detected.append(outage_data)
                    affected_zones.append(zone)
            
            # Determine overall outage severity
            if not outages_detected:
                outage_severity = "none"
            elif len(outages_detected) >= len(config.DEFAULT_ZONES) * 0.5:
                outage_severity = "widespread"
            elif any(o["outage_type"] == "complete_outage" for o in outages_detected):
                outage_severity = "critical"
            else:
                outage_severity = "localized"
            
            state["outages_detected"] = outages_detected
            state["affected_zones"] = affected_zones
            state["outage_severity"] = outage_severity
            state["detection_time"] = datetime.now().isoformat()
            
            if outages_detected:
                logger.warning(f"OUTAGES DETECTED - {len(outages_detected)} zones affected, severity: {outage_severity}")
            else:
                logger.info("No outages detected - grid operating normally")
            
            return state
            
        except Exception as e:
            logger.error(f"Error detecting outages: {e}")
            state["errors"] = state.get("errors", []) + [f"Outage detection failed: {str(e)}"]
            return state
    
    def _assess_impact_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Assess impact of detected outages"""
        try:
            logger.info("Assessing outage impact")
            
            outages_detected = state.get("outages_detected", [])
            affected_zones = state.get("affected_zones", [])
            
            if not outages_detected:
                state["impact_assessment"] = {"total_impact": "none"}
                return state
            
            # Calculate impact metrics
            total_affected = len(affected_zones)
            critical_zones_affected = len([zone for zone in affected_zones if zone in config.PRIORITY_ZONES])
            
            # Estimate affected population and services
            estimated_people_affected = total_affected * 500  # Assume 500 people per zone
            estimated_load_lost = sum(50 + hash(zone) % 30 for zone in affected_zones)  # kW
            
            # Categorize impact
            if critical_zones_affected > 0:
                impact_category = "critical_infrastructure"
            elif total_affected >= len(config.DEFAULT_ZONES) * 0.3:
                impact_category = "major_disruption"
            elif total_affected >= 3:
                impact_category = "significant_impact"
            else:
                impact_category = "minor_impact"
            
            # LLM impact analysis
            prompt = f"""
            Assess the impact of detected power outages:
            
            Outages: {json.dumps(outages_detected, indent=2)}
            Total Affected Zones: {total_affected}
            Critical Infrastructure Affected: {critical_zones_affected}
            Estimated People Affected: {estimated_people_affected}
            Estimated Load Lost: {estimated_load_lost} kW
            
            Evaluate:
            1. Service disruption severity
            2. Economic impact estimation
            3. Public safety concerns
            4. Infrastructure vulnerability
            5. Recovery priority recommendations
            
            Return impact assessment in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            impact_assessment = {
                "total_affected_zones": total_affected,
                "critical_zones_affected": critical_zones_affected,
                "estimated_people_affected": estimated_people_affected,
                "estimated_load_lost": estimated_load_lost,
                "impact_category": impact_category,
                "llm_analysis": response.content
            }
            
            state["impact_assessment"] = impact_assessment
            
            logger.info(f"Impact assessment completed - Category: {impact_category}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error assessing impact: {e}")
            state["errors"] = state.get("errors", []) + [f"Impact assessment failed: {str(e)}"]
            return state
    
    def _determine_cause_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Determine root cause of outages"""
        try:
            logger.info("Determining outage root cause")
            
            outages_detected = state.get("outages_detected", [])
            power_quality_issues = state.get("power_quality_issues", [])
            connectivity_logs = state.get("connectivity_logs", [])
            
            if not outages_detected:
                state["root_cause"] = None
                return state
            
            # Analyze patterns to determine cause
            outage_types = [o["outage_type"] for o in outages_detected]
            affected_zones = state.get("affected_zones", [])
            
            # Simple root cause analysis
            if len(set(outage_types)) == 1 and outage_types[0] == "complete_outage":
                if len(affected_zones) > len(config.DEFAULT_ZONES) * 0.5:
                    root_cause = "transmission_failure"
                else:
                    root_cause = "distribution_failure"
            elif "communication_outage" in outage_types:
                root_cause = "communication_system_failure"
            elif len([i for i in power_quality_issues if "frequency_deviation" in i["issues"]]) > 0:
                root_cause = "generation_imbalance"
            else:
                root_cause = "equipment_failure"
            
            # LLM root cause analysis
            prompt = f"""
            Determine root cause of power outages:
            
            Outage Types: {outage_types}
            Affected Zones: {affected_zones}
            Power Quality Issues: {len(power_quality_issues)} zones affected
            Communication Issues: {len([log for log in connectivity_logs if 'disconnected' in log['result']])} devices
            
            Pattern Analysis:
            - Widespread vs Localized: {len(affected_zones)} of {len(config.DEFAULT_ZONES)} zones
            - Simultaneous vs Sequential: All detected at same time
            - Infrastructure Type: Mixed residential/commercial zones
            
            Determine most likely root cause and provide:
            1. Primary cause identification
            2. Contributing factors
            3. Failure propagation analysis
            4. Prevention recommendations
            
            Return root cause analysis in JSON format.
            """
            
            response = self.llm.invoke(prompt)
            
            state["root_cause"] = root_cause
            state["cause_analysis"] = response.content
            state["recovery_estimate"] = self._estimate_recovery_time(root_cause, len(affected_zones))
            
            logger.info(f"Root cause determined: {root_cause}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error determining root cause: {e}")
            state["errors"] = state.get("errors", []) + [f"Root cause analysis failed: {str(e)}"]
            return state
    
    def _alert_stakeholders_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Send alerts to stakeholders"""
        try:
            logger.info("Sending outage alerts to stakeholders")
            
            outages_detected = state.get("outages_detected", [])
            
            if not outages_detected:
                state["status"] = "monitoring_complete"
                return state
            
            # Prepare alert data
            alert_data = {
                "outages": outages_detected,
                "affected_zones": state.get("affected_zones", []),
                "severity": state.get("outage_severity", "unknown"),
                "impact_assessment": state.get("impact_assessment", {}),
                "root_cause": state.get("root_cause"),
                "recovery_estimate": state.get("recovery_estimate"),
                "detected_at": state.get("detection_time"),
                "alert_id": f"outage_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            # Send to Kafka
            success = power_producer.send_power_outage_alert({
                "outage_type": "multiple" if len(outages_detected) > 1 else outages_detected[0]["outage_type"],
                "affected_zones": state.get("affected_zones", []),
                "severity": state.get("outage_severity", "unknown"),
                "outage_data": alert_data
            })
            
            if success:
                state["status"] = "alerts_sent"
                state["alert_sent_at"] = datetime.now().isoformat()
                logger.info("Outage alerts sent successfully")
            else:
                state["status"] = "alert_failed"
                state["errors"] = state.get("errors", []) + ["Failed to send outage alerts"]
            
            return state
            
        except Exception as e:
            logger.error(f"Error sending alerts: {e}")
            state["errors"] = state.get("errors", []) + [f"Alert sending failed: {str(e)}"]
            state["status"] = "alert_failed"
            return state
    
    def _estimate_outage_duration(self, outage_type: str) -> int:
        """Estimate outage duration in minutes"""
        duration_map = {
            "complete_outage": 120,  # 2 hours
            "brownout": 30,          # 30 minutes
            "communication_outage": 15  # 15 minutes
        }
        return duration_map.get(outage_type, 60)
    
    def _estimate_recovery_time(self, root_cause: str, affected_count: int) -> int:
        """Estimate recovery time in minutes"""
        base_times = {
            "transmission_failure": 240,      # 4 hours
            "distribution_failure": 120,      # 2 hours
            "equipment_failure": 60,          # 1 hour
            "communication_system_failure": 30,  # 30 minutes
            "generation_imbalance": 45        # 45 minutes
        }
        
        base_time = base_times.get(root_cause, 90)
        # Scale by affected zones
        scaling_factor = 1 + (affected_count - 1) * 0.2
        return int(base_time * scaling_factor)
    
    def detect_power_outages(self, initial_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute power outage detection workflow"""
        try:
            logger.info("Starting power outage detection workflow")
            
            # Initialize state
            if initial_state is None:
                initial_state = {
                    "workflow_id": f"outage_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "started_at": datetime.now().isoformat(),
                    "errors": []
                }
            
            # Execute workflow
            result = self.workflow.invoke(initial_state)
            
            logger.info(f"Power outage detection completed - Status: {result.get('status', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Power outage detection workflow failed: {e}")
            return {
                "status": "detection_failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Create singleton instance
power_outage_detection_agent = PowerOutageDetectionAgent()
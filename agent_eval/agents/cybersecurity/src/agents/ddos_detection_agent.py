# backend/cybersecurity/src/agents/ddos_detection_agent.py

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from collections import Counter, defaultdict
from kafka import KafkaConsumer
from ..config.settings import config

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# MITRE ATT&CK for ICS — DDoS-related TTPs
# ═══════════════════════════════════════════════════════════════════════════════

DDOS_MITRE_TTP_MAP = {
    "http_flood":        {"ttps": ["T0813", "T0883"], "tactic": "Inhibit Response Function"},
    "syn_flood":         {"ttps": ["T0813", "T0804"], "tactic": "Inhibit Response Function"},
    "udp_flood":         {"ttps": ["T0813"],          "tactic": "Inhibit Response Function"},
    "slowloris":         {"ttps": ["T0813", "T0883"], "tactic": "Inhibit Response Function"},
    "dns_amplification": {"ttps": ["T0813", "T0834"], "tactic": "Impact"},
    "volumetric":        {"ttps": ["T0813", "T0834"], "tactic": "Impact"},
}

class DDoSDetectionState(BaseModel):
    """State for DDoS detection operations"""
    messages: list = []
    traffic_data: list = []
    baseline_metrics: Dict[str, Any] = {}
    current_metrics: Dict[str, Any] = {}
    attack_detected: bool = False
    attack_type: str = "none"
    attack_metrics: Dict[str, Any] = {}
    severity: str = "none"
    confidence: float = 0.0
    attacker_ips: list = []
    mitigation_actions: list = []
    analysis_summary: str = ""

class DDoSDetectionAgent:
    """
    LangGraph agent specialized in detecting DDoS and volumetric attacks.
    
    Primary Attack Types Detected:
    1. DDoS Attacks - Layer 3/4/7 (HTTP floods, SYN floods, UDP floods)
    2. Volumetric Attacks - Bandwidth saturation, amplification attacks
    
    Detection Capabilities:
    - Real-time traffic pattern analysis
    - Request rate monitoring per IP/zone
    - Baseline deviation detection
    - Geographic anomaly detection
    - Packet size analysis
    - Protocol-level attack detection
    """
    
    def __init__(self, llm=None, model_registry=None):
        self.llm = llm
        self.model_registry = model_registry
        self._init_llm()
        
        self.kafka_config = config.get_kafka_config()
        
        self.graph = self._create_graph()

    def _init_llm(self):
        """Initialize LLM from ModelRegistry (multi-provider) with fallback."""
        if self.llm:
            return
        try:
            if self.model_registry:
                self.llm = self.model_registry.get_llm()
                logger.info("DDoS Agent: LLM from ModelRegistry")
                return
            # Try ModelRegistry auto-discovery
            try:
                import sys
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "arena"))
                from model_registry import ModelRegistry
                registry = ModelRegistry()
                self.llm = registry.get_llm()
                logger.info("DDoS Agent: LLM from auto-discovered ModelRegistry")
                return
            except Exception:
                pass
            # Fallback: try providers in order
            for provider_fn in [
                lambda: self._try_groq(),
                lambda: self._try_cerebras(),
                lambda: self._try_mistral(),
            ]:
                llm = provider_fn()
                if llm:
                    self.llm = llm
                    return
        except Exception as e:
            logger.warning(f"LLM initialization failed: {e}")
        # Final fallback: Groq from config
        try:
            from langchain_groq import ChatGroq
            self.llm = ChatGroq(
                temperature=0,
                model_name="llama3-8b-8192",
                groq_api_key=config.GROQ_API_KEY
            )
            logger.info("DDoS Agent: LLM from Groq (config fallback)")
        except Exception as e:
            logger.error(f"All LLM providers failed: {e}")

    def _try_groq(self):
        try:
            from langchain_groq import ChatGroq
            key = os.getenv("GROQ_API_KEY", "")
            if key:
                return ChatGroq(temperature=0, model_name="llama3-8b-8192", groq_api_key=key)
        except ImportError:
            pass
        return None

    def _try_cerebras(self):
        try:
            from langchain_cerebras import ChatCerebras
            key = os.getenv("CEREBRAS_API_KEY", "")
            if key:
                return ChatCerebras(temperature=0, model="llama-3.3-70b", api_key=key)
        except ImportError:
            pass
        return None

    def _try_mistral(self):
        try:
            from langchain_mistralai import ChatMistralAI
            key = os.getenv("MISTRAL_API_KEY", "")
            if key:
                return ChatMistralAI(temperature=0, model="mistral-small-latest", api_key=key)
        except ImportError:
            pass
        return None
    
    @property
    def thresholds(self):
        """Read thresholds from config singleton at runtime so dashboard changes take effect."""
        return {
            "normal_rps_min": config.DDOS_NORMAL_RPS_MIN,
            "normal_rps_max": config.DDOS_NORMAL_RPS_MAX,
            "critical_rps": config.DDOS_CRITICAL_RPS,
            "high_rps": config.DDOS_HIGH_RPS,
            "requests_per_ip_threshold": config.DDOS_REQUESTS_PER_IP_SUSPICIOUS,
            "unique_ip_normal_max": config.DDOS_UNIQUE_IPS_NORMAL,
            "unique_ip_attack_min": config.DDOS_UNIQUE_IPS_ATTACK,
            "response_time_normal_ms": config.DDOS_RESPONSE_TIME_NORMAL_MS,
            "failed_request_rate_normal": config.DDOS_FAILED_REQUEST_RATE,
            "syn_flood_threshold": config.DDOS_SYN_FLOOD_THRESHOLD,
            "packet_size_anomaly_min": config.DDOS_PACKET_SIZE_ANOMALY_MIN,
            "packet_size_anomaly_max": config.DDOS_PACKET_SIZE_ANOMALY_MAX,
            "geo_concentration_threshold": config.DDOS_GEO_CONCENTRATION_THRESHOLD,
        }
    
    def _create_graph(self):
        """Create LangGraph workflow for DDoS detection"""
        workflow = StateGraph(DDoSDetectionState)
        
        # Add nodes following standard pattern
        workflow.add_node("collect_traffic_data", self._collect_traffic_data)
        workflow.add_node("analyze_patterns", self._analyze_patterns)
        workflow.add_node("detect_ddos_attacks", self._detect_ddos_attacks)
        workflow.add_node("assess_severity", self._assess_severity)
        workflow.add_node("generate_mitigation", self._generate_mitigation)
        
        # Define workflow edges
        workflow.set_entry_point("collect_traffic_data")
        workflow.add_edge("collect_traffic_data", "analyze_patterns")
        workflow.add_edge("analyze_patterns", "detect_ddos_attacks")
        workflow.add_edge("detect_ddos_attacks", "assess_severity")
        workflow.add_edge("assess_severity", "generate_mitigation")
        workflow.add_edge("generate_mitigation", END)
        
        return workflow.compile()
    
    def _collect_traffic_data(self, state: DDoSDetectionState) -> DDoSDetectionState:
        """Collect network traffic data from Kafka"""
        try:
            consumer = KafkaConsumer(
                'network_events',
                'cyber_alerts',
                bootstrap_servers=self.kafka_config['bootstrap_servers'],
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                consumer_timeout_ms=3000,
                auto_offset_reset='latest'
            )
            
            traffic_data = []
            cutoff_time = datetime.now() - timedelta(seconds=300)  # Last 5 minutes
            
            for message in consumer:
                try:
                    data = message.value
                    if data.get('event_type') in ['network_traffic', 'http_request', 'connection_attempt']:
                        msg_time = datetime.fromisoformat(data.get('timestamp', ''))
                        if msg_time > cutoff_time:
                            traffic_data.append(data)
                except Exception as e:
                    logger.warning(f"Error parsing traffic message: {e}")
                    continue
            
            consumer.close()
            
            state.traffic_data = traffic_data
            state.messages.append(f"Collected {len(traffic_data)} traffic events")
            logger.info(f"DDoS Agent: Collected {len(traffic_data)} traffic events")
            
        except Exception as e:
            logger.error(f"Error collecting traffic data: {e}")
            state.messages.append(f"Traffic data collection failed: {str(e)}")
        
        return state
    
    def _analyze_patterns(self, state: DDoSDetectionState) -> DDoSDetectionState:
        """Analyze traffic patterns and calculate metrics"""
        if not state.traffic_data:
            state.messages.append("No traffic data available for analysis")
            logger.warning("DDoS Agent: No traffic data available")
            return state
        
        # Calculate time window
        timestamps = [datetime.fromisoformat(d.get('timestamp', '')) for d in state.traffic_data if d.get('timestamp')]
        if timestamps:
            time_window_seconds = (max(timestamps) - min(timestamps)).total_seconds() or 1
        else:
            time_window_seconds = 300
        
        # Calculate current metrics
        total_requests = len(state.traffic_data)
        requests_per_second = total_requests / time_window_seconds
        
        # IP analysis
        ip_counts = Counter(event.get('source_ip', 'unknown') for event in state.traffic_data if event.get('source_ip'))
        unique_ips = len(ip_counts)
        top_ips = dict(ip_counts.most_common(10))
        max_requests_per_ip = max(ip_counts.values()) if ip_counts else 0
        
        # Geographic analysis
        geo_distribution = Counter(event.get('geo_location', 'unknown') for event in state.traffic_data if event.get('geo_location'))
        geo_concentration = max(geo_distribution.values()) / total_requests if geo_distribution and total_requests > 0 else 0
        
        # Response time analysis
        response_times = [event.get('response_time_ms', 0) for event in state.traffic_data if event.get('response_time_ms')]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Failed requests
        failed_requests = sum(1 for event in state.traffic_data if event.get('status_code', 200) >= 400)
        failed_rate = failed_requests / total_requests if total_requests > 0 else 0
        
        # Packet size analysis
        packet_sizes = [event.get('packet_size', 0) for event in state.traffic_data if event.get('packet_size')]
        avg_packet_size = sum(packet_sizes) / len(packet_sizes) if packet_sizes else 0
        
        # Connection type analysis
        connection_types = Counter(event.get('connection_type', 'unknown') for event in state.traffic_data)
        syn_connections = connection_types.get('SYN', 0)
        
        # Protocol analysis
        protocols = Counter(event.get('protocol', 'unknown') for event in state.traffic_data)
        
        # Store baseline (would typically come from historical data)
        state.baseline_metrics = {
            "normal_rps_min": self.thresholds["normal_rps_min"],
            "normal_rps_max": self.thresholds["normal_rps_max"],
            "normal_unique_ips": self.thresholds["unique_ip_normal_max"],
            "normal_response_time": self.thresholds["response_time_normal_ms"],
            "normal_failed_rate": self.thresholds["failed_request_rate_normal"]
        }
        
        # Store current metrics
        state.current_metrics = {
            "total_requests": total_requests,
            "requests_per_second": round(requests_per_second, 2),
            "unique_ips": unique_ips,
            "top_ips": top_ips,
            "max_requests_per_ip": max_requests_per_ip,
            "avg_response_time_ms": round(avg_response_time, 2),
            "failed_requests": failed_requests,
            "failed_rate": round(failed_rate, 4),
            "geo_concentration": round(geo_concentration, 2),
            "geo_distribution": dict(geo_distribution.most_common(5)),
            "avg_packet_size": round(avg_packet_size, 2),
            "syn_connections": syn_connections,
            "protocols": dict(protocols),
            "time_window_seconds": time_window_seconds
        }
        
        state.messages.append(f"Pattern analysis complete: {requests_per_second:.2f} RPS, {unique_ips} unique IPs")
        logger.info(f"DDoS Agent: Current RPS={requests_per_second:.2f}, Unique IPs={unique_ips}")
        
        return state
    
    def _detect_ddos_attacks(self, state: DDoSDetectionState) -> DDoSDetectionState:
        """Detect DDoS attacks using LLM analysis with specialized prompts"""
        try:
            current = state.current_metrics
            baseline = state.baseline_metrics
            
            # Calculate deviations
            rps_deviation = ((current["requests_per_second"] - baseline["normal_rps_max"]) / baseline["normal_rps_max"] * 100) if baseline["normal_rps_max"] > 0 else 0
            response_time_deviation = ((current["avg_response_time_ms"] - baseline["normal_response_time"]) / baseline["normal_response_time"] * 100) if baseline["normal_response_time"] > 0 else 0
            
            # Prepare specialized DDoS detection prompt
            detection_prompt = f"""You are a specialized DDoS Detection Expert analyzing smart lighting infrastructure traffic.

CURRENT TRAFFIC ANALYSIS:
- Total Requests: {current["total_requests"]}
- Requests per Second: {current["requests_per_second"]} (Baseline: {baseline["normal_rps_min"]}-{baseline["normal_rps_max"]})
- RPS Deviation: {rps_deviation:+.1f}%
- Unique Source IPs: {current["unique_ips"]} (Normal: <{baseline["normal_unique_ips"]})
- Geographic Concentration: {current["geo_concentration"]*100:.1f}% from top region
- Top 5 Geographic Sources: {current["geo_distribution"]}
- Top 5 IPs by Request Count: {list(current["top_ips"].items())[:5]}
- Max Requests from Single IP: {current["max_requests_per_ip"]}
- Average Response Time: {current["avg_response_time_ms"]}ms (Normal: <{baseline["normal_response_time"]}ms)
- Response Time Deviation: {response_time_deviation:+.1f}%
- Failed Requests: {current["failed_requests"]} ({current["failed_rate"]*100:.2f}%)
- Average Packet Size: {current["avg_packet_size"]} bytes
- SYN Connections: {current["syn_connections"]}
- Protocol Distribution: {current["protocols"]}

BASELINE METRICS (Normal Operation):
- Normal RPS Range: {baseline["normal_rps_min"]}-{baseline["normal_rps_max"]}
- Expected Unique IPs: <{baseline["normal_unique_ips"]}
- Normal Response Time: <{baseline["normal_response_time"]}ms
- Normal Failed Rate: <{baseline["normal_failed_rate"]*100}%

ATTACK INDICATORS TO DETECT:

1. DDoS Attack Signatures:
   - Sudden spike in requests (>500% baseline = CRITICAL, >200% = HIGH)
   - Single IP making >{self.thresholds["requests_per_ip_threshold"]} requests/minute
   - Multiple IPs from same subnet attacking (check top IPs for patterns)
   - Uniform request patterns (bot-like behavior)
   - Geographic concentration >{self.thresholds["geo_concentration_threshold"]*100}% from single region
   - Response time degradation (>3x baseline)
   - High failed request rate (>{baseline["normal_failed_rate"]*100*2}%)

2. Specific Attack Types:
   - HTTP Flood: High RPS, distributed IPs, application layer
   - SYN Flood: High SYN connections (>{self.thresholds["syn_flood_threshold"]}), incomplete handshakes
   - UDP Flood: High UDP traffic, unusual packet sizes
   - Slowloris: Many concurrent connections, slow data transmission
   - DNS Amplification: Large response packets, UDP protocol

3. Volumetric Attack Signatures:
   - Unusual packet sizes (<{self.thresholds["packet_size_anomaly_min"]} or >{self.thresholds["packet_size_anomaly_max"]} bytes)
   - Protocol anomalies (unexpected protocol distribution)
   - Bandwidth saturation indicators

ANALYSIS REQUIREMENTS:
1. Determine if DDoS attack is occurring (true/false)
2. Calculate deviation from baseline as percentage
3. Identify specific attack type: http_flood, syn_flood, udp_flood, volumetric, slowloris, dns_amplification, or none
4. Assign confidence score (0-100) based on indicator strength
5. Identify attack severity: critical (>90% confidence), high (70-90%), medium (50-70%), low (<50%)
6. List top 5 attacker IPs with their request counts
7. Explain the technical reasoning

OUTPUT ONLY VALID JSON:
{{
    "attack_detected": true or false,
    "attack_type": "http_flood" or "syn_flood" or "udp_flood" or "volumetric" or "slowloris" or "dns_amplification" or "none",
    "confidence": 85.5,
    "severity": "critical" or "high" or "medium" or "low" or "none",
    "baseline_deviation_percent": "+450.2",
    "primary_indicators": [
        "RPS spike: 2500 (500% above baseline)",
        "Single IP flooding: 192.168.1.100 with 5000 requests"
    ],
    "attacker_ips": [
        {{"ip": "192.168.1.100", "requests": 5000, "suspicious_score": 95}},
        {{"ip": "10.0.0.50", "requests": 3000, "suspicious_score": 85}}
    ],
    "technical_explanation": "Detected Layer 7 HTTP flood attack. RPS increased from baseline 300 to 2500 (733% increase). Single IP 192.168.1.100 responsible for 50% of traffic. Response times degraded to 450ms (4.5x normal). Pattern indicates coordinated botnet attack."
}}

Be precise, technical, and focus on quantifiable metrics. Output ONLY the JSON object, no additional text."""

            response = self.llm.invoke(detection_prompt)
            
            # Parse LLM response
            try:
                # Extract JSON from response
                content = response.content.strip()
                # Remove markdown code blocks if present
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                content = content.strip()
                
                analysis_result = json.loads(content)
                
                state.attack_detected = analysis_result.get("attack_detected", False)
                state.attack_type = analysis_result.get("attack_type", "none")
                state.confidence = analysis_result.get("confidence", 0.0)
                state.severity = analysis_result.get("severity", "none")
                
                state.attack_metrics = {
                    "baseline_deviation": analysis_result.get("baseline_deviation_percent", "0%"),
                    "primary_indicators": analysis_result.get("primary_indicators", []),
                    "technical_explanation": analysis_result.get("technical_explanation", "")
                }
                
                state.attacker_ips = analysis_result.get("attacker_ips", [])[:5]
                
                if state.attack_detected:
                    state.messages.append(f"DDoS ATTACK DETECTED: {state.attack_type} - {state.severity} severity ({state.confidence}% confidence)")
                    logger.warning(f"DDoS Agent: ATTACK DETECTED - Type={state.attack_type}, Severity={state.severity}, Confidence={state.confidence}%")
                else:
                    state.messages.append(f"No DDoS attack detected (confidence: {state.confidence}%)")
                    logger.info(f"DDoS Agent: No attack detected")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.debug(f"LLM Response: {response.content}")
                # Fallback to simple rule-based detection
                state.attack_detected = current["requests_per_second"] > self.thresholds["critical_rps"]
                state.attack_type = "http_flood" if state.attack_detected else "none"
                state.confidence = 60.0 if state.attack_detected else 40.0
                state.severity = "high" if state.attack_detected else "none"
                state.messages.append("LLM parsing failed, using rule-based detection")
            
        except Exception as e:
            logger.error(f"Error in DDoS detection: {e}")
            state.messages.append(f"DDoS detection failed: {str(e)}")
            state.attack_detected = False
            state.attack_type = "none"
        
        return state
    
    def _assess_severity(self, state: DDoSDetectionState) -> DDoSDetectionState:
        """Assess the severity and business impact of detected attack"""
        if not state.attack_detected:
            state.severity = "none"
            state.messages.append("No attack detected - severity assessment skipped")
            return state
        
        try:
            # Severity already assigned by LLM, but validate and enhance
            current = state.current_metrics
            
            # Calculate impact score
            impact_factors = {
                "rps_impact": min((current["requests_per_second"] / self.thresholds["critical_rps"]) * 30, 30),
                "response_degradation": min((current["avg_response_time_ms"] / self.thresholds["response_time_normal_ms"]) * 20, 20),
                "failed_requests": min((current["failed_rate"] / 0.1) * 20, 20),
                "ip_concentration": min((current["max_requests_per_ip"] / self.thresholds["requests_per_ip_threshold"]) * 15, 15),
                "geo_concentration": current["geo_concentration"] * 15
            }
            
            total_impact_score = sum(impact_factors.values())
            
            # Override severity if impact score suggests different level
            if total_impact_score >= 80:
                state.severity = "critical"
            elif total_impact_score >= 60:
                state.severity = "high"
            elif total_impact_score >= 40:
                state.severity = "medium"
            else:
                state.severity = "low"
            
            state.attack_metrics["impact_score"] = round(total_impact_score, 2)
            state.attack_metrics["impact_factors"] = {k: round(v, 2) for k, v in impact_factors.items()}
            
            # Business impact assessment
            if state.severity in ["critical", "high"]:
                business_impact = "Service disruption likely. User experience severely affected. Immediate action required."
            elif state.severity == "medium":
                business_impact = "Partial service degradation. User experience impacted. Action recommended."
            else:
                business_impact = "Minimal service impact. Monitoring recommended."
            
            state.attack_metrics["business_impact"] = business_impact
            
            state.messages.append(f"Severity assessed: {state.severity} (impact score: {total_impact_score:.1f}/100)")
            logger.info(f"DDoS Agent: Severity={state.severity}, Impact={total_impact_score:.1f}")
            
        except Exception as e:
            logger.error(f"Error in severity assessment: {e}")
            state.messages.append(f"Severity assessment error: {str(e)}")
        
        return state
    
    def _generate_mitigation(self, state: DDoSDetectionState) -> DDoSDetectionState:
        """Generate specific mitigation actions based on attack type"""
        if not state.attack_detected:
            state.mitigation_actions = ["Continue normal monitoring"]
            state.analysis_summary = "No DDoS attack detected. System operating normally."
            return state
        
        try:
            # Generate attack-specific mitigation actions
            mitigation_actions = []
            
            # Common actions for all DDoS attacks
            mitigation_actions.append("IMMEDIATE: Enable rate limiting on all endpoints")
            mitigation_actions.append("IMMEDIATE: Activate DDoS protection mode in load balancer")
            
            # Attack-type specific actions
            if state.attack_type == "http_flood":
                mitigation_actions.extend([
                    "Block top attacking IPs at firewall level: " + ", ".join([ip["ip"] for ip in state.attacker_ips[:3]]),
                    "Implement CAPTCHA challenges for suspicious traffic",
                    "Enable HTTP request validation and filtering",
                    "Activate CDN-level DDoS protection",
                    "Increase server resources temporarily"
                ])
            
            elif state.attack_type == "syn_flood":
                mitigation_actions.extend([
                    "Enable SYN cookies at OS/firewall level",
                    "Reduce SYN-RECEIVED timeout values",
                    "Implement SYN proxy at network edge",
                    "Block source IPs: " + ", ".join([ip["ip"] for ip in state.attacker_ips[:3]]),
                    "Contact ISP for upstream filtering"
                ])
            
            elif state.attack_type == "udp_flood":
                mitigation_actions.extend([
                    "Block UDP traffic from attacking IPs",
                    "Implement UDP rate limiting",
                    "Enable anti-spoofing filters",
                    "Coordinate with ISP for upstream mitigation"
                ])
            
            elif state.attack_type == "slowloris":
                mitigation_actions.extend([
                    "Reduce connection timeout values",
                    "Limit concurrent connections per IP",
                    "Block slow-sending IPs: " + ", ".join([ip["ip"] for ip in state.attacker_ips[:3]]),
                    "Enable reverse proxy with connection management"
                ])
            
            elif state.attack_type == "dns_amplification":
                mitigation_actions.extend([
                    "Block DNS response traffic from open resolvers",
                    "Implement BCP38 filtering at network edge",
                    "Contact ISP about amplification attacks",
                    "Enable DNS response rate limiting"
                ])
            
            elif state.attack_type == "volumetric":
                mitigation_actions.extend([
                    "Activate scrubbing center services",
                    "Implement BGP blackholing for attacking networks",
                    "Contact ISP for upstream mitigation",
                    "Enable network-level traffic filtering",
                    "Scale bandwidth capacity if possible"
                ])
            
            # Severity-based additional actions
            if state.severity == "critical":
                mitigation_actions.insert(0, "CRITICAL: Consider temporary service shutdown for affected zones")
                mitigation_actions.insert(1, "CRITICAL: Notify security team and management immediately")
                mitigation_actions.append("CRITICAL: Activate incident response team")
                mitigation_actions.append("CRITICAL: Document attack for forensics")
            
            state.mitigation_actions = mitigation_actions
            
            # Generate comprehensive summary
            state.analysis_summary = f"""
DDoS Attack Analysis Summary:
- Attack Type: {state.attack_type.upper().replace('_', ' ')}
- Severity: {state.severity.upper()}
- Confidence: {state.confidence}%
- Impact Score: {state.attack_metrics.get('impact_score', 0)}/100
- Baseline Deviation: {state.attack_metrics.get('baseline_deviation', 'N/A')}
- Top Attacker IPs: {len(state.attacker_ips)}
- Mitigation Actions Required: {len(state.mitigation_actions)}
- Business Impact: {state.attack_metrics.get('business_impact', 'Unknown')}

Technical Details:
{state.attack_metrics.get('technical_explanation', 'No additional details')}
            """.strip()
            
            state.messages.append(f"Generated {len(mitigation_actions)} mitigation actions")
            logger.info(f"DDoS Agent: Generated {len(mitigation_actions)} mitigation actions for {state.attack_type}")
            
        except Exception as e:
            logger.error(f"Error generating mitigation actions: {e}")
            state.messages.append(f"Mitigation generation error: {str(e)}")
            state.mitigation_actions = ["Error generating actions - manual intervention required"]
        
        return state
    
    def detect_ddos(self, state: Optional[DDoSDetectionState] = None) -> Dict[str, Any]:
        """
        Main entry point for DDoS detection.
        Executes the complete LangGraph workflow.
        """
        if state is None:
            state = DDoSDetectionState()
        
        try:
            logger.info("DDoS Detection Agent: Starting analysis")
            result_state = self.graph.invoke(state)
            
            # Map attack type to MITRE ATT&CK TTPs
            attack_type = result_state.attack_type
            mitre_info = DDOS_MITRE_TTP_MAP.get(attack_type, {"ttps": [], "tactic": "Unknown"})
            
            # Format output with standardized schema
            return {
                "agent": "ddos_detection",
                "timestamp": datetime.now().isoformat(),
                "attack_detected": result_state.attack_detected,
                "attack_type": result_state.attack_type,
                "severity": result_state.severity,
                "confidence": result_state.confidence,
                # MITRE ATT&CK TTP tagging (P3.3)
                "mitre_ttps": mitre_info["ttps"],
                "mitre_tactic": mitre_info["tactic"],
                # Detailed metrics
                "baseline_metrics": result_state.baseline_metrics,
                "current_metrics": result_state.current_metrics,
                "attack_metrics": result_state.attack_metrics,
                "attacker_ips": result_state.attacker_ips,
                "mitigation_actions": result_state.mitigation_actions,
                "analysis_summary": result_state.analysis_summary,
                "messages": result_state.messages,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"DDoS detection workflow failed: {e}")
            return {
                "agent": "ddos_detection",
                "timestamp": datetime.now().isoformat(),
                "attack_detected": False,
                "mitre_ttps": [],
                "mitre_tactic": "Unknown",
                "error": str(e),
                "status": "failed"
            }

# Create singleton instance
try:
    ddos_detection_agent = DDoSDetectionAgent()
except Exception as e:
    logger.warning(f"Could not create DDoS agent singleton: {e}")
    ddos_detection_agent = None
import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app
from agents.data_integrity_agent import data_integrity_agent, DataIntegrityState
from agents.threat_detection_agent import threat_detection_agent, ThreatDetectionState
from agents.intrusion_response_agent import intrusion_response_agent, IntrusionResponseState
from agents.reporting_agent import reporting_agent, ReportingState
from graph.cybersecurity_graph import cybersecurity_graph, CybersecurityGraphState
from kafka.kafka_producer import cybersecurity_producer
from kafka.kafka_consumer import cybersecurity_consumer

# Test client for FastAPI
client = TestClient(app)

class TestDataIntegrityAgent:
    """Test cases for Data Integrity Agent"""
    
    @patch('agents.data_integrity_agent.KafkaConsumer')
    def test_data_integrity_validation_success(self, mock_consumer):
        """Test successful data integrity validation"""
        # Mock Kafka messages
        mock_messages = [
            Mock(value={
                'event_type': 'sensor_data',
                'source_id': 'sensor_001',
                'timestamp': datetime.now().isoformat(),
                'checksum': 'abc123',
                'data': {'temperature': 25.5, 'humidity': 60.0}
            })
        ]
        
        mock_consumer_instance = Mock()
        mock_consumer_instance.__iter__ = Mock(return_value=iter(mock_messages))
        mock_consumer.return_value = mock_consumer_instance
        
        # Test validation
        result = data_integrity_agent.validate_data_integrity()
        
        assert result['status'] == 'validation_complete'
        assert 'integrity_results' in result
        assert 'validation_status' in result
    
    def test_checksum_validation(self):
        """Test checksum validation logic"""
        test_data = {
            'source_id': 'test_sensor',
            'timestamp': '2024-01-01T10:00:00',
            'data': {'temp': 20.0}
        }
        
        # Test checksum calculation
        checksum = data_integrity_agent._calculate_checksum(test_data)
        assert isinstance(checksum, str)
        assert len(checksum) == 16  # Expected length
    
    def test_tampering_detection(self):
        """Test tampering detection algorithms"""
        # Test with suspicious timestamps
        timestamps = ['2024-01-01T10:00:00', '2024-01-01T09:30:00']  # Out of order
        has_anomalies = data_integrity_agent._has_timestamp_anomalies(timestamps)
        assert has_anomalies == True
        
        # Test with normal timestamps
        normal_timestamps = ['2024-01-01T10:00:00', '2024-01-01T10:01:00']
        has_anomalies = data_integrity_agent._has_timestamp_anomalies(normal_timestamps)
        assert has_anomalies == False

class TestThreatDetectionAgent:
    """Test cases for Threat Detection Agent"""
    
    @patch('agents.threat_detection_agent.KafkaConsumer')
    @patch('agents.threat_detection_agent.ChatGroq')
    def test_threat_detection_success(self, mock_llm, mock_consumer):
        """Test successful threat detection"""
        # Mock Kafka messages
        mock_messages = [
            Mock(value={
                'event_type': 'security_alert',
                'severity': 'high',
                'timestamp': datetime.now().isoformat(),
                'source_ip': '192.168.1.100'
            })
        ]
        
        mock_consumer_instance = Mock()
        mock_consumer_instance.__iter__ = Mock(return_value=iter(mock_messages))
        mock_consumer.return_value = mock_consumer_instance
        
        # Mock LLM response
        mock_llm_response = Mock()
        mock_llm_response.content = "High severity malware threat detected with high confidence"
        mock_llm.return_value.invoke.return_value = mock_llm_response
        
        # Test detection
        result = threat_detection_agent.detect_threats()
        
        assert result['status'] == 'detection_complete'
        assert 'detected_threats' in result
        assert 'alert_level' in result
    
    def test_threat_pattern_analysis(self):
        """Test threat pattern analysis"""
        # Test with high severity events
        test_events = [
            {'severity': 'critical', 'event_type': 'security_alert'},
            {'severity': 'high', 'event_type': 'security_alert'},
            {'severity': 'high', 'event_type': 'threat_detection'}
        ]
        
        # Create test state
        state = ThreatDetectionState(security_events=test_events)
        result_state = threat_detection_agent._analyze_patterns(state)
        
        patterns = result_state.threat_patterns
        assert patterns['total_events'] == 3
        assert patterns['severity_distribution']['critical'] == 1
        assert patterns['severity_distribution']['high'] == 2

class TestIntrusionResponseAgent:
    """Test cases for Intrusion Response Agent"""
    
    @patch('agents.intrusion_response_agent.KafkaConsumer')
    @patch('agents.intrusion_response_agent.ChatGroq')
    def test_intrusion_response_success(self, mock_llm, mock_consumer):
        """Test successful intrusion response"""
        # Mock network events
        mock_messages = [
            Mock(value={
                'event_type': 'network_traffic',
                'source_ip': '192.168.1.100',
                'severity': 'high',
                'timestamp': datetime.now().isoformat()
            })
        ]
        
        mock_consumer_instance = Mock()
        mock_consumer_instance.__iter__ = Mock(return_value=iter(mock_messages))
        mock_consumer.return_value = mock_consumer_instance
        
        # Mock LLM response
        mock_llm_response = Mock()
        mock_llm_response.content = "Critical threat level requiring immediate response"
        mock_llm.return_value.invoke.return_value = mock_llm_response
        
        # Test response
        result = intrusion_response_agent.respond_to_intrusion()
        
        assert result['status'] == 'response_complete'
        assert 'threat_level' in result
        assert 'response_actions' in result
    
    def test_suspicious_ip_identification(self):
        """Test suspicious IP identification logic"""
        # Create test network data with repeated IP
        network_data = []
        for i in range(15):  # Above threshold
            network_data.append({
                'source_ip': '192.168.1.100',
                'severity': 'high' if i < 5 else 'low'
            })
        
        # Test identification
        state = IntrusionResponseState(network_data=network_data)
        result_state = intrusion_response_agent._identify_threats(state)
        
        assert len(result_state.suspicious_ips) > 0
        suspicious_ip = result_state.suspicious_ips[0]
        assert suspicious_ip['ip_address'] == '192.168.1.100'
        assert suspicious_ip['activity_count'] == 15

class TestReportingAgent:
    """Test cases for Reporting Agent"""
    
    @patch('agents.reporting_agent.KafkaConsumer')
    @patch('agents.reporting_agent.KafkaProducer')
    @patch('agents.reporting_agent.ChatGroq')
    def test_report_generation_success(self, mock_llm, mock_producer, mock_consumer):
        """Test successful report generation"""
        # Mock incident data
        mock_messages = [
            Mock(value={
                'event_type': 'security_alert',
                'severity': 'high',
                'timestamp': datetime.now().isoformat()
            })
        ]
        
        mock_consumer_instance = Mock()
        mock_consumer_instance.__iter__ = Mock(return_value=iter(mock_messages))
        mock_consumer.return_value = mock_consumer_instance
        
        # Mock producer
        mock_producer_instance = Mock()
        mock_producer_future = Mock()
        mock_producer_future.get.return_value = None
        mock_producer_instance.send.return_value = mock_producer_future
        mock_producer.return_value = mock_producer_instance
        
        # Mock LLM response
        mock_llm_response = Mock()
        mock_llm_response.content = "Executive Summary: High priority security incidents detected. Recommend immediate investigation."
        mock_llm.return_value.invoke.return_value = mock_llm_response
        
        # Test report generation
        result = reporting_agent.generate_security_report()
        
        assert result['status'] == 'report_complete'
        assert 'executive_summary' in result
        assert 'publication_status' in result
    
    def test_incident_data_analysis(self):
        """Test incident data analysis"""
        # Test data with various severities
        test_incidents = [
            {'severity': 'critical', 'event_type': 'security_alert'},
            {'severity': 'high', 'event_type': 'threat_detection'},
            {'severity': 'medium', 'event_type': 'network_traffic'}
        ]
        
        state = ReportingState(incident_data=test_incidents)
        result_state = reporting_agent._analyze_data(state)
        
        report_content = result_state.report_content
        assert report_content['summary_stats']['total_incidents'] == 3
        assert report_content['critical_incidents'] == 1

class TestCybersecurityGraph:
    """Test cases for Multi-Agent Cybersecurity Graph"""
    
    @patch('graph.cybersecurity_graph.data_integrity_agent')
    @patch('graph.cybersecurity_graph.threat_detection_agent')
    @patch('graph.cybersecurity_graph.intrusion_response_agent')
    @patch('graph.cybersecurity_graph.reporting_agent')
    @patch('graph.cybersecurity_graph.ChatGroq')
    def test_full_cybersecurity_analysis(self, mock_llm, mock_reporting, 
                                       mock_intrusion, mock_threat, mock_integrity):
        """Test full multi-agent cybersecurity analysis"""
        # Mock agent responses
        mock_integrity.validate_data_integrity.return_value = {
            'status': 'validation_complete',
            'validation_status': 'healthy',
            'tampering_detected': False
        }
        
        mock_threat.detect_threats.return_value = {
            'status': 'detection_complete',
            'alert_level': 'medium',
            'detected_threats': []
        }
        
        mock_intrusion.respond_to_intrusion.return_value = {
            'status': 'response_complete',
            'threat_level': 'low',
            'suspicious_ips_count': 0
        }
        
        mock_reporting.generate_security_report.return_value = {
            'status': 'report_complete',
            'publication_status': 'published'
        }
        
        # Mock LLM coordination response
        mock_llm_response = Mock()
        mock_llm_response.content = "Overall security posture is good with low risk level"
        mock_llm.return_value.invoke.return_value = mock_llm_response
        
        # Execute analysis
        result = cybersecurity_graph.execute_cybersecurity_analysis()
        
        assert result['status'] == 'multi_agent_analysis_complete'
        assert result['risk_level'] == 'low'
        assert 'agent_results' in result
        assert 'completion_status' in result
    
    def test_targeted_analysis(self):
        """Test targeted analysis for specific agents"""
        with patch('graph.cybersecurity_graph.data_integrity_agent') as mock_agent:
            mock_agent.validate_data_integrity.return_value = {
                'status': 'validation_complete'
            }
            
            result = cybersecurity_graph.execute_targeted_analysis('integrity')
            
            assert result['status'] == 'targeted_analysis_complete'
            assert result['focus_area'] == 'integrity'

class TestKafkaIntegration:
    """Test cases for Kafka Producer and Consumer"""
    
    @patch('kafka.kafka_producer.KafkaProducer')
    def test_security_alert_publishing(self, mock_producer):
        """Test publishing security alerts"""
        mock_producer_instance = Mock()
        mock_future = Mock()
        mock_future.get.return_value = Mock(partition=0)
        mock_producer_instance.send.return_value = mock_future
        mock_producer.return_value = mock_producer_instance
        
        # Test alert publishing
        result = cybersecurity_producer.publish_security_alert(
            {'alert_type': 'test'}, 
            'high'
        )
        
        assert result == True
        mock_producer_instance.send.assert_called_once()
    
    @patch('kafka.kafka_producer.KafkaProducer')
    def test_batch_event_publishing(self, mock_producer):
        """Test batch event publishing"""
        mock_producer_instance = Mock()
        mock_future = Mock()
        mock_future.get.return_value = Mock(partition=0)
        mock_producer_instance.send.return_value = mock_future
        mock_producer.return_value = mock_producer_instance
        
        # Test batch publishing
        events = [
            {
                'event_type': 'security_alert',
                'data': {'test': 'data'},
                'severity': 'medium'
            },
            {
                'event_type': 'threat_detection',
                'threat_type': 'malware',
                'confidence': 'high'
            }
        ]
        
        results = cybersecurity_producer.publish_batch_events(events)
        
        assert results['success'] == 2
        assert results['failed'] == 0

class TestFastAPIEndpoints:
    """Test cases for FastAPI endpoints"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert data['status'] == 'healthy'
    
    @patch('main.cybersecurity_graph')
    def test_security_analysis_endpoint(self, mock_graph):
        """Test security analysis endpoint"""
        mock_graph.execute_cybersecurity_analysis.return_value = {
            'status': 'multi_agent_analysis_complete',
            'risk_level': 'low'
        }
        
        response = client.post("/analyze/security", json={
            "analysis_type": "full",
            "time_window": 300,
            "priority": "normal"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert 'result' in data
        assert 'analysis_id' in data
    
    @patch('main.threat_detection_agent')
    def test_threat_detection_endpoint(self, mock_agent):
        """Test threat detection endpoint"""
        mock_agent.detect_threats.return_value = {
            'status': 'detection_complete',
            'alert_level': 'medium'
        }
        
        response = client.post("/analyze/threats")
        
        assert response.status_code == 200
        data = response.json()
        assert 'detection_id' in data
        assert 'result' in data
    
    @patch('main.cybersecurity_producer')
    def test_threat_alert_publishing_endpoint(self, mock_producer):
        """Test threat alert publishing endpoint"""
        mock_producer.publish_threat_detection.return_value = True
        
        response = client.post("/events/threat", json={
            "threat_type": "malware",
            "confidence": "high",
            "source_ip": "192.168.1.100"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['published'] == True
        assert 'event_id' in data
    
    def test_agents_status_endpoint(self):
        """Test agents status endpoint"""
        response = client.get("/status/agents")
        assert response.status_code == 200
        data = response.json()
        assert 'agents' in data
        assert data['agents']['data_integrity'] == 'active'

class TestErrorHandling:
    """Test cases for error handling and edge cases"""
    
    @patch('agents.data_integrity_agent.KafkaConsumer')
    def test_kafka_connection_failure(self, mock_consumer):
        """Test handling of Kafka connection failures"""
        mock_consumer.side_effect = Exception("Kafka connection failed")
        
        result = data_integrity_agent.validate_data_integrity()
        
        assert 'error' in result or result['status'] == 'validation_failed'
    
    @patch('main.cybersecurity_graph')
    def test_analysis_failure_handling(self, mock_graph):
        """Test handling of analysis failures"""
        mock_graph.execute_cybersecurity_analysis.side_effect = Exception("Analysis failed")
        
        response = client.post("/analyze/security", json={
            "analysis_type": "full"
        })
        
        assert response.status_code == 500
    
    def test_invalid_request_data(self):
        """Test handling of invalid request data"""
        response = client.post("/events/threat", json={
            "invalid_field": "test"
        })
        
        assert response.status_code == 422  # Validation error

# Pytest configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
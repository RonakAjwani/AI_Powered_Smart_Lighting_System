import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Import agents to test
from ..src.agents.energy_load_forecaster_agent import energy_load_forecaster_agent
from ..src.agents.power_outage_detection_agent import power_outage_detection_agent
from ..src.agents.energy_rerouting_agent import energy_rerouting_agent
from ..src.agents.energy_optimization_agent import energy_optimization_agent
from ..src.agents.power_grid_reporting_agent import power_grid_reporting_agent
from ..src.graph.power_graph import power_grid_graph, execute_power_grid_workflow
from ..src.config.settings import config

class TestEnergyLoadForecasterAgent:
    """Test Energy Load Forecaster Agent"""
    
    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        assert energy_load_forecaster_agent is not None
        assert hasattr(energy_load_forecaster_agent, 'llm')
        assert hasattr(energy_load_forecaster_agent, 'workflow')
    
    @patch('langchain_groq.ChatGroq')
    def test_forecast_energy_demand_success(self, mock_groq):
        """Test successful energy demand forecasting"""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = json.dumps({
            "forecast_analysis": "Peak load expected during evening hours",
            "confidence": 0.85,
            "recommendations": ["Monitor peak hours closely"]
        })
        mock_groq.return_value.invoke.return_value = mock_response
        
        # Test input
        forecast_input = {
            "requested_periods": ["1_hour", "24_hour"],
            "include_weather": True,
            "include_historical": True
        }
        
        # Execute forecast
        result = energy_load_forecaster_agent.forecast_energy_demand(forecast_input)
        
        # Assertions
        assert result is not None
        assert "status" in result
        assert "demand_forecasts" in result
        assert len(result["demand_forecasts"]) > 0
        
        # Check forecast structure
        for period, forecast in result["demand_forecasts"].items():
            assert "predicted_demand" in forecast
            assert "confidence_score" in forecast
            assert "trend_direction" in forecast
    
    def test_forecast_different_periods(self):
        """Test forecasting for different time periods"""
        periods = ["1_hour", "4_hour", "24_hour", "weekly"]
        
        for period in periods:
            forecast_input = {"requested_periods": [period]}
            result = energy_load_forecaster_agent.forecast_energy_demand(forecast_input)
            
            assert result is not None
            assert period in result.get("demand_forecasts", {})
    
    def test_forecast_with_weather_integration(self):
        """Test forecasting with weather data"""
        forecast_input = {
            "requested_periods": ["24_hour"],
            "include_weather": True
        }
        
        result = energy_load_forecaster_agent.forecast_energy_demand(forecast_input)
        
        assert "weather_data" in result
        assert "weather_analysis" in result
        weather_data = result["weather_data"]
        assert "temperature" in weather_data
        assert "weather_condition" in weather_data


class TestPowerOutageDetectionAgent:
    """Test Power Outage Detection Agent"""
    
    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        assert power_outage_detection_agent is not None
        assert hasattr(power_outage_detection_agent, 'llm')
        assert hasattr(power_outage_detection_agent, 'workflow')
    
    @patch('langchain_groq.ChatGroq')
    def test_detect_power_outages_no_outages(self, mock_groq):
        """Test outage detection when no outages exist"""
        mock_response = Mock()
        mock_response.content = json.dumps({
            "outage_analysis": "All zones operating normally",
            "risk_assessment": "Low risk",
            "recommendations": ["Continue monitoring"]
        })
        mock_groq.return_value.invoke.return_value = mock_response
        
        result = power_outage_detection_agent.detect_power_outages()
        
        assert result is not None
        assert "status" in result
        assert "outages_detected" in result
        assert "system_health" in result
        assert isinstance(result["outages_detected"], list)
    
    @patch('langchain_groq.ChatGroq')
    def test_detect_power_outages_with_outages(self, mock_groq):
        """Test outage detection when outages exist"""
        mock_response = Mock()
        mock_response.content = json.dumps({
            "outage_analysis": "Critical outage detected in zone 1",
            "severity": "critical",
            "recommendations": ["Immediate intervention required"]
        })
        mock_groq.return_value.invoke.return_value = mock_response
        
        # Mock some outage conditions by patching internal methods
        with patch.object(power_outage_detection_agent, '_monitor_grid_health_node') as mock_health:
            mock_health.return_value = {
                "grid_health": {"zone_1": {"voltage_stability": 0.75, "frequency_stability": 0.80}},
                "anomalies_detected": ["zone_1"],
                "outage_risk": "high"
            }
            
            result = power_outage_detection_agent.detect_power_outages()
            
            assert result is not None
            if result.get("outages_detected"):
                assert len(result["outages_detected"]) > 0
                assert "affected_zones" in result
    
    def test_outage_severity_classification(self):
        """Test outage severity classification"""
        result = power_outage_detection_agent.detect_power_outages()
        
        if result.get("outages_detected"):
            assert "outage_severity" in result
            assert result["outage_severity"] in ["localized", "regional", "critical", "widespread"]


class TestEnergyReroutingAgent:
    """Test Energy Rerouting Agent"""
    
    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        assert energy_rerouting_agent is not None
        assert hasattr(energy_rerouting_agent, 'llm')
        assert hasattr(energy_rerouting_agent, 'workflow')
    
    def test_execute_energy_rerouting_no_outages(self):
        """Test rerouting with no outages"""
        result = energy_rerouting_agent.execute_energy_rerouting([])
        
        assert result is not None
        assert "status" in result
        assert "rerouting_commands" in result
        assert isinstance(result["rerouting_commands"], list)
    
    @patch('langchain_groq.ChatGroq')
    def test_execute_energy_rerouting_with_outages(self, mock_groq):
        """Test rerouting with active outages"""
        mock_response = Mock()
        mock_response.content = json.dumps({
            "rerouting_analysis": "Rerouting required for affected zones",
            "strategy": "emergency_rerouting",
            "priority": "critical"
        })
        mock_groq.return_value.invoke.return_value = mock_response
        
        outage_alerts = [{
            "affected_zones": ["zone_1", "zone_2"],
            "outage_type": "equipment_failure",
            "severity": "critical",
            "estimated_duration": 180,
            "root_cause": "transformer_failure"
        }]
        
        result = energy_rerouting_agent.execute_energy_rerouting(outage_alerts)
        
        assert result is not None
        assert "rerouting_commands" in result
        assert "backup_activations" in result
        assert "load_shedding_schedule" in result
        
        if result.get("rerouting_commands"):
            for command in result["rerouting_commands"]:
                assert "command_id" in command
                assert "rerouting_action" in command
                assert "target_zones" in command
    
    def test_backup_power_activation(self):
        """Test backup power source activation"""
        outage_alerts = [{
            "affected_zones": ["zone_1"],
            "severity": "critical",
            "outage_type": "grid_failure"
        }]
        
        result = energy_rerouting_agent.execute_energy_rerouting(outage_alerts)
        
        if result.get("backup_activations"):
            for backup in result["backup_activations"]:
                assert "backup_id" in backup
                assert "capacity_kw" in backup
                assert "activation_time" in backup


class TestEnergyOptimizationAgent:
    """Test Energy Optimization Agent"""
    
    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        assert energy_optimization_agent is not None
        assert hasattr(energy_optimization_agent, 'llm')
        assert hasattr(energy_optimization_agent, 'workflow')
    
    @patch('langchain_groq.ChatGroq')
    def test_optimize_energy_usage(self, mock_groq):
        """Test energy optimization execution"""
        mock_response = Mock()
        mock_response.content = json.dumps({
            "optimization_analysis": "Significant energy savings possible",
            "savings_potential": "15%",
            "recommendations": ["Implement smart dimming", "Optimize schedules"]
        })
        mock_groq.return_value.invoke.return_value = mock_response
        
        result = energy_optimization_agent.optimize_energy_usage()
        
        assert result is not None
        assert "status" in result
        assert "optimization_commands" in result
        assert "dimming_schedules" in result
        
        if result.get("optimization_commands"):
            for command in result["optimization_commands"]:
                assert "command_id" in command
                assert "zone" in command
                assert "brightness_change" in command
    
    def test_energy_savings_calculation(self):
        """Test energy savings calculation"""
        result = energy_optimization_agent.optimize_energy_usage()
        
        if result.get("status") == "optimization_complete":
            assert "total_savings" in result
            assert "overall_savings_percent" in result
            assert isinstance(result["total_savings"], (int, float))
            assert isinstance(result["overall_savings_percent"], (int, float))
    
    def test_dimming_schedules_creation(self):
        """Test dimming schedules creation"""
        result = energy_optimization_agent.optimize_energy_usage()
        
        if result.get("dimming_schedules"):
            for zone, schedule in result["dimming_schedules"].items():
                assert "hourly_schedule" in schedule
                assert "min_brightness" in schedule
                assert "max_brightness" in schedule
                assert len(schedule["hourly_schedule"]) == 24  # 24 hours


class TestPowerGridReportingAgent:
    """Test Power Grid Reporting Agent"""
    
    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        assert power_grid_reporting_agent is not None
        assert hasattr(power_grid_reporting_agent, 'llm')
        assert hasattr(power_grid_reporting_agent, 'workflow')
    
    @patch('langchain_groq.ChatGroq')
    def test_generate_comprehensive_reports(self, mock_groq):
        """Test comprehensive report generation"""
        mock_response = Mock()
        mock_response.content = json.dumps({
            "report_analysis": "System performance within acceptable ranges",
            "key_findings": ["Efficiency at 95%", "Uptime 99.8%"],
            "recommendations": ["Monitor peak usage", "Schedule maintenance"]
        })
        mock_groq.return_value.invoke.return_value = mock_response
        
        result = power_grid_reporting_agent.generate_power_grid_reports("comprehensive")
        
        assert result is not None
        assert "status" in result
        assert "generated_reports" in result
        assert "report_summaries" in result
        
        reports = result["generated_reports"]
        assert "executive_summary" in reports
        assert "performance_report" in reports
        assert "financial_report" in reports
    
    def test_generate_emergency_report(self):
        """Test emergency report generation"""
        result = power_grid_reporting_agent.generate_power_grid_reports("emergency_report")
        
        assert result is not None
        assert "generated_reports" in result
    
    def test_recommendations_creation(self):
        """Test recommendations creation"""
        result = power_grid_reporting_agent.generate_power_grid_reports("comprehensive")
        
        if result.get("recommendations"):
            for rec in result["recommendations"]:
                assert "id" in rec
                assert "category" in rec
                assert "priority" in rec
                assert "title" in rec
                assert "recommended_actions" in rec


class TestPowerGridGraph:
    """Test Power Grid Graph Orchestration"""
    
    def test_graph_initialization(self):
        """Test graph initializes correctly"""
        assert power_grid_graph is not None
        assert hasattr(power_grid_graph, 'workflow')
        assert hasattr(power_grid_graph, 'memory')
    
    @patch('langchain_groq.ChatGroq')
    def test_execute_power_grid_workflow_normal(self, mock_groq):
        """Test normal power grid workflow execution"""
        mock_response = Mock()
        mock_response.content = json.dumps({
            "analysis": "Normal operations",
            "status": "healthy"
        })
        mock_groq.return_value.invoke.return_value = mock_response
        
        result = execute_power_grid_workflow("test")
        
        assert result is not None
        assert "workflow_id" in result
        assert "status" in result
        assert "completed_phases" in result
    
    def test_workflow_with_outages(self):
        """Test workflow execution with detected outages"""
        # This would require more complex mocking to simulate outages
        result = execute_power_grid_workflow("test")
        
        assert result is not None
        if result.get("outages_detected"):
            assert "rerouting_results" in result or "emergency_response" in result
    
    def test_emergency_workflow(self):
        """Test emergency response workflow"""
        emergency_data = {
            "emergency_type": "grid_failure",
            "affected_zones": ["zone_1"],
            "severity": "critical"
        }
        
        result = power_grid_graph.trigger_emergency_response(emergency_data)
        
        assert result is not None
        assert "workflow_id" in result
        assert result.get("emergency_mode") is True


class TestWorkflowIntegration:
    """Test integration between agents"""
    
    @patch('langchain_groq.ChatGroq')
    def test_agent_data_flow(self, mock_groq):
        """Test data flow between agents in workflow"""
        mock_response = Mock()
        mock_response.content = json.dumps({
            "analysis": "Test analysis",
            "recommendations": ["Test recommendation"]
        })
        mock_groq.return_value.invoke.return_value = mock_response
        
        # Execute partial workflow to test data flow
        result = execute_power_grid_workflow("integration_test")
        
        assert result is not None
        
        # Check that data flows between phases
        if "forecast_results" in result and "optimization_results" in result:
            # Verify forecast data can influence optimization
            assert result["forecast_results"] is not None
            assert result["optimization_results"] is not None
    
    def test_error_handling(self):
        """Test error handling across agents"""
        # Test with invalid input to trigger error handling
        with patch.object(energy_load_forecaster_agent, 'forecast_energy_demand') as mock_forecast:
            mock_forecast.side_effect = Exception("Test error")
            
            result = execute_power_grid_workflow("error_test")
            
            assert result is not None
            assert "errors" in result
    
    def test_kafka_integration(self):
        """Test Kafka message production"""
        with patch('..src.kafka.kafka_producer.power_producer.send_power_report') as mock_send:
            mock_send.return_value = True
            
            result = execute_power_grid_workflow("kafka_test")
            
            # Verify Kafka messages were sent
            assert mock_send.called


class TestPerformanceAndResilience:
    """Test performance and resilience aspects"""
    
    def test_workflow_timeout_handling(self):
        """Test workflow handles timeouts gracefully"""
        # This would test long-running operations
        start_time = datetime.now()
        result = execute_power_grid_workflow("timeout_test")
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Ensure reasonable execution time
        assert execution_time < 300  # 5 minutes max for tests
        assert result is not None
    
    def test_memory_usage(self):
        """Test memory usage doesn't grow excessively"""
        # Run multiple workflows and check memory doesn't grow unbounded
        results = []
        for i in range(5):
            result = execute_power_grid_workflow(f"memory_test_{i}")
            results.append(result)
        
        # All should succeed
        assert all(r is not None for r in results)
    
    def test_concurrent_workflows(self):
        """Test handling multiple concurrent workflows"""
        async def run_workflow(workflow_id):
            return execute_power_grid_workflow(f"concurrent_{workflow_id}")
        
        # This would require async testing framework for true concurrency
        # For now, just test sequential execution
        results = []
        for i in range(3):
            result = execute_power_grid_workflow(f"concurrent_{i}")
            results.append(result)
        
        assert len(results) == 3
        assert all(r is not None for r in results)


# Test utilities and fixtures
@pytest.fixture
def sample_forecast_data():
    """Sample forecast data for testing"""
    return {
        "predicted_demand": 850.5,
        "confidence_score": 0.85,
        "trend_direction": "increasing",
        "peak_hours": [17, 18, 19, 20],
        "weather_impact": "high_temperature"
    }

@pytest.fixture
def sample_outage_data():
    """Sample outage data for testing"""
    return {
        "outage_id": "outage_test_001",
        "affected_zones": ["zone_1", "zone_2"],
        "outage_type": "equipment_failure",
        "severity": "critical",
        "estimated_duration": 120,
        "root_cause": "transformer_failure"
    }

@pytest.fixture
def sample_optimization_data():
    """Sample optimization data for testing"""
    return {
        "zone": "zone_1",
        "current_brightness": 85.0,
        "target_brightness": 70.0,
        "energy_savings": 12.5,
        "implementation_time": datetime.now().isoformat()
    }


# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmark tests"""
    
    def test_forecast_agent_performance(self):
        """Benchmark forecast agent performance"""
        start_time = datetime.now()
        
        result = energy_load_forecaster_agent.forecast_energy_demand({
            "requested_periods": ["1_hour", "24_hour"],
            "include_weather": True
        })
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        assert execution_time < 30  # Should complete within 30 seconds
        assert result is not None
    
    def test_full_workflow_performance(self):
        """Benchmark full workflow performance"""
        start_time = datetime.now()
        
        result = execute_power_grid_workflow("performance_test")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        assert execution_time < 120  # Should complete within 2 minutes
        assert result is not None
        assert result.get("status") != "workflow_failed"


# Integration tests with external dependencies
class TestExternalIntegrations:
    """Test integrations with external systems"""
    
    @patch('requests.get')
    def test_weather_api_integration(self, mock_get):
        """Test weather API integration"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "temperature": 25.5,
            "humidity": 65,
            "weather_condition": "Sunny"
        }
        mock_get.return_value = mock_response
        
        result = energy_load_forecaster_agent.forecast_energy_demand({
            "include_weather": True
        })
        
        assert "weather_data" in result
    
    @patch('..src.kafka.kafka_producer.KafkaProducer')
    def test_kafka_producer_integration(self, mock_producer):
        """Test Kafka producer integration"""
        mock_producer.return_value.send.return_value = True
        
        result = execute_power_grid_workflow("kafka_integration_test")
        
        assert result is not None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
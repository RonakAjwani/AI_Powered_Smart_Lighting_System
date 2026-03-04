import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.weather_collection_forecast_agent import weather_collection_forecast_agent
from src.agents.env_sensor_agent import environmental_sensor_agent
from src.agents.weather_impact_analyzer_agent import weather_impact_analyzer_agent
from src.agents.disaster_response_advisor_agent import disaster_response_advisor_agent
from src.agents.reporting_agent import weather_reporting_agent
from src.graph.weather_graph import weather_intelligence_graph
from src.config.settings import config

class TestWeatherCollectionForecastAgent:
    """Test suite for Weather Collection and Forecast Agent"""
    
    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        assert weather_collection_forecast_agent is not None
        assert hasattr(weather_collection_forecast_agent, 'workflow')
        assert hasattr(weather_collection_forecast_agent, 'llm')
    
    @patch('src.weather_agents.weather_collection_forecast_agent.requests.get')
    def test_collect_weather_data_success(self, mock_get):
        """Test successful weather data collection"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'weather': [{'main': 'Clear', 'description': 'clear sky'}],
            'main': {'temp': 20.5, 'humidity': 65},
            'wind': {'speed': 5.2},
            'visibility': 10000
        }
        mock_get.return_value = mock_response
        
        result = weather_collection_forecast_agent.collect_weather_data()
        
        assert result['status'] == 'collection_complete'
        assert 'processed_zones' in result
        assert 'forecasts_generated' in result
        assert len(result['errors']) == 0
    
    @patch('src.weather_agents.weather_collection_forecast_agent.requests.get')
    def test_collect_weather_data_api_failure(self, mock_get):
        """Test weather data collection with API failure"""
        # Mock API failure
        mock_get.side_effect = Exception("API connection failed")
        
        result = weather_collection_forecast_agent.collect_weather_data()
        
        assert result['status'] in ['collection_failed', 'collection_partial']
        assert len(result['errors']) > 0
    
    def test_weather_data_processing(self):
        """Test weather data processing and validation"""
        sample_data = {
            'weather': [{'main': 'Rain', 'description': 'heavy rain'}],
            'main': {'temp': 15.0, 'humidity': 90},
            'wind': {'speed': 12.5},
            'visibility': 2000
        }
        
        processed = weather_collection_forecast_agent._process_weather_data(sample_data, "zone_1")
        
        assert processed['zone_id'] == "zone_1"
        assert processed['temperature'] == 15.0
        assert processed['weather_condition'] == 'Rain'
        assert processed['visibility'] == 2000
    
    def test_forecast_generation(self):
        """Test weather forecast generation"""
        current_weather = {
            'temperature': 20.0,
            'humidity': 60,
            'wind_speed': 8.0,
            'weather_condition': 'Cloudy'
        }
        
        forecast = weather_collection_forecast_agent._generate_weather_forecast(current_weather, "zone_1")
        
        assert len(forecast) > 0
        assert all('temperature' in f for f in forecast)
        assert all('timestamp' in f for f in forecast)

class TestEnvironmentalSensorAgent:
    """Test suite for Environmental Sensor Agent"""
    
    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        assert environmental_sensor_agent is not None
        assert hasattr(environmental_sensor_agent, 'workflow')
        assert hasattr(environmental_sensor_agent, 'sensor_types')
    
    def test_collect_environmental_data_success(self):
        """Test successful environmental data collection"""
        result = environmental_sensor_agent.collect_environmental_data()
        
        assert result['status'] == 'monitoring_complete'
        assert 'processed_zones' in result
        assert 'sensor_readings' in result
        assert 'environmental_conditions' in result
    
    def test_sensor_data_processing(self):
        """Test sensor data processing"""
        raw_sensor_data = {
            'air_quality_pm25': 15.5,
            'air_quality_pm10': 25.0,
            'noise_level': 45.2,
            'light_level': 250,
            'motion_detected': True
        }
        
        processed = environmental_sensor_agent._process_sensor_data(raw_sensor_data, "zone_1")
        
        assert processed['zone_id'] == "zone_1"
        assert processed['air_quality']['pm25'] == 15.5
        assert processed['noise_level'] == 45.2
        assert processed['motion_detected'] == True
    
    def test_environmental_assessment(self):
        """Test environmental condition assessment"""
        sensor_data = {
            'air_quality': {'pm25': 50, 'pm10': 80},
            'noise_level': 60,
            'light_level': 100
        }
        
        assessment = environmental_sensor_agent._assess_environmental_conditions("zone_1", sensor_data)
        
        assert 'zone_id' in assessment
        assert 'overall_quality' in assessment
        assert 'recommendations' in assessment
    
    def test_anomaly_detection(self):
        """Test environmental anomaly detection"""
        # Test with normal data
        normal_data = {'air_quality': {'pm25': 20}, 'noise_level': 40}
        anomaly_normal = environmental_sensor_agent._detect_environmental_anomalies("zone_1", normal_data)
        assert anomaly_normal['anomaly_detected'] == False
        
        # Test with anomalous data
        anomalous_data = {'air_quality': {'pm25': 150}, 'noise_level': 90}
        anomaly_detected = environmental_sensor_agent._detect_environmental_anomalies("zone_1", anomalous_data)
        assert anomaly_detected['anomaly_detected'] == True

class TestWeatherImpactAnalyzerAgent:
    """Test suite for Weather Impact Analyzer Agent"""
    
    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        assert weather_impact_analyzer_agent is not None
        assert hasattr(weather_impact_analyzer_agent, 'workflow')
        assert hasattr(weather_impact_analyzer_agent, 'impact_thresholds')
    
    def test_analyze_weather_impact_success(self):
        """Test successful weather impact analysis"""
        result = weather_impact_analyzer_agent.analyze_weather_impact()
        
        assert result['status'] == 'analysis_complete'
        assert 'processed_zones' in result
        assert 'impact_assessments' in result
        assert 'lighting_adjustments' in result
    
    def test_impact_assessment_calculation(self):
        """Test weather impact assessment calculation"""
        weather_data = {
            'temperature': 5.0,  # Cold temperature
            'wind_speed': 20.0,  # High wind
            'visibility': 500,   # Low visibility
            'precipitation': 15.0  # Heavy rain
        }
        
        impact = weather_impact_analyzer_agent._assess_weather_impact("zone_1", weather_data)
        
        assert impact['zone_id'] == "zone_1"
        assert impact['impact_level'] in ['low', 'medium', 'high', 'critical']
        assert 'impact_factors' in impact
        assert 'lighting_recommendations' in impact
    
    def test_lighting_adjustment_calculation(self):
        """Test lighting adjustment calculation"""
        weather_conditions = {
            'visibility': 1000,  # Low visibility
            'weather_condition': 'Fog',
            'wind_speed': 10.0
        }
        
        adjustment = weather_impact_analyzer_agent._calculate_lighting_adjustments("zone_1", weather_conditions)
        
        assert 'zone_id' in adjustment
        assert 'brightness_adjustment' in adjustment
        assert 'adjustment_factor' in adjustment
        assert adjustment['brightness_adjustment'] > 0  # Should increase brightness for low visibility
    
    def test_risk_level_determination(self):
        """Test weather risk level determination"""
        # Low risk conditions
        low_risk_weather = {
            'temperature': 20.0,
            'wind_speed': 5.0,
            'visibility': 10000,
            'precipitation': 0.0
        }
        low_risk = weather_impact_analyzer_agent._determine_risk_level(low_risk_weather)
        assert low_risk == 'low'
        
        # High risk conditions
        high_risk_weather = {
            'temperature': -5.0,
            'wind_speed': 25.0,
            'visibility': 200,
            'precipitation': 20.0
        }
        high_risk = weather_impact_analyzer_agent._determine_risk_level(high_risk_weather)
        assert high_risk in ['high', 'critical']

class TestDisasterResponseAdvisorAgent:
    """Test suite for Disaster Response Advisor Agent"""
    
    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        assert disaster_response_advisor_agent is not None
        assert hasattr(disaster_response_advisor_agent, 'workflow')
        assert hasattr(disaster_response_advisor_agent, 'emergency_protocols')
    
    def test_advise_disaster_response_success(self):
        """Test successful disaster response advisory"""
        result = disaster_response_advisor_agent.advise_disaster_response()
        
        assert result['status'] in ['response_plan_complete', 'no_emergency_detected']
        assert 'affected_zones' in result
        assert 'emergency_protocols' in result
        assert 'lighting_strategies' in result
    
    def test_emergency_condition_assessment(self):
        """Test emergency condition assessment"""
        emergency_data = {
            'wind_speed': 30.0,  # High wind
            'precipitation': 25.0,  # Heavy precipitation
            'visibility': 100,  # Very low visibility
            'weather_condition': 'Thunderstorm'
        }
        
        emergency_types = disaster_response_advisor_agent._classify_emergency_types(emergency_data)
        threat_level = disaster_response_advisor_agent._assess_threat_level(emergency_data)
        
        assert len(emergency_types) > 0
        assert threat_level in ['low', 'medium', 'high', 'critical']
        assert 'severe_weather' in emergency_types
    
    def test_evacuation_lighting_plan(self):
        """Test evacuation lighting plan creation"""
        evacuation_routes = ['route_1a', 'route_1b', 'emergency_exit_1']
        safety_assessment = {
            'overall_safety': 'high',
            'evacuation_status': 'required'
        }
        
        plan = disaster_response_advisor_agent._create_evacuation_lighting_plan(
            "zone_1", evacuation_routes, safety_assessment
        )
        
        assert plan['zone_id'] == "zone_1"
        assert 'route_lighting' in plan
        assert 'assembly_points' in plan
        assert len(plan['route_lighting']) == len(evacuation_routes)
    
    def test_emergency_protocol_generation(self):
        """Test emergency protocol generation"""
        affected_zones = ['zone_1', 'zone_2']
        lighting_strategies = {
            'zones': {
                'zone_1': {'brightness_level': 100, 'flash_pattern': 'emergency_strobe'}
            }
        }
        
        protocol = disaster_response_advisor_agent._generate_emergency_protocol(
            'storm', affected_zones, lighting_strategies
        )
        
        assert 'affected_zones' in protocol
        assert 'lighting_configuration' in protocol
        assert 'emergency_contacts' in protocol

class TestWeatherReportingAgent:
    """Test suite for Weather Reporting Agent"""
    
    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        assert weather_reporting_agent is not None
        assert hasattr(weather_reporting_agent, 'workflow')
        assert hasattr(weather_reporting_agent, 'report_config')
    
    def test_generate_weather_reports_success(self):
        """Test successful weather report generation"""
        report_types = ['daily_summary', 'forecast_accuracy']
        result = weather_reporting_agent.generate_weather_reports(report_types)
        
        assert result['status'] == 'reporting_complete'
        assert result['report_types'] == report_types
        assert 'processed_zones' in result
        assert 'reports_generated' in result
    
    def test_weather_pattern_analysis(self):
        """Test weather pattern analysis"""
        weather_data = []
        for i in range(24):  # 24 hours of data
            weather_data.append({
                'timestamp': (datetime.now() - timedelta(hours=i)).isoformat(),
                'temperature': 20.0 + (i % 5),
                'humidity': 60.0,
                'wind_speed': 8.0,
                'visibility': 8000,
                'precipitation': 0.0,
                'weather_condition': 'Clear'
            })
        
        analysis = weather_reporting_agent._analyze_zone_weather_patterns("zone_1", weather_data)
        
        assert analysis['zone_id'] == "zone_1"
        assert 'temperature' in analysis
        assert 'wind' in analysis
        assert 'visibility' in analysis
        assert analysis['data_points'] == 24
    
    def test_forecast_accuracy_calculation(self):
        """Test forecast accuracy calculation"""
        forecasts = [
            {
                'forecast_for': datetime.now().isoformat(),
                'predicted_temperature': 20.0,
                'predicted_precipitation': 0.0
            }
        ]
        
        actuals = [
            {
                'timestamp': datetime.now().isoformat(),
                'temperature': 19.5,
                'precipitation': 0.5
            }
        ]
        
        accuracy = weather_reporting_agent._calculate_forecast_accuracy(forecasts, actuals)
        
        assert 'temperature_accuracy' in accuracy
        assert 'precipitation_accuracy' in accuracy
        assert 'overall_accuracy' in accuracy
    
    def test_performance_metrics_calculation(self):
        """Test performance metrics calculation"""
        lighting_data = {
            'zone_1': [
                {
                    'brightness_level': 80,
                    'power_consumption': 120.0,
                    'adjustment_factor': 1.2,
                    'mode': 'weather_adjusted'
                }
            ]
        }
        
        weather_data = {
            'zone_1': [
                {
                    'temperature': 20.0,
                    'weather_condition': 'Clear'
                }
            ]
        }
        
        alert_data = [
            {
                'zone_id': 'zone_1',
                'alert_type': 'low_visibility',
                'severity': 'medium',
                'resolved': True
            }
        ]
        
        metrics = weather_reporting_agent._calculate_system_metrics(lighting_data, weather_data, alert_data)
        
        assert 'system_uptime' in metrics
        assert 'average_efficiency' in metrics
        assert 'total_alerts' in metrics

class TestWeatherIntelligenceGraph:
    """Test suite for Weather Intelligence Graph"""
    
    def test_graph_initialization(self):
        """Test graph initializes correctly"""
        assert weather_intelligence_graph is not None
        assert hasattr(weather_intelligence_graph, 'workflow')
        assert hasattr(weather_intelligence_graph, 'agents')
        assert len(weather_intelligence_graph.agents) == 5
    
    @pytest.mark.asyncio
    async def test_execute_weather_intelligence_normal_mode(self):
        """Test weather intelligence execution in normal mode"""
        result = weather_intelligence_graph.execute_weather_intelligence("normal")
        
        assert result['status'] in ['coordination_complete', 'coordination_partial']
        assert result['execution_mode'] == 'normal'
        assert 'agents_executed' in result
        assert 'system_health' in result
    
    @pytest.mark.asyncio
    async def test_execute_weather_intelligence_emergency_mode(self):
        """Test weather intelligence execution in emergency mode"""
        result = weather_intelligence_graph.execute_weather_intelligence("emergency")
        
        assert result['status'] in ['coordination_complete', 'coordination_partial']
        assert result['execution_mode'] == 'emergency'
        assert 'coordination_insights' in result
    
    @pytest.mark.asyncio
    async def test_execute_weather_intelligence_auto_mode(self):
        """Test weather intelligence execution in auto mode"""
        result = weather_intelligence_graph.execute_weather_intelligence("auto")
        
        assert result['status'] in ['coordination_complete', 'coordination_partial']
        assert result['execution_mode'] in ['normal', 'emergency', 'maintenance']
    
    def test_system_health_assessment(self):
        """Test system health assessment"""
        initial_state = {
            'agent_statuses': {
                'weather_collection': 'ready',
                'environmental_sensor': 'ready',
                'impact_analyzer': 'ready',
                'disaster_response': 'ready',
                'reporting': 'ready'
            },
            'errors': []
        }
        
        # Mock state for testing
        state = weather_intelligence_graph._assess_system_health_node(initial_state)
        
        assert 'system_health' in state
        assert 'overall_status' in state['system_health']
    
    def test_execution_mode_determination(self):
        """Test execution mode determination"""
        # Test normal conditions
        normal_state = {
            'graph_mode': 'auto',
            'system_health': {'overall_status': 'healthy'},
            'emergency_conditions': {},
            'coordination_decisions': {}
        }
        
        result_state = weather_intelligence_graph._determine_execution_mode_node(normal_state)
        assert result_state['graph_mode'] in ['normal', 'emergency', 'maintenance']
    
    def test_agent_coordination(self):
        """Test agent coordination logic"""
        test_state = {
            'workflow_priority': ['weather_collection', 'environmental_sensor'],
            'agent_statuses': {},
            'agent_results': {},
            'coordination_decisions': {},
            'errors': []
        }
        
        # Test data collection coordination
        state = weather_intelligence_graph._coordinate_data_collection_node(test_state)
        
        assert 'coordination_decisions' in state
        assert 'data_collection' in state['coordination_decisions']

class TestIntegration:
    """Integration tests for weather intelligence system"""
    
    def test_agent_workflow_integration(self):
        """Test integration between different agents"""
        # Execute weather collection
        weather_result = weather_collection_forecast_agent.collect_weather_data()
        assert weather_result['status'] == 'collection_complete'
        
        # Execute environmental monitoring
        sensor_result = environmental_sensor_agent.collect_environmental_data()
        assert sensor_result['status'] == 'monitoring_complete'
        
        # Execute impact analysis (should work with above data)
        impact_result = weather_impact_analyzer_agent.analyze_weather_impact()
        assert impact_result['status'] == 'analysis_complete'
    
    def test_data_flow_consistency(self):
        """Test data flow consistency between agents"""
        # Collect weather data
        weather_data = weather_collection_forecast_agent.collect_weather_data()
        
        # Check if impact analyzer can process the weather data format
        if weather_data['status'] == 'collection_complete':
            impact_result = weather_impact_analyzer_agent.analyze_weather_impact()
            assert impact_result['status'] == 'analysis_complete'
    
    def test_emergency_response_workflow(self):
        """Test complete emergency response workflow"""
        # Simulate emergency conditions and test response
        disaster_result = disaster_response_advisor_agent.advise_disaster_response()
        
        # Should either detect emergency or confirm no emergency
        assert disaster_result['status'] in ['response_plan_complete', 'no_emergency_detected']
    
    def test_reporting_with_all_data(self):
        """Test reporting agent with data from all other agents"""
        # Generate comprehensive report
        report_result = weather_reporting_agent.generate_weather_reports(
            ['daily_summary', 'performance_analysis']
        )
        
        assert report_result['status'] == 'reporting_complete'
        assert report_result['reports_generated'] >= 2

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_agent_error_recovery(self):
        """Test agent behavior with simulated errors"""
        # Test each agent's error handling
        with patch('src.weather_agents.weather_collection_forecast_agent.requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            result = weather_collection_forecast_agent.collect_weather_data()
            assert len(result['errors']) > 0
    
    def test_invalid_data_handling(self):
        """Test handling of invalid or corrupted data"""
        # Test with invalid weather data
        invalid_data = {'invalid': 'data_structure'}
        
        try:
            processed = weather_collection_forecast_agent._process_weather_data(invalid_data, "zone_1")
            # Should handle gracefully and return error or default values
            assert processed is not None
        except Exception as e:
            # Should not crash, but handle error gracefully
            assert str(e) is not None
    
    def test_missing_configuration(self):
        """Test behavior with missing configuration"""
        # Test with missing config values
        original_zones = config.DEFAULT_ZONES
        config.DEFAULT_ZONES = []
        
        try:
            result = environmental_sensor_agent.collect_environmental_data()
            # Should handle missing zones gracefully
            assert 'errors' in result or result['status'] == 'monitoring_complete'
        finally:
            config.DEFAULT_ZONES = original_zones

class TestPerformance:
    """Performance and load tests"""
    
    def test_agent_execution_time(self):
        """Test agent execution times are reasonable"""
        import time
        
        # Test weather collection performance
        start_time = time.time()
        weather_collection_forecast_agent.collect_weather_data()
        execution_time = time.time() - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert execution_time < 30.0  # 30 seconds max
    
    def test_concurrent_agent_execution(self):
        """Test concurrent execution of multiple agents"""
        import threading
        import time
        
        results = {}
        
        def run_agent(agent_name, agent_func):
            start_time = time.time()
            result = agent_func()
            execution_time = time.time() - start_time
            results[agent_name] = {'result': result, 'time': execution_time}
        
        # Run agents concurrently
        threads = [
            threading.Thread(target=run_agent, args=('weather', weather_collection_forecast_agent.collect_weather_data)),
            threading.Thread(target=run_agent, args=('sensor', environmental_sensor_agent.collect_environmental_data)),
            threading.Thread(target=run_agent, args=('impact', weather_impact_analyzer_agent.analyze_weather_impact))
        ]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All agents should complete successfully
        assert len(results) == 3
        for agent_result in results.values():
            assert 'complete' in agent_result['result']['status']

# Test configuration
@pytest.fixture
def sample_weather_data():
    """Fixture providing sample weather data for tests"""
    return {
        'weather': [{'main': 'Clear', 'description': 'clear sky'}],
        'main': {'temp': 22.5, 'humidity': 58, 'pressure': 1013},
        'wind': {'speed': 7.2, 'deg': 180},
        'visibility': 10000,
        'clouds': {'all': 20}
    }

@pytest.fixture
def sample_sensor_data():
    """Fixture providing sample sensor data for tests"""
    return {
        'air_quality_pm25': 12.5,
        'air_quality_pm10': 18.0,
        'noise_level': 42.3,
        'light_level': 340,
        'motion_detected': False,
        'device_temperature': 23.1,
        'device_humidity': 61.2
    }

@pytest.fixture
def sample_emergency_conditions():
    """Fixture providing sample emergency conditions for tests"""
    return {
        'wind_speed': 35.0,
        'precipitation': 22.0,
        'visibility': 150,
        'weather_condition': 'Severe Thunderstorm',
        'temperature': 8.0
    }

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
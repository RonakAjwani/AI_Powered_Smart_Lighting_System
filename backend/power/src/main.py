from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import uvicorn
import asyncio
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator

# Import power grid components
from src.graph.power_graph import (
    power_grid_graph,
    execute_power_grid_workflow,
    get_workflow_status,
    trigger_emergency_response
)
from src.agents.energy_load_forecaster_agent import energy_load_forecaster_agent
from src.agents.energy_optimization_agent import energy_optimization_agent
from src.agents.power_outage_detection_agent import power_outage_detection_agent
from src.agents.energy_rerouting_agent import energy_rerouting_agent
from src.agents.power_grid_reporting_agent import power_grid_reporting_agent
from src.config.settings import config
from src.kafka.kafka_producer import power_producer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models for API requests and responses
class WorkflowTriggerRequest(BaseModel):
    trigger_type: str = Field(default="manual", description="Type of workflow trigger")
    config_overrides: Optional[Dict[str, Any]] = Field(default=None, description="Configuration overrides")
    description: Optional[str] = Field(default=None, description="Workflow description")

class EmergencyRequest(BaseModel):
    emergency_type: str = Field(..., description="Type of emergency")
    affected_zones: List[str] = Field(..., description="List of affected zones")
    severity: str = Field(default="critical", description="Emergency severity level")
    description: Optional[str] = Field(default=None, description="Emergency description")
    contact_info: Optional[Dict[str, str]] = Field(default=None, description="Emergency contact information")

class ForecastRequest(BaseModel):
    periods: List[str] = Field(default=["1_hour", "4_hour", "24_hour"], description="Forecast periods")
    include_weather: bool = Field(default=True, description="Include weather data")
    include_historical: bool = Field(default=True, description="Include historical analysis")
    zones: Optional[List[str]] = Field(default=None, description="Specific zones to forecast")

class OptimizationRequest(BaseModel):
    zones: Optional[List[str]] = Field(default=None, description="Zones to optimize")
    savings_target: Optional[float] = Field(default=None, description="Target savings percentage")
    priority_mode: str = Field(default="balanced", description="Optimization priority mode")

class ReportRequest(BaseModel):
    report_type: str = Field(default="comprehensive", description="Type of report to generate")
    time_period: str = Field(default="30_days", description="Report time period")
    include_recommendations: bool = Field(default=True, description="Include recommendations")

# Background task manager for long-running workflows
class WorkflowManager:
    def __init__(self):
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_history: List[Dict[str, Any]] = []
    
    def add_workflow(self, workflow_id: str, workflow_info: Dict[str, Any]):
        self.active_workflows[workflow_id] = {
            **workflow_info,
            "started_at": datetime.now().isoformat(),
            "status": "running"
        }
    
    def update_workflow(self, workflow_id: str, update_data: Dict[str, Any]):
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id].update(update_data)
    
    def complete_workflow(self, workflow_id: str, final_data: Dict[str, Any]):
        if workflow_id in self.active_workflows:
            workflow_data = self.active_workflows.pop(workflow_id)
            workflow_data.update(final_data)
            workflow_data["completed_at"] = datetime.now().isoformat()
            self.workflow_history.append(workflow_data)

workflow_manager = WorkflowManager()

# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    logger.info("🚀 Starting Power Grid Management Service")
    
    # Startup tasks
    try:
        # Initialize agents
        logger.info("🔧 Initializing power grid agents...")
        
        # Start background monitoring task
        asyncio.create_task(background_monitoring())
        
        logger.info("✅ Power Grid Management Service started successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
    
    yield
    
    logger.info("✅ Power Grid Management Service shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="AI-Powered Smart Lighting - Power Grid Management Service",
    description="Advanced power grid management with AI agents for load forecasting, outage detection, energy rerouting, optimization, and reporting",
    version="1.0.0",
    lifespan=lifespan
)

# Add Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Background monitoring task
async def background_monitoring():
    """Background task for continuous monitoring"""
    while True:
        try:
            # Run automated monitoring every 5 minutes
            await asyncio.sleep(300)  # 5 minutes
            
            logger.info("🔍 Running automated power grid monitoring...")
            
            # Execute automated workflow
            result = execute_power_grid_workflow(
                trigger_type="automated_monitoring"
            )
            
            workflow_id = result.get("workflow_id")
            if workflow_id:
                workflow_manager.add_workflow(workflow_id, {
                    "trigger_type": "automated_monitoring",
                    "automated": True
                })
            
            logger.info(f"✅ Automated monitoring completed - Status: {result.get('status')}")
            
        except Exception as e:
            logger.error(f"❌ Background monitoring error: {e}")

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "service": "power_grid_management",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "agents": {
            "load_forecaster": "active",
            "outage_detector": "active",
            "energy_router": "active",
            "energy_optimizer": "active",
            "grid_reporter": "active"
        }
    }

# Main workflow endpoints
@app.post("/workflow/execute", tags=["Workflow"])
async def execute_workflow(
    request: WorkflowTriggerRequest,
    background_tasks: BackgroundTasks
):
    """Execute complete power grid management workflow"""
    try:
        logger.info(f"🚀 Executing power grid workflow - Trigger: {request.trigger_type}")
        
        # Execute workflow in background for long-running operations
        def run_workflow():
            result = execute_power_grid_workflow(
                trigger_type=request.trigger_type,
                config_overrides=request.config_overrides
            )
            
            workflow_id = result.get("workflow_id")
            if workflow_id:
                workflow_manager.complete_workflow(workflow_id, result)
            
            return result
        
        background_tasks.add_task(run_workflow)
        
        # Return immediate response
        workflow_id = f"power_grid_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        workflow_manager.add_workflow(workflow_id, {
            "trigger_type": request.trigger_type,
            "description": request.description,
            "manual_trigger": True
        })
        
        return {
            "message": "Power grid workflow initiated",
            "workflow_id": workflow_id,
            "trigger_type": request.trigger_type,
            "status": "running",
            "estimated_duration": "2-5 minutes",
            "check_status_url": f"/workflow/status/{workflow_id}"
        }
        
    except Exception as e:
        logger.error(f"❌ Workflow execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}"
        )

@app.get("/workflow/status/{workflow_id}", tags=["Workflow"])
async def get_workflow_status_endpoint(workflow_id: str):
    """Get status of a specific workflow"""
    try:
        # Check active workflows first
        if workflow_id in workflow_manager.active_workflows:
            workflow_data = workflow_manager.active_workflows[workflow_id]
            
            # Get detailed status from LangGraph
            detailed_status = get_workflow_status(workflow_id)
            
            return {
                **workflow_data,
                **detailed_status,
                "source": "active"
            }
        
        # Check completed workflows
        completed_workflow = next(
            (w for w in workflow_manager.workflow_history if w.get("workflow_id") == workflow_id),
            None
        )
        
        if completed_workflow:
            return {
                **completed_workflow,
                "source": "completed"
            }
        
        # Try to get from LangGraph memory
        detailed_status = get_workflow_status(workflow_id)
        if detailed_status.get("status") != "not_found":
            return detailed_status
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting workflow status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving workflow status: {str(e)}"
        )

@app.get("/workflow/active", tags=["Workflow"])
async def get_active_workflows():
    """Get all active workflows"""
    return {
        "active_workflows": workflow_manager.active_workflows,
        "total_active": len(workflow_manager.active_workflows),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/workflow/history", tags=["Workflow"])
async def get_workflow_history(limit: int = 10):
    """Get workflow history"""
    recent_workflows = workflow_manager.workflow_history[-limit:] if workflow_manager.workflow_history else []
    
    return {
        "workflow_history": recent_workflows,
        "total_completed": len(workflow_manager.workflow_history),
        "showing_recent": len(recent_workflows),
        "timestamp": datetime.now().isoformat()
    }

# Emergency response endpoint
@app.post("/emergency/trigger", tags=["Emergency"])
async def trigger_emergency_endpoint(request: EmergencyRequest):
    """Trigger emergency response procedures"""
    try:
        logger.warning(f"🚨 Emergency triggered: {request.emergency_type}")
        
        emergency_data = {
            "emergency_type": request.emergency_type,
            "affected_zones": request.affected_zones,
            "severity": request.severity,
            "description": request.description,
            "contact_info": request.contact_info,
            "triggered_at": datetime.now().isoformat()
        }
        
        result = trigger_emergency_response(emergency_data)
        
        workflow_id = result.get("workflow_id")
        if workflow_id:
            workflow_manager.add_workflow(workflow_id, {
                "trigger_type": "emergency",
                "emergency_type": request.emergency_type,
                "severity": request.severity,
                "affected_zones": request.affected_zones
            })
        
        return {
            "message": "Emergency response initiated",
            "workflow_id": workflow_id,
            "emergency_type": request.emergency_type,
            "affected_zones": request.affected_zones,
            "status": result.get("status", "unknown"),
            "estimated_response_time": "immediate"
        }
        
    except Exception as e:
        logger.error(f"❌ Emergency response failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Emergency response failed: {str(e)}"
        )

# Individual agent endpoints
@app.post("/agents/forecast", tags=["Agents"])
async def forecast_energy_load(request: ForecastRequest):
    """Execute energy load forecasting"""
    try:
        forecast_input = {
            "requested_periods": request.periods,
            "include_weather": request.include_weather,
            "include_historical": request.include_historical,
            "zones": request.zones or config.DEFAULT_ZONES
        }
        
        result = energy_load_forecaster_agent.forecast_energy_demand(forecast_input)
        
        return {
            "agent": "energy_load_forecaster",
            "status": result.get("status", "unknown"),
            "forecast_results": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Load forecasting failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Load forecasting failed: {str(e)}"
        )

@app.post("/agents/detect-outages", tags=["Agents"])
async def detect_outages():
    """Execute power outage detection"""
    try:
        result = power_outage_detection_agent.detect_power_outages()
        
        return {
            "agent": "power_outage_detection",
            "status": result.get("status", "unknown"),
            "outage_results": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Outage detection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Outage detection failed: {str(e)}"
        )

@app.post("/agents/reroute-energy", tags=["Agents"])
async def reroute_energy(outage_alerts: Optional[List[Dict[str, Any]]] = None):
    """Execute energy rerouting"""
    try:
        result = energy_rerouting_agent.execute_energy_rerouting(outage_alerts)
        
        return {
            "agent": "energy_rerouting",
            "status": result.get("status", "unknown"),
            "rerouting_results": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Energy rerouting failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Energy rerouting failed: {str(e)}"
        )

@app.post("/agents/optimize-energy", tags=["Agents"])
async def optimize_energy(request: OptimizationRequest):
    """Execute energy optimization"""
    try:
        optimization_input = {
            "zones": request.zones,
            "savings_target": request.savings_target,
            "priority_mode": request.priority_mode
        }
        
        result = energy_optimization_agent.optimize_energy_usage(optimization_input)
        
        return {
            "agent": "energy_optimization",
            "status": result.get("status", "unknown"),
            "optimization_results": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Energy optimization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Energy optimization failed: {str(e)}"
        )

@app.post("/agents/generate-reports", tags=["Agents"])
async def generate_reports(request: ReportRequest):
    """Generate power grid reports"""
    try:
        result = power_grid_reporting_agent.generate_power_grid_reports(request.report_type)
        
        return {
            "agent": "power_grid_reporting",
            "status": result.get("status", "unknown"),
            "report_results": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Report generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}"
        )

# System status and monitoring endpoints
@app.get("/system/status", tags=["System"])
async def get_system_status():
    """Get comprehensive system status"""
    try:
        # Get current grid status
        current_time = datetime.now()
        
        system_status = {
            "service_info": {
                "name": "Power Grid Management Service",
                "version": "1.0.0",
                "uptime": "running",  # Calculate actual uptime if needed
                "timestamp": current_time.isoformat()
            },
            "agents_status": {
                "energy_load_forecaster": "active",
                "power_outage_detection": "active", 
                "energy_rerouting": "active",
                "energy_optimization": "active",
                "power_grid_reporting": "active"
            },
            "workflow_status": {
                "active_workflows": len(workflow_manager.active_workflows),
                "completed_workflows": len(workflow_manager.workflow_history),
                "last_execution": workflow_manager.workflow_history[-1].get("completed_at") if workflow_manager.workflow_history else None
            },
            "system_health": {
                "kafka_connected": True,  # Test actual connection if needed
                "agents_operational": True,
                "memory_usage": "normal",
                "error_rate": "low"
            }
        }
        
        return system_status
        
    except Exception as e:
        logger.error(f"❌ Error getting system status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving system status: {str(e)}"
        )

@app.get("/system/metrics", tags=["System"])
async def get_system_metrics():
    """Get system performance metrics"""
    try:
        # Calculate basic metrics
        total_workflows = len(workflow_manager.workflow_history)
        successful_workflows = len([w for w in workflow_manager.workflow_history if w.get("status", "").startswith("success") or w.get("status") == "normal_operations"])
        success_rate = (successful_workflows / total_workflows * 100) if total_workflows > 0 else 0
        
        recent_24h = [
            w for w in workflow_manager.workflow_history 
            if datetime.fromisoformat(w.get("completed_at", "1970-01-01T00:00:00")) > datetime.now() - timedelta(hours=24)
        ]
        
        metrics = {
            "performance_metrics": {
                "total_workflows_executed": total_workflows,
                "successful_workflows": successful_workflows,
                "success_rate_percent": round(success_rate, 2),
                "workflows_last_24h": len(recent_24h),
                "average_execution_time": "2-5 minutes",  # Calculate actual if needed
            },
            "operational_metrics": {
                "active_workflows": len(workflow_manager.active_workflows),
                "emergency_responses_24h": len([w for w in recent_24h if w.get("trigger_type") == "emergency"]),
                "automated_executions_24h": len([w for w in recent_24h if w.get("trigger_type") == "automated_monitoring"]),
                "manual_executions_24h": len([w for w in recent_24h if w.get("trigger_type") in ["manual", "scheduled"]])
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"❌ Error getting system metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving system metrics: {str(e)}"
        )

# Configuration endpoints
@app.get("/config", tags=["Configuration"])
async def get_configuration():
    """Get current service configuration"""
    return {
        "service_config": {
            "default_zones": config.DEFAULT_ZONES,
            "priority_zones": config.PRIORITY_ZONES,
            "energy_savings_target": config.ENERGY_SAVINGS_TARGET,
            "reliability_target": config.RELIABILITY_TARGET,
            "efficiency_baseline": config.EFFICIENCY_BASELINE,
            "monitoring_interval": "5 minutes",
            "kafka_enabled": True
        },
        "agent_config": {
            "groq_model": config.GROQ_MODEL,
            "temperature": config.GROQ_TEMPERATURE,
            "max_tokens": config.GROQ_MAX_TOKENS
        },
        "timestamp": datetime.now().isoformat()
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

# Main execution
if __name__ == "__main__":
    logger.info("🚀 Starting Power Grid Management Service...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,  # Different port for power service
        reload=True,
        log_level="info",
        access_log=True
    )
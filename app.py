"""
FastAPI Main Application
Provides REST API endpoints for the reminder service
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import our modules
from scheduler import ReminderScheduler
from wekan_client import WekanClient
from sns_notifier import SNSNotifier

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    global scheduler
    
    # Startup
    logger.info("Starting Reminder Service")
    try:
        scheduler = ReminderScheduler()
        scheduler.start()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler during startup: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Reminder Service")
    if scheduler:
        scheduler.stop()
    logger.info("Application shutdown completed")

# Create FastAPI app with lifespan management
app = FastAPI(
    title="Wekan Reminder Service",
    description="Microservice for sending SNS notifications about due Wekan cards",
    version="1.0.0",
    lifespan=lifespan
)

# Pydantic models for API responses
class StatusResponse(BaseModel):
    """Response model for status endpoint"""
    service: str
    status: str
    timestamp: str
    scheduler: Dict
    wekan_connection: bool
    email_config: bool

class ReminderRunResponse(BaseModel):
    """Response model for manual reminder run"""
    success: bool
    timestamp: str
    due_cards_count: int
    due_cards: List[Dict]
    notification_sent: bool
    execution_time_seconds: float
    error: Optional[str] = None

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint - basic service information"""
    return {
        "service": "Wekan Reminder Service",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get comprehensive service status including scheduler, Wekan connection, and SNS config
    """
    try:
        logger.info("Status check requested")
        
        # Get scheduler status
        scheduler_status = scheduler.get_status() if scheduler else {"running": False, "error": "Scheduler not initialized"}
        
        # Test Wekan connection
        wekan_client = WekanClient()
        wekan_connection = wekan_client.test_connection()
        
        # Test SNS configuration
        try:
            sns_notifier = SNSNotifier()
            sns_config = sns_notifier.test_connection()
        except Exception as e:
            logger.warning(f"SNS configuration test failed: {str(e)}")
            sns_config = False
        
        status_response = StatusResponse(
            service="Wekan Reminder Service",
            status="healthy" if scheduler_status.get("running") and wekan_connection and sns_config else "degraded",
            timestamp=datetime.now().isoformat(),
            scheduler=scheduler_status,
            wekan_connection=wekan_connection,
            email_config=sns_config  # Keeping the same field name for backward compatibility
        )
        
        return status_response
        
    except Exception as e:
        logger.error(f"Error getting service status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting service status: {str(e)}")

@app.post("/reminders/run", response_model=ReminderRunResponse)
async def run_reminders_manual():
    """
    Manually trigger a reminder check and send SNS notifications if due cards are found
    This endpoint is useful for testing and on-demand checks
    """
    try:
        logger.info("Manual reminder run requested via API")
        
        if not scheduler:
            raise HTTPException(status_code=500, detail="Scheduler not initialized")
        
        # Run manual check
        result = scheduler.run_manual_check()
        
        # Convert to response model
        response = ReminderRunResponse(
            success=result.get("success", False),
            timestamp=result.get("timestamp", datetime.now().isoformat()),
            due_cards_count=result.get("due_cards_count", 0),
            due_cards=result.get("due_cards", []),
            notification_sent=result.get("notification_sent", False),
            execution_time_seconds=result.get("execution_time_seconds", 0),
            error=result.get("error")
        )
        
        # Return appropriate HTTP status
        if response.success:
            return response
        else:
            return JSONResponse(
                status_code=500,
                content=response.dict()
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during manual reminder run: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error running reminders: {str(e)}")

@app.post("/test/sns")
async def test_sns():
    """
    Send a test SNS notification to verify AWS configuration
    """
    try:
        logger.info("Test SNS notification requested via API")
        
        sns_notifier = SNSNotifier()
        success = sns_notifier.send_test_notification()
        
        if success:
            return {
                "success": True,
                "message": "Test SNS notification sent successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Failed to send test SNS notification",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
    except Exception as e:
        logger.error(f"Error sending test SNS notification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending test SNS notification: {str(e)}")

@app.post("/test/wekan")
async def test_wekan():
    """
    Test Wekan API connection and authentication
    """
    try:
        logger.info("Wekan connection test requested via API")
        
        wekan_client = WekanClient()
        
        # Test basic connection
        connection_ok = wekan_client.test_connection()
        
        # Test authentication
        auth_ok = wekan_client.login()
        
        result = {
            "connection": connection_ok,
            "authentication": auth_ok,
            "timestamp": datetime.now().isoformat()
        }
        
        if connection_ok and auth_ok:
            # Get some basic info
            boards = wekan_client.get_boards()
            result["boards_count"] = len(boards)
            result["success"] = True
            result["message"] = "Wekan connection and authentication successful"
        else:
            result["success"] = False
            result["message"] = "Wekan connection or authentication failed"
            
        return result
        
    except Exception as e:
        logger.error(f"Error testing Wekan connection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error testing Wekan connection: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Simple health check endpoint for container orchestration
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    # Configure logging for uvicorn
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Run the application
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        log_config=log_config,
        reload=False
    )
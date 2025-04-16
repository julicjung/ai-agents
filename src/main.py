"""
Main application module for the FastAPI application.
Sets up the production-grade API service with OpenTelemetry integration, CORS,
and proper request routing.
"""
import logging
import os
import sys
import traceback
from typing import Callable
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# Load environment variables from .env file
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from azure.ai.inference.tracing import AIInferenceInstrumentor 
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Import our application components
from ports.rest.pizza import router as pizza_router
from infra.router import router as infra_router
from infra.errors import AppError, ErrorDetail
from config import settings, EnvironmentMode

# Configure logging based on environment
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
log_level = logging.DEBUG if settings.environment == EnvironmentMode.DEVELOPMENT else logging.INFO

logging.basicConfig(
    level=log_level,
    format=log_format,
    stream=sys.stdout
)

# Reduce noise from Azure SDK logging
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logging.getLogger("azure.monitor.opentelemetry.exporter.export._base").setLevel(logging.WARNING)
logging.getLogger("azure.identity._internal.decorators").setLevel(logging.WARNING)
logging.getLogger("azure.monitor.opentelemetry._configure").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class ExceptionMiddleware(BaseHTTPMiddleware):
    """
    Custom middleware to handle exceptions in a controlled way.
    Prevents exceptions from being logged by ASGI server.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            # Log exception details
            if settings.environment == EnvironmentMode.DEVELOPMENT:
                logger.exception("Unhandled exception occurred")
            else:
                logger.error(f"Error processing request: {str(e)}")
            # Re-raise for FastAPI's exception handler
            raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    logger.info(f"Starting application in {settings.environment} mode")
    yield
    logger.info("Application shutdown initiated")

# Initialize FastAPI application
app = FastAPI(
    title="Pizza API Service",
    description="Production-grade Pizza API Service with OpenTelemetry integration",
    version="1.0.0",
    docs_url="/docs" if settings.environment == EnvironmentMode.DEVELOPMENT else None,
    redoc_url="/redoc" if settings.environment == EnvironmentMode.DEVELOPMENT else None,
    openapi_url="/openapi.json" if settings.environment == EnvironmentMode.DEVELOPMENT else None,
    lifespan=lifespan,
)

# Add exception middleware before other middleware
app.add_middleware(ExceptionMiddleware)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for all unhandled exceptions.
    Provides detailed errors in development, generic errors in production.
    
    Args:
        request: The incoming request
        exc: The exception that was raised
        
    Returns:
        JSONResponse: RFC 7807 compliant error response
    """
    # Handle known application errors
    if isinstance(exc, AppError):
        error_detail = exc.to_error_detail()
    else:
        # For unknown errors, create a generic error detail
        error_detail = ErrorDetail(
            type="https://api.pizza.com/errors/internal",
            title="Internal Server Error",
            status=500,
            detail="An unexpected error occurred" if settings.environment == EnvironmentMode.PRODUCTION
                  else f"{str(exc)}\n{''.join(traceback.format_tb(exc.__traceback__))}",
            instance=str(request.url)
        )
    
    return JSONResponse(
        status_code=error_detail.status,
        content={
            "type": error_detail.type,
            "title": error_detail.title,
            "status": error_detail.status,
            "detail": error_detail.detail,
            "instance": error_detail.instance
        }
    )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: In production, specify exact domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup OpenTelemetry with Azure Monitor if enabled
if settings.enable_telemetry:
    try:
        configure_azure_monitor(
            connection_string=settings.azure_monitor_connection_string,
            resource = Resource.create({
                "service.name": "agent-pizza-dough",
                "service.namespace": "agent-demo"
            }),
        )
        FastAPIInstrumentor.instrument_app(app)
        AIInferenceInstrumentor().instrument()
        LoggingInstrumentor(set_logging_format=True).instrument()
        RequestsInstrumentor().instrument()
        logger.info("OpenTelemetry instrumentation configured successfully")
    except Exception as e:
        logger.error(f"Failed to configure OpenTelemetry: {e}")

# Log core config items
logger.info(f"Configured backendtype: {settings.backend_type}")

# Include routers
app.include_router(pizza_router)     # Pizza domain endpoints
app.include_router(infra_router)     # Infrastructure endpoints

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info" if settings.environment == EnvironmentMode.PRODUCTION else "debug"
    )
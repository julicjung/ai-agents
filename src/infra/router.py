"""
Infrastructure router for handling system-level HTTP requests.
Provides endpoints for system health monitoring and infrastructure-related operations.
"""
from fastapi import APIRouter, status, Header, HTTPException
from typing import Dict, Optional
from config import settings

router = APIRouter(tags=["infrastructure"])

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(authorization: Optional[str] = Header(None)) -> Dict[str, str]:
    """
    Health check endpoint for monitoring system status.
    Protected by Bearer token authentication for security.
    
    Used by:
    - Kubernetes liveness/readiness probes
    - Load balancer health checks
    - Monitoring systems
    
    Args:
        authorization: Bearer token from Authorization header
        
    Returns:
        Dict[str, str]: Status message indicating the service is healthy
        
    Raises:
        HTTPException(401): If Bearer token is missing or invalid
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token"
        )
        
    token = authorization.split("Bearer ")[1]
    if token != settings.health_check_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
        
    return {"status": "healthy"}
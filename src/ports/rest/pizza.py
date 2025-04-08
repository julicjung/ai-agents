"""
REST API endpoints for pizza-related operations.
"""
from fastapi import APIRouter, status, HTTPException

from domains.pizza.models.messages import PizzaRequest, PizzaResponse
from domains.pizza.services.pizza_service import PizzaService
from infra.errors import ValidationError, DomainError

# Initialize router with tag for API documentation grouping
router = APIRouter(tags=["pizza"])

@router.post("/pizza", response_model=PizzaResponse, status_code=status.HTTP_200_OK)
async def process_pizza_request(request: PizzaRequest) -> PizzaResponse:
    """
    Handle pizza-related requests using the pizza service.
    
    Args:
        request: PizzaRequest containing the user's message and optional thread_id
        
    Returns:
        PizzaResponse: The AI agent's response with conversation tracking info
        
    Raises:
        ValidationError: If the request validation fails
        DomainError: If there's an error processing the request
        
    Examples:
        Request: {"message": "How do I make Neapolitan pizza dough?"}
        Response: {
            "status": "success",
            "message": "To make Neapolitan pizza dough...",
            "thread_id": "thread_123..."
        }
    """
    # Validate request
    if not request.message or not request.message.strip():
        raise ValidationError("Message cannot be empty")
        
    # Process request with service layer
    service = PizzaService()
    return await service.process_request(request)
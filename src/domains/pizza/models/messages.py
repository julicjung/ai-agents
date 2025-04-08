"""
Message models for the pizza domain.
Defines the data structures for pizza-related requests and responses.
"""
from typing import Protocol, runtime_checkable
from dataclasses import dataclass
from typing import Optional

@dataclass
class PizzaRequest:
    """
    Model for pizza-related requests.
    Validates incoming pizza query messages and conversation context.
    """
    message: str          # The user's pizza-related query
    thread_id: Optional[str] = None  # Optional thread ID for maintaining conversation context

@dataclass
class PizzaResponse:
    """
    Model for pizza-related responses.
    Structures the AI agent's response and conversation tracking.
    """
    status: str          # Response status ("success" or "error")
    message: str         # The AI agent's response text
    message_id: Optional[str] = None  # Unique ID for this message
    thread_id: Optional[str] = None   # Thread ID for conversation tracking

@runtime_checkable
class PizzaAgent(Protocol):
    """
    Protocol defining the interface for pizza agents.
    All pizza agent implementations must satisfy this protocol.
    """
    async def process_message(self, message: str, thread_id: Optional[str] = None) -> PizzaResponse:
        """
        Process a pizza-related message and return a response.
        
        Args:
            message: The user's pizza-related query
            thread_id: Optional thread ID for continuing an existing conversation
            
        Returns:
            PizzaResponse: The agent's response with conversation tracking info
        """
        ...
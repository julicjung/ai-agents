"""
Pizza agent implementation using Semantic Kernel with AzureAIAgent.
"""
import os
import logging
from typing import Optional
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from semantic_kernel.agents import AzureAIAgentThread, AzureAIAgent

from domains.pizza.models.messages import PizzaAgent, PizzaResponse

logger = logging.getLogger(__name__)

class SemanticKernelPizzaAgent:
    """
    Implementation of PizzaAgent using Semantic Kernel with AzureAIAgent.
    Handles agent initialization, thread management, and message processing.
    """
    
    def __init__(self) -> None:
        """Initialize agent with Azure credentials and project client."""
        # Initialize Azure credentials and project client
        self.credential = DefaultAzureCredential()
        self.project_client = AIProjectClient.from_connection_string(
            credential=self.credential,
            conn_str=os.environ["PROJECT_CONNECTION_STRING"]
        )
        self._initialize_agent()
    
    def _initialize_agent(self) -> None:
        """Initialize or retrieve the pizza-agent instance."""
        try:
            # Look for existing pizza-agent
            all_agents = self.project_client.agents.list_agents().data
            self.agent = next(
                (a for a in all_agents if a.name == "pizza-agent"),
                None
            )
            
            if not self.agent:
                logger.info("Creating new pizza-agent")
                model_name = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o")
                instructions = (
                    "You are a helpful assistant which answers questions on pizza dough recipes and methods. "
                    "You politely refuse to talk about any other topic."
                )
                
                self.agent = self.project_client.agents.create_agent(
                    model=model_name,
                    name="pizza-agent",
                    instructions=instructions
                )
                logger.info(f"Created new pizza-agent with ID: {self.agent.id}")
            else:
                logger.info("Using existing pizza-agent")
            
        except Exception as e:
            logger.error(f"Failed to initialize pizza-agent: {e}")
            raise
    
    async def process_message(self, message: str, thread_id: Optional[str] = None) -> PizzaResponse:
        """
        Process a message using the Semantic Kernel pizza agent.
        
        Args:
            message: The user's pizza-related query
            thread_id: Optional thread ID for maintaining conversation context
            
        Returns:
            PizzaResponse: Agent's response with conversation tracking info
        """
        try:
            # Create or reuse conversation thread
            thread = AzureAIAgentThread(
                client=self.project_client,
                thread_id=thread_id,
            )
            
            logger.info(f"Processing message with thread {thread_id}")
            response = await self.agent.get_response(messages=[message], thread=thread)
            logger.info("Received response")

            return PizzaResponse(
                status="success",
                message=response.content.content,
                thread_id=response.thread.id
            )
            
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            return PizzaResponse(
                status="error",
                message=str(e),
                thread_id=thread_id
            )
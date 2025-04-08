"""
Pizza agent module for handling pizza-related AI interactions.
This implementation uses the full Azure AI Agent service capabilities,
providing advanced features like conversation thread management and error handling.
"""
import os
import logging
from typing import Optional
from azure.identity import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import ThreadMessage, MessageRole

from domains.pizza.models.messages import PizzaResponse
from config import settings

logger = logging.getLogger(__name__)

class PizzaAgent:
    """
    Class for interacting with the pizza-agent using Azure AI Agent service.
    Provides full agent capabilities including persistent conversation threads,
    message history, and robust error handling.
    """
    
    def __init__(self, project_client: AIProjectClient, agent_definition: any) -> None:
        """
        Initialize the PizzaAgent with provided client and agent definition.
        
        Args:
            project_client: Configured Azure AI project client
            agent_definition: Pre-fetched agent definition
        """
        self.project_client = project_client
        self.agent = agent_definition
        
    @classmethod
    async def create(cls) -> "PizzaAgent":
        """
        Create and initialize a new PizzaAgent instance.
        
        Returns:
            PizzaAgent: Initialized agent instance with configured client
        """
        credential = DefaultAzureCredential()
        project_client = AIProjectClient.from_connection_string(
            credential=credential,
            conn_str=os.environ["PROJECT_CONNECTION_STRING"]
        )
        
        try:
            logger.info(f"Retrieving agent with ID: {settings.pizza_agent_id}")
            agent_definition = await project_client.agents.get_agent(
                agent_id=settings.pizza_agent_id
            )
            logger.info(f"Retrieved agent definition with ID: {agent_definition.id}")
            
            return cls(project_client=project_client, agent_definition=agent_definition)
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise
    
    async def process_message(self, message: str, thread_id: Optional[str] = None) -> PizzaResponse:
        """
        Process a message using the pizza-agent.
        Maintains conversation context through thread management.
        
        Args:
            message: The user's pizza-related query
            thread_id: Optional thread ID for continuing an existing conversation
            
        Returns:
            PizzaResponse: Structured response containing the agent's reply and metadata
            
        Examples:
            >>> result = await agent.process_message("How do I make pizza dough?")
            >>> print(result)
            PizzaResponse(
                status="success",
                message="To make pizza dough...",
                thread_id="thread_456..."
            )
        """
        try:
            # Handle thread management
            if thread_id:
                try:
                    # Verify thread exists and is accessible
                    await self.project_client.agents.list_messages(thread_id=thread_id)
                    self.thread = type('Thread', (), {'id': thread_id})()
                    logger.info(f"Using existing thread: {thread_id}")
                except Exception as e:
                    logger.error(f"Thread {thread_id} not found: {e}")
                    return PizzaResponse(
                        status="error",
                        message=f"Thread {thread_id} not found",
                        thread_id=None
                    )
            else:
                # Create new conversation thread
                self.thread = await self.project_client.agents.create_thread()
                logger.info(f"Created new thread: {self.thread.id}")
            
            # Add user message to thread
            logger.info(f"Creating new message in thread {self.thread.id}")
            await self.project_client.agents.create_message(
                thread_id=self.thread.id,
                role="user",
                content=message
            )
            logger.info("Message created successfully")
            
            # Process the message with the agent
            logger.info(f"Starting agent run with agent_id: {self.agent.id}")
            run = await self.project_client.agents.create_and_process_run(
                thread_id=self.thread.id,
                agent_id=self.agent.id
            )
            logger.info(f"Agent run created with run_id: {run.id}")
            
            # Retrieve the agent's response
            logger.info("Retrieving messages from thread")
            messages = await self.project_client.agents.list_messages(
                thread_id=self.thread.id
            )
            
            # Get the most recent agent response
            last_agent_msg = messages.get_last_message_by_role(MessageRole.AGENT)

            if last_agent_msg:
                logger.info("Successfully retrieved assistant's response")
                return PizzaResponse(
                    status="success",
                    message=last_agent_msg.content[0].text.value,
                    message_id=last_agent_msg.id,
                    thread_id=self.thread.id
                )
            else:
                logger.warning("No completed assistant messages found")
                return PizzaResponse(
                    status="error",
                    message="No response received from agent",
                    thread_id=self.thread.id
                )
                
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            return PizzaResponse(
                status="error",
                message=str(e),
                thread_id=getattr(self.thread, 'id', None)
            )
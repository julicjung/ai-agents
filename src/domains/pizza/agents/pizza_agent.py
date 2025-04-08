"""
Pizza agent module for handling pizza-related AI interactions.
This implementation uses the full Azure AI Agent service capabilities,
providing advanced features like conversation thread management and error handling.
"""
import os
import logging
from typing import Dict, Any
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ThreadMessage, MessageRole
from dotenv import load_dotenv
import json

logger = logging.getLogger(__name__)

class PizzaAgent:
    """
    Class for interacting with the pizza-agent using Azure AI Agent service.
    Provides full agent capabilities including persistent conversation threads,
    message history, and robust error handling.
    """
    
    def __init__(self) -> None:
        """
        Initialize the PizzaAgent with Azure AI project client.
        Sets up authentication and creates/retrieves the agent instance.
        """
        load_dotenv()
        
        # Initialize Azure credentials and client for API access
        self.credential = DefaultAzureCredential()
        self.project_client = AIProjectClient.from_connection_string(
            credential=self.credential,
            conn_str=os.environ["PROJECT_CONNECTION_STRING"]
        )
        
        # Initialize agent-specific attributes
        self.agent = None
        self.thread = None
        self._initialize_agent()
    
    def _initialize_agent(self) -> None:
        """
        Initialize or retrieve the pizza-agent.
        Either finds an existing agent or creates a new one with pizza-specific instructions.
        
        Raises:
            Exception: If agent initialization fails
        """
        try:
            # Look for existing pizza-agent in the project
            all_agents = self.project_client.agents.list_agents().data
            self.agent = next(
                (a for a in all_agents if a.name == "pizza-agent"),
                None
            )
            
            if not self.agent:
                logger.info("Creating new pizza-agent, agent wasn't found")
                # Create new agent with pizza-specific behavior
                model_name = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o")
                instructions = (
                    "You are a helpful assistant which answers questions on pizza dough recipies and methods." 
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
    
    async def process_message(self, message: str, thread_id: str | None = None) -> Dict[str, Any]:
        """
        Process a message using the pizza-agent.
        Maintains conversation context through thread management.
        
        Args:
            message: The user's pizza-related query
            thread_id: Optional thread ID for continuing an existing conversation
            
        Returns:
            Dict[str, Any]: Response containing:
                - status: "success" or "error"
                - message: The agent's response text
                - message_id: Unique ID of the response message
                - thread_id: Conversation thread identifier
            
        Examples:
            >>> result = await agent.process_message("How do I make pizza dough?")
            >>> print(result)
            {
                "status": "success",
                "message": "To make pizza dough...",
                "message_id": "msg_123...",
                "thread_id": "thread_456..."
            }
        """
        try:
            # Handle thread management
            if thread_id:
                try:
                    # Verify thread exists and is accessible
                    self.project_client.agents.list_messages(thread_id=thread_id)
                    self.thread = type('Thread', (), {'id': thread_id})()
                    logger.info(f"Using existing thread: {thread_id}")
                except Exception as e:
                    logger.error(f"Thread {thread_id} not found: {e}")
                    return {
                        "status": "error",
                        "message": f"Thread {thread_id} not found",
                        "thread_id": None
                    }
            else:
                # Create new conversation thread
                self.thread = self.project_client.agents.create_thread()
                logger.info(f"Created new thread: {self.thread.id}")
            
            # Add user message to thread
            logger.info(f"Creating new message in thread {self.thread.id}")
            self.project_client.agents.create_message(
                thread_id=self.thread.id,
                role="user",
                content=message
            )
            logger.info("Message created successfully")
            
            # Process the message with the agent
            logger.info(f"Starting agent run with agent_id: {self.agent.id}")
            run = self.project_client.agents.create_and_process_run(
                thread_id=self.thread.id,
                agent_id=self.agent.id
            )
            logger.info(f"Agent run created with run_id: {run.id}")
            
            # Retrieve the agent's response
            logger.info("Retrieving messages from thread")
            messages = self.project_client.agents.list_messages(
                thread_id=self.thread.id
            )
            
            # Get the most recent agent response
            last_agent_msg = messages.get_last_message_by_role(MessageRole.AGENT)

            if last_agent_msg:
                logger.info("Successfully retrieved assistant's response")
                return {
                    "status": "success",
                    "message": last_agent_msg.content[0].text.value,
                    "message_id": last_agent_msg.id,
                    "thread_id": self.thread.id
                }
            else:
                logger.warning("No completed assistant messages found")
                return {
                    "status": "error",
                    "message": "No response received from agent",
                    "thread_id": self.thread.id
                }
                
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            return {
                "status": "error",
                "message": str(e),
                "thread_id": getattr(self.thread, 'id', None)
            }
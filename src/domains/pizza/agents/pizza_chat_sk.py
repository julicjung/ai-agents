"""
Pizza chat module using Semantic Kernel for handling pizza-related AI interactions.
This implementation uses direct Semantic Kernel integration without the Azure AI Agent
wrapper, providing a simpler but more limited chat experience.
"""
import os
import logging
from typing import Dict, Any
from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory
from semantic_kernel.connectors.ai.azure_ai_inference import AzureAIInferenceChatCompletion, AzureAIInferenceChatPromptExecutionSettings
from semantic_kernel.memory import VolatileMemoryStore
from dotenv import load_dotenv
import json

logger = logging.getLogger(__name__)

class PizzaChatSK:
    """
    Class for interacting with the pizza-chat using direct Semantic Kernel integration.
    Provides a straightforward chat experience using Azure AI Chat Completion.
    """
    
    def __init__(self) -> None:
        """
        Initialize the PizzaChatSK with Semantic Kernel setup.
        Sets up the system prompt that defines the assistant's behavior.
        """
        load_dotenv()
                
        # System prompt defines the AI's role and behavior
        self.system_prompt = """You are a helpful assistant which answers questions on pizza dough recipes and methods.
You politely refuse to talk about any other topic.
Base your answers on established pizza-making techniques and best practices."""
    
    async def process_message(self, message: str, conversation_id: str | None = None) -> Dict[str, Any]:
        """
        Process a message using direct Semantic Kernel chat completion.
        Simpler than the Agent-based approach but lacks advanced features.
        
        Args:
            message: The user's message about pizza-related topics
            conversation_id: Optional ID for conversation tracking (not used in this implementation)
            
        Returns:
            Dict[str, Any]: Response containing:
                - status: "success" or "error"
                - message: The AI's response text
                - conversation_id: Always returns the input conversation_id
            
        Note:
            This implementation doesn't maintain conversation history between calls.
            Each request is treated as a new conversation with just the system prompt
            and the current user message.
        """
        try:
            # Initialize a new Kernel for each request
            kernel = Kernel()
            
            # Configure Azure OpenAI Chat Completion with default settings
            azure_chat_completion = AzureAIInferenceChatCompletion(
                ai_model_id="gpt-4o",
            )

            # Create a fresh chat history for this request
            chat_history = ChatHistory()
            chat_history.add_system_message(self.system_prompt)
            chat_history.add_user_message(message)

            # Configure completion parameters
            execution_settings = AzureAIInferenceChatPromptExecutionSettings(
                max_tokens=400,     # Limit response length
                temperature=0.7,    # Moderate creativity
                top_p=0.9,         # Diverse but focused responses
            )
            
            # Get the chat response
            response = await azure_chat_completion.get_chat_message_content(
                chat_history, 
                settings=execution_settings
            )
            
            logger.info(f"Response received:\n{json.dumps(response.to_dict(), indent=2)}")

            return {
                "status": "success",
                "message": response.content,
                "conversation_id": conversation_id
            }
            
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            return {
                "status": "error",
                "message": str(e),
                "conversation_id": conversation_id
            }
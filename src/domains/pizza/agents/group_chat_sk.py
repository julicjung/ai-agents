"""
Semantic Kernel group chat agent skeleton for pizza domain.
"""
import logging
import os
from typing import Optional, Protocol
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel import Kernel
from semantic_kernel.functions import FunctionResult
from semantic_kernel.agents import AzureAIAgentThread, AzureAIAgent

from domains.pizza.models.messages import PizzaResponse

from config import settings  # Ensure settings is imported
from azure.identity import DefaultAzureCredential
from semantic_kernel.functions import KernelFunctionFromPrompt

from semantic_kernel.connectors.ai.azure_ai_inference import AzureAIInferenceChatCompletion

# Import AgentGroupChat from the appropriate module
from semantic_kernel.agents import AgentGroupChat
from semantic_kernel.agents.strategies import KernelFunctionSelectionStrategy, KernelFunctionTerminationStrategy

logger = logging.getLogger(__name__)

class GroupChatAgent(Protocol):
    """
    Protocol for group chat agent supporting message processing.
    """
    async def process_message(self, message: str, thread_id: Optional[str] = None) -> PizzaResponse:
        ...

class SemanticKernelGroupChatAgent:
    """
    Implementation of an experimental group chat.

    It involves routing to a specific agent based on user input analysis.
    The turn taking is based on a rule set over the chat history and implemented by an LLM call.

    There are several simplification options across this class - however, the purpose is to show the concept of a group chat agent.
    """
    def __init__(self, project_client: AIProjectClient, agent_group: AgentGroupChat) -> None:
        """
        Initialize with preconfigured client and agent.
        """
        self.project_client = project_client
        self.agent_group = agent_group

    @classmethod
    async def create(cls) -> "SemanticKernelGroupChatAgent":
        """
        Create and initialize a new SemanticKernelGroupChatAgent instance.
        Returns:
            SemanticKernelGroupChatAgent: Initialized agent instance
        """
        credential = DefaultAzureCredential()
        project_client = AIProjectClient.from_connection_string(
            credential=credential,
            conn_str=os.environ["PROJECT_CONNECTION_STRING"]
        )
        
        try:
            logger.info(f"Initializing agent with ID: {settings.pizza_agent_id}")
            
            # Fetch simplifier agent
            aif_simplifier_agent = await project_client.agents.get_agent(
                agent_id=settings.dough_simplifier_agent
            )
            
            simplifier_agent_name="SimplifierAgent"
            simplifier_agent = AzureAIAgent(
                client=project_client,
                definition=aif_simplifier_agent,
                name=simplifier_agent_name,
            )
            logger.info(f"Initialized simplifier agent with ID: {aif_simplifier_agent.id}")


            # Fetch neaolitan agent
            aif_neapolitan_agent = await project_client.agents.get_agent(
                agent_id=settings.neapolitan_dough_agent
            )

            neapolitan_agent_name="NeapolitanDoughAgent"
            neapolitan_agent = AzureAIAgent(
                client=project_client,
                definition=aif_neapolitan_agent,
                name=neapolitan_agent_name,
            )
            logger.info(f"Initialized Neapolitan agent with ID: {aif_neapolitan_agent.id}")


            # Fetch roman agent
            aif_roman_agent = await project_client.agents.get_agent(
                agent_id=settings.roman_dough_agent
            )

            roman_agent_name="RomanDoughAgent"
            roman_agent = AzureAIAgent(
                client=project_client,
                definition=aif_roman_agent,
                name=roman_agent_name,
            )
            logger.info(f"Initialized Roman agent with ID: {aif_roman_agent.id}")

            # Create kernel with chat completion
            kernel = Kernel()
            chat_completion_service = AzureAIInferenceChatCompletion(
                ai_model_id="gpt-4o",
            )
            kernel.add_service(chat_completion_service)            

            # Create selection strategy
            selection_function = KernelFunctionFromPrompt(
                function_name="selection",
                prompt=f"""
                Determine which participant takes the next turn in a conversation based on conversation.
                State only the name of the participant to take the next turn.
                No participant should take more than one turn in a row.

                Choose only from these participants:
                - '{simplifier_agent_name}' only after you selected either '{neapolitan_agent_name}' or '{roman_agent_name}
                - '{neapolitan_agent_name}' if the question sounds like neapolitan pizza
                - '{roman_agent_name}' if the question sounds like roman pizza

                Always follow these rules when selecting the next participant:
                1) With only one message of role user in the history below, examine the user input and select either {neapolitan_agent_name}'s *or* {roman_agent_name}'s turn.
                2) After either replies, it is always {simplifier_agent_name}'s turn.
                3) If the last message in the chat history if from role = assistant and name = {simplifier_agent_name} you must again choose the same agent which responded initially. Examine messages with role = assistant and *never* mix selection between {neapolitan_agent_name} or {roman_agent_name}.

                History:
                {{{{$history}}}}
                """,
            )

            """
            Parse the result from the selection function for agent selection.
            Strips whitespace and returns the participant name as a string.
            Args:
                result: The raw result string from the selection function.
            Returns:
                str: The cleaned participant name.
            """
            def parse_selection_result(result: FunctionResult) -> str:
                return result.value[0].content.strip()

            selection_strategy = KernelFunctionSelectionStrategy(
                function=selection_function,
                kernel=kernel,
                agent_variable_name="agents",
                history_variable_name="history",
                result_parser=parse_selection_result,
            )

            termination_function = KernelFunctionFromPrompt(
                function_name="termination",
                prompt="""
                Check if '{simplifier_agent_name}' has added the last message and if its only response is 'yes'. If true, also respond with 'yes'
                If '{simplifier_agent_name}' has  added the last message and gave instructions to either '{neapolitan_agent_name}' or '{roman_agent_name}', respond with 'no'.

                History:
                {{$history}}
                """,
            )
            termination_strategy = KernelFunctionTerminationStrategy(
                maximum_iterations=5,
                function=termination_function,
                kernel=kernel,
                agent_variable_name="agents",
                history_variable_name="history",
                agents=[simplifier_agent],
                result_parser=lambda result: result.value[0].content.lower().strip() == "yes",
            )

            chat = AgentGroupChat(
                agents=[simplifier_agent, neapolitan_agent, roman_agent],
                selection_strategy=selection_strategy,
                termination_strategy=termination_strategy
            )

            return cls(project_client=project_client, agent_group=chat)

        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise

    async def process_message(self, message: str, thread_id: str = None) -> PizzaResponse:
        """
        Process a message in the group chat context.
        Args:
            message: The user's group chat message
            thread_id: Optional thread ID for conversation context
        Returns:
            PizzaResponse: Agent's response with conversation tracking info
        """
        # ...implementation needed...
        await self.agent_group.add_chat_message(
            message=message
        )

        async for response in self.agent_group.invoke():
            logger.info(f"Chat from group: {response}")

        # As the last message [-1] will be a yes or no of simplifier agent, we take the second to last [-2] message as the response
        # TODO: This may be improved by properly parsing the chat history
        response = self.agent_group.history.messages[-2]
        pizza_response = PizzaResponse(
            message=response.content,
            status="success",
        )
        return pizza_response

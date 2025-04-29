import asyncio
import re
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

from kirara_ai.im.message import ImageMessage, IMMessage, MessageElement, TextMessage
from kirara_ai.im.sender import ChatSender
from kirara_ai.ioc.container import DependencyContainer
from kirara_ai.llm.format import LLMChatMessage, LLMChatTextContent
from kirara_ai.llm.format.message import LLMChatContentPartType, LLMChatImageContent
from kirara_ai.llm.format.request import LLMChatRequest, Tool
from kirara_ai.llm.format.response import LLMChatResponse
from kirara_ai.llm.llm_manager import LLMManager
from kirara_ai.llm.llm_registry import LLMAbility
from kirara_ai.logger import get_logger
from kirara_ai.memory.composes.base import ComposableMessageType
from kirara_ai.workflow.core.block import Block, Input, Output, ParamMeta
from kirara_ai.workflow.core.execution.executor import WorkflowExecutor


def model_name_options_provider(container: DependencyContainer, block: Block) -> List[str]:
    llm_manager: LLMManager = container.resolve(LLMManager)
    return sorted(llm_manager.get_supported_models(LLMAbility.TextChat))


class ChatMessageConstructor(Block):
    name = "chat_message_constructor"
    inputs = {
        "user_msg": Input("user_msg", "Current Turn Message", IMMessage, "User message"),
        "user_prompt_format": Input("user_prompt_format", "Current Turn Message Format", str,
                                    "Format of the user message", default=""),
        "memory_content": Input("memory_content", "Historical Dialog", List[ComposableMessageType],
                                "Historical conversation records"),
        "system_prompt_format": Input("system_prompt_format", "System Prompt", str, "System prompt template",
                                      default=""),
    }
    outputs = {
        "llm_msg": Output("llm_msg", "LLM Conversation Records", List[LLMChatMessage], "Records for LLM conversations")
    }
    container: DependencyContainer

    def substitute_variables(self, text: str, executor: WorkflowExecutor) -> str:
        """Substitutes variable placeholders in text, supporting object attributes and dictionary keys."""

        def replace_var(match):
            var_path = match.group(1).split(".")
            var_name = var_path[0]
            value = executor.get_variable(var_name, match.group(0))
            for attr in var_path[1:]:
                try:
                    if isinstance(value, dict):
                        value = value.get(attr, match.group(0))
                    elif hasattr(value, attr):
                        value = getattr(value, attr)
                    else:
                        return match.group(0)
                except Exception:
                    return match.group(0)
            return str(value)

        return re.sub(r"\{([^}]+)\}", replace_var, text)

    def execute(self, user_msg: IMMessage, memory_content: str, system_prompt_format: str = "",
                user_prompt_format: str = "") -> Dict[str, Any]:
        executor = self.container.resolve(WorkflowExecutor)

        replacements = {
            "{current_date_time}": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "{user_msg}": user_msg.content,
            "{user_name}": user_msg.sender.display_name,
            "{user_id}": user_msg.sender.user_id
        }
        if isinstance(memory_content, list) and all(isinstance(item, str) for item in memory_content):
            replacements["{memory_content}"] = "\n".join(memory_content)

        for old, new in replacements.items():
            system_prompt_format = system_prompt_format.replace(old, new)
            user_prompt_format = user_prompt_format.replace(old, new)

        system_prompt = self.substitute_variables(system_prompt_format, executor)
        user_prompt = self.substitute_variables(user_prompt_format, executor)

        content: List[LLMChatContentPartType] = [LLMChatTextContent(text=user_prompt)]
        for image in user_msg.images or []:
            content.append(LLMChatImageContent(media_id=image.media_id))

        llm_msg = [
            LLMChatMessage(role="system", content=[LLMChatTextContent(text=system_prompt)]),
        ]

        if isinstance(memory_content, list) and all(isinstance(item, LLMChatMessage) for item in memory_content):
            llm_msg.extend(memory_content)  # type: ignore

        llm_msg.append(LLMChatMessage(role="user", content=content))
        return {"llm_msg": llm_msg}


class ChatCompletion(Block):
    name = "chat_completion"
    inputs = {"prompt": Input("prompt", "LLM Conversation Records", List[LLMChatMessage], "Prompt for LLM")}
    outputs = {"resp": Output("resp", "LLM Response", LLMChatResponse, "LLM's response")}
    container: DependencyContainer

    def __init__(self, model_name: Annotated[
        Optional[str], ParamMeta(label="Model ID", description="The ID of the model to use",
                                 options_provider=model_name_options_provider)] = None):
        self.model_name = model_name
        self.logger = get_logger("ChatCompletionBlock")

    def execute(self, prompt: List[LLMChatMessage]) -> Dict[str, Any]:
        llm_manager = self.container.resolve(LLMManager)
        model_id = self.model_name or llm_manager.get_llm_id_by_ability(LLMAbility.TextChat)
        if not model_id:
            raise ValueError("No available LLM models found")

        llm = llm_manager.get_llm(model_id)
        if not llm:
            raise ValueError(f"LLM {model_id} not found, check model name")

        req = LLMChatRequest(messages=prompt, model=model_id)
        return {"resp": llm.chat(req)}


class ChatResponseConverter(Block):
    name = "chat_response_converter"
    inputs = {"resp": Input("resp", "LLM Response", LLMChatResponse, "Response from LLM")}
    outputs = {"msg": Output("msg", "IM Message", IMMessage, "Message to send via IM")}
    container: DependencyContainer

    def execute(self, resp: LLMChatResponse) -> Dict[str, Any]:
        message_elements: List[MessageElement] = []

        for part in resp.message.content:
            if isinstance(part, LLMChatTextContent):
                for element in part.text.split("<break>"):
                    if element.strip():
                        message_elements.append(TextMessage(element.strip()))
            elif isinstance(part, LLMChatImageContent):
                message_elements.append(ImageMessage(media_id=part.media_id))
        return {"msg": IMMessage(sender=ChatSender.get_bot_sender(), message_elements=message_elements)}


class ChatCompletionWithTools(Block):
    """LLM Conversation block with Tool Calling support."""
    name = "chat_completion_with_tools"
    inputs = {
        "msg": Input("msg", "LLM Conversation Records", List[LLMChatMessage],
                     "Complete conversation history with system, user, assistant and tool calls"),
        "tools": Input("tools", "Tool List", List[Tool], "Available tool list")
    }
    outputs = {
        "resp": Output("resp", "LLM Final Response", LLMChatResponse, "Final message returned by LLM"),
        "iteration_msgs": Output("iteration_msgs", "Intermediate Messages", List[ComposableMessageType],
                                 "All intermediate messages, can be stored for memory")
    }
    container: DependencyContainer

    def __init__(self, model_name: Annotated[
        str, ParamMeta(label="Model ID", description="Model that supports tool calling",
                       options_provider=model_name_options_provider)], max_iterations: Annotated[
        int, ParamMeta(label="Max Iterations", description="Maximum number of allowed LLM iterations")] = 4):
        self.model_name = model_name
        self.max_iterations = max_iterations
        self.logger = get_logger("Block.ChatCompletionWithTools")

    def execute(self, msg: List[LLMChatMessage], tools: List[Tool]) -> Dict[str, Any]:
        if not self.model_name:
            raise ValueError("A model supporting function calling must be specified")

        loop = self.container.resolve(asyncio.AbstractEventLoop)
        llm = self.container.resolve(LLMManager).get_llm(self.model_name)
        if not llm:
            raise ValueError(f"LLM {self.model_name} not found, check model name")

        iteration_msgs: List[LLMChatMessage] = []
        iter_count = 0
        while iter_count < self.max_iterations:
            request_body = LLMChatRequest(messages=msg + iteration_msgs, model=self.model_name)
            if tools:
                request_body.tools = tools
            if iter_count == self.max_iterations - 1:
                request_body.tool_choice = "none"

            tools_mapping = {t.name: t for t in tools}

            response: LLMChatResponse = llm.chat(request_body)
            iter_count += 1
            if response.message.tool_calls:
                iteration_msgs.append(response.message)
                for tool_call in response.message.tool_calls:
                    actual_tool = tools_mapping.get(tool_call.function.name)
                    if actual_tool:
                        resp_future = asyncio.run_coroutine_threadsafe(
                            actual_tool.invokeFunc(tool_call), loop
                        )
                        tool_result_msg = LLMChatMessage(role="tool", content=[resp_future.result()])
                        iteration_msgs.append(tool_result_msg)
            else:
                return {"resp": response, "iteration_msgs": iteration_msgs}

        return {"resp": response, "iteration_msgs": iteration_msgs}

from typing import Annotated, Any, Dict, List, Optional

from kirara_ai.im.message import IMMessage
from kirara_ai.im.sender import ChatSender
from kirara_ai.ioc.container import DependencyContainer
from kirara_ai.llm.format.response import LLMChatResponse
from kirara_ai.logger import get_logger
from kirara_ai.memory.composes.base import ComposableMessageType
from kirara_ai.memory.memory_manager import MemoryManager
from kirara_ai.memory.registry import ComposerRegistry, DecomposerRegistry, ScopeRegistry
from kirara_ai.workflow.core.block import Block, Input, Output, ParamMeta


def scope_type_options_provider(container: DependencyContainer, block: Block) -> List[str]:
    return ["global", "member", "group"]


def decomposer_name_options_provider(container: DependencyContainer, block: Block) -> List[str]:
    return ["default", "multi_element"]


class ChatMemoryQuery(Block):
    name = "chat_memory_query"
    inputs = {
        "chat_sender": Input(
            "chat_sender", "Chat Sender", ChatSender, "The chat sender whose memory is to be queried"
        )
    }
    outputs = {"memory_content": Output(
        "memory_content", "Memory Content", List[ComposableMessageType], "Memory Content")}
    container: DependencyContainer

    def __init__(
        self,
        scope_type: Annotated[
            Optional[str],
            ParamMeta(
                label="Scope Type",
                description="Scope of the memory to query",
                options_provider=scope_type_options_provider,
            ),
        ],
        decomposer_name: Annotated[
            Optional[str],
            ParamMeta(
                label="Decomposer Name",
                description="Name of the decomposer to use",
                options_provider=decomposer_name_options_provider,
            ),
        ] = "default",
    ):
        self.scope_type = scope_type
        self.decomposer_name: str = decomposer_name or "default"

    def execute(self, chat_sender: ChatSender) -> Dict[str, Any]:
        self.memory_manager = self.container.resolve(MemoryManager)

        # Use default scope if not specified
        if self.scope_type is None:
            self.scope_type = self.memory_manager.config.default_scope

        # Get scope instance
        scope_registry = self.container.resolve(ScopeRegistry)
        self.scope = scope_registry.get_scope(self.scope_type)

        # Get decomposer instance
        decomposer_registry = self.container.resolve(DecomposerRegistry)
        self.decomposer = decomposer_registry.get_decomposer(
            self.decomposer_name)

        entries = self.memory_manager.query(self.scope, chat_sender)
        memory_content = self.decomposer.decompose(entries)
        return {"memory_content": memory_content}


class ChatMemoryStore(Block):
    name = "chat_memory_store"

    inputs = {
        "user_msg": Input("user_msg", "User Message", IMMessage, "User Message", nullable=True),
        "llm_resp": Input(
            "llm_resp", "LLM Response", LLMChatResponse, "LLM Response", nullable=True
        ),
        "middle_steps": Input(
            "middle_steps", "Intermediate Step Messages", List[ComposableMessageType], "Intermediate Step Messages",
            nullable=True
        )
    }
    outputs = {}
    container: DependencyContainer

    def __init__(
        self,
        scope_type: Annotated[
            Optional[str],
            ParamMeta(
                label="Scope Type",
                description="Scope of the memory to store",
                options_provider=scope_type_options_provider,
            ),
        ],
    ):
        self.scope_type = scope_type
        self.logger = get_logger("Block.ChatMemoryStore")

    def execute(
        self,
        user_msg: Optional[IMMessage] = None,
        llm_resp: Optional[LLMChatResponse] = None,
        middle_steps: Optional[List[ComposableMessageType]] = None,
    ) -> Dict[str, Any]:
        self.memory_manager = self.container.resolve(MemoryManager)

        # Use default scope if not specified
        if self.scope_type is None:
            self.scope_type = self.memory_manager.config.default_scope

        # Get scope instance
        scope_registry = self.container.resolve(ScopeRegistry)
        self.scope = scope_registry.get_scope(self.scope_type)

        # Get composer instance
        composer_registry = self.container.resolve(ComposerRegistry)
        self.composer = composer_registry.get_composer("default")

        # Store user messages and LLM responses
        if user_msg is None:
            composed_messages: List[ComposableMessageType] = []
        else:
            composed_messages = [user_msg]

        if middle_steps is not None:
            composed_messages.extend(middle_steps)

        if llm_resp is not None:
            if llm_resp.message:
                composed_messages.append(llm_resp.message)

        if not composed_messages:
            self.logger.warning("No messages to store")
            return {}

        self.logger.debug(f"Composed messages: {composed_messages}")
        memory_entries = self.composer.compose(
            user_msg.sender if user_msg else None, composed_messages)
        self.memory_manager.store(self.scope, memory_entries)

        return {}

from typing import Annotated, Any, Dict

from kirara_ai.im.message import IMMessage, TextMessage
from kirara_ai.im.sender import ChatSender
from kirara_ai.ioc.container import DependencyContainer
from kirara_ai.memory.memory_manager import MemoryManager
from kirara_ai.memory.registry import ScopeRegistry
from kirara_ai.workflow.core.block import Block, Input, Output, ParamMeta


class ClearMemory(Block):
    """Block for clearing conversation memory."""

    name = "clear_memory"
    inputs = {
        "chat_sender": Input("chat_sender", "Message Sender", ChatSender, "Message Sender")
    }
    outputs = {"response": Output("response", "Response", IMMessage, "Response")}
    container: DependencyContainer

    def __init__(
        self,
        scope_type: Annotated[
            str, ParamMeta(label="Scope Type", description="Scope to clear memory from")
        ] = "member",
    ):
        self.scope_type = scope_type

    def execute(self, chat_sender: ChatSender) -> Dict[str, Any]:
        self.memory_manager = self.container.resolve(MemoryManager)

        # Get scope instance
        scope_registry = self.container.resolve(ScopeRegistry)
        self.scope = scope_registry.get_scope(self.scope_type)

        # Clear memory using the manager's method
        self.memory_manager.clear_memory(self.scope, chat_sender)
        return {
            "response": IMMessage(
                sender=chat_sender,
                message_elements=[TextMessage("The memory of the current conversation has been cleared.")],
            )
        }

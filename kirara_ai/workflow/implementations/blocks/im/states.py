import asyncio
from typing import Annotated, Any, Dict

from kirara_ai.im.adapter import EditStateAdapter, IMAdapter
from kirara_ai.im.sender import ChatSender
from kirara_ai.ioc.container import DependencyContainer
from kirara_ai.workflow.core.block import Block, Input, ParamMeta


# Toggle edit state
class ToggleEditState(Block):
    name = "toggle_edit_state"
    inputs = {
        "sender": Input("sender", "Chat Target", ChatSender, "Chat target whose edit state needs to be toggled")
    }
    outputs = {}
    container: DependencyContainer

    def __init__(
        self,
        is_editing: Annotated[
            bool, ParamMeta(label="Is Editing", description="Whether to switch to editing state")
        ],
    ):
        self.is_editing = is_editing

    def execute(self, sender: ChatSender) -> Dict[str, Any]:
        im_adapter = self.container.resolve(IMAdapter)
        if isinstance(im_adapter, EditStateAdapter):
            loop: asyncio.AbstractEventLoop = self.container.resolve(
                asyncio.AbstractEventLoop
            )
            loop.create_task(im_adapter.set_chat_editing_state(sender, self.is_editing))
        return {}

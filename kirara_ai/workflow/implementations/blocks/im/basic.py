from typing import Any, Dict

from kirara_ai.im.message import IMMessage
from kirara_ai.im.sender import ChatSender
from kirara_ai.ioc.container import DependencyContainer
from kirara_ai.workflow.core.block import Block
from kirara_ai.workflow.core.block.input_output import Input, Output


class ExtractChatSender(Block):
    """Extract the sender of a message."""

    name = "extract_chat_sender"
    container: DependencyContainer
    inputs = {"msg": Input("msg", "IM Message", IMMessage, "IM Message")}
    outputs = {"sender": Output("sender", "Message Sender", ChatSender, "Message Sender")}

    def execute(self, **kwargs) -> Dict[str, Any]:
        msg = self.container.resolve(IMMessage)
        return {"sender": msg.sender}

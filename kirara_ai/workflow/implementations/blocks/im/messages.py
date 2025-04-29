import asyncio
from typing import Annotated, Any, Dict, List, Optional

from kirara_ai.im.adapter import IMAdapter
from kirara_ai.im.manager import IMManager
from kirara_ai.im.message import IMMessage, MessageElement, TextMessage
from kirara_ai.im.sender import ChatSender
from kirara_ai.ioc.container import DependencyContainer
from kirara_ai.workflow.core.block import Block, Input, Output, ParamMeta


def im_adapter_options_provider(container: DependencyContainer, block: Block) -> List[str]:
    return [key for key, _ in container.resolve(IMManager).adapters.items()]


class GetIMMessage(Block):
    """Retrieve the latest IM message."""

    name = "msg_input"
    container: DependencyContainer
    outputs = {
        "msg": Output("msg", "IM Message", IMMessage, "Retrieve the latest IM message sent"),
        "sender": Output("sender", "Sender", ChatSender, "Retrieve the sender of the IM message"),
    }

    def execute(self, **kwargs) -> Dict[str, Any]:
        msg = self.container.resolve(IMMessage)
        return {"msg": msg, "sender": msg.sender}


class SendIMMessage(Block):
    """Send an IM message."""

    name = "msg_sender"
    inputs = {
        "msg": Input("msg", "IM Message", IMMessage, "Message to be sent via IM"),
        "target": Input(
            "target",
            "Target Recipient",
            ChatSender,
            "Recipient of the message; defaults to the sender if left empty",
            nullable=True,
        ),
    }
    outputs = {}
    container: DependencyContainer

    def __init__(
        self, im_name: Annotated[Optional[str], ParamMeta(label="Chat Platform Adapter Name", options_provider=im_adapter_options_provider)] = None
    ):
        self.im_name = im_name

    def execute(self, msg: IMMessage, target: Optional[ChatSender] = None) -> Dict[str, Any]:
        src_msg = self.container.resolve(IMMessage)
        if not self.im_name:
            adapter = self.container.resolve(IMAdapter)
        else:
            adapter = self.container.resolve(IMManager).get_adapter(self.im_name)
        loop: asyncio.AbstractEventLoop = self.container.resolve(asyncio.AbstractEventLoop)
        loop.create_task(adapter.send_message(msg, target or src_msg.sender))
        return {"ok": True}


class IMMessageToText(Block):
    """Convert IMMessage to plain text."""

    name = "im_message_to_text"
    container: DependencyContainer
    inputs = {"msg": Input("msg", "IM Message", IMMessage, "IM Message")}
    outputs = {"text": Output("text", "Plain Text", str, "Plain Text")}

    def execute(self, msg: IMMessage) -> Dict[str, Any]:
        return {"text": msg.content}


class TextToIMMessage(Block):
    """Convert plain text to IMMessage."""

    name = "text_to_im_message"
    container: DependencyContainer
    inputs = {"text": Input("text", "Plain Text", str, "Plain Text")}
    outputs = {"msg": Output("msg", "IM Message", IMMessage, "IM Message")}

    def __init__(self, split_by: Annotated[Optional[str], ParamMeta(label="Segment Separator")] = None):
        self.split_by = split_by

    def execute(self, text: str) -> Dict[str, Any]:
        if self.split_by:
            return {
                "msg": IMMessage(
                    sender=ChatSender.get_bot_sender(),
                    message_elements=[TextMessage(line.strip()) for line in text.split(self.split_by) if line.strip()]
                )
            }
        else:
            return {
                "msg": IMMessage(
                    sender=ChatSender.get_bot_sender(),
                    message_elements=[TextMessage(text)]
                )
            }


class AppendIMMessage(Block):
    """Append a new message fragment to an IMMessage."""

    name = "concat_im_message"
    container: DependencyContainer
    inputs = {
        "base_msg": Input("base_msg", "IM Message", IMMessage, "IM Message"),
        "append_msg": Input("append_msg", "New Message Fragment", MessageElement, "New Message Fragment"),
    }
    outputs = {"msg": Output("msg", "IM Message", IMMessage, "IM Message")}

    def execute(self, base_msg: IMMessage, append_msg: MessageElement) -> Dict[str, Any]:
        return {"msg": IMMessage(sender=base_msg.sender, message_elements=base_msg.message_elements + [append_msg])}

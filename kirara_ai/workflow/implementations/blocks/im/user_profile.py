import asyncio
from typing import Any, Dict, Optional

from kirara_ai.im.adapter import IMAdapter, UserProfileAdapter
from kirara_ai.im.profile import UserProfile
from kirara_ai.im.sender import ChatSender
from kirara_ai.ioc.container import DependencyContainer
from kirara_ai.workflow.core.block import Block
from kirara_ai.workflow.core.block.input_output import Input, Output


class QueryUserProfileBlock(Block):
    def __init__(self, container: DependencyContainer):
        inputs = {
            "chat_sender": Input(
                "chat_sender", "Chat Target", ChatSender, "The chat target whose profile is to be queried"
            ),
            "im_adapter": Input(
                "im_adapter", "IM Platform", IMAdapter, "IM Platform Adapter", nullable=True
            ),
        }
        outputs = {"profile": Output("profile", "User Profile", UserProfile, "User Profile")}
        super().__init__("query_user_profile", inputs, outputs)
        self.container = container

    def execute(
        self, chat_sender: ChatSender, im_adapter: Optional[IMAdapter] = None
    ) -> Dict[str, Any]:
        # If no im_adapter is provided, retrieve the default one from the container
        if im_adapter is None:
            im_adapter = self.container.resolve(IMAdapter)

        # Check if the im_adapter implements the UserProfileAdapter protocol
        if not isinstance(im_adapter, UserProfileAdapter):
            raise TypeError(
                f"IM Adapter {type(im_adapter)} does not support user profile querying"
            )

        # Synchronously call the asynchronous method (handled correctly in the workflow executor)
        profile = asyncio.run(im_adapter.query_user_profile(chat_sender))  # type: ignore

        return {"profile": profile}

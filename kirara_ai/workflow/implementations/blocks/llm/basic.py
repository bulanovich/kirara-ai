# Convert LLM response to plain text
from typing import Any, Dict

from kirara_ai.ioc.container import DependencyContainer
from kirara_ai.llm.format.response import LLMChatResponse
from kirara_ai.workflow.core.block.base import Block
from kirara_ai.workflow.core.block.input_output import Input, Output


class LLMResponseToText(Block):
    """Convert LLM response to plain text."""

    name = "llm_response_to_text"
    container: DependencyContainer
    inputs = {"response": Input("response", "LLM Response", LLMChatResponse, "LLM Response")}
    outputs = {"text": Output("text", "Plain Text", str, "Plain Text")}

    def execute(self, response: LLMChatResponse) -> Dict[str, Any]:
        content = ""
        if response.message:
            for part in response.message.content:
                if part.type == "text":
                    content += part.text
                elif part.type == "image":
                    content += f"<media_msg id={part.media_id} />"

        return {"text": content}

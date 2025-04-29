from kirara_ai.workflow.core.block.registry import BlockRegistry
from kirara_ai.workflow.implementations.blocks.im.basic import ExtractChatSender
from kirara_ai.workflow.implementations.blocks.llm.basic import LLMResponseToText
from kirara_ai.workflow.implementations.blocks.llm.image import SimpleStableDiffusionWebUI
from kirara_ai.workflow.implementations.blocks.mcp.tool import MCPToolProvider
from kirara_ai.workflow.implementations.blocks.memory.clear_memory import ClearMemory
from kirara_ai.workflow.implementations.blocks.system.basic import (CurrentTimeBlock, TextBlock, TextConcatBlock,
                                                                    TextExtractByRegexBlock, TextReplaceBlock)

from .game.dice import DiceRoll
from .game.gacha import GachaSimulator
from .im.messages import AppendIMMessage, GetIMMessage, IMMessageToText, SendIMMessage, TextToIMMessage
from .im.states import ToggleEditState
from .llm.chat import ChatCompletion, ChatCompletionWithTools, ChatMessageConstructor, ChatResponseConverter
from .memory.chat_memory import ChatMemoryQuery, ChatMemoryStore
from .system.help import GenerateHelp


def register_system_blocks(registry: BlockRegistry):
    """Register system built-in blocks."""
    # Basic blocks
    registry.register("text_block", "internal", TextBlock, "Basic: Text")
    registry.register("text_concat_block", "internal", TextConcatBlock, "Basic: Concatenate Text")
    registry.register("text_replace_block", "internal", TextReplaceBlock, "Basic: Replace Text")
    registry.register("text_extract_by_regex_block", "internal", TextExtractByRegexBlock,
                      "Basic: Extract Text by Regex")
    registry.register("current_time_block", "internal", CurrentTimeBlock, "Basic: Current Time")

    # IM related blocks
    registry.register("get_message", "internal", GetIMMessage, "IM: Get Latest Message")
    registry.register("send_message", "internal", SendIMMessage, "IM: Send Message")
    registry.register(
        "toggle_edit_state", "internal", ToggleEditState, "IM: Toggle Edit State"
    )
    registry.register(
        "extract_chat_sender", "internal", ExtractChatSender, "IM: Extract Message Sender"
    )
    registry.register("append_im_message", "internal", AppendIMMessage, "IM: Append Message")
    registry.register("im_message_to_text", "internal", IMMessageToText, "IM: Message to Text")
    registry.register("text_to_im_message", "internal", TextToIMMessage, "Text: Text to Message")

    # LLM related blocks
    registry.register("chat_memory_query", "internal", ChatMemoryQuery, "LLM: Query Memory")
    registry.register(
        "chat_message_constructor",
        "internal",
        ChatMessageConstructor,
        "LLM: Construct Chat Record",
    )
    registry.register("chat_completion", "internal", ChatCompletion, "LLM: Execute Chat")
    registry.register("chat_completion_with_tools", "internal", ChatCompletionWithTools, "LLM: Execute Chat with Tools")
    registry.register(
        "chat_response_converter",
        "internal",
        ChatResponseConverter,
        "LLM->IM: Convert Message",
    )
    registry.register("chat_memory_store", "internal", ChatMemoryStore, "LLM: Store Memory")
    registry.register("llm_response_to_text", "internal", LLMResponseToText, "LLM: Response to Text")

    # Drawing related blocks
    registry.register(
        "simple_stable_diffusion_webui",
        "internal",
        SimpleStableDiffusionWebUI,
        "Drawing: Simple Stable Diffusion WebUI",
    )

    # Game related blocks
    registry.register("dice_roll", "game", DiceRoll, "Game: Dice Roll")
    registry.register("gacha_simulator", "game", GachaSimulator, "Game: Gacha Simulator")

    # System related blocks
    registry.register("generate_help", "system", GenerateHelp, "System: Generate Help")
    registry.register("clear_memory", "system", ClearMemory, "System: Clear Memory")

    # MCP related blocks
    registry.register("mcp_tool_provider", "mcp", MCPToolProvider, "MCP: Provide Tool")

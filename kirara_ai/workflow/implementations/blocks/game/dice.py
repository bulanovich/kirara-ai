import random
import re
from typing import Any, Dict

from kirara_ai.im.message import IMMessage, TextMessage
from kirara_ai.im.sender import ChatSender
from kirara_ai.workflow.core.block import Block
from kirara_ai.workflow.core.block.input_output import Input, Output


class DiceRoll(Block):
    """Dice roll block"""

    name = "dice_roll"
    inputs = {
        "message": Input("message", "Input Message", IMMessage, "Input message containing dice command")
    }
    outputs = {
        "response": Output(
            "response", "Response Message", IMMessage, "Response message containing the dice roll result"
        )
    }

    def execute(self, message: IMMessage) -> Dict[str, Any]:
        # Parse the command
        command = message.content
        match = re.match(r"^[.。]roll\s*(\d+)?d(\d+)", command)
        if not match:
            return {
                "response": IMMessage(
                    sender=ChatSender.get_bot_sender(),
                    message_elements=[TextMessage("Invalid dice command")],
                )
            }

        count = int(match.group(1) or "1")  # Default to 1 die
        sides = int(match.group(2))

        if count > 100:  # Limit number of dice
            return {
                "response": IMMessage(
                    sender=ChatSender.get_bot_sender(),
                    message_elements=[TextMessage("Too many dice (max 100)")],
                )
            }

        # Roll the dice
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls)

        # Generate details
        details = f"🎲 Rolled {count}d{sides}: {' + '.join(map(str, rolls))}"
        if count > 1:
            details += f" = {total}"

        return {
            "response": IMMessage(
                sender=ChatSender.get_bot_sender(),
                message_elements=[TextMessage(details)]
            )
        }

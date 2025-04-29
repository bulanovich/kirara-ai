import random
from typing import Dict, Optional

from kirara_ai.im.message import IMMessage, TextMessage
from kirara_ai.im.sender import ChatSender
from kirara_ai.workflow.core.block import Block
from kirara_ai.workflow.core.block.input_output import Input, Output


class GachaSimulator(Block):
    """Gacha Simulator Block"""

    name = "gacha_simulator"
    inputs = {
        "message": Input("message", "Input Message", IMMessage, "Input message containing gacha command")
    }
    outputs = {
        "response": Output("response", "Response Message", IMMessage, "Response message containing gacha results")
    }

    def __init__(self, rates: Optional[Dict[str, float]] = None):
        # Default gacha rates
        self.rates = rates or {"SSR": 0.03, "SR": 0.12, "R": 0.85}  # 3%  # 12%  # 85%

    def _single_pull(self) -> str:
        rand = random.random()
        cumulative = 0
        for rarity, rate in self.rates.items():
            cumulative += rate
            if rand <= cumulative:
                return rarity
        return list(self.rates.keys())[-1]  # Guaranteed minimum

    def execute(self, message: IMMessage) -> Dict[str, IMMessage]:
        # Parse command
        command = message.content
        is_ten_pull = "十连" in command
        pulls = 10 if is_ten_pull else 1

        # Perform gacha pulls
        results = [self._single_pull() for _ in range(pulls)]

        # Generate results statistics
        stats = {rarity: results.count(rarity) for rarity in self.rates.keys()}

        # Generate detailed results
        details = []
        for rarity in results:
            if rarity == "SSR":
                details.append("🌟 SSR")
            elif rarity == "SR":
                details.append("✨ SR")
            else:
                details.append("⭐ R")

        result_text = f"Gacha Results: {'、'.join(details)}"
        stats_text = "Statistics:\n" + "\n".join(
            f"{rarity}: {count}" for rarity, count in stats.items()
        )

        return {
            "response": IMMessage(
                sender=ChatSender.get_bot_sender(),
                message_elements=[TextMessage(result_text), TextMessage(stats_text)],
            )
        }

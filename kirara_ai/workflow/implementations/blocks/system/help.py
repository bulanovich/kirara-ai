from typing import Any, Dict, List

from kirara_ai.im.message import IMMessage, TextMessage
from kirara_ai.im.sender import ChatSender
from kirara_ai.ioc.container import DependencyContainer
from kirara_ai.workflow.core.block import Block, Output
from kirara_ai.workflow.core.dispatch.models.dispatch_rules import RuleGroup
from kirara_ai.workflow.core.dispatch.registry import DispatchRuleRegistry


def _format_rule_condition(rule_type: str, config: Dict[str, Any]) -> str:
    """Format a single rule's condition description."""
    if rule_type == "prefix":
        return f"Input starts with {config['prefix']}"
    elif rule_type == "keyword":
        keywords = config.get("keywords", [])
        return f"Input contains {' or '.join(keywords)}"
    elif rule_type == "regex":
        return f"Input matches regex {config['pattern']}"
    elif rule_type == "fallback":
        return "Any input"
    elif rule_type == "bot_mention":
        return "@me"
    elif rule_type == "chat_type":
        return f"Chat type: {config['chat_type']}"
    return f"Using {rule_type} rule"


def _format_rule_group(group: RuleGroup) -> str:
    """Format a rule group's condition description."""
    rule_conditions = []
    for rule in group.rules:
        rule_conditions.append(
            _format_rule_condition(rule.type, rule.config)
        )

    operator = " and " if group.operator == "and" else " or "
    return operator.join(rule_conditions)


class GenerateHelp(Block):
    """Block to generate help information."""

    name = "generate_help"
    inputs = {}  # No inputs required
    outputs = {"response": Output("response", "Help Information", IMMessage, "Help Information")}
    container: DependencyContainer

    def execute(self) -> Dict[str, Any]:
        # Get the dispatch rule registry from the container
        registry = self.container.resolve(DispatchRuleRegistry)
        rules = registry.get_active_rules()

        # Organize commands by category
        commands: Dict[str, List[Dict[str, Any]]] = {}
        for rule in rules:
            # Get category from workflow ID
            category = rule.workflow_id.split(":")[0].lower()
            if category not in commands:
                commands[category] = []

            # Format rule group conditions
            conditions = []
            for group in rule.rule_groups:
                conditions.append(_format_rule_group(group))

            # Combine all conditions (AND relationship between rule groups)
            rule_format = " and ".join(f"({condition})" for condition in conditions)

            commands[category].append(
                {
                    "name": rule.name,
                    "format": rule_format,
                    "description": rule.description,
                }
            )

        # Generate help text
        help_text = "🤖 Bot Command Help\n\n"

        for category, cmds in sorted(commands.items()):
            help_text += f"📑 {category.upper()}\n"
            for cmd in sorted(cmds, key=lambda x: x["name"]):
                help_text += f"🔸 {cmd['name']}\n"
                help_text += f"  Trigger Condition: {cmd['format']}\n"
                if cmd["description"]:
                    help_text += f"  Description: {cmd['description']}\n"
                help_text += "\n"
            help_text += "\n"

        return {
            "response": IMMessage(
                sender=ChatSender.get_bot_sender(),
                message_elements=[TextMessage(help_text)],
            )
        }

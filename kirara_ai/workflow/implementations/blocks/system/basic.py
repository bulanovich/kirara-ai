import re
from datetime import datetime
from typing import Annotated, Any, Dict

from kirara_ai.workflow.core.block import Block, Output, ParamMeta
from kirara_ai.workflow.core.block.input_output import Input


class TextBlock(Block):
    name = "text_block"
    outputs = {"text": Output("text", "Text", str, "Text")}

    def __init__(
        self, text: Annotated[str, ParamMeta(label="Text", description="Text to output")]
    ):
        self.text = text

    def execute(self) -> Dict[str, Any]:
        return {"text": self.text}


# Concatenate text
class TextConcatBlock(Block):
    name = "text_concat_block"
    inputs = {
        "text1": Input("text1", "Text 1", str, "Text 1"),
        "text2": Input("text2", "Text 2", str, "Text 2"),
    }
    outputs = {"text": Output("text", "Concatenated Text", str, "Concatenated Text")}

    def execute(self, text1: str, text2: str) -> Dict[str, Any]:
        return {"text": text1 + text2}


# Replace a part of the input text with a variable
class TextReplaceBlock(Block):
    name = "text_replace_block"
    inputs = {
        "text": Input("text", "Original Text", str, "Original Text"),
        "new_text": Input("new_text", "New Text", Any, "New Text"),  # type: ignore
    }
    outputs = {"text": Output("text", "Replaced Text", str, "Replaced Text")}

    def __init__(
        self, variable: Annotated[str, ParamMeta(label="Text to Replace", description="Text to be replaced")]
    ):
        self.variable = variable

    def execute(self, text: str, new_text: Any) -> Dict[str, Any]:
        return {
            "text": text.replace(self.variable, str(new_text))
        }


# Extract text using regular expression
class TextExtractByRegexBlock(Block):
    name = "text_extract_by_regex_block"
    inputs = {"text": Input("text", "Original Text", str, "Original Text")}
    outputs = {"text": Output("text", "Extracted Text", str, "Extracted Text")}

    def __init__(
        self, regex: Annotated[str, ParamMeta(label="Regex Pattern", description="Regex Pattern")]
    ):
        self.regex = regex

    def execute(self, text: str) -> Dict[str, Any]:
        # Extract text using regex
        regex = re.compile(self.regex)
        match = regex.search(text)
        # Return the matched group if exists, otherwise return an empty string
        if match and len(match.groups()) > 0:
            return {"text": match.group(1)}
        else:
            return {"text": ""}


# Get current time
class CurrentTimeBlock(Block):
    name = "current_time_block"
    outputs = {"time": Output("time", "Current Time", str, "Current Time")}

    def execute(self) -> Dict[str, Any]:
        return {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

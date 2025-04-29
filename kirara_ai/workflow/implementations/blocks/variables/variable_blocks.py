from typing import Any, Dict, Optional, Type, TypeVar

from kirara_ai.ioc.container import DependencyContainer
from kirara_ai.workflow.core.block import Block
from kirara_ai.workflow.core.block.input_output import Input, Output
from kirara_ai.workflow.core.execution.executor import WorkflowExecutor

T = TypeVar("T")


class SetVariableBlock(Block):
    def __init__(self, container: DependencyContainer):
        inputs: Dict[str, Input] = {
            "name": Input("name", "Variable Name", str, "Variable Name"),
            "value": Input("value", "Variable Value", Any, "Variable Value"),  # type: ignore
        }
        outputs: Dict[str, Output] = {}  # This block does not require outputs
        super().__init__("set_variable", inputs, outputs)
        self.container = container

    def execute(self, name: str, value: Any) -> Dict[str, Any]:
        executor = self.container.resolve(WorkflowExecutor)
        executor.set_variable(name, value)
        return {}


class GetVariableBlock(Block):
    def __init__(self, container: DependencyContainer, var_type: Type[T]):
        inputs = {
            "name": Input("name", "Variable Name", str, "Variable Name"),
            "default": Input("default", "Default Value", var_type, "Default Value", nullable=True),
        }
        outputs = {"value": Output("value", "Variable Value", var_type, "Variable Value")}
        super().__init__("get_variable", inputs, outputs)
        self.container = container
        self.var_type = var_type

    def execute(self, name: str, default: Optional[T] = None) -> Dict[str, T]:
        executor = self.container.resolve(WorkflowExecutor)
        value = executor.get_variable(name, default)

        # Type checking
        if value is not None and not isinstance(value, self.var_type):
            raise TypeError(
                f"Variable '{name}' must be of type {self.var_type}, got {type(value)}"
            )

        return {"value": value}  # type: ignore

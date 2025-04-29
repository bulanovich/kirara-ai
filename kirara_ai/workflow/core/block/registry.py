
import warnings
from inspect import Parameter, signature
from typing import Annotated, Dict, List, Optional, Tuple, Type, get_args, get_origin

from kirara_ai.workflow.core.block import Block
from kirara_ai.workflow.core.block.param import ParamMeta

from .schema import BlockConfig, BlockInput, BlockOutput
from .type_system import TypeSystem


def extract_block_param(param: Parameter, type_system: TypeSystem) -> BlockConfig:
    """
    Extract Block parameter information, including type string, label, whether it is required, description, and default value.
    """
    param_type = param.annotation
    label = param.name
    description = None
    has_options = False
    options_provider = None
    if get_origin(param_type) is Annotated:
        args = get_args(param_type)
        if len(args) > 0:
            actual_type = args[0]
            metadata = args[1] if len(args) > 1 else None

            if isinstance(metadata, ParamMeta):
                label = metadata.label
                description = metadata.description
                has_options = metadata.options_provider is not None
                options_provider = metadata.options_provider

            # Recursively call extract_block_param to process the actual type
            block_config = extract_block_param(
                Parameter(
                    name=param.name,
                    kind=Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=actual_type,
                    default=param.default,
                ),
                type_system
            )
            type_string = block_config.type
            required = block_config.required
            default = block_config.default
        else:
            type_string = "Any"
            required = True
            default = None
    else:
        type_string, required, default = type_system.extract_type_info(param)

    return BlockConfig(
        name=param.name,
        description=description,
        type=type_string,
        required=required,
        default=default,
        label=label,
        has_options=has_options,
        options=[],
        options_provider=options_provider,
    )


class BlockRegistry:
    """Block registry for managing all registered blocks."""

    def __init__(self):
        self._blocks = {}
        self._localized_names = {}
        self._type_system = TypeSystem()

    def register(
        self,
        block_id: str,
        group_id: str,
        block_class: Type[Block],
        localized_name: Optional[str] = None,
    ):
        """Register a block.

        Args:
            block_id: Unique identifier for the block.
            group_id: Group identifier (internal for built-in framework blocks).
            block_class: The block class.
            localized_name: Localized name.
        """
        full_name = f"{group_id}:{block_id}"
        if full_name in self._blocks:
            raise ValueError(f"Block {full_name} already registered")
        self._blocks[full_name] = block_class
        block_class.id = block_id
        if localized_name:
            self._localized_names[full_name] = localized_name
        # Register Input and Output types
        for _, input_info in getattr(block_class, "inputs", {}).items():
            type_name = self._type_system.get_type_name(input_info.data_type)
            self._type_system.register_type(type_name, input_info.data_type)
        for _, output_info in getattr(block_class, "outputs", {}).items():
            type_name = self._type_system.get_type_name(output_info.data_type)
            self._type_system.register_type(type_name, output_info.data_type)

    def get(self, full_name: str) -> Optional[Type[Block]]:
        """Get the registered block class."""
        return self._blocks.get(full_name)

    def get_localized_name(self, block_id: str) -> Optional[str]:
        """Get the localized name."""
        return self._localized_names.get(block_id, block_id)

    def clear(self):
        """Clear the registry."""
        self._blocks.clear()
        self._type_system = TypeSystem()

    def get_block_type_name(self, block_class: Type[Block]) -> str:
        """Get the block type name, prioritizing the registered name."""
        for full_name, registered_class in self._blocks.items():
            if registered_class == block_class:
                return full_name

        warnings.warn(
            f"Block class {block_class.__name__} is not registered. Using class path instead.",
            UserWarning,
        )
        return f"!!{block_class.__module__}.{block_class.__name__}"

    def get_all_types(self) -> List[Type[Block]]:
        """Get all registered block types."""
        return list(self._blocks.values())

    def extract_block_info(
        self, block_type: Type[Block]
    ) -> Tuple[Dict[str, BlockInput], Dict[str, BlockOutput], Dict[str, BlockConfig]]:
        """Extract input, output, and configuration information from the Block type."""
        inputs = {}
        outputs = {}
        configs = {}

        for name, input_info in getattr(block_type, "inputs", {}).items():
            type_name, _, _ = self._type_system.extract_type_info(input_info.data_type)
            self._type_system.register_type(type_name, input_info.data_type)

            inputs[name] = BlockInput(
                name=name,
                label=input_info.label,
                description=input_info.description,
                type=type_name,
                required=not input_info.nullable,
                default=input_info.default if hasattr(input_info, "default") else None,
            )

        for name, output_info in getattr(block_type, "outputs", {}).items():
            type_name, _, _ = self._type_system.extract_type_info(output_info.data_type)
            self._type_system.register_type(type_name, output_info.data_type)

            outputs[name] = BlockOutput(
                name=name,
                label=output_info.label,
                description=output_info.description,
                type=type_name,
            )

        builtin_params = self.get_builtin_params()

        sig = signature(block_type.__init__)
        for param in sig.parameters.values():
            if param.name == "self" or param.name in builtin_params:
                continue

            block_config = extract_block_param(param, self._type_system)
            configs[param.name] = block_config

        return inputs, outputs, configs

    def get_builtin_params(self) -> List[str]:
        """Get built-in parameters."""
        sig = signature(Block.__init__)
        return [param.name for param in sig.parameters.values()]

    def get_type_compatibility_map(self) -> Dict[str, Dict[str, bool]]:
        """Get the compatibility map of all types."""
        return self._type_system.get_compatibility_map()

    def is_type_compatible(self, source_type: str, target_type: str) -> bool:
        """Check if the source type can be assigned to the target type."""
        return self._type_system.is_compatible(source_type, target_type)

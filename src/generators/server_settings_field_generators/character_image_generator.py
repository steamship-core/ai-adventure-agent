from typing import Optional

from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.generator_context_utils import get_profile_image_generator
from generators.server_settings_field_generator import ServerSettingsFieldGenerator


class CharacterImageGenerator(ServerSettingsFieldGenerator):
    @staticmethod
    def get_field() -> str:
        return "characters.image"

    def inner_generate(
        self,
        variables: dict,
        generator: PluginInstance,
        context: AgentContext,
        generation_config: Optional[dict] = None,
    ) -> Block:

        name = variables.get("this_name", "")
        description = variables.get("this_description", "")
        generator = get_profile_image_generator(context)
        task = generator.request_character_image_generation(
            name=name, description=description, context=context
        )
        task.wait()
        return task.output.blocks[0]

from typing import Optional, Type

from steamship import Task, SteamshipError, Block, PluginInstance
from steamship.agents.schema import AgentContext
from steamship.data.operations.generator import GenerateResponse

from generators.server_settings_field_generator import ServerSettingsFieldGenerator
from generators.server_settings_generator import ServerSettingsGenerator
from generators.server_settings_generators.generate_using_title_and_description_generator import \
    GenerateUsingTitleAndDescriptionGenerator
from generators.utils import safe_format
from utils.agent_service import AgentService
from utils.context_utils import get_server_settings, get_story_text_generator, save_server_settings

INSTRUCTION_PREFIX = "Answer only with the minimum amount of information needed to answer the question."


def field_generator(prompt: str, field: str) -> ServerSettingsFieldGenerator:
    prompt = f"{INSTRUCTION_PREFIX}\n\n{prompt}"

    class FieldGenerator(ServerSettingsFieldGenerator):
        PROMPT = prompt

        @staticmethod
        def get_field():
            return field

        def inner_generate(
            self,
            variables: dict,
            generator: PluginInstance,
            context: AgentContext,
            generation_config: Optional[dict] = None,
        ) -> Block:
            task = generator.generate(
                text=safe_format(self.PROMPT, variables)
            )
            return self.task_to_str_block(task)
    return FieldGenerator()


characters_generator = field_generator(
    "Who are the main characters associated with {media_name}?",
    "characters"
)

narrative_voice_generator = field_generator(
    "What is the genre of fiction stories associated with {media_name}?",
    "narrative_voice"
)

adventure_name_generator = field_generator(
    """Come up with a title for an unpublished story based on the following parameters:
    
    Fictional Universe: {media_name}
    Characters: {characters}
    """,
    "name"
)

description_generator = field_generator(
    """Come up with three introductory paragraphs describing the beginning of the following story:
    
    Title: {adventure_name}
    Fictional Universe: {media_name}
    Characters: {characters}
    """,
    "description",
)


def task_for_prompt(generator: PluginInstance, prompt: str, **kwargs) -> Task[GenerateResponse]:
    return generator.generate(text=safe_format(f"{INSTRUCTION_PREFIX}\n\n{prompt}", kwargs))


class GenerateUsingKnownStoryGenerator(ServerSettingsGenerator):
    def inner_generate(
           self,
           agent_service: AgentService,
           context: AgentContext,
           wait_on_task: Task = None,
           generation_config: Optional[dict] = None
    ) -> Task:
        generator = get_story_text_generator(context)
        server_settings = get_server_settings(context)

        media_name = server_settings.media_name
        if not media_name:
            raise SteamshipError(message="No media name from which to generate an adventure.")

        variables = {
            "media_name": media_name
        }

        characters_result = characters_generator.generate(variables, generator, context, generation_config).text
        variables["characters"] = characters_result

        adventure_name_result = adventure_name_generator.generate(variables, generator, context, generation_config).text
        variables["adventure_name"] = adventure_name_result
        server_settings.name = adventure_name_result

        description_result = description_generator.generate(variables, generator, context, generation_config).text
        server_settings.description = description_result

        save_server_settings(server_settings, context)

        # Generate suggestion
        next_generator = GenerateUsingTitleAndDescriptionGenerator()
        return next_generator.inner_generate(
            agent_service,
            context,
            wait_on_task=wait_on_task,
            generation_config=generation_config
        )

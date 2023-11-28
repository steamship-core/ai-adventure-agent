from typing import Optional

from steamship import Task
from steamship.agents.schema import AgentContext

from generators.server_settings_generator import ServerSettingsGenerator
from generators.server_settings_generators.generate_using_title_and_description_generator import (
    GenerateUsingTitleAndDescriptionGenerator,
)
from utils.agent_service import AgentService
from utils.context_utils import get_server_settings


class GenerateUsingTitleAndStoryGenerator(ServerSettingsGenerator):
    """Generates a Adventure Template based on a short story's title and content.

    - If the story is too long, it takes a prefix of it to avoid going through the token budget.

    Assumptions:

    - Requires the title and story

    Connections to other generators:

    - Just turns the story into a 2-3 paragraph description and then defers to the generator
      which uses that shorter description as the starting place. This way we have a clean way to
      reuse these generation pipelines in a variety of ways (e.g. generate from a book jacket,
      genereate a plot from Shakeaspeare and then pass it to the description generator)
    """

    def inner_generate(
        self,
        agent_service: AgentService,
        context: AgentContext,
        wait_on_task: Task = None,
        generation_config: Optional[dict] = None,
    ) -> Task:
        # Assemble a linked list of things to generate
        server_settings = get_server_settings(context)

        title = server_settings.name
        story = server_settings.source_story_text

        if not title:
            raise ValueError("No title from which to generate an adventure.")
        if not story:
            raise ValueError("No story from which to generate an adventure.")

        # First we generate the description from the story text.
        create_description_task = self.schedule_generation(
            "description", ["description"], [], agent_service
        )

        next_generator = GenerateUsingTitleAndDescriptionGenerator()
        return next_generator.inner_generate(
            agent_service,
            context,
            wait_on_task=create_description_task,
            generation_config=generation_config,
        )

from typing import Optional

from steamship import SteamshipError, Task
from steamship.agents.schema import AgentContext

from generators.server_settings_generator import ServerSettingsGenerator
from utils.agent_service import AgentService
from utils.context_utils import get_server_settings

# Note: We go somewhat in reverse to the generate_all_generator since the idea here is to use an existing
#       story and whiddle it down (rather than build up). The constituent generators know we're in this mode
#       because of the presence of the story text, which is an encapsulation leak that we can consider fixing
#       later if it's actually a problem.
#
# Note: should_block is True for all of these because we don't want to awaken the parallel state management ghosts.
GENERATE_KEY_PATHS_AND_SHOULD_BLOCK = [
    [["narrative_voice"], True],  # Genre
    [["narrative_tone"], True],  # Writing Style
    [["short_description"], True],
    [["adventure_goal"], True],
    [["adventure_background"], True],
    # [["image"], True],
    [["tags", 0], True],
    [["tags", 1], True],
    [["tags", 2], True],
    [["characters", 0, "name"], True],
    [["characters", 0, "tagline"], True],
    [["characters", 0, "background"], True],
    [["characters", 0, "description"], True],
    # [["characters", 0, "image"], True],
    [["characters", 1, "name"], True],
    [["characters", 1, "tagline"], True],
    [["characters", 1, "background"], True],
    [["characters", 1, "description"], True],
    # [["characters", 1, "image"], True],
]


class GenerateUsingTitleAndDescriptionGenerator(ServerSettingsGenerator):
    """Generates a Adventure Template based on a short story's title and content.

    - If the story is too long, it takes a prefix of it to avoid going through the token budget.

    ASSUMPTIONS: Requires the title and story
    """

    @staticmethod
    def get_style() -> str:
        return "reddit"

    def inner_generate(
        self,
        agent_service: AgentService,
        context: AgentContext,
        wait_on_task: Task = None,
        generation_config: Optional[dict] = None,
    ) -> Task:
        # Assemble a linked list of things to generate
        server_settings = get_server_settings(context)
        fields_to_generate = []

        title = server_settings.name
        if not title:
            fields_to_generate.append([["name"], True])

        description = server_settings.description
        if not description:
            raise SteamshipError(
                message="No description from which to generate an adventure."
            )

        last_task = wait_on_task

        fields_to_generate.extend(GENERATE_KEY_PATHS_AND_SHOULD_BLOCK)

        for field_key_path_and_should_block in fields_to_generate:
            field_key_path = field_key_path_and_should_block[0]
            should_block = field_key_path_and_should_block[1]

            wait_on_tasks = [last_task] if last_task else []

            # Either something like `name` or `characters.name`
            if len(field_key_path) == 3:
                field_name = field_key_path[2]
            else:
                field_name = field_key_path[0]

            generation_config = generation_config or {}

            generation_config.update({"variant": "generate-from-description"})

            this_task = self.schedule_generation(
                field_name,
                field_key_path,
                wait_on_tasks,
                agent_service,
                generation_config=generation_config,
            )
            if should_block:
                last_task = this_task

        return last_task

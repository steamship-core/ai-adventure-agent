from steamship import Task
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

    def inner_generate(
        self,
        agent_service: AgentService,
        context: AgentContext,
        wait_on_task: Task = None,
    ) -> Task:
        # Assemble a linked list of things to generate
        server_settings = get_server_settings(context)

        title = server_settings.name
        description = server_settings.description

        if not title:
            raise ValueError("No title from which to generate an adventure.")
        if not description:
            raise ValueError("No description from which to generate an adventure.")

        raise NotImplementedError()

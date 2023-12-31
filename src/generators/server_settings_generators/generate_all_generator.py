from typing import Optional

from steamship import Task
from steamship.agents.schema import AgentContext

from generators.server_settings_generator import ServerSettingsGenerator
from utils.agent_service import AgentService

# Note: should_block is True for all of these because we don't want to awaken the parallel state management ghosts.
GENERATE_KEY_PATHS_AND_SHOULD_BLOCK = [
    [["narrative_voice"], True],  # Genre
    [["narrative_tone"], True],  # Writing Style
    [["name"], True],
    [["short_description"], True],
    [["description"], True],
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


class GenerateAllGenerator(ServerSettingsGenerator):
    """Generates an ENTIRE Adventure Template given no inputs at all: whatever comes out is totally up to the LLM."""

    def inner_generate(
        self,
        agent_service: AgentService,
        context: AgentContext,
        wait_on_task: Task = None,
        generation_config: Optional[dict] = None,
    ) -> Task:
        # Assemble a linked list of things to generate
        last_task = wait_on_task
        for field_key_path_and_should_block in GENERATE_KEY_PATHS_AND_SHOULD_BLOCK:
            field_key_path = field_key_path_and_should_block[0]
            should_block = field_key_path_and_should_block[1]

            wait_on_tasks = [last_task] if last_task else []

            # Either something like `name` or `characters.name`
            if len(field_key_path) == 3:
                field_name = field_key_path[2]
            else:
                field_name = field_key_path[0]

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

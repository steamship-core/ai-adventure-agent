from steamship import Task
from steamship.agents.schema import AgentContext

from generators.adventure_template_generator import AdventureTemplateGenerator
from utils.agent_service import AgentService

GENERATE_KEY_PATHS = [
    ["name"],
    ["short_description"],
    ["description"],
    ["adventure_goal"],
    ["adventure_background"],
    ["narrative_tone"],
    ["narrative_voice"],
    ["image"],
    ["tags", 0],
    ["tags", 1],
    ["tags", 2],
]


class GenerateAllGenerator(AdventureTemplateGenerator):
    """Generates the entire Adventure Template given nothing."""

    def inner_generate(
        self, agent_service: AgentService, context: AgentContext
    ) -> Task:
        # Assemble a linked list of things to generate
        last_task = None
        for field_key_path in GENERATE_KEY_PATHS:
            wait_on_tasks = [last_task] if last_task else []

            # Either something like `name` or `characters.name`
            if len(field_key_path) == 3:
                field_name = f"{field_key_path[0]}.{field_key_path[2]}"
            else:
                field_name = field_key_path[0]

            last_task = self.schedule_generation(
                field_name, field_key_path, wait_on_tasks, agent_service
            )

        return last_task

from steamship import SteamshipError, Task
from steamship.agents.schema import AgentContext

from generators.adventure_template_generator import AdventureTemplateGenerator
from utils.agent_service import AgentService
from utils.context_utils import get_adventure_template


class GenerateUsingTitleAndStoryGenerator(AdventureTemplateGenerator):
    """Generates a Adventure Template based on a short story's title and content.

    - If the story is too long, it takes a prefix of it to avoid going through the token budget.

    ASSUMPTIONS: Requires the title and story

    """

    def inner_generate(
        self, agent_service: AgentService, context: AgentContext
    ) -> Task:
        # Assemble a linked list of things to generate
        adventure_template = get_adventure_template(context)

        title = adventure_template.name
        story = adventure_template.source_story_text

        if not title:
            raise SteamshipError(
                message="No title from which to generate an adventure."
            )
        if not story:
            raise SteamshipError(
                message="No story from which to generate an adventure."
            )

        raise NotImplementedError()

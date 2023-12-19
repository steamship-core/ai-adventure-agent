import json
import logging
from typing import Optional

from steamship import Block, MimeTypes, PluginInstance
from steamship.agents.schema import AgentContext

from generators.server_settings_field_generator import ServerSettingsFieldGenerator
from generators.utils import safe_format
from schema.quest import QuestDescription
from utils.context_utils import get_quest_arc_generator


class AdventureFixedQuestArcGenerator(ServerSettingsFieldGenerator):
    prompt = """# Instructions

You are an expert storyteller. We need you to design {quests_per_arc} narrative arcs for an story based the story pitch.
The arcs should be in increasing difficulty that the main character will go through to achieve their goal.

# Story Pitch

Title: {name}

{description}

# Narrative Arcs

Now design {quests_per_arc} narrative arcs for that story pitch.
They should fit the setting of the story.

Responses should ONLY be in the form of: GOAL: <goal> LOCATION: <location name>

Examples (for a story about a dog):
GOAL: find a treat LOCATION: Dog Park
GOAL: make a friend LOCATION: Main Street
GOAL: get bacon from the butcher LOCATION: Butcher Shop
GOAL: learn a new trick LOCATION: Trainer's Office
GOAL: fetch the newspaper LOCATION: Owner's House
GOAL: prevent a robbery LOCATION: Owner's Store
GOAL: impress the teacher during a show and tell LOCATION: Owner's Kid's School
GOAL: steal some turkey LOCATION: Thanksgiving Dinner at Grandma's
GOAL: get your nails trimmed LOCATION: Dog Wash
GOAL: win an award LOCATION: Westminister Dog Show

Narrative arcs for the story pitch above:"""

    @staticmethod
    def get_field() -> str:
        return "fixed_quest_arc"

    def inner_generate(
        self,
        variables: dict,
        generator: PluginInstance,
        context: AgentContext,
        generation_config: Optional[dict] = None,
    ) -> Block:

        # NOTE: We use a specific generator for this because it's important it's gpt-4
        # otherwise the prompts have been a bit too shaky.
        generator = get_quest_arc_generator(context)

        prompt = self.prompt

        task = generator.generate(
            text=safe_format(prompt, variables),
            streaming=True,
            append_output_to_file=True,
            make_output_public=True,
        )
        block = self.task_to_str_block(task)
        logging.info(f"Generated quest_arcs: {block.text}")

        quest_arc = []
        items = block.text.split("GOAL:")
        for item in items:
            if len(item.strip()) > 0 and "LOCATION" in item:
                parts = item.split("LOCATION:")
                if len(parts) == 2:
                    goal = parts[0].strip()
                    location = parts[1].strip().rstrip(".")
                    if "\n" in location:
                        location = location[: location.index("\n")]
                    quest_arc.append(
                        QuestDescription(goal=goal, location=location).dict()
                    )

        block.text = json.dumps(quest_arc)
        block.mime_type = MimeTypes.JSON
        return block

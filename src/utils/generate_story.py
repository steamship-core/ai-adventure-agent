import json
import os
import sys

import yaml
from steamship import Steamship

PROMPT_PREFIX = "Answer with the minimum amount of information necessary to satisfy the request."


class StoryGenerator:
    def __init__(self, steamship: Steamship):
        self.steamship = steamship
        self.generator = steamship.use_plugin("gpt-4")

    def ask_gpt_min(self, prompt: str):
        return self.ask_gpt(f"{PROMPT_PREFIX}\n\n{prompt}")

    def ask_gpt(self, prompt: str) -> str:
        return self.generator.generate(text=prompt, streaming=False, options=dict(max_tokens=512)).wait_until_completed().blocks[0].text

    def generate_story(self, media_name: str):
        print("Getting characters...", file=sys.stderr)
        characters = self.ask_gpt_min(f"Respond with one name per line.  Who are the main characters associated with \"{media_name}\"?  List protagonists first.")
        print("Getting title...", file=sys.stderr)
        title = self.ask_gpt_min(f"Come up with the title for an unpublished \"{media_name}\" story involving the characters:\n\n{characters}")
        print("Getting description...", file=sys.stderr)
        description = self.ask_gpt_min(f"Come up with three paragraphs describing the beginning of a plot for the unpublished \"{media_name}\" story \"{title}\" involving the characters:\n\n{characters}")
        print("Getting summary...", file=sys.stderr)
        summary = self.ask_gpt_min(f"Come up with a one sentence summary of this story:\n\n{description}")

        print("Getting quests...", file=sys.stderr)
        quests = self.ask_gpt_min(f"Format your result as a full, valid, json array, containing objects with keys \"name\", \"location\", and \"description\".  Come up with five chapter names for this unpublished \"{media_name}\" story, without prepending chapter numbers:\n\n{description}")
        print(quests, file=sys.stderr)
        quests = json.loads(quests)
        for quest in quests:
            assert "name" in quest and "location" in quest and "description" in quest
            quest["goal"] = quest["name"]
            del quest["name"]

        character_names = characters.split("\n")
        chars = []
        for character_name in character_names[:1]:
            tagline = self.ask_gpt_min(f"Describe the character \"{character_name}\" from \"{media_name}\" in one sentence.")
            char = {
                "name": character_name,
                "tagline": tagline
            }
            chars.append(char)

        result = {
            "name": title,
            "adventure_name": title,
            "description": description,
            "adventure_description": description,
            "short_description": summary,
            "adventure_short_description": summary,
            "characters": chars,
            "fixed_quest_arc": quests
        }
        return result


if __name__ == "__main__":
    media_name = "Captain America"
    if len(sys.argv) > 1:
        media_name = sys.argv[1]
    with Steamship.temporary_workspace() as client:
        story_gen = StoryGenerator(client)
        print(yaml.dump(story_gen.generate_story(media_name)))

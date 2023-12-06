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
        return self.generator.generate(text=prompt, streaming=False).wait_until_completed().blocks[0].text

    def generate_story(self, media_name: str):
        characters = self.ask_gpt_min(f"Respond with one name per line.  Who are the main characters associated with \"{media_name}\"?  List protagonists first.")
        title = self.ask_gpt_min(f"Come up with the title for an unpublished \"{media_name}\" story involving the characters:\n\n{characters}")
        description = self.ask_gpt_min(f"Come up with three paragraphs describing the beginning of a plot for the unpublished \"{media_name}\" story \"{title}\" involving the characters:\n\n{characters}")
        summary = self.ask_gpt_min(f"Come up with a one sentence summary of this story:\n\n{description}")

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
            "characters": chars
        }
        return result


if __name__ == "__main__":
    media_name = "Captain America"
    if len(sys.argv) > 1:
        media_name = sys.argv[1]
    with Steamship.temporary_workspace() as client:
        story_gen = StoryGenerator(client)
        print(yaml.dump(story_gen.generate_story(media_name)))

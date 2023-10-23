from steamship.agents.schema import AgentContext

from generators.social_media_generator import SocialMediaGenerator
from schema.quest import Quest
from utils.context_utils import get_game_state, get_story_text_generator


class HaikuTweetGenerator(SocialMediaGenerator):
    def generate_shareable_quest_snippet(
        self, quest: Quest, context: AgentContext
    ) -> str:
        game_state = get_game_state(context)
        generator = get_story_text_generator(context)

        prompt = f"Write a funny, sassy haiku about the following story: {quest.text_summary}"
        haiku_task = generator.generate(text=prompt)
        haiku_task.wait()  # this should be a short Task

        haiku_text = quest.text_summary
        output_blocks = haiku_task.output.blocks
        if len(output_blocks) >= 0:
            haiku_text = output_blocks[0].text

        quests_total = len(game_state.quest_arc)
        quests_completed = sum(
            map(lambda q: q.completed_timestamp is not None, game_state.quests)
        )
        quests_left = quests_total - quests_completed
        green_progress = "🟩" * quests_completed
        grey_progress = "⬜" * quests_left
        progress_bar = "".join([green_progress, grey_progress])

        # TODO: validate haiku length
        tweet_body = f"{haiku_text}\n\n{progress_bar}\n\n#ai-adventure"

        if len(quest.new_items) > 0:
            item = quest.new_items[0]
            # title = urllib.parse.quote(item.name, safe="")
            # description = urllib.parse.quote(item.description, safe="")

            # TODO: validate picture url format and indices
            picture_url = item.picture_url
            raw_less = picture_url.rstrip("/raw")
            slash_index = raw_less.rfind("/") + 1
            block_id = raw_less[slash_index:]
            url = f"https://ai-adventure.steamship.com/og?blockId={block_id}"
            # url = f"https://ai-adventure.steamship.com/social/items/share?title={title}&description={description}&block_id={block_id}"
            tweet_body = f"{tweet_body}\n\n{url}"

        return tweet_body

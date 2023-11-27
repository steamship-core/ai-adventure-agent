import requests
from bs4 import BeautifulSoup
from steamship import SteamshipError, Task
from steamship.agents.schema import AgentContext

from generators.adventure_template_generator import AdventureTemplateGenerator
from generators.adventure_template_generators.generate_using_title_and_story_generator import (
    GenerateUsingTitleAndStoryGenerator,
)
from utils.agent_service import AgentService
from utils.context_utils import get_adventure_template, save_adventure_template


class GenerateUsingRedditPostGenerator(AdventureTemplateGenerator):
    """Generates an Adventure Template based on a Reddit post's Title and Content.

    Works by scraping the contents of the provided Reddit URL and then applying the GenerateUsingTitleAndStoryGenerator."""

    def inner_generate(
        self, agent_service: AgentService, context: AgentContext
    ) -> Task:
        # Get the URL to scrape
        adventure_template = get_adventure_template(context)
        url = adventure_template.source_url

        if not url:
            raise SteamshipError(
                message="No `source_url` variable was present on the provided Adventure Template."
            )
        if "reddit.com" not in url:
            raise SteamshipError(
                message="The `source_url` variable does not contain reddit.com"
            )

        reddit_resp = requests.get(url)
        reddit = BeautifulSoup(reddit_resp.text, "html.parser")

        # post_content = reddit.find(class_ = "post-content")

        # Get the content
        title = reddit.find(lambda tag: tag.name == "shreddit-title")
        title_text = title["title"]

        # Get the content
        body = reddit.find(
            lambda tag: tag.name == "div"
            and tag.has_attr("slot")
            and tag["slot"] == "text-body"
        )
        body_text = body.text

        if not title_text:
            raise SteamshipError(
                message=f"Unable to find title from Reddit post at {url}"
            )
        if not body_text:
            raise SteamshipError(
                message=f"Unable to find body text from Reddit post at {url}"
            )

        title_text = title_text.split("]")[1]
        title_text = title_text.split(" : ")[0]
        title_text = title_text.strip()

        body_text = body_text.strip()

        adventure_template.name = title_text
        adventure_template.source_story_text = body_text
        save_adventure_template(adventure_template, context)

        generator = GenerateUsingTitleAndStoryGenerator()
        return generator.generate(agent_service=agent_service, context=context)

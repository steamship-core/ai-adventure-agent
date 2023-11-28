from typing import Optional

import requests
from bs4 import BeautifulSoup
from steamship import SteamshipError, Task
from steamship.agents.schema import AgentContext

from generators.server_settings_generator import ServerSettingsGenerator
from generators.server_settings_generators.generate_using_title_and_story_generator import (
    GenerateUsingTitleAndStoryGenerator,
)
from utils.agent_service import AgentService
from utils.context_utils import get_server_settings, save_server_settings


class GenerateUsingRedditPostGenerator(ServerSettingsGenerator):
    """Generates an Adventure Template based on a Reddit post's Title and Content.

    Works by scraping the contents of the provided Reddit URL and then applying the GenerateUsingTitleAndStoryGenerator."""

    def inner_generate(
        self,
        agent_service: AgentService,
        context: AgentContext,
        wait_on_task: Task = None,
        generation_config: Optional[dict] = None,
    ) -> Task:
        # Get the URL to scrape
        server_settings = get_server_settings(context)
        url = server_settings.source_url

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

        server_settings.name = title_text
        server_settings.source_story_text = body_text
        save_server_settings(server_settings, context)

        generator = GenerateUsingTitleAndStoryGenerator()
        return generator.inner_generate(
            agent_service=agent_service,
            context=context,
            wait_on_task=wait_on_task,
            generation_config=generation_config,
        )

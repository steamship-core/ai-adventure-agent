from typing import List, Optional

from pydantic import Field

from schema.characters import Character
from schema.server_settings import ServerSettings


class AdventureTemplate(ServerSettings):
    """Adventure Template is a game one might play.

    This is a superset of:
     - ServerSettings - the game parameters of the game in progress
     - GameState - the gameplay parameters of the game in progress

    This AdventureTemplate object isn't used to actually play the game. It's just a typed mirror of some of the
    data that needs to exist on the website side of things:

     - Marketing and SEO information:
        - description
        - tags

     - Template characters to play
        - Name
        - Description
        - Image
        - etc

     The only reason this information is typed out on the agent-side of things is that GAME DESIGN is as much a part
     of this experience as GAME PLAY -- and this object describes part of the model of the game design process.

     That enables us to assist in suggestions & auto-generation
    """

    source_url: Optional[str] = Field(
        default=None,
        description="The source URL from which this adventure template originates",
    )

    source_story_text: Optional[str] = Field(
        default=None,
        description="The source story text from which this adventure template originates",
    )

    description: Optional[str] = Field(
        default="An amazing story of exploration.",
        description="What is a short, 4-8 word description of the story?",
    )

    tags: Optional[List[Optional[str]]] = Field(
        default=None, description="List of tags that describe this Adventure Template"
    )

    characters: Optional[List[Optional[Character]]] = Field(
        default=None, description=""
    )

    def update_from_web(self, other: "AdventureTemplate"):  # noqa: C901
        """Perform a gentle update so that the website doesn't accidentally blast over this if it diverges in
        structure."""

        # Override values if they're present in the new version, but not in the old
        # Possible clobber here if the web doesn't send a value for a field with a default,
        # since it will be filled in when the ServerSettings object is init'd
        for k, v in other.dict().items():
            if v is not None:
                setattr(self, k, v)

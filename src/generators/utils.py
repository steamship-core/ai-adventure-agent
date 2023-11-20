from steamship.agents.schema import AgentContext

from schema.dalle_theme import DEFAULT_THEME, PREMADE_THEMES
from utils.context_utils import get_server_settings


def safe_format(text: str, params: dict) -> str:
    """Safely formats a user-provided string by replacing {key} with `value` for all (key,value) pairs in `params`."""
    ret = text
    for (key, value) in params.items():
        if value is not None:
            ret = ret.replace("{" + key + "}", str(value))

    return ret


def get_theme(name: str, context: AgentContext) -> StableDiffusionTheme:
    server_settings = get_server_settings(context)
    for theme in server_settings.image_themes or []:
        if name == theme.name:
            return theme
    for theme in PREMADE_THEMES:
        if name == theme.name:
            return theme
    return DEFAULT_THEME

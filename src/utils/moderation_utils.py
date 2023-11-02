from typing import Final

from steamship import Block
from steamship.data.tags.tag_utils import get_tag

_ADMIN_TAG_KIND: Final[str] = "admin"
_EXCLUDED_TAG_NAME: Final[str] = "excluded"


def mark_block_as_excluded(block: Block):
    if not block:
        return
    block._one_time_set_tag(
        tag_kind=_ADMIN_TAG_KIND,
        tag_name=_EXCLUDED_TAG_NAME,
        string_value="flagged",
    )


def is_block_excluded(block: Block) -> bool:
    if not block:
        return True
    return (
        True
        if get_tag(tags=block.tags, kind=_ADMIN_TAG_KIND, name=_EXCLUDED_TAG_NAME)
        else False
    )

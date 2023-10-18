import time
from typing import Dict, Optional

from steamship import Block, File, Task, TaskState


def await_blocks_created_and_task_started(
    num_known_blocks: int,
    file: File,
    task: Task,
    new_block_tag_kind: str,
    new_block_tag_name: str,
) -> Task:
    while new_block_not_present(
        file, num_known_blocks, new_block_tag_kind, new_block_tag_name
    ) or (task.state in [TaskState.waiting]):
        time.sleep(0.1)
        file.refresh()
        task.refresh()
    return task


def new_block_not_present(
    file: File, num_known_blocks: int, new_block_tag_kind: str, new_block_tag_name: str
) -> bool:
    return (
        find_new_block(file, num_known_blocks, new_block_tag_kind, new_block_tag_name)
        is None
    )


def find_new_block(
    file: File, num_known_blocks: int, new_block_tag_kind: str, new_block_tag_name: str
) -> Optional[Block]:
    if len(file.blocks) == num_known_blocks:
        return None
    else:
        for block in file.blocks[num_known_blocks:]:
            if block.tags is not None:
                for tag in block.tags:
                    if (
                        tag.kind == new_block_tag_kind
                        and tag.name == new_block_tag_name
                    ):
                        return block
    return None


def safe_format(
    text: str, params: dict, loras_and_triggers: Optional[Dict[str, str]] = None
) -> str:
    """Safely formats a user-provided string by replacing {key} with `value` for all (key,value) pairs in `params`."""
    ret = text
    for (key, value) in params.items():
        ret = ret.replace(f"{key}", value)

    # If a Lora -> Trigger dict was provided, make sure to include all the triggers
    if loras_and_triggers:
        triggers = [trigger for (lora, trigger) in loras_and_triggers.items()]
        trigger_list = ",".join(triggers)
        ret = f"{trigger_list}, {ret}"

    return ret

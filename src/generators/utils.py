import time
from typing import Optional

from steamship import File, Task, TaskState, Block


def await_blocks_created_and_task_started(
    num_known_blocks: int, file: File, task: Task, new_block_tag_kind: str, new_block_tag_name: str
) -> Task:
    while new_block_not_present(file, num_known_blocks, new_block_tag_kind, new_block_tag_name) or (task.state in [TaskState.waiting]):
        time.sleep(0.1)
        file.refresh()
        task.refresh()
    return task


def new_block_not_present(file: File, num_known_blocks: int, new_block_tag_kind: str, new_block_tag_name: str) -> bool:
    return find_new_block(file, num_known_blocks, new_block_tag_kind, new_block_tag_name) is None


def find_new_block(file: File, num_known_blocks: int, new_block_tag_kind: str, new_block_tag_name: str) -> Optional[Block]:
    if len(file.blocks) == num_known_blocks:
        return None
    else:
        for block in file.blocks[num_known_blocks:]:
            if block.tags is not None:
                for tag in block.tags:
                    if tag.kind == new_block_tag_kind and tag.name == new_block_tag_name:
                        return block
    return None



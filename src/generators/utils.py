import time

from steamship import File, Task, TaskState


def await_blocks_created_and_task_started(
    num_known_blocks: int, file: File, task: Task
) -> Task:
    while (len(file.blocks) == num_known_blocks) or (task.state in [TaskState.waiting]):
        time.sleep(0.1)
        file.refresh()
        task.refresh()
    return task

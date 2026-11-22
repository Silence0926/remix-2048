"""Task service for 2048 Remix."""


def generate_tasks(game):
    game.tasks = game.generate_random_tasks_fn(game.rng)


def task_text(task):
    if task["type"] == "tile_in_steps":
        return f"Reach {task['target_tile']} in {task['max_steps']} steps"
    if task["type"] == "double_merge_total":
        return f"Trigger {task['target']} double-merges ({task['progress']}/{task['target']})"
    if task["type"] == "reach_score":
        return f"Reach score {task['target_score']}"
    return "Unknown task"


def get_task_status(task):
    if task["done"]:
        return "done"
    if task["failed"]:
        return "failed"
    return "running"


def complete_task(game, task):
    task["done"] = True
    game.tasks_completed += 1
    reward = task["reward"]
    game.score += reward
    game.show_info("Task Complete!", f"+{reward} bonus score")


def evaluate_tasks(game, highest_tile, merged_count):
    for task in game.tasks:
        if task["done"] or task["failed"]:
            continue

        if task["type"] == "tile_in_steps":
            if highest_tile >= task["target_tile"] and game.steps_taken <= task["max_steps"]:
                complete_task(game, task)
            elif game.steps_taken > task["max_steps"]:
                task["failed"] = True
        elif task["type"] == "double_merge_total":
            if merged_count >= 2:
                task["progress"] += 1
            if task["progress"] >= task["target"]:
                complete_task(game, task)
        elif task["type"] == "reach_score":
            if game.score >= task["target_score"]:
                complete_task(game, task)

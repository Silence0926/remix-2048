"""State snapshot helpers for 2048 Remix."""


def build_snapshot(game):
    return {
        "grid": [row[:] for row in game.grid],
        "score": game.score,
        "combo_streak": game.combo_streak,
        "game_over": game.game_over,
        "max_tile": game.max_tile,
        "max_combo_streak": game.max_combo_streak,
        "milestones_reached": game.milestones_reached.copy(),
        "steps_taken": game.steps_taken,
        "best_move_score": game.best_move_score,
        "best_move_turn": game.best_move_turn,
        "mode_name": game.mode_name,
        "remaining_time": game.remaining_time,
        "tasks": [task.copy() for task in game.tasks],
        "tasks_completed": game.tasks_completed,
        "hammer_uses": game.hammer_uses,
        "freeze_uses": game.freeze_uses,
        "selected_tool": game.selected_tool,
        "frozen_cells": game.frozen_cells.copy(),
        "daily_seed": game.daily_seed,
        "rng_state": game.rng.getstate(),
    }


def restore_snapshot(game, snapshot):
    game.grid = [row[:] for row in snapshot["grid"]]
    game.score = snapshot["score"]
    game.combo_streak = snapshot["combo_streak"]
    game.game_over = snapshot["game_over"]
    game.max_tile = snapshot["max_tile"]
    game.max_combo_streak = snapshot["max_combo_streak"]
    game.milestones_reached = snapshot["milestones_reached"].copy()
    game.steps_taken = snapshot["steps_taken"]
    game.best_move_score = snapshot["best_move_score"]
    game.best_move_turn = snapshot["best_move_turn"]
    game.mode_name = snapshot.get("mode_name", game.mode_name)
    game.remaining_time = snapshot.get("remaining_time", game.remaining_time)
    game.mode_var.set(game.mode_name)
    game.tasks = [task.copy() for task in snapshot["tasks"]]
    game.tasks_completed = snapshot["tasks_completed"]
    game.hammer_uses = snapshot["hammer_uses"]
    game.freeze_uses = snapshot["freeze_uses"]
    game.selected_tool = snapshot["selected_tool"]
    game.frozen_cells = snapshot["frozen_cells"].copy()
    if "rng_state" in snapshot:
        game.rng.setstate(snapshot["rng_state"])
    game.daily_seed = snapshot.get("daily_seed", game.daily_seed)

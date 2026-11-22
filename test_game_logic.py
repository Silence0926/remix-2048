"""Minimal logic regression checks for refactored 2048 Remix modules.

Run: python test_game_logic.py
"""

import random

from game_engine import build_move, check_game_over, tick_frozen_cells
from game_rules import generate_random_tasks
from game_state import build_snapshot, restore_snapshot


class _ModeVar:
    def __init__(self):
        self.value = None

    def set(self, value):
        self.value = value


class DummyGame:
    def __init__(self):
        self.grid = [[2, 0, 0, 0], [2, 4, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        self.score = 10
        self.combo_streak = 1
        self.game_over = False
        self.max_tile = 4
        self.max_combo_streak = 2
        self.milestones_reached = set([4])
        self.steps_taken = 3
        self.best_move_score = 16
        self.best_move_turn = 2
        self.mode_name = "Classic"
        self.remaining_time = 120
        self.tasks = []
        self.tasks_completed = 0
        self.hammer_uses = 2
        self.freeze_uses = 2
        self.selected_tool = None
        self.frozen_cells = {(0, 0): 2}
        self.daily_seed = None
        self.rng = random.Random(123)
        self.mode_var = _ModeVar()


def test_engine_freeze_blocks_merge():
    grid = [
        [2, 0, 2, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    frozen = {(0, 1): 2}
    result = build_move(grid, frozen, 4, "left")
    assert result["new_grid"][0] == [2, 0, 2, 0], "Frozen lock should split movement segment"
    assert not result["merge_happened"], "Tiles separated by a lock must not merge"


def test_engine_basic_merge():
    grid = [
        [2, 2, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    result = build_move(grid, {}, 4, "left")
    assert result["new_grid"][0] == [4, 0, 0, 0]
    assert result["move_base_score"] == 4
    assert result["merged_in_move"] == 1


def test_tick_frozen_cells():
    frozen = {(0, 0): 2, (1, 1): 1}
    updated = tick_frozen_cells(frozen)
    assert updated == {(0, 0): 1}


def test_check_game_over_with_locks():
    grid = [
        [2, 4, 2, 4],
        [4, 2, 4, 2],
        [2, 4, 2, 4],
        [4, 2, 4, 2],
    ]
    assert check_game_over(grid, {}, 4)


def test_task_generation_seeded_repeatable():
    rng_a = random.Random(20260728)
    rng_b = random.Random(20260728)
    tasks_a = generate_random_tasks(rng_a)
    tasks_b = generate_random_tasks(rng_b)
    assert tasks_a == tasks_b


def test_snapshot_restore_roundtrip():
    game = DummyGame()
    snapshot = build_snapshot(game)

    game.score = 999
    game.grid[0][0] = 64
    game.mode_name = "Timed"

    restore_snapshot(game, snapshot)
    assert game.score == 10
    assert game.grid[0][0] == 2
    assert game.mode_name == "Classic"
    assert game.mode_var.value == "Classic"


def run_all():
    test_engine_freeze_blocks_merge()
    test_engine_basic_merge()
    test_tick_frozen_cells()
    test_check_game_over_with_locks()
    test_task_generation_seeded_repeatable()
    test_snapshot_restore_roundtrip()
    print("All logic tests passed")


if __name__ == "__main__":
    run_all()

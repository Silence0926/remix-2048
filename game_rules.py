"""Core gameplay rule helpers for 2048 Remix."""

import random


def compress_row(row, size):
    new_row = [num for num in row if num != 0]
    new_row += [0] * (size - len(new_row))
    return new_row


def merge_row(row, size):
    gained = 0
    merged_count = 0
    for i in range(size - 1):
        if row[i] != 0 and row[i] == row[i + 1]:
            row[i] *= 2
            gained += row[i]
            merged_count += 1
            row[i + 1] = 0
    return row, gained, merged_count


def has_valid_moves(grid, size):
    for row in grid:
        if 0 in row:
            return True

    for i in range(size):
        for j in range(size - 1):
            if grid[i][j] == grid[i][j + 1]:
                return True

    for j in range(size):
        for i in range(size - 1):
            if grid[i][j] == grid[i + 1][j]:
                return True

    return False


def generate_random_tasks(rng=None):
    rnd = rng if rng is not None else random
    pool = [
        {
            "type": "tile_in_steps",
            "target_tile": rnd.choice([64, 128, 256]),
            "max_steps": rnd.choice([8, 10, 12]),
            "reward": rnd.choice([180, 220, 260]),
            "done": False,
            "failed": False,
        },
        {
            "type": "double_merge_total",
            "target": rnd.choice([2, 3, 4]),
            "progress": 0,
            "reward": rnd.choice([200, 240, 280]),
            "done": False,
            "failed": False,
        },
        {
            "type": "reach_score",
            "target_score": rnd.choice([900, 1200, 1600]),
            "reward": rnd.choice([150, 200, 250]),
            "done": False,
            "failed": False,
        },
    ]
    return rnd.sample(pool, k=rnd.choice([1, 2]))

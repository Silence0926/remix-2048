"""Core move engine for 2048 Remix with lock-aware movement."""


def process_segment(segment):
    size = len(segment)
    compressed = [num for num in segment if num != 0]
    compressed += [0] * (size - len(compressed))

    gained = 0
    merged_count = 0
    for idx in range(size - 1):
        if compressed[idx] != 0 and compressed[idx] == compressed[idx + 1]:
            compressed[idx] *= 2
            gained += compressed[idx]
            merged_count += 1
            compressed[idx + 1] = 0

    final = [num for num in compressed if num != 0]
    final += [0] * (size - len(final))
    return final, gained, merged_count


def process_line_with_locks(line_values, locked_mask):
    result = line_values[:]
    gained_total = 0
    merged_total = 0
    n = len(line_values)
    start = 0

    while start < n:
        if locked_mask[start]:
            start += 1
            continue

        end = start
        while end < n and not locked_mask[end]:
            end += 1

        segment = line_values[start:end]
        final_segment, gained, merged_count = process_segment(segment)
        result[start:end] = final_segment
        gained_total += gained
        merged_total += merged_count
        start = end

    moved = result != line_values
    return result, moved, gained_total, merged_total


def build_move(grid, frozen_cells, size, direction):
    moved = False
    merge_happened = False
    move_base_score = 0
    merged_in_move = 0

    if direction in ("left", "right"):
        new_grid = []
        for i, row in enumerate(grid):
            if direction == "left":
                line = row
                lock_mask = [(i, j) in frozen_cells for j in range(size)]
                final, row_moved, gained, merged_count = process_line_with_locks(line, lock_mask)
            else:
                line = row[::-1]
                lock_mask = [((i, size - 1 - j) in frozen_cells) for j in range(size)]
                final, row_moved, gained, merged_count = process_line_with_locks(line, lock_mask)
                final = final[::-1]

            new_grid.append(final)
            move_base_score += gained
            merged_in_move += merged_count
            if merged_count > 0:
                merge_happened = True
            if row_moved:
                moved = True

        return {
            "new_grid": new_grid,
            "moved": moved,
            "merge_happened": merge_happened,
            "move_base_score": move_base_score,
            "merged_in_move": merged_in_move,
        }

    new_grid = [row[:] for row in grid]
    for j in range(size):
        col = [grid[i][j] for i in range(size)]
        if direction == "up":
            line = col
            lock_mask = [(i, j) in frozen_cells for i in range(size)]
            final, col_moved, gained, merged_count = process_line_with_locks(line, lock_mask)
        else:
            line = col[::-1]
            lock_mask = [((size - 1 - i, j) in frozen_cells) for i in range(size)]
            final, col_moved, gained, merged_count = process_line_with_locks(line, lock_mask)
            final = final[::-1]

        for i in range(size):
            new_grid[i][j] = final[i]

        move_base_score += gained
        merged_in_move += merged_count
        if merged_count > 0:
            merge_happened = True
        if col_moved:
            moved = True

    return {
        "new_grid": new_grid,
        "moved": moved,
        "merge_happened": merge_happened,
        "move_base_score": move_base_score,
        "merged_in_move": merged_in_move,
    }


def tick_frozen_cells(frozen_cells):
    new_frozen = {}
    for pos, turns_left in frozen_cells.items():
        if turns_left - 1 > 0:
            new_frozen[pos] = turns_left - 1
    return new_frozen


def can_move_in_direction(grid, frozen_cells, size, direction):
    move_result = build_move(grid, frozen_cells, size, direction)
    return move_result["new_grid"] != grid


def check_game_over(grid, frozen_cells, size):
    if any(
        grid[i][j] == 0 and (i, j) not in frozen_cells
        for i in range(size)
        for j in range(size)
    ):
        return False

    for direction in ("left", "right", "up", "down"):
        if can_move_in_direction(grid, frozen_cells, size, direction):
            return False

    return True

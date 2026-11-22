"""Tool interaction service for 2048 Remix."""


def on_cell_click(game, row, col):
    if game.game_over or game.is_animating or game.is_paused:
        return
    if game.selected_tool == "hammer":
        use_hammer(game, row, col)
    elif game.selected_tool == "freeze":
        use_freeze(game, row, col)


def activate_hammer(game, event=None):
    if game.game_over or game.hammer_uses <= 0 or game.is_animating or game.is_paused:
        return
    game.selected_tool = None if game.selected_tool == "hammer" else "hammer"
    game.update_tool_label()


def activate_freeze(game, event=None):
    if game.game_over or game.freeze_uses <= 0 or game.is_animating or game.is_paused:
        return
    game.selected_tool = None if game.selected_tool == "freeze" else "freeze"
    game.update_tool_label()


def use_hammer(game, row, col):
    if game.hammer_uses <= 0:
        return
    if (row, col) in game.frozen_cells:
        game.selected_tool = None
        game.update_tool_label()
        game.show_info("Hammer", "Frozen tiles cannot be broken right now")
        return
    if game.grid[row][col] == 0:
        game.selected_tool = None
        game.update_tool_label()
        return

    game.last_state = game.snapshot_state()
    game.grid[row][col] = 0
    game.hammer_uses -= 1
    game.selected_tool = None
    game.update_board()


def use_freeze(game, row, col):
    if game.freeze_uses <= 0:
        return
    if game.grid[row][col] == 0:
        game.selected_tool = None
        game.update_tool_label()
        game.show_info("Freeze", "Select a non-empty tile to freeze")
        return
    if (row, col) in game.frozen_cells:
        game.selected_tool = None
        game.update_tool_label()
        return

    game.last_state = game.snapshot_state()
    game.frozen_cells[(row, col)] = 3
    game.freeze_uses -= 1
    game.selected_tool = None
    game.update_board()


def toggle_mute(game, event=None):
    game.is_muted = not game.is_muted
    game.update_tool_label()

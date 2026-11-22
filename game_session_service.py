"""Session-level flow service for 2048 Remix."""


def show_info(game, title, message, force=False):
    if game.is_muted and not force:
        return
    game.messagebox.showinfo(title, message)


def check_milestones(game):
    highest = max(max(row) for row in game.grid)
    if highest > game.max_tile:
        game.max_tile = highest

    for milestone in game.milestones:
        if highest >= milestone and milestone not in game.milestones_reached:
            game.milestones_reached.add(milestone)
            game.play_milestone_animation(milestone)
            show_info(game, "Milestone!", f"Awesome! You reached {milestone}!")


def end_game(game, reason=""):
    if game.game_over:
        return

    game.game_over = True
    game.is_paused = False
    game.pause_overlay.place_forget()
    game.stop_timer()
    game.best_score = max(game.best_score, game.score)
    game.save_best_score()

    prefix = f"{reason}\n" if reason else ""
    summary = (
        f"{prefix}"
        f"Final Score: {game.score}\n"
        f"Highest Tile: {game.max_tile}\n"
        f"Max Combo: x{(1.0 + min(game.max_combo_streak, 7) * 0.2):.1f}\n"
        f"Steps: {game.steps_taken}\n"
        f"Best Move: +{game.best_move_score} (Turn {game.best_move_turn})\n"
        f"Tasks Completed: {game.tasks_completed}/{len(game.tasks)}\n"
        f"Best All-Time Score: {game.best_score}"
    )
    game.update_tool_label()
    game.update_mode_status_label()
    show_info(game, "Game Over!", summary, force=True)

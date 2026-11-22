"""Mode and timer service for 2048 Remix."""

from datetime import date
import random


def change_mode(game, selected_mode=None):
    previous_mode = game.mode_name
    game.mode_name = selected_mode if selected_mode else game.mode_var.get()
    game.mode_var.set(game.mode_name)

    if game.mode_name == "Daily" and game.size != 4:
        game.size_var.set(4)
        game.size = 4

    reset_mode_state(game)
    update_mode_status_label(game)

    if previous_mode != game.mode_name:
        game.restart_game()


def reset_mode_state(game, preserve_time=False):
    stop_timer(game)
    if not preserve_time:
        game.remaining_time = game.time_limit
    if game.mode_name == "Timed" and not game.game_over and not game.is_paused:
        start_timer(game)


def start_timer(game):
    if game.timer_job is not None:
        game.root.after_cancel(game.timer_job)

    def tick():
        if game.game_over or game.mode_name != "Timed":
            game.timer_job = None
            return

        game.remaining_time -= 1
        update_mode_status_label(game)
        if game.remaining_time <= 0:
            game.remaining_time = 0
            game.end_game("Time is up")
            return
        game.timer_job = game.root.after(1000, tick)

    game.timer_job = game.root.after(1000, tick)


def stop_timer(game):
    if game.timer_job is not None:
        game.root.after_cancel(game.timer_job)
        game.timer_job = None


def update_mode_status_label(game):
    if game.mode_name == "Timed":
        game.mode_status_label.config(text=f"Mode: Timed | Time Left: {game.remaining_time}s")
    elif game.mode_name == "Steps":
        remaining_steps = max(0, game.steps_limit - game.steps_taken)
        game.mode_status_label.config(text=f"Mode: Steps | Remaining Moves: {remaining_steps}")
    elif game.mode_name == "Daily":
        seed_text = game.daily_seed if game.daily_seed is not None else "N/A"
        game.mode_status_label.config(text=f"Mode: Daily | Seed: {seed_text} | Fixed Grid: 4x4")
    else:
        game.mode_status_label.config(text="Mode: Classic")


def reset_rng(game):
    if game.mode_name == "Daily":
        game.daily_seed = int(date.today().strftime("%Y%m%d"))
        game.rng = random.Random(f"daily-{game.daily_seed}-size-{game.size}")
    else:
        game.daily_seed = None
        game.rng = random.Random()


def toggle_pause(game, event=None):
    if game.game_over or game.is_animating:
        return

    game.is_paused = not game.is_paused
    if game.is_paused:
        stop_timer(game)
        game.pause_overlay.config(bg=game.ui["panel"], fg=game.ui["text_dark"])
        game.pause_overlay.place(relx=0.5, rely=0.5, anchor="center")
    else:
        game.pause_overlay.place_forget()
        if game.mode_name == "Timed":
            start_timer(game)

    game.update_tool_label()
    update_mode_status_label(game)

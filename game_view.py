"""UI rendering helpers for 2048 Remix."""

import tkinter as tk


def create_board(game):
    for widget in game.board_frame.winfo_children():
        widget.destroy()
    game.cells = []
    font_size = 24 if game.size <= 5 else 20

    for i in range(game.size):
        row_cells = []
        for j in range(game.size):
            cell = tk.Label(
                game.board_frame,
                text="",
                bg=game.colors[0],
                font=("Segoe UI", font_size, "bold"),
                width=4,
                height=2,
                bd=0,
            )
            cell.grid(row=i, column=j, padx=5, pady=5, ipadx=2, ipady=2)
            cell.bind("<Button-1>", lambda event, r=i, c=j: game.on_cell_click(r, c))
            row_cells.append(cell)
        game.cells.append(row_cells)


def update_board(game):
    combo_multiplier = game.get_combo_multiplier()
    score_changed = game.score > int(game.score_label.cget("text") or 0)
    combo_changed = combo_multiplier > game.last_combo_multiplier

    for i in range(game.size):
        for j in range(game.size):
            val = game.grid[i][j]
            game.cells[i][j].config(
                text=str(val) if val != 0 else "",
                bg=game.colors.get(val, "#1A1917"),
                fg="#776E65" if val < 8 else "#F9F6F2",
            )
            if (i, j) in game.frozen_cells:
                game.cells[i][j].config(
                    highlightthickness=3,
                    highlightbackground=game.ui["freeze_border"],
                    highlightcolor=game.ui["freeze_border"],
                )
            else:
                game.cells[i][j].config(highlightthickness=0)

    game.score_label.config(text=f"{game.score}")
    game.combo_label.config(text=f"x{combo_multiplier:.1f}")
    game.steps_label.config(text=f"{game.steps_taken}")
    game.last_combo_multiplier = combo_multiplier

    if score_changed:
        pulse_card(game, game.score_card, game.score_label)
    if combo_changed:
        pulse_card(game, game.combo_card, game.combo_label)

    update_task_label(game)
    update_tool_label(game)
    game.update_mode_status_label()
    game.check_milestones()
    if not game.game_over and game.check_game_over():
        game.end_game("No more valid moves")


def update_task_label(game):
    for widget in game.task_rows_frame.winfo_children():
        widget.destroy()

    if not game.tasks:
        tk.Label(
            game.task_rows_frame,
            text="No active tasks",
            bg=game.ui["panel"],
            fg=game.task_status_colors["running"],
            font=game.fonts["body"],
            anchor="w",
        ).pack(fill="x", pady=1)
        return

    for idx, task in enumerate(game.tasks, start=1):
        status = game.get_task_status(task)
        line = f"{idx}. {game.task_text(task)}"
        if status == "done":
            line += "  [DONE]"
        elif status == "failed":
            line += "  [FAILED]"
        else:
            line += "  [RUNNING]"

        tk.Label(
            game.task_rows_frame,
            text=line,
            bg=game.ui["panel"],
            fg=game.task_status_colors[status],
            font=game.fonts["body"],
            justify=tk.LEFT,
            anchor="w",
        ).pack(fill="x", pady=1)


def update_tool_label(game):
    selected = game.selected_tool if game.selected_tool else "None"
    freeze_cells = len(game.frozen_cells)
    muted = "On" if game.is_muted else "Off"
    paused = "Yes" if game.is_paused else "No"
    game.tool_label.config(
        text=(
            f"Tools: Hammer({game.hammer_uses}) Freeze({game.freeze_uses}) "
            f"| Active: {selected} | Frozen: {freeze_cells} | Pause: {paused} | Mute: {muted}"
        )
    )
    game.hammer_button.config(text=f"Hammer (H) {game.hammer_uses}")
    game.freeze_button.config(text=f"Freeze (F) {game.freeze_uses}")
    game.pause_button.config(text="Resume (P)" if game.is_paused else "Pause (P)")
    game.mute_button.config(text=f"Mute (M) {muted}")

    if game.selected_tool == "hammer":
        game.hammer_button.config(bg=game.ui["tool_selected"], fg="#FFFFFF")
        game.freeze_button.config(bg=game.ui["btn"], fg=game.ui["text_dark"])
    elif game.selected_tool == "freeze":
        game.freeze_button.config(bg=game.ui["tool_selected"], fg="#FFFFFF")
        game.hammer_button.config(bg=game.ui["btn"], fg=game.ui["text_dark"])
    else:
        game.hammer_button.config(bg=game.ui["btn"], fg=game.ui["text_dark"])
        game.freeze_button.config(bg=game.ui["btn"], fg=game.ui["text_dark"])

    can_play = not game.game_over and not game.is_paused
    game.hammer_button.config(state=tk.NORMAL if game.hammer_uses > 0 and can_play else tk.DISABLED)
    game.freeze_button.config(state=tk.NORMAL if game.freeze_uses > 0 and can_play else tk.DISABLED)
    game.undo_button.config(state=tk.NORMAL if game.last_state and can_play else tk.DISABLED)
    game.pause_button.config(state=tk.NORMAL if not game.game_over else tk.DISABLED)


def play_milestone_animation(game, milestone):
    milestone_cells = []
    for i in range(game.size):
        for j in range(game.size):
            if game.grid[i][j] == milestone:
                milestone_cells.append(game.cells[i][j])

    if not milestone_cells:
        return

    sequence = [game.ui["accent"], game.ui["board"], game.ui["accent"], game.ui["board"]]

    def animate(index=0):
        if index >= len(sequence):
            game.header_label.config(fg=game.ui["text_dark"])
            game.board_frame.config(bg=game.ui["board"])
            game.update_board()
            return

        flash_color = sequence[index]
        if index % 2 == 0:
            game.header_label.config(fg=flash_color)
        else:
            game.header_label.config(fg=game.ui["text_dark"])

        game.board_frame.config(bg=flash_color)
        for cell in milestone_cells:
            cell.config(highlightthickness=4, highlightbackground=flash_color, highlightcolor=flash_color)

        game.root.after(120, lambda: animate(index + 1))

    animate()


def pulse_card(game, card, value_label):
    original_bg = game.ui["chip"]
    pulse_bg = game.ui["accent"]
    title_label = card.winfo_children()[0]
    original_font = value_label.cget("font")

    def phase_one():
        card.config(bg=pulse_bg)
        title_label.config(bg=pulse_bg, fg="#FFFFFF")
        value_label.config(bg=pulse_bg, fg="#FFFFFF", font=("Segoe UI", 18, "bold"))

    def phase_two():
        card.config(bg=original_bg)
        title_label.config(bg=original_bg, fg=game.ui["text_mid"])
        value_label.config(bg=original_bg, fg=game.ui["text_dark"], font=original_font)

    phase_one()
    game.root.after(120, phase_two)


def animate_score_float(game, gained_total, combo_bonus):
    if gained_total <= 0:
        return

    text = f"+{gained_total}"
    if combo_bonus > 0:
        text += f"  (Combo +{combo_bonus})"

    float_label = tk.Label(
        game.root,
        text=text,
        bg=game.ui["bg"],
        fg=game.ui["accent"],
        font=("Segoe UI", 11, "bold"),
    )
    float_label.place(relx=0.5, y=120, anchor="center")

    steps = 10

    def drift(step=0):
        if step >= steps:
            float_label.destroy()
            return

        float_label.place_configure(y=120 - step * 3)
        if step > 6:
            float_label.config(fg=game.ui["text_mid"])
        game.root.after(35, lambda: drift(step + 1))

    drift()


def animate_move_feedback(game, previous_grid, new_grid, spawned_pos=None):
    changed = []
    for i in range(game.size):
        for j in range(game.size):
            if previous_grid[i][j] != new_grid[i][j] and new_grid[i][j] != 0:
                changed.append((i, j))

    if spawned_pos and spawned_pos not in changed:
        changed.append(spawned_pos)

    if not changed:
        return

    game.is_animating = True

    def pulse_cell(index=0):
        if index >= len(changed):
            game.is_animating = False
            game.update_board()
            return

        r, c = changed[index]
        cell = game.cells[r][c]
        pulse_color = game.ui["accent"] if (r, c) != spawned_pos else game.ui["tool_selected"]
        cell.config(highlightthickness=4, highlightbackground=pulse_color, highlightcolor=pulse_color)

        def clear_and_next():
            if (r, c) in game.frozen_cells:
                cell.config(
                    highlightthickness=3,
                    highlightbackground=game.ui["freeze_border"],
                    highlightcolor=game.ui["freeze_border"],
                )
            else:
                cell.config(highlightthickness=0)
            pulse_cell(index + 1)

        game.root.after(45, clear_and_next)

    pulse_cell()


def apply_theme(game, theme_name):
    if theme_name not in game.themes:
        theme_name = "Classic"

    game.ui = game.themes[theme_name].copy()
    game.colors = game.tile_palettes.get(theme_name, game.tile_palettes["Classic"]).copy()

    game.root.configure(bg=game.ui["bg"])
    game.header_label.config(bg=game.ui["bg"], fg=game.ui["text_dark"])
    game.sub_label.config(bg=game.ui["bg"], fg=game.ui["text_mid"])
    game.top_frame.config(bg=game.ui["panel"])
    game.grid_frame.config(bg=game.ui["panel"])
    game.theme_frame.config(bg=game.ui["panel"])
    game.mode_frame.config(bg=game.ui["panel"])
    game.board_frame.config(bg=game.ui["board"])
    game.bottom_panel.config(bg=game.ui["panel"])
    game.task_label.config(bg=game.ui["panel"], fg=game.ui["text_dark"])
    game.task_rows_frame.config(bg=game.ui["panel"])
    game.tools_row.config(bg=game.ui["panel"])
    game.tool_label.config(bg=game.ui["panel"], fg=game.ui["text_mid"])
    game.mode_status_label.config(bg=game.ui["panel"], fg=game.ui["text_mid"])
    game.control_hint.config(bg=game.ui["bg"], fg=game.ui["text_mid"])

    game.theme_menu.config(
        bg=game.ui["chip"],
        fg=game.ui["text_dark"],
        activebackground=game.ui["btn_active"],
        activeforeground=game.ui["text_dark"],
    )
    game.theme_menu["menu"].config(bg=game.ui["chip"], fg=game.ui["text_dark"])

    game.mode_menu.config(
        bg=game.ui["chip"],
        fg=game.ui["text_dark"],
        activebackground=game.ui["btn_active"],
        activeforeground=game.ui["text_dark"],
    )
    game.mode_menu["menu"].config(bg=game.ui["chip"], fg=game.ui["text_dark"])

    for frame in [game.grid_frame, game.theme_frame, game.mode_frame]:
        for widget in frame.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(bg=game.ui["panel"], fg=game.ui["text_dark"])
            elif isinstance(widget, tk.Radiobutton):
                widget.config(
                    bg=game.ui["panel"],
                    fg=game.ui["text_dark"],
                    activebackground=game.ui["panel"],
                    activeforeground=game.ui["text_dark"],
                    selectcolor=game.ui["chip"],
                )

    for card in [game.score_card, game.combo_card, game.steps_card]:
        card.config(bg=game.ui["chip"])
        for child in card.winfo_children():
            if isinstance(child, tk.Label):
                child.config(bg=game.ui["chip"])
        card.winfo_children()[0].config(fg=game.ui["text_mid"])
        card.winfo_children()[1].config(fg=game.ui["text_dark"])

    game.pause_overlay.config(bg=game.ui["panel"], fg=game.ui["text_dark"])

    for button in [
        game.hammer_button,
        game.freeze_button,
        game.undo_button,
        game.restart_button,
        game.pause_button,
        game.mute_button,
    ]:
        button.config(bg=game.ui["btn"], fg=game.ui["text_dark"], activebackground=game.ui["btn_active"])

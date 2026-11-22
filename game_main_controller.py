import tkinter as tk
from tkinter import messagebox
import random
import os
import sys
import importlib.util

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
STATS_FILE = os.path.join(CURRENT_DIR, "game_stats.json")
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)


def _load_module(module_name, filename):
    module_path = os.path.join(CURRENT_DIR, filename)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_style = _load_module("game_style", "game_style.py")
_rules = _load_module("game_rules", "game_rules.py")
_state = _load_module("game_state", "game_state.py")
_persistence = _load_module("game_persistence", "game_persistence.py")
_engine = _load_module("game_engine", "game_engine.py")
_view = _load_module("game_view", "game_view.py")
_task_service = _load_module("game_task_service", "game_task_service.py")
_mode_service = _load_module("game_mode_service", "game_mode_service.py")
_tool_service = _load_module("game_tool_service", "game_tool_service.py")
_session_service = _load_module("game_session_service", "game_session_service.py")

DEFAULT_TILE_COLORS = _style.DEFAULT_TILE_COLORS
DEFAULT_UI = _style.DEFAULT_UI
FONTS = _style.FONTS
MILESTONES = _style.MILESTONES
TASK_STATUS_COLORS = _style.TASK_STATUS_COLORS
THEMES = _style.THEMES
TILE_PALETTES = _style.TILE_PALETTES

generate_random_tasks = _rules.generate_random_tasks
build_snapshot = _state.build_snapshot
restore_snapshot = _state.restore_snapshot
ScoreStore = _persistence.ScoreStore
build_move = _engine.build_move
check_game_over_state = _engine.check_game_over
tick_frozen_cells_state = _engine.tick_frozen_cells
create_board_ui = _view.create_board
update_board_ui = _view.update_board
update_task_label_ui = _view.update_task_label
update_tool_label_ui = _view.update_tool_label
play_milestone_animation_ui = _view.play_milestone_animation
pulse_card_ui = _view.pulse_card
animate_score_float_ui = _view.animate_score_float
animate_move_feedback_ui = _view.animate_move_feedback
apply_theme_ui = _view.apply_theme
generate_tasks_service = _task_service.generate_tasks
task_text_service = _task_service.task_text
get_task_status_service = _task_service.get_task_status
evaluate_tasks_service = _task_service.evaluate_tasks
complete_task_service = _task_service.complete_task
change_mode_service = _mode_service.change_mode
reset_mode_state_service = _mode_service.reset_mode_state
start_timer_service = _mode_service.start_timer
stop_timer_service = _mode_service.stop_timer
update_mode_status_label_service = _mode_service.update_mode_status_label
reset_rng_service = _mode_service.reset_rng
toggle_pause_service = _mode_service.toggle_pause
on_cell_click_service = _tool_service.on_cell_click
activate_hammer_service = _tool_service.activate_hammer
activate_freeze_service = _tool_service.activate_freeze
use_hammer_service = _tool_service.use_hammer
use_freeze_service = _tool_service.use_freeze
toggle_mute_service = _tool_service.toggle_mute
show_info_service = _session_service.show_info
check_milestones_service = _session_service.check_milestones
end_game_service = _session_service.end_game

class Game2048:
    def __init__(self, root, size=4):
        self.root = root
        self.root.title(f"2048 Game - {size}x{size}")
        self.root.configure(bg="#F6F2E9")
        self.root.minsize(760, 760)
        self.size = size
        self.grid = [[0] * size for _ in range(size)]
        self.score = 0
        self.game_over = False
        self.combo_streak = 0
        self.last_state = None
        self.max_tile = 0
        self.max_combo_streak = 0
        self.milestones_reached = set()
        self.steps_taken = 0
        self.best_move_score = 0
        self.best_move_turn = 0
        self.stats_path = STATS_FILE
        self.score_store = ScoreStore(self.stats_path)
        self.best_score = self.score_store.load_best_score()
        self.generate_random_tasks_fn = generate_random_tasks
        self.last_combo_multiplier = 1.0
        self.is_animating = False
        self.is_paused = False
        self.is_muted = False
        self.rng = random.Random()
        self.daily_seed = None
        self.mode_name = "Classic"
        self.time_limit = 120
        self.remaining_time = self.time_limit
        self.steps_limit = 30
        self.timer_job = None

        self.tasks = []
        self.tasks_completed = 0

        self.hammer_uses = 2
        self.freeze_uses = 2
        self.selected_tool = None
        self.frozen_cells = {}

        self.ui = DEFAULT_UI.copy()
        self.themes = THEMES.copy()
        self.fonts = FONTS
        self.task_status_colors = TASK_STATUS_COLORS
        self.milestones = MILESTONES
        self.messagebox = messagebox
        self.colors = DEFAULT_TILE_COLORS.copy()
        self.tile_palettes = TILE_PALETTES

        # UI Setup
        self.header_label = tk.Label(
            root,
            text="2048 Remix",
            bg=self.ui["bg"],
            fg=self.ui["text_dark"],
            font=self.fonts["title"]
        )
        self.header_label.pack(pady=(16, 2))

        self.sub_label = tk.Label(
            root,
            text="Merge smart, complete tasks, and use tools wisely",
            bg=self.ui["bg"],
            fg=self.ui["text_mid"],
            font=self.fonts["subtitle"]
        )
        self.sub_label.pack(pady=(0, 12))

        self.top_frame = tk.Frame(root, bg=self.ui["panel"], padx=12, pady=10, bd=0, highlightthickness=0)
        self.top_frame.pack(padx=14, pady=4, fill="x")

        self.score_card = tk.Frame(self.top_frame, bg=self.ui["chip"], padx=10, pady=6)
        self.score_card.pack(side=tk.LEFT, padx=6)
        tk.Label(self.score_card, text="SCORE", bg=self.ui["chip"], fg=self.ui["text_mid"], font=self.fonts["stat_title"]).pack()
        self.score_label = tk.Label(self.score_card, text=f"{self.score}", bg=self.ui["chip"], fg=self.ui["text_dark"], font=self.fonts["stat_value"])
        self.score_label.pack()

        self.combo_card = tk.Frame(self.top_frame, bg=self.ui["chip"], padx=10, pady=6)
        self.combo_card.pack(side=tk.LEFT, padx=6)
        tk.Label(self.combo_card, text="COMBO", bg=self.ui["chip"], fg=self.ui["text_mid"], font=self.fonts["stat_title"]).pack()
        self.combo_label = tk.Label(self.combo_card, text="x1.0", bg=self.ui["chip"], fg=self.ui["text_dark"], font=self.fonts["stat_value"])
        self.combo_label.pack()

        self.steps_card = tk.Frame(self.top_frame, bg=self.ui["chip"], padx=10, pady=6)
        self.steps_card.pack(side=tk.LEFT, padx=6)
        tk.Label(self.steps_card, text="STEPS", bg=self.ui["chip"], fg=self.ui["text_mid"], font=self.fonts["stat_title"]).pack()
        self.steps_label = tk.Label(self.steps_card, text="0", bg=self.ui["chip"], fg=self.ui["text_dark"], font=self.fonts["stat_value"])
        self.steps_label.pack()

        # Grid size selection
        self.size_var = tk.IntVar(value=self.size)
        self.grid_frame = tk.Frame(self.top_frame, bg=self.ui["panel"])
        self.grid_frame.pack(side=tk.RIGHT, padx=8)
        tk.Label(self.grid_frame, text="Grid", bg=self.ui["panel"], fg=self.ui["text_dark"], font=self.fonts["stat_title"]).pack(side=tk.LEFT, padx=(0, 8))
        for s in [4, 5, 6]:
            tk.Radiobutton(
                self.grid_frame,
                text=f"{s}x{s}",
                variable=self.size_var,
                value=s,
                command=self.change_size,
                bg=self.ui["panel"],
                fg=self.ui["text_dark"],
                activebackground=self.ui["panel"],
                activeforeground=self.ui["text_dark"],
                highlightthickness=0,
                selectcolor=self.ui["chip"],
                font=self.fonts["body"]
            ).pack(side=tk.LEFT, padx=2)

        self.theme_var = tk.StringVar(value="Classic")
        self.theme_frame = tk.Frame(self.top_frame, bg=self.ui["panel"])
        self.theme_frame.pack(side=tk.RIGHT, padx=8)
        tk.Label(self.theme_frame, text="Theme", bg=self.ui["panel"], fg=self.ui["text_dark"], font=self.fonts["stat_title"]).pack(side=tk.LEFT, padx=(0, 8))
        self.theme_menu = tk.OptionMenu(self.theme_frame, self.theme_var, *self.themes.keys(), command=self.change_theme)
        self.theme_menu.config(
            bg=self.ui["chip"],
            fg=self.ui["text_dark"],
            activebackground=self.ui["btn_active"],
            activeforeground=self.ui["text_dark"],
            highlightthickness=0,
            bd=0,
            font=self.fonts["body"]
        )
        self.theme_menu["menu"].config(bg=self.ui["chip"], fg=self.ui["text_dark"], font=self.fonts["body"])
        self.theme_menu.pack(side=tk.LEFT)

        self.mode_var = tk.StringVar(value="Classic")
        self.mode_frame = tk.Frame(self.top_frame, bg=self.ui["panel"])
        self.mode_frame.pack(side=tk.RIGHT, padx=8)
        tk.Label(self.mode_frame, text="Mode", bg=self.ui["panel"], fg=self.ui["text_dark"], font=self.fonts["stat_title"]).pack(side=tk.LEFT, padx=(0, 8))
        self.mode_menu = tk.OptionMenu(self.mode_frame, self.mode_var, "Classic", "Timed", "Steps", "Daily", command=self.change_mode)
        self.mode_menu.config(
            bg=self.ui["chip"],
            fg=self.ui["text_dark"],
            activebackground=self.ui["btn_active"],
            activeforeground=self.ui["text_dark"],
            highlightthickness=0,
            bd=0,
            font=self.fonts["body"]
        )
        self.mode_menu["menu"].config(bg=self.ui["chip"], fg=self.ui["text_dark"], font=self.fonts["body"])
        self.mode_menu.pack(side=tk.LEFT)

        self.board_frame = tk.Frame(root, bg=self.ui["board"], padx=8, pady=8, bd=0)
        self.board_frame.pack(pady=(10, 8))

        self.bottom_panel = tk.Frame(root, bg=self.ui["panel"], padx=12, pady=10)
        self.bottom_panel.pack(padx=14, pady=(2, 10), fill="x")

        self.task_label = tk.Label(
            self.bottom_panel,
            text="Tasks",
            font=self.fonts["task"],
            fg=self.ui["text_dark"],
            bg=self.ui["panel"],
            justify=tk.LEFT,
            anchor="w"
        )
        self.task_label.pack(fill="x", pady=(0, 4))

        self.task_rows_frame = tk.Frame(self.bottom_panel, bg=self.ui["panel"])
        self.task_rows_frame.pack(fill="x", pady=(0, 8))

        self.tools_row = tk.Frame(self.bottom_panel, bg=self.ui["panel"])
        self.tools_row.pack(fill="x")

        self.hammer_button = tk.Button(self.tools_row, text="Hammer (H)", command=self.activate_hammer,
                                       bg=self.ui["btn"], fg=self.ui["text_dark"], bd=0,
                                       font=self.fonts["body"], activebackground=self.ui["btn_active"], padx=10, pady=5)
        self.hammer_button.pack(side=tk.LEFT, padx=(0, 8))

        self.freeze_button = tk.Button(self.tools_row, text="Freeze (F)", command=self.activate_freeze,
                                       bg=self.ui["btn"], fg=self.ui["text_dark"], bd=0,
                                       font=self.fonts["body"], activebackground=self.ui["btn_active"], padx=10, pady=5)
        self.freeze_button.pack(side=tk.LEFT, padx=(0, 8))

        self.undo_button = tk.Button(self.tools_row, text="Undo (U)", command=self.undo_move,
                                     bg=self.ui["btn"], fg=self.ui["text_dark"], bd=0,
                                     font=self.fonts["body"], activebackground=self.ui["btn_active"], padx=10, pady=5)
        self.undo_button.pack(side=tk.LEFT, padx=(0, 8))

        self.restart_button = tk.Button(self.tools_row, text="Restart (R)", command=self.restart_game,
                                        bg=self.ui["btn"], fg=self.ui["text_dark"], bd=0,
                                        font=self.fonts["body"], activebackground=self.ui["btn_active"], padx=10, pady=5)
        self.restart_button.pack(side=tk.LEFT)

        self.pause_button = tk.Button(self.tools_row, text="Pause (P)", command=self.toggle_pause,
                          bg=self.ui["btn"], fg=self.ui["text_dark"], bd=0,
                          font=self.fonts["body"], activebackground=self.ui["btn_active"], padx=10, pady=5)
        self.pause_button.pack(side=tk.LEFT, padx=(8, 0))

        self.mute_button = tk.Button(self.tools_row, text="Mute (M) Off", command=self.toggle_mute,
                         bg=self.ui["btn"], fg=self.ui["text_dark"], bd=0,
                         font=self.fonts["body"], activebackground=self.ui["btn_active"], padx=10, pady=5)
        self.mute_button.pack(side=tk.LEFT, padx=(8, 0))

        self.tool_label = tk.Label(self.bottom_panel, text="Tools: Hammer(2) Freeze(2)", font=self.fonts["body"], fg=self.ui["text_mid"], bg=self.ui["panel"], anchor="w")
        self.tool_label.pack(fill="x", pady=(8, 2))

        self.mode_status_label = tk.Label(
            self.bottom_panel,
            text="Mode: Classic",
            font=self.fonts["body"],
            fg=self.ui["text_mid"],
            bg=self.ui["panel"],
            anchor="w"
        )
        self.mode_status_label.pack(fill="x", pady=(2, 2))

        self.control_hint = tk.Label(root, text="Arrow Keys Move | Freeze locks a tile for 3 moves | Hammer can break unlocked tiles",
                         bg=self.ui["bg"], font=self.fonts["body"], fg=self.ui["text_mid"])
        self.control_hint.pack(pady=(0, 10))

        self.cells = []
        self.pause_overlay = tk.Label(
            self.board_frame,
            text="PAUSED",
            bg=self.ui["panel"],
            fg=self.ui["text_dark"],
            font=("Segoe UI", 18, "bold"),
            padx=16,
            pady=8
        )
        self.apply_theme(self.theme_var.get())
        self.reset_rng()
        self.change_mode(self.mode_var.get())
        self.create_board()
        self.spawn_new_tile()
        self.spawn_new_tile()
        self.update_board()

        # Key bindings
        root.bind("<Up>", self.move_up)
        root.bind("<Down>", self.move_down)
        root.bind("<Left>", self.move_left)
        root.bind("<Right>", self.move_right)
        root.bind("<r>", self.restart_game)
        root.bind("<R>", self.restart_game)
        root.bind("<u>", self.undo_move)
        root.bind("<U>", self.undo_move)
        root.bind("<h>", self.activate_hammer)
        root.bind("<H>", self.activate_hammer)
        root.bind("<f>", self.activate_freeze)
        root.bind("<F>", self.activate_freeze)
        root.bind("<p>", self.toggle_pause)
        root.bind("<P>", self.toggle_pause)
        root.bind("<m>", self.toggle_mute)
        root.bind("<M>", self.toggle_mute)

        self.generate_tasks()
        self.update_task_label()
        self.update_tool_label()

    def create_board(self):
        create_board_ui(self)

    def change_size(self):
        self.size = self.size_var.get()
        self.grid = [[0]*self.size for _ in range(self.size)]
        self.score = 0
        self.game_over = False
        self.combo_streak = 0
        self.last_state = None
        self.max_tile = 0
        self.max_combo_streak = 0
        self.milestones_reached = set()
        self.steps_taken = 0
        self.best_move_score = 0
        self.best_move_turn = 0
        self.stop_timer()

        self.tasks = []
        self.tasks_completed = 0

        self.hammer_uses = 2
        self.freeze_uses = 2
        self.selected_tool = None
        self.frozen_cells = {}
        self.is_paused = False
        self.pause_overlay.place_forget()

        self.reset_rng()
        self.create_board()
        self.generate_tasks()
        self.spawn_new_tile()
        self.spawn_new_tile()
        self.reset_mode_state()
        self.update_board()
        self.score_label.config(text=f"{self.score}")
        self.last_combo_multiplier = 1.0

    def spawn_new_tile(self):
        empty_cells = [
            (i, j)
            for i in range(self.size)
            for j in range(self.size)
            if self.grid[i][j] == 0 and (i, j) not in self.frozen_cells
        ]
        if empty_cells:
            i, j = self.rng.choice(empty_cells)
            self.grid[i][j] = 2 if self.rng.random() < 0.9 else 4
            return (i, j)
        return None

    def update_board(self):
        update_board_ui(self)

    def get_combo_multiplier(self):
        return min(2.5, 1.0 + self.combo_streak * 0.2)

    def generate_tasks(self):
        generate_tasks_service(self)

    def task_text(self, task):
        return task_text_service(task)

    def get_task_status(self, task):
        return get_task_status_service(task)

    def update_task_label(self):
        update_task_label_ui(self)

    def update_tool_label(self):
        update_tool_label_ui(self)

    def evaluate_tasks(self, highest_tile, merged_count):
        evaluate_tasks_service(self, highest_tile, merged_count)

    def complete_task(self, task):
        complete_task_service(self, task)

    def play_milestone_animation(self, milestone):
        play_milestone_animation_ui(self, milestone)

    def pulse_card(self, card, value_label):
        pulse_card_ui(self, card, value_label)

    def animate_score_float(self, gained_total, combo_bonus):
        animate_score_float_ui(self, gained_total, combo_bonus)

    def animate_move_feedback(self, previous_grid, new_grid, spawned_pos=None):
        animate_move_feedback_ui(self, previous_grid, new_grid, spawned_pos)

    def change_theme(self, selected_theme=None):
        theme_name = selected_theme if selected_theme else self.theme_var.get()
        self.apply_theme(theme_name)
        self.update_board()

    def change_mode(self, selected_mode=None):
        change_mode_service(self, selected_mode)

    def reset_mode_state(self, preserve_time=False):
        reset_mode_state_service(self, preserve_time)

    def start_timer(self):
        start_timer_service(self)

    def stop_timer(self):
        stop_timer_service(self)

    def update_mode_status_label(self):
        update_mode_status_label_service(self)

    def show_info(self, title, message, force=False):
        show_info_service(self, title, message, force)

    def reset_rng(self):
        reset_rng_service(self)

    def toggle_pause(self, event=None):
        toggle_pause_service(self, event)

    def toggle_mute(self, event=None):
        toggle_mute_service(self, event)

    def load_best_score(self):
        return self.score_store.load_best_score()

    def save_best_score(self):
        self.score_store.save_best_score(self.best_score)

    def end_game(self, reason=""):
        end_game_service(self, reason)

    def apply_theme(self, theme_name):
        apply_theme_ui(self, theme_name)

    def tick_frozen_cells(self):
        self.frozen_cells = tick_frozen_cells_state(self.frozen_cells)

    def on_cell_click(self, row, col):
        on_cell_click_service(self, row, col)

    def activate_hammer(self, event=None):
        activate_hammer_service(self, event)

    def activate_freeze(self, event=None):
        activate_freeze_service(self, event)

    def use_hammer(self, row, col):
        use_hammer_service(self, row, col)

    def use_freeze(self, row, col):
        use_freeze_service(self, row, col)

    def snapshot_state(self):
        return build_snapshot(self)

    def perform_move(self, direction):
        previous_state = self.snapshot_state()
        move_result = build_move(self.grid, self.frozen_cells, self.size, direction)
        self.apply_move_results(
            move_result["new_grid"],
            move_result["moved"],
            move_result["merge_happened"],
            move_result["move_base_score"],
            move_result["merged_in_move"],
            previous_state,
        )

    def apply_move_results(self, new_grid, moved, merge_happened, move_base_score, merged_in_move, previous_state):
        if not moved:
            return

        self.last_state = previous_state
        previous_grid = [row[:] for row in previous_state["grid"]]
        self.grid = new_grid
        self.steps_taken += 1

        if merge_happened:
            self.combo_streak += 1
            combo_bonus = int(move_base_score * (self.get_combo_multiplier() - 1.0))
        else:
            self.combo_streak = 0
            combo_bonus = 0

        self.max_combo_streak = max(self.max_combo_streak, self.combo_streak)
        gained_total = move_base_score + combo_bonus
        self.score += gained_total
        if gained_total > self.best_move_score:
            self.best_move_score = gained_total
            self.best_move_turn = self.steps_taken

        highest_tile = max(max(row) for row in self.grid)
        self.evaluate_tasks(highest_tile, merged_in_move)

        if self.mode_name == "Steps" and self.steps_taken >= self.steps_limit:
            self.update_board()
            self.end_game("Step limit reached")
            return

        self.tick_frozen_cells()
        spawned_pos = self.spawn_new_tile()
        self.update_board()
        self.animate_score_float(gained_total, combo_bonus)
        self.animate_move_feedback(previous_grid, self.grid, spawned_pos)

    def check_milestones(self):
        check_milestones_service(self)

    def undo_move(self, event=None):
        if not self.last_state or self.is_animating or self.is_paused:
            return

        restore_snapshot(self, self.last_state)
        self.last_state = None
        self.reset_mode_state(preserve_time=True)
        self.update_board()

    def move_left(self, event=None):
        if self.game_over or self.is_animating or self.is_paused:
            return
        self.perform_move("left")

    def move_right(self, event=None):
        if self.game_over or self.is_animating or self.is_paused:
            return
        self.perform_move("right")

    def move_up(self, event=None):
        if self.game_over or self.is_animating or self.is_paused:
            return
        self.perform_move("up")

    def move_down(self, event=None):
        if self.game_over or self.is_animating or self.is_paused:
            return
        self.perform_move("down")

    def check_game_over(self):
        return check_game_over_state(self.grid, self.frozen_cells, self.size)

    def restart_game(self, event=None):
        self.change_size()

if __name__ == "__main__":
    root = tk.Tk()
    game = Game2048(root, size=4)
    root.mainloop()
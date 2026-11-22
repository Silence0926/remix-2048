# 2048 Remix (Refactored)

A modular Tkinter-based 2048 variant with tools, tasks, themes, multiple modes, daily challenge seed, and undo.

## Quick Start

Run the game:

```powershell
python app.py
```

Run logic regression tests:

```powershell
python test_game_logic.py
```

## Project Structure

- `app.py`: App entrypoint.
- `game_main_controller.py`: Main controller class wiring UI/services/engine together.
- `game_controller.py`: Bridge that exposes `Game2048` from the standard controller file.
- `legacy_launcher.py`: Legacy compatibility launcher.
- `game_view.py`: UI rendering and animation helpers.
- `game_engine.py`: Lock-aware movement, merge scoring, game-over checks.
- `game_task_service.py`: Task generation, status, evaluation, rewards.
- `game_mode_service.py`: Mode switching, timer, daily seed, pause handling.
- `game_tool_service.py`: Hammer/freeze/mute interactions.
- `game_session_service.py`: Milestones, notifications, end-game summary flow.
- `game_state.py`: Snapshot and restore for undo/session continuity.
- `game_persistence.py`: Best-score persistence.
- `game_rules.py`: Core row-level gameplay helpers and task templates.
- `game_style.py`: Themes, palettes, fonts, UI constants.
- `test_game_logic.py`: Minimal automated logic checks.

## Notes

- Daily mode uses date-based deterministic random seed.
- Best score is stored in `game_stats.json` in the same directory.
- `app.py` is the recommended launch command.
- `legacy_launcher.py` is kept as a backward-compatible launcher for older shortcuts/workflows.

## Web Version

Run web client:

```powershell
python -m http.server 8080
```

Open:

- http://localhost:8080/web/

Optional online leaderboard API:

```powershell
python web/leaderboard_server.py
```

Deployment helper file:

- `render.yaml` (API service blueprint)

Launch planning:

- `LAUNCH_CHECKLIST.md` (remaining work, priorities, and time estimate)

Android packaging and release:

- `ANDROID_RELEASE_GUIDE.md` (Android-only publish path)
- `scripts/setup_android_wrapper.ps1` (one-command Capacitor Android wrapper setup)
- `android-wrapper/` (Capacitor project scaffold)

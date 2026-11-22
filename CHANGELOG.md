# Changelog

## 2026-07-28

### Refactor Milestone

- Split large monolithic game file into modular layers:
  - `game_engine.py` (movement and game-over logic)
  - `game_view.py` (rendering and animations)
  - `game_task_service.py` (tasks and rewards)
  - `game_mode_service.py` (mode, timer, daily seed, pause)
  - `game_tool_service.py` (hammer/freeze/mute interactions)
  - `game_session_service.py` (milestones, notifications, end-game summary)
  - `game_state.py` (snapshot/restore)
  - `game_persistence.py` (best score storage)

### Compatibility And Entrypoints

- Added `app.py` as the recommended launch entrypoint.
- Added `game_controller.py` as a stable bridge export for `Game2048`.
- Migrated main controller code to `game_main_controller.py`.
- Converted `legacy_launcher.py` into a compatibility launcher.

### Quality

- Added `test_game_logic.py` for lightweight regression checks.
- Verified tests pass after refactor.

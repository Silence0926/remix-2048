# 2048 Remix

A modular 2048 game project with a Python desktop implementation, a browser-based version, and an Android packaging scaffold.

## Project components

- **Python desktop game** — Tkinter-based game with multiple modes, themes, tasks, tools, undo, and daily challenges.
- **Web game** — browser client in `web/`, with an optional leaderboard API.
- **Android wrapper** — Capacitor project scaffold in `android-wrapper/`.

## Run the Python game

Python 3.10+ is recommended.

```bash
python app.py
```

Run the logic regression tests:

```bash
python test_game_logic.py
```

## Run the web version

From the repository root:

```bash
python -m http.server 8080
```

Then open http://localhost:8080/web/.

The optional leaderboard API is started with:

```bash
python web/leaderboard_server.py
```

## Android

See [ANDROID_RELEASE_GUIDE.md](ANDROID_RELEASE_GUIDE.md) for the Android release workflow and [scripts/setup_android_wrapper.ps1](scripts/setup_android_wrapper.ps1) for the setup helper.

## Repository hygiene

Local virtual environments, dependency caches, build output, local saves, and SQLite runtime databases should not be committed. See [\.gitignore](.gitignore).

## Current status

This repository is being prepared for its initial source import. Features and release targets should be considered in-development until verified by CI and a packaged build.

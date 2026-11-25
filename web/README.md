# 2048 Remix Web

## Run Locally

From the project root:

```powershell
python -m http.server 8080
```

Then open:

- http://localhost:8080/web/

Optional online leaderboard API:

```powershell
python web/leaderboard_server.py
```

API endpoint default used by the web app:

- http://localhost:8787/api

## API Base Configuration

Priority order used by web app:

1. URL query parameter `?api=...`
2. `localStorage` key `remix2048_api_base`
3. `window.REMIX2048_API_BASE` in `web/config.js`
4. fallback `http://localhost:8787/api`

Examples:

- `http://localhost:8080/web/?api=https://your-api.onrender.com/api`
- Edit `web/config.js` and set:

```js
window.REMIX2048_API_BASE = "https://your-api.onrender.com/api";
```

## Controls

Desktop:

- Move: Arrow keys
- Hammer: H
- Freeze: F
- Undo: U
- Restart: R
- Pause: P
- Mute: M

Mobile:

- Move: swipe on board
- Tool use: tap tile after selecting Hammer/Freeze

## Features Included

- Classic / Timed / Steps / Daily mode
- 4x4, 5x5, 6x6 grids (Daily fixed to 4x4)
- Freeze lock behavior
- Hammer tool
- Undo
- Local best score
- Tasks and milestone toasts
- Daily Top 5 and All-Time Top 5 local leaderboard
- Online leaderboard sync (when API is running)
- PWA install support ("Install App" button when available)

## PWA Notes

- Service worker caches core files for offline play.
- If updates do not show immediately, close the tab and reopen `http://localhost:8080/web/`.
- If online API is unavailable, app automatically falls back to local-only leaderboard.

## Deploy API (Render)

This repo already includes `render.yaml` for API service deployment.

Server env vars supported:

- `HOST` (default: `0.0.0.0`)
- `PORT` (default: `8787`)
- `LEADERBOARD_DB_FILE` (default: `web/leaderboard.sqlite3`)
- `LEADERBOARD_DATA_FILE` (optional legacy JSON path, used only for first-run migration)
- `CORS_ALLOW_ORIGINS` (comma-separated exact origins; defaults to `https://silence0926.github.io`)
- `CORS_ALLOW_ORIGIN` (legacy single-origin setting; defaults to the published Pages origin)
- `ADMIN_API_KEY` (optional; enables admin endpoints when set)

Deployment storage warning:

- The current `render.yaml` uses `/tmp/remix2048_leaderboard.sqlite3` for a free Render web service. This is suitable only for a temporary beta: the filesystem is ephemeral and leaderboard data can be lost when the service restarts or redeploys.
- Do not treat this as production-persistent storage. Before inviting players to rely on global rankings, attach a persistent database (preferably managed PostgreSQL) and migrate the API storage layer, or use a paid persistent disk with an explicit backup plan. No paid database or hosting resource is provisioned by this repository.

Online API protections:

- Per-client cooldown: one submit every 5 seconds, keyed by remote address and client ID
- Duplicate suppression: same run payload within 60 seconds is ignored
- Request body limit (16 KB), JSON/type validation, and input sanitization
- Server-generated submission timestamps for duplicate checks
- Exact-origin CORS allowlist; configure additional trusted web origins through `CORS_ALLOW_ORIGINS`
- SQLite busy timeout and WAL mode for better local concurrency

These controls reduce accidental abuse; they do not make client-submitted scores cheat-proof. A fully authoritative anti-cheat system would require server-side game/replay validation.

API notes:

- `GET /api/leaderboard` supports `limit` query (1-50), default 5.
- Existing JSON leaderboard data is auto-migrated to SQLite on first run when DB is empty.

Admin API notes (enabled only when `ADMIN_API_KEY` is set):

- `GET /api/admin/stats` with `X-Admin-Key` header (or `?key=`)
- `POST /api/admin/cleanup` with filters and admin key

`/api/admin/cleanup` request body example:

```json
{
	"key": "your-admin-key",
	"dryRun": true,
	"minScore": 0,
	"maxScore": 100,
	"nameContains": "test",
	"beforeAt": "2026-07-01T00:00:00+08:00",
	"dailySeed": 20260701,
	"mode": "Classic"
}
```

At least one valid filter is required for cleanup.

After API is live, point your web app to that URL using either `?api=` or `web/config.js`.

## Android Packaging

Android wrapper scaffold is prepared in `android-wrapper/`.

Quick setup from project root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_android_wrapper.ps1
```

Full release steps:

- See `ANDROID_RELEASE_GUIDE.md`

# Launch Checklist (Web/PWA)

Last update: 2026-07-28

## Current Readiness (Estimate)

- Playable quality: 90%
- Online leaderboard feature: 80%
- Production deployment readiness: 55%
- Compliance/store-readiness: 35%
- Overall launch readiness: 65%

## P0 - Must Have Before Public Launch

1. Production data storage for leaderboard
- Status: TODO
- Why: current JSON file storage is simple but weak for concurrent writes and long-term operations.
- Action: migrate API storage to SQLite/Postgres.
- Effort: 0.5-1 day

2. Stable hosting topology
- Status: PARTIAL
- Why: API render config exists, but static web hosting + domain + HTTPS + final API URL binding still pending.
- Action: deploy web to static host (Cloudflare Pages/Netlify/Vercel) and API to Render/Fly/Railway.
- Effort: 0.5 day

3. Basic monitoring and recovery
- Status: TODO
- Why: no uptime check, no structured logging, no backup routine.
- Action: add health monitor, keep 7-day log snapshots, periodic backup/export.
- Effort: 0.5 day

4. Abuse controls baseline
- Status: PARTIAL
- Why: cooldown and dedup exist; still no IP-level throttling or admin cleanup flow.
- Action: add reverse-proxy rate limit and admin cleanup endpoint/page.
- Effort: 0.5 day

## P1 - Strongly Recommended

1. Privacy and terms pages
- Status: TODO
- Why: public launch should disclose data usage (nickname, score, timestamp, clientId).
- Action: add Privacy Policy + Terms pages and footer links.
- Effort: 0.5 day

2. Crash/error telemetry
- Status: TODO
- Why: hard to debug mobile/browser-specific issues in production.
- Action: add lightweight error reporting (Sentry or custom endpoint).
- Effort: 0.5 day

3. Performance and offline validation
- Status: PARTIAL
- Why: service worker exists; no Lighthouse budget checks yet.
- Action: run Lighthouse and fix blocking items (PWA/installability/accessibility/perf).
- Effort: 0.5 day

4. API contract versioning
- Status: TODO
- Why: future changes may break older web clients.
- Action: add `/api/v1/*` pathing and deprecation notes.
- Effort: 0.5 day

## P2 - Nice to Have

1. Admin dashboard
- read leaderboard, filter by date/mode, remove suspicious records.

2. Event analytics
- retention, mode popularity, daily active players.

3. Anti-cheat improvements
- server-side plausibility checks for impossible score growth.

## Practical Timeline

- Fast public beta (minimum): 2-3 days (finish all P0)
- More reliable launch: 4-6 days (P0 + most P1)
- "Store-like" polish: 1-2 additional weeks

## Recommended Next Execution Order

1. Storage migration (JSON -> SQLite)
2. Deploy web + API + final domain/HTTPS
3. Add privacy/terms pages
4. Add admin cleanup tool for leaderboard
5. Add monitoring/telemetry

"""Lightweight online leaderboard API for 2048 Remix Web.

Run:
  python web/leaderboard_server.py
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8787"))
DB_FILE = os.getenv("LEADERBOARD_DB_FILE", os.path.join(os.path.dirname(__file__), "leaderboard.sqlite3"))
LEGACY_JSON_FILE = os.getenv("LEADERBOARD_DATA_FILE", os.path.join(os.path.dirname(__file__), "leaderboard_data.json"))
CORS_ALLOW_ORIGINS = {origin.strip() for origin in os.getenv("CORS_ALLOW_ORIGINS", os.getenv("CORS_ALLOW_ORIGIN", "https://silence0926.github.io")).split(",") if origin.strip()}
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "").strip()
MAX_STORE = 200
MAX_RETURN = 5
SCORE_MIN = 0
SCORE_MAX = 2_000_000_000
SIZE_MIN = 2
SIZE_MAX = 12
STEPS_MIN = 0
STEPS_MAX = 1_000_000
POST_COOLDOWN_SECONDS = 5.0
DUPLICATE_WINDOW_SECONDS = 60.0
NAME_PATTERN = re.compile(r"[^A-Za-z0-9_\- ]+")

LAST_POST_BY_CLIENT: dict[str, float] = {}
DB_LOCK = threading.Lock()


def today_seed() -> int:
    return int(datetime.now().strftime("%Y%m%d"))


class HybridRow(dict):
    """Dictionary-style database row that also supports SQLite-style numeric indexes."""

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


def hybrid_row_factory(cursor):
    column_names = [column.name for column in (cursor.description or ())]

    def make_row(values):
        return HybridRow(zip(column_names, values))

    return make_row


class PostgresConnection:
    """Small compatibility adapter for the existing SQLite-shaped SQL layer."""

    def __init__(self, database_url: str):
        import psycopg
        self.raw = psycopg.connect(database_url, row_factory=hybrid_row_factory)

    def execute(self, sql: str, params=()):
        return self.raw.execute(sql.replace("?", "%s"), params)

    def commit(self):
        self.raw.commit()

    @property
    def row_factory(self):
        return None

    @row_factory.setter
    def row_factory(self, _value):
        # psycopg already uses hybrid_row_factory for every cursor.
        pass

    def __enter__(self):
        self.raw.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self.raw.__exit__(exc_type, exc_value, traceback)


def get_connection():
    if DATABASE_URL:
        return PostgresConnection(DATABASE_URL)
    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


def ensure_db() -> None:
    if DATABASE_URL:
        with get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS leaderboard_entries (
                    id BIGSERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    score BIGINT NOT NULL,
                    mode TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    steps INTEGER NOT NULL,
                    daily_seed BIGINT NOT NULL,
                    at TEXT NOT NULL,
                    client_id TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_score_steps ON leaderboard_entries(score DESC, steps ASC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_daily_seed ON leaderboard_entries(daily_seed)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_signature ON leaderboard_entries(name, score, mode, size, steps, daily_seed)")
            conn.commit()
        return

    db_directory = os.path.dirname(os.path.abspath(DB_FILE))
    os.makedirs(db_directory, exist_ok=True)
    with get_connection() as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leaderboard_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                score INTEGER NOT NULL,
                mode TEXT NOT NULL,
                size INTEGER NOT NULL,
                steps INTEGER NOT NULL,
                daily_seed INTEGER NOT NULL,
                at TEXT NOT NULL,
                client_id TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_score_steps ON leaderboard_entries(score DESC, steps ASC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_daily_seed ON leaderboard_entries(daily_seed)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_signature ON leaderboard_entries(name, score, mode, size, steps, daily_seed)")
        conn.commit()


def parse_json_data_file(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as file_obj:
            data = json.load(file_obj)
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(data, dict):
        return []

    all_rows = data.get("all", [])
    if not isinstance(all_rows, list):
        return []
    return all_rows


def migrate_from_legacy_json_if_needed() -> None:
    rows = parse_json_data_file(LEGACY_JSON_FILE)
    if not rows:
        return

    with get_connection() as conn:
        current_count = conn.execute("SELECT COUNT(*) FROM leaderboard_entries").fetchone()[0]
        if current_count > 0:
            return

        for raw in rows:
            if not isinstance(raw, dict):
                continue
            entry = normalize_entry(raw)
            conn.execute(
                """
                INSERT INTO leaderboard_entries
                (name, score, mode, size, steps, daily_seed, at, client_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry["name"],
                    entry["score"],
                    entry["mode"],
                    entry["size"],
                    entry["steps"],
                    entry["dailySeed"],
                    entry["at"],
                    entry["clientId"],
                ),
            )

        conn.commit()


def normalize_entry(raw: dict) -> dict:
    raw_name = str(raw.get("name", "Player")).strip()
    name = NAME_PATTERN.sub("", raw_name)[:18] or "Player"
    mode = str(raw.get("mode", "Classic")).strip()[:20] or "Classic"
    score = max(SCORE_MIN, min(SCORE_MAX, int(raw.get("score", 0))))
    size = max(SIZE_MIN, min(SIZE_MAX, int(raw.get("size", 4))))
    steps = max(STEPS_MIN, min(STEPS_MAX, int(raw.get("steps", 0))))
    client_id = str(raw.get("clientId", "anon")).strip()[:64] or "anon"
    if NAME_PATTERN.search(client_id):
        client_id = "anon"

    raw_at = str(raw.get("at") or "").strip()
    try:
        if raw_at.endswith("Z"):
            datetime.fromisoformat(raw_at.replace("Z", "+00:00"))
        elif raw_at:
            datetime.fromisoformat(raw_at)
        at_value = raw_at or datetime.now().isoformat(timespec="seconds")
    except ValueError:
        at_value = datetime.now().isoformat(timespec="seconds")

    return {
        "name": name,
        "score": score,
        "mode": mode,
        "size": size,
        "steps": steps,
        "dailySeed": int(raw.get("dailySeed") or today_seed()),
        "at": at_value,
        "clientId": client_id,
    }


def row_to_entry(row: sqlite3.Row) -> dict:
    return {
        "name": row["name"],
        "score": row["score"],
        "mode": row["mode"],
        "size": row["size"],
        "steps": row["steps"],
        "dailySeed": row["daily_seed"],
        "at": row["at"],
        "clientId": row["client_id"],
    }


def parse_iso_to_ts(iso_text: str) -> float:
    try:
        return datetime.fromisoformat(iso_text.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return time.time()


def is_valid_iso_text(value: str) -> bool:
    text = (value or "").strip()
    if not text:
        return False
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def fetch_entries(scope: str, seed: int, limit: int) -> list[dict]:
    limit = max(1, min(50, limit))
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        if scope == "daily":
            rows = conn.execute(
                """
                SELECT name, score, mode, size, steps, daily_seed, at, client_id
                FROM leaderboard_entries
                WHERE daily_seed = ?
                ORDER BY score DESC, steps ASC, id ASC
                LIMIT ?
                """,
                (seed, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT name, score, mode, size, steps, daily_seed, at, client_id
                FROM leaderboard_entries
                ORDER BY score DESC, steps ASC, id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    return [row_to_entry(row) for row in rows]


def is_duplicate_recent_in_db(entry: dict) -> bool:
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT name, score, mode, size, steps, daily_seed, at, client_id
            FROM leaderboard_entries
            WHERE name = ? AND score = ? AND mode = ? AND size = ? AND steps = ? AND daily_seed = ?
            ORDER BY id DESC
            LIMIT 50
            """,
            (
                entry["name"],
                entry["score"],
                entry["mode"],
                entry["size"],
                entry["steps"],
                entry["dailySeed"],
            ),
        ).fetchall()

    if not rows:
        return False

    new_ts = parse_iso_to_ts(entry["at"])
    for row in rows:
        old_ts = parse_iso_to_ts(str(row["at"]))
        if abs(new_ts - old_ts) <= DUPLICATE_WINDOW_SECONDS:
            return True
    return False


def trim_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        DELETE FROM leaderboard_entries
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           ORDER BY score DESC, steps ASC, id ASC
                       ) AS rn
                FROM leaderboard_entries
            ) ranked
            WHERE rn > ?
        )
        """,
        (MAX_STORE,),
    )

    conn.execute(
        """
        DELETE FROM leaderboard_entries
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY daily_seed
                           ORDER BY score DESC, steps ASC, id ASC
                       ) AS rn
                FROM leaderboard_entries
            ) ranked
            WHERE rn > ?
        )
        """,
        (MAX_STORE,),
    )


def insert_entry(entry: dict) -> None:
    with DB_LOCK:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO leaderboard_entries
                (name, score, mode, size, steps, daily_seed, at, client_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry["name"],
                    entry["score"],
                    entry["mode"],
                    entry["size"],
                    entry["steps"],
                    entry["dailySeed"],
                    entry["at"],
                    entry["clientId"],
                ),
            )
            trim_tables(conn)
            conn.commit()


def fetch_admin_stats() -> dict:
    with get_connection() as conn:
        total_entries = conn.execute("SELECT COUNT(*) FROM leaderboard_entries").fetchone()[0]
        unique_clients = conn.execute("SELECT COUNT(DISTINCT client_id) FROM leaderboard_entries").fetchone()[0]
        unique_daily = conn.execute("SELECT COUNT(DISTINCT daily_seed) FROM leaderboard_entries").fetchone()[0]
        top_row = conn.execute(
            """
            SELECT name, score, mode, size, steps, daily_seed, at, client_id
            FROM leaderboard_entries
            ORDER BY score DESC, steps ASC, id ASC
            LIMIT 1
            """
        ).fetchone()

    top_entry = None
    if top_row:
        top_entry = {
            "name": top_row[0],
            "score": top_row[1],
            "mode": top_row[2],
            "size": top_row[3],
            "steps": top_row[4],
            "dailySeed": top_row[5],
            "at": top_row[6],
            "clientId": top_row[7],
        }

    return {
        "totalEntries": total_entries,
        "uniqueClients": unique_clients,
        "uniqueDailySeeds": unique_daily,
        "topEntry": top_entry,
    }


def cleanup_entries(filters: dict, dry_run: bool = False) -> tuple[int, int]:
    where_parts = []
    params: list = []

    if "minScore" in filters:
        where_parts.append("score >= ?")
        params.append(int(filters["minScore"]))

    if "maxScore" in filters:
        where_parts.append("score <= ?")
        params.append(int(filters["maxScore"]))

    if "dailySeed" in filters:
        where_parts.append("daily_seed = ?")
        params.append(int(filters["dailySeed"]))

    if "mode" in filters:
        where_parts.append("mode = ?")
        params.append(str(filters["mode"]).strip()[:20])

    if "nameContains" in filters:
        token = NAME_PATTERN.sub("", str(filters["nameContains"]).strip())
        if token:
            where_parts.append("name LIKE ?")
            params.append(f"%{token}%")

    if "beforeAt" in filters:
        before_at = str(filters["beforeAt"]).strip()
        if is_valid_iso_text(before_at):
            where_parts.append("at < ?")
            params.append(before_at)

    if not where_parts:
        return 0, -1

    where_clause = " AND ".join(where_parts)
    with DB_LOCK:
        with get_connection() as conn:
            count_sql = f"SELECT COUNT(*) FROM leaderboard_entries WHERE {where_clause}"
            matched_count = conn.execute(count_sql, tuple(params)).fetchone()[0]

            if not dry_run and matched_count > 0:
                delete_sql = f"DELETE FROM leaderboard_entries WHERE {where_clause}"
                conn.execute(delete_sql, tuple(params))
                conn.commit()

            remaining = conn.execute("SELECT COUNT(*) FROM leaderboard_entries").fetchone()[0]

    return matched_count, remaining


def prune_rate_limit_map() -> None:
    now = time.time()
    stale_keys = [key for key, ts in LAST_POST_BY_CLIENT.items() if now - ts > 3600]
    for key in stale_keys:
        LAST_POST_BY_CLIENT.pop(key, None)


class LeaderboardHandler(BaseHTTPRequestHandler):
    @staticmethod
    def _safe_int(value: str, fallback: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

    def _origin_allowed(self) -> bool:
        origin = (self.headers.get("Origin") or "").strip()
        return not origin or "*" in CORS_ALLOW_ORIGINS or origin in CORS_ALLOW_ORIGINS

    def _send(self, status: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        origin = (self.headers.get("Origin") or "").strip()
        if origin and self._origin_allowed():
            self.send_header("Access-Control-Allow-Origin", "*" if "*" in CORS_ALLOW_ORIGINS else origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Admin-Key")
        self.end_headers()
        self.wfile.write(body)

    def _parse_json_body(self) -> tuple[dict | None, str | None]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0:
                return None, "invalid content length"
            if length > 16384:
                return None, "request body too large"
            raw = self.rfile.read(length)
            payload = json.loads(raw.decode("utf-8") or "{}")
            if not isinstance(payload, dict):
                return None, "payload must be object"
            return payload, None
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            return None, "invalid json"

    def _admin_auth_ok(self, payload: dict | None = None) -> bool:
        if not ADMIN_API_KEY:
            self._send(503, {"ok": False, "error": "admin api disabled"})
            return False

        header_key = (self.headers.get("X-Admin-Key") or "").strip()
        query_key = parse_qs(urlparse(self.path).query).get("key", [""])[0].strip()
        body_key = ""
        if payload and isinstance(payload, dict):
            body_key = str(payload.get("key", "")).strip()

        supplied = header_key or query_key or body_key
        if supplied != ADMIN_API_KEY:
            self._send(401, {"ok": False, "error": "unauthorized"})
            return False
        return True

    def do_OPTIONS(self):
        if not self._origin_allowed():
            self._send(403, {"ok": False, "error": "origin not allowed"})
            return
        self._send(200, {"ok": True})

    def do_GET(self):
        if not self._origin_allowed():
            self._send(403, {"ok": False, "error": "origin not allowed"})
            return
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            try:
                with get_connection() as conn:
                    conn.execute("SELECT 1").fetchone()
                database_ok = True
            except Exception:
                database_ok = False
            self._send(200 if database_ok else 503, {
                "ok": database_ok,
                "database": "ok" if database_ok else "unavailable",
                "now": datetime.now().isoformat(timespec="seconds"),
                "adminEnabled": bool(ADMIN_API_KEY),
            })
            return

        if parsed.path == "/api/admin/stats":
            if not self._admin_auth_ok():
                return
            self._send(200, {"ok": True, "stats": fetch_admin_stats()})
            return

        if parsed.path != "/api/leaderboard":
            self._send(404, {"ok": False, "error": "not found"})
            return

        query = parse_qs(parsed.query)
        scope = (query.get("scope", ["all"])[0] or "all").lower()
        if scope not in {"all", "daily"}:
            self._send(400, {"ok": False, "error": "invalid scope"})
            return

        seed = self._safe_int(query.get("seed", [today_seed()])[0], today_seed())
        limit = self._safe_int(query.get("limit", [MAX_RETURN])[0], MAX_RETURN)

        rows = fetch_entries(scope, seed, limit)
        self._send(200, {"ok": True, "scope": scope, "seed": seed, "entries": rows})

    def do_POST(self):
        if not self._origin_allowed():
            self._send(403, {"ok": False, "error": "origin not allowed"})
            return
        parsed = urlparse(self.path)
        if parsed.path == "/api/admin/cleanup":
            payload, error = self._parse_json_body()
            if error:
                self._send(400, {"ok": False, "error": error})
                return

            if not self._admin_auth_ok(payload):
                return

            min_score = payload.get("minScore")
            max_score = payload.get("maxScore")
            daily_seed = payload.get("dailySeed")
            mode = payload.get("mode")
            name_contains = payload.get("nameContains")
            before_at = payload.get("beforeAt")
            dry_run = bool(payload.get("dryRun", False))

            filters = {}
            try:
                if min_score is not None:
                    filters["minScore"] = int(min_score)
                if max_score is not None:
                    filters["maxScore"] = int(max_score)
                if daily_seed is not None:
                    filters["dailySeed"] = int(daily_seed)
            except (TypeError, ValueError):
                self._send(400, {"ok": False, "error": "invalid numeric filter"})
                return
            if mode is not None:
                filters["mode"] = str(mode)
            if name_contains is not None:
                filters["nameContains"] = str(name_contains)
            if before_at is not None and is_valid_iso_text(str(before_at)):
                filters["beforeAt"] = str(before_at)

            removed, remaining = cleanup_entries(filters, dry_run=dry_run)
            if remaining < 0:
                self._send(400, {
                    "ok": False,
                    "error": "at least one valid cleanup filter is required",
                })
                return

            self._send(200, {
                "ok": True,
                "dryRun": dry_run,
                "matched": removed,
                "remaining": remaining,
            })
            return

        if parsed.path != "/api/score":
            self._send(404, {"ok": False, "error": "not found"})
            return

        payload, error = self._parse_json_body()
        if error:
            self._send(400, {"ok": False, "error": error})
            return

        try:
            entry = normalize_entry(payload)
        except (TypeError, ValueError, OverflowError):
            self._send(400, {"ok": False, "error": "invalid score payload"})
            return

        # Use server time for duplicate detection; never trust a client-supplied timestamp.
        entry["at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        client_ip = self.client_address[0] if self.client_address else "unknown"
        rate_key = client_ip + ":" + entry["clientId"]

        prune_rate_limit_map()
        now_ts = time.time()
        recent = LAST_POST_BY_CLIENT.get(rate_key)
        if recent is not None and now_ts - recent < POST_COOLDOWN_SECONDS:
            wait_seconds = max(0.0, POST_COOLDOWN_SECONDS - (now_ts - recent))
            self._send(429, {
                "ok": False,
                "error": "too many requests",
                "retryAfter": round(wait_seconds, 2),
            })
            return

        if is_duplicate_recent_in_db(entry):
            self._send(200, {"ok": True, "deduplicated": True})
            return

        insert_entry(entry)
        LAST_POST_BY_CLIENT[rate_key] = now_ts
        self._send(200, {"ok": True})

    def log_message(self, format, *args):
        return


def main():
    ensure_db()
    migrate_from_legacy_json_if_needed()
    server = ThreadingHTTPServer((HOST, PORT), LeaderboardHandler)
    print(f"Leaderboard API listening on http://{HOST}:{PORT}")
    print("Database: PostgreSQL" if DATABASE_URL else f"Database: SQLite ({DB_FILE})")
    print(f"CORS allowed origins: {', '.join(sorted(CORS_ALLOW_ORIGINS)) or '(none)'}")
    print("GET  /api/health")
    print("GET  /api/leaderboard?scope=all")
    print("GET  /api/leaderboard?scope=daily&seed=20260728")
    print("POST /api/score")
    if ADMIN_API_KEY:
        print("GET  /api/admin/stats (needs key)")
        print("POST /api/admin/cleanup (needs key)")
    else:
        print("Admin API disabled (set ADMIN_API_KEY to enable)")
    server.serve_forever()


if __name__ == "__main__":
    main()

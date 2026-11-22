"""Persistence helpers for 2048 Remix."""

import json
import os


class ScoreStore:
    def __init__(self, path):
        self.path = path

    def load_best_score(self):
        try:
            if not os.path.exists(self.path):
                return 0
            with open(self.path, "r", encoding="utf-8") as file_obj:
                data = json.load(file_obj)
            best = int(data.get("best_score", 0))
            return max(0, best)
        except (ValueError, TypeError, OSError, json.JSONDecodeError):
            return 0

    def save_best_score(self, score):
        try:
            with open(self.path, "w", encoding="utf-8") as file_obj:
                json.dump({"best_score": int(score)}, file_obj)
        except OSError:
            pass

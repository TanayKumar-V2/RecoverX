from __future__ import annotations

import json
import sqlite3
from pathlib import Path

CACHE_DB_PATH = Path("data/llm_cache.db")


class LLMCache:
    def __init__(self, db_path: Path = CACHE_DB_PATH) -> None:
        self.db_path = db_path

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS llm_cache (
                    cache_key TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt_version TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            connection.commit()

    def get(self, cache_key: str) -> dict[str, object] | None:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                SELECT response_json
                FROM llm_cache
                WHERE cache_key = ?
                """,
                (cache_key,),
            )

            row = cursor.fetchone()

        if row is None:
            return None

        return json.loads(row[0])

    def set(
        self,
        cache_key: str,
        provider: str,
        model: str,
        prompt_version: str,
        response: dict[str, object],
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO llm_cache (
                    cache_key,
                    provider,
                    model,
                    prompt_version,
                    response_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    cache_key,
                    provider,
                    model,
                    prompt_version,
                    json.dumps(response),
                ),
            )

            connection.commit()

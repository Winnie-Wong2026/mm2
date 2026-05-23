"""Local file storage with a no-dependency JSONL fallback."""

from __future__ import annotations

import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping


class LocalDataStore:
    def __init__(self, root: str | Path = "data") -> None:
        self.root = Path(root)

    def write_jsonl(
        self,
        records: Iterable[Mapping[str, Any]],
        dataset: str,
        partition: str | None = None,
    ) -> Path:
        path = self._path(dataset, partition, "jsonl")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(_json_safe(dict(record)), ensure_ascii=False) + "\n")
        return path

    def write_csv(
        self,
        records: Iterable[Mapping[str, Any]],
        dataset: str,
        partition: str | None = None,
    ) -> Path:
        rows = [dict(record) for record in records]
        path = self._path(dataset, partition, "csv")
        path.parent.mkdir(parents=True, exist_ok=True)
        if not rows:
            path.write_text("", encoding="utf-8")
            return path
        fieldnames = sorted({key for row in rows for key in row.keys()})
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(_json_safe(row))
        return path

    def _path(self, dataset: str, partition: str | None, suffix: str) -> Path:
        if partition:
            return self.root / dataset / partition / f"part.{suffix}"
        return self.root / dataset / f"part.{suffix}"


def _json_safe(record: Mapping[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, (date, datetime)):
            safe[key] = value.isoformat()
        else:
            safe[key] = value
    return safe

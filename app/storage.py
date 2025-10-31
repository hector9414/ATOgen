"""Utility helpers to persist ATO data on disk."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from .models import ATO


class ATOStorage:
    """Simple JSON based persistence for ATOs."""

    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self._write([])

    def _read(self) -> List[dict]:
        with self.storage_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _write(self, data: List[dict]) -> None:
        with self.storage_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)

    def load_all(self) -> List[ATO]:
        return [ATO.from_dict(item) for item in self._read()]

    def save_all(self, atos: List[ATO]) -> None:
        payload = [ato.to_dict() for ato in atos]
        self._write(payload)

    def upsert(self, ato: ATO) -> None:
        atos = self.load_all()
        for idx, existing in enumerate(atos):
            if existing.id == ato.id:
                atos[idx] = ato
                break
        else:
            atos.append(ato)
        self.save_all(atos)

    def delete(self, ato_id: str) -> None:
        atos = [ato for ato in self.load_all() if ato.id != ato_id]
        self.save_all(atos)

    def get(self, ato_id: str) -> Optional[ATO]:
        for ato in self.load_all():
            if ato.id == ato_id:
                return ato
        return None

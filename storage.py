"""Dosya G/Ç katmanı: mekanlar ve rotalar için JSON (ve mekanlar için CSV)."""
from __future__ import annotations

import csv
import json
import os
from typing import List

from models import Location, Route

CSV_FIELDS = ["id", "name", "lat", "lon", "theme", "rating", "popularity", "description"]


class JsonStorage:
    """``data_dir`` altında ``locations.json`` ve ``routes.json`` yönetir."""

    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir
        self.locations_path = os.path.join(data_dir, "locations.json")
        self.routes_path = os.path.join(data_dir, "routes.json")

    # ---- mekanlar ----
    def load_locations(self) -> List[Location]:
        with open(self.locations_path, encoding="utf-8") as f:
            return [Location.from_dict(d) for d in json.load(f)]

    def save_locations(self, locations: List[Location]) -> None:
        self._write_json(self.locations_path, [l.to_dict() for l in locations])

    @staticmethod
    def import_locations_csv(path: str) -> List[Location]:
        with open(path, encoding="utf-8", newline="") as f:
            return [Location.from_dict(row) for row in csv.DictReader(f)]

    @staticmethod
    def export_locations_csv(path: str, locations: List[Location]) -> None:
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            w.writeheader()
            w.writerows(l.to_dict() for l in locations)

    # ---- rotalar ----
    def load_routes(self) -> List[Route]:
        if not os.path.exists(self.routes_path):
            return []
        with open(self.routes_path, encoding="utf-8") as f:
            return [Route.from_dict(d) for d in json.load(f)]

    def save_route(self, route: Route) -> None:
        """Aynı isimli rota varsa üzerine yazar."""
        routes = [r for r in self.load_routes() if r.name != route.name]
        routes.append(route)
        self._write_json(self.routes_path, [r.to_dict() for r in routes])

    def delete_route(self, name: str) -> bool:
        routes = self.load_routes()
        kept = [r for r in routes if r.name != name]
        self._write_json(self.routes_path, [r.to_dict() for r in kept])
        return len(kept) < len(routes)

    @staticmethod
    def _write_json(path: str, payload) -> None:
        tmp = path + ".tmp"                       # atomik yazım
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)

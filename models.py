"""Alan modelleri (domain models).

Bu modül yalnızca veri taşıyan sınıfları içerir; iş mantığı ``services.py``,
veri yapıları ``data_structures.py`` içindedir (Single Responsibility ilkesi).
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Dict, List


@dataclass(frozen=True)
class Location:
    """Haritadaki bir mekanı temsil eder (değiştirilemez / hashable)."""

    id: int
    name: str
    lat: float
    lon: float
    theme: str
    rating: float          # 0.0 - 5.0
    popularity: int        # 0 - 100
    description: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "Location":
        return Location(
            id=int(data["id"]), name=data["name"],
            lat=float(data["lat"]), lon=float(data["lon"]),
            theme=data["theme"], rating=float(data["rating"]),
            popularity=int(data["popularity"]),
            description=data.get("description", ""),
        )


@dataclass
class Route:
    """Kullanıcının kaydettiği rota (durak kimliklerinin sıralı listesi)."""

    name: str
    theme: str
    stop_ids: List[int] = field(default_factory=list)
    total_km: float = 0.0

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "Route":
        return Route(data["name"], data.get("theme", ""),
                     [int(i) for i in data.get("stop_ids", [])],
                     float(data.get("total_km", 0.0)))


@dataclass
class RoutePlan:
    """Hesaplanmış rota: duraklar + graf üzerindeki tam yol + toplam mesafe."""

    stop_ids: List[int]
    path_ids: List[int]
    total_km: float
    algorithm: str

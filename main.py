"""Uygulama giriş noktası.

Kullanım:
    python main.py          # GUI
    python main.py --demo   # ekransız (konsol) gösterim
"""
from __future__ import annotations

import argparse
import os

from services import PlannerService
from storage import JsonStorage

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def build_service() -> PlannerService:
    storage = JsonStorage(DATA_DIR)
    return PlannerService(storage.load_locations(), storage)


def run_demo(svc: PlannerService) -> None:
    lat, lon = 41.0082, 28.9784
    print("== 50 km içindeki yerler (puana göre, Heapsort) ==")
    for d, l in svc.nearby(lat, lon, 50, criterion="rating", algorithm="heapsort"):
        print(f"  {l.name:<20} {d:6.1f} km  ★{l.rating}")
    print("\n== Trie 'a' önekli arama ==")
    print("  ", [l.name for l in svc.search("a")])
    print("== AVL tam arama 'Pamukkale' ==", svc.find_by_name("pamukkale"))
    for name in ("Ayasofya", "Efes Antik Kenti", "Pamukkale", "Ölüdeniz"):
        svc.add_stop(svc.find_by_name(name)[0].id)
    svc.undo(); svc.redo()
    svc.optimize_order((lat, lon))
    for algo in ("dijkstra", "astar"):
        plan = svc.compute_route(algo)
        print(f"\n[{algo}] {' -> '.join(l.name for l in svc.stops())}: {plan.total_km:.1f} km")
    print("Kaydedildi:", svc.save_route("Demo Rota", "Karma"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    svc = build_service()
    if args.demo:
        run_demo(svc)
    else:
        from gui import TravelPlannerApp     # tkinter yalnızca GUI'de gerekli
        TravelPlannerApp(svc).mainloop()


if __name__ == "__main__":
    main()

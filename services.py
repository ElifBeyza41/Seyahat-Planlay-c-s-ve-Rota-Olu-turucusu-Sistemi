"""İş mantığı katmanı: arama, filtreleme, sıralama, rota oluşturma, Undo/Redo.

``PlannerService`` tüm veri yapılarını ve algoritmaları bir araya getirir;
GUI yalnızca bu sınıfla konuşur (Facade deseni).
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from algorithms import (binary_search, haversine, heap_sort, merge_sort,
                        quicksort, upper_bound)
from data_structures import AVLTree, Queue, Stack, Trie
from graph import Graph
from models import Location, Route, RoutePlan
from storage import JsonStorage

ALL_THEMES = "Tümü"
SORTERS = {"quicksort": quicksort, "mergesort": merge_sort, "heapsort": heap_sort}
Pair = Tuple[float, Location]          # (kullanıcıya uzaklık km, mekan)


class PlannerService:
    """Uygulamanın ana servisi."""

    def __init__(self, locations: List[Location], storage: JsonStorage) -> None:
        self.storage = storage
        self.locations: Dict[int, Location] = {l.id: l for l in locations}
        self.name_tree = AVLTree()      # isim -> Location (tam / önek arama)
        self.trie = Trie()              # isim -> id (otomatik tamamlama)
        for loc in locations:
            self.name_tree.insert(loc.name, loc)
            self.trie.insert(loc.name, loc.id)
        self.graph = Graph.from_locations(locations)
        self._queue = Queue()           # ziyaret sırası (FIFO)
        self._undo, self._redo = Stack(), Stack()

    # ------------------------------------------------------------ sorgular
    def all_locations(self) -> List[Location]:
        return list(self.locations.values())

    def themes(self) -> List[str]:
        return sorted({l.theme for l in self.locations.values()})

    def find_by_name(self, name: str) -> List[Location]:
        """AVL ağacı ile tam isim araması: O(log n)."""
        return self.name_tree.search(name)

    def search(self, prefix: str, limit: int = 50) -> List[Location]:
        """Trie ile önek araması (otomatik tamamlama): O(L + k)."""
        ids = [i for _, vals in self.trie.autocomplete(prefix, limit) for i in vals]
        return [self.locations[i] for i in ids]

    def rank(self, pairs: List[Pair], criterion: str = "distance",
             algorithm: str = "mergesort") -> List[Pair]:
        """Mekanları mesafe / puan / popülerliğe göre sıralar (seçilen algoritma)."""
        keys = {
            "distance": lambda p: p[0],
            "rating": lambda p: -p[1].rating,
            "popularity": lambda p: -p[1].popularity,
        }
        return SORTERS[algorithm](pairs, key=keys[criterion])

    def nearby(self, lat: float, lon: float, radius_km: float,
               theme: Optional[str] = None, criterion: str = "distance",
               algorithm: str = "mergesort") -> List[Pair]:
        """Yarıçap + tema filtresi.

        1) Tüm mesafeler hesaplanır ve mesafeye göre sıralanır  O(n log n)
        2) Yarıçap sınırı Binary Search ile bulunur               O(log n)
        3) Tema filtresi ve istenen kritere göre sıralama
        """
        pairs = [(haversine(lat, lon, l.lat, l.lon), l) for l in self.locations.values()]
        pairs = merge_sort(pairs, key=lambda p: p[0])
        pairs = pairs[:upper_bound(pairs, radius_km, key=lambda p: p[0])]
        if theme and theme != ALL_THEMES:
            pairs = [p for p in pairs if p[1].theme == theme]
        return self.rank(pairs, criterion, algorithm)

    # ------------------------------------------------- rota + undo / redo
    def stops(self) -> List[Location]:
        return [self.locations[i] for i in self._queue.to_list()]

    def _restore(self, ids: List[int]) -> None:
        self._queue.clear()
        for i in ids:
            self._queue.enqueue(i)

    def _commit(self) -> None:
        """Değişiklikten ÖNCE durumu Undo yığınına atar, Redo'yu sıfırlar."""
        self._undo.push(self._queue.to_list())
        self._redo.clear()

    def add_stop(self, loc_id: int) -> bool:
        if loc_id not in self.locations:
            raise KeyError(loc_id)
        if loc_id in self._queue.to_list():
            return False
        self._commit()
        self._queue.enqueue(loc_id)
        return True

    def remove_stop(self, loc_id: int) -> bool:
        ids = self._queue.to_list()
        if loc_id not in ids:
            return False
        self._commit()
        self._restore([i for i in ids if i != loc_id])
        return True

    def clear_route(self) -> None:
        if not self._queue.is_empty():
            self._commit()
            self._queue.clear()

    def undo(self) -> bool:
        if self._undo.is_empty():
            return False
        self._redo.push(self._queue.to_list())
        self._restore(self._undo.pop())
        return True

    def redo(self) -> bool:
        if self._redo.is_empty():
            return False
        self._undo.push(self._queue.to_list())
        self._restore(self._redo.pop())
        return True

    def optimize_order(self, user_pos: Optional[Tuple[float, float]] = None) -> None:
        """En yakın komşu sezgiseli (Dijkstra mesafeleriyle) ile durak sırasını
        kısaltır. Zaman: O(k · (V+E) log V), k = durak sayısı."""
        ids = self._queue.to_list()
        if len(ids) < 3:
            return
        if user_pos:
            first = min(ids, key=lambda i: haversine(*user_pos, self.locations[i].lat,
                                                     self.locations[i].lon))
        else:
            first = ids[0]
        order, remaining = [first], set(ids) - {first}
        while remaining:
            dist, _ = self.graph.dijkstra(order[-1])
            nxt = min(remaining, key=lambda i: dist[i])
            order.append(nxt)
            remaining.discard(nxt)
        if order != ids:
            self._commit()
            self._restore(order)

    def compute_route(self, algorithm: str = "astar") -> RoutePlan:
        """Kuyruğu sırayla boşaltarak ardışık duraklar arası en kısa yolu bulur."""
        working = Queue()
        for i in self._queue.to_list():
            working.enqueue(i)
        finder = (self.graph.shortest_path_astar if algorithm == "astar"
                  else self.graph.shortest_path_dijkstra)
        path: List[int] = []
        total, prev = 0.0, None
        while not working.is_empty():
            cur = working.dequeue()
            if prev is None:
                path = [cur]
            else:
                seg, d = finder(prev, cur)
                path.extend(seg[1:])
                total += d
            prev = cur
        return RoutePlan(self._queue.to_list(), path, total, algorithm)

    # ------------------------------------------------------------ kalıcılık
    def save_route(self, name: str, theme: str = "Karma") -> Route:
        plan = self.compute_route()
        route = Route(name, theme, plan.stop_ids, round(plan.total_km, 2))
        self.storage.save_route(route)
        return route

    def saved_route_names(self) -> List[str]:
        return [r.name for r in self.storage.load_routes()]

    def load_route(self, name: str) -> bool:
        for r in self.storage.load_routes():
            if r.name == name:
                self._commit()
                self._restore([i for i in r.stop_ids if i in self.locations])
                return True
        return False

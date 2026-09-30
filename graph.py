"""Mekanlar arası yol ağı ve en kısa yol algoritmaları (Dijkstra, A*)."""
from __future__ import annotations

import heapq
import itertools
import math
from typing import Dict, List, Optional, Sequence, Tuple

from algorithms import haversine, quicksort
from models import Location


class Graph:
    """Ağırlıklı, yönsüz graf (komşuluk listesi). Ağırlık = km."""

    def __init__(self) -> None:
        self._adj: Dict[int, Dict[int, float]] = {}
        self._coords: Dict[int, Tuple[float, float]] = {}

    def add_node(self, node: int, lat: float, lon: float) -> None:
        self._adj.setdefault(node, {})
        self._coords[node] = (lat, lon)

    def add_edge(self, u: int, v: int, w: float) -> None:
        self._adj[u][v] = w
        self._adj[v][u] = w

    def nodes(self) -> List[int]:
        return list(self._adj)

    @classmethod
    def from_locations(cls, locations: Sequence[Location], k: int = 4) -> "Graph":
        """Her mekanı en yakın ``k`` komşusuna bağlar ve bağlantısızlık varsa
        bileşenleri en yakın çiftlerden köprüler. Zaman: O(n² log n)."""
        g = cls()
        for loc in locations:
            g.add_node(loc.id, loc.lat, loc.lon)
        for a in locations:
            dists = [(haversine(a.lat, a.lon, b.lat, b.lon), b.id)
                     for b in locations if b.id != a.id]
            for d, bid in quicksort(dists, key=lambda t: t[0])[:k]:
                g.add_edge(a.id, bid, d)
        g._connect_components()
        return g

    def _components(self) -> List[List[int]]:
        seen, comps = set(), []
        for s in self._adj:
            if s in seen:
                continue
            comp, stack = [], [s]
            seen.add(s)
            while stack:
                u = stack.pop(); comp.append(u)
                for v in self._adj[u]:
                    if v not in seen:
                        seen.add(v); stack.append(v)
            comps.append(comp)
        return comps

    def _connect_components(self) -> None:
        while len(comps := self._components()) > 1:
            main, best = set(comps[0]), None
            for other in comps[1:]:
                for a in main:
                    for b in other:
                        d = haversine(*self._coords[a], *self._coords[b])
                        if best is None or d < best[0]:
                            best = (d, a, b)
            self.add_edge(best[1], best[2], best[0])

    # ---- Dijkstra ----
    def dijkstra(self, source: int, target: Optional[int] = None
                 ) -> Tuple[Dict[int, float], Dict[int, int]]:
        """Min-heap'li Dijkstra. Zaman O((V+E) log V), uzay O(V)."""
        dist = {n: math.inf for n in self._adj}
        prev: Dict[int, int] = {}
        dist[source] = 0.0
        heap = [(0.0, source)]
        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:
                continue
            if u == target:
                break
            for v, w in self._adj[u].items():
                nd = d + w
                if nd < dist[v]:
                    dist[v], prev[v] = nd, u
                    heapq.heappush(heap, (nd, v))
        return dist, prev

    def shortest_path_dijkstra(self, s: int, t: int) -> Tuple[List[int], float]:
        dist, prev = self.dijkstra(s, t)
        return self._rebuild(prev, s, t), dist[t]

    # ---- A* ----
    def shortest_path_astar(self, s: int, t: int) -> Tuple[List[int], float]:
        """A*; sezgisel = Haversine kuş uçuşu mesafe (kabul edilebilir, çünkü
        kenar ağırlıkları da Haversine'dir). En kötü O(E log V), pratikte
        Dijkstra'dan az düğüm genişletir."""
        goal = self._coords[t]
        h = lambda n: haversine(*self._coords[n], *goal)
        g = {s: 0.0}
        prev: Dict[int, int] = {}
        counter = itertools.count()
        heap = [(h(s), next(counter), s)]
        closed = set()
        while heap:
            _, _, u = heapq.heappop(heap)
            if u == t:
                return self._rebuild(prev, s, t), g[t]
            if u in closed:
                continue
            closed.add(u)
            for v, w in self._adj[u].items():
                ng = g[u] + w
                if ng < g.get(v, math.inf):
                    g[v], prev[v] = ng, u
                    heapq.heappush(heap, (ng + h(v), next(counter), v))
        return [], math.inf

    @staticmethod
    def _rebuild(prev: Dict[int, int], s: int, t: int) -> List[int]:
        if s != t and t not in prev:
            return []
        path = [t]
        while path[-1] != s:
            path.append(prev[path[-1]])
        return path[::-1]

"""Sıralama (Quick/Merge/Heap), Binary Search ve Haversine mesafe fonksiyonları.

Üç sıralama da ``key`` fonksiyonu alır, girdiyi değiştirmez (kopya döndürür).
"""
from __future__ import annotations

import math
import random
from typing import Any, Callable, List, Optional, Sequence

KeyFn = Optional[Callable[[Any], Any]]


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """İki koordinat arası büyük daire mesafesi (km). O(1)."""
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def quicksort(items: Sequence[Any], key: KeyFn = None) -> List[Any]:
    """Rastgele pivotlu, yerinde (in-place) Quicksort.

    Zaman: ortalama O(n log n), en kötü O(n²). Uzay: O(log n) (küçük parçaya
    özyineleme). Kararlı değildir.
    """
    key = key or (lambda x: x)
    arr = list(items)

    def partition(lo: int, hi: int) -> int:
        r = random.randint(lo, hi)
        arr[r], arr[hi] = arr[hi], arr[r]
        pivot, i = key(arr[hi]), lo
        for j in range(lo, hi):
            if key(arr[j]) < pivot:
                arr[i], arr[j] = arr[j], arr[i]
                i += 1
        arr[i], arr[hi] = arr[hi], arr[i]
        return i

    def sort(lo: int, hi: int) -> None:
        while lo < hi:
            p = partition(lo, hi)
            if p - lo < hi - p:
                sort(lo, p - 1); lo = p + 1
            else:
                sort(p + 1, hi); hi = p - 1

    sort(0, len(arr) - 1)
    return arr


def merge_sort(items: Sequence[Any], key: KeyFn = None) -> List[Any]:
    """Kararlı Mergesort. Zaman: her durumda O(n log n). Uzay: O(n)."""
    key = key or (lambda x: x)
    arr = list(items)
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left, right = merge_sort(arr[:mid], key), merge_sort(arr[mid:], key)
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if key(right[j]) < key(left[i]):
            out.append(right[j]); j += 1
        else:
            out.append(left[i]); i += 1
    out.extend(left[i:]); out.extend(right[j:])
    return out


def heap_sort(items: Sequence[Any], key: KeyFn = None) -> List[Any]:
    """Yerinde Heapsort (max-heap). Zaman: O(n log n). Uzay: O(1) ek."""
    key = key or (lambda x: x)
    arr = list(items)
    n = len(arr)

    def sift_down(root: int, end: int) -> None:
        while (child := 2 * root + 1) < end:
            if child + 1 < end and key(arr[child]) < key(arr[child + 1]):
                child += 1
            if key(arr[root]) >= key(arr[child]):
                return
            arr[root], arr[child] = arr[child], arr[root]
            root = child

    for start in range(n // 2 - 1, -1, -1):     # heap oluştur: O(n)
        sift_down(start, n)
    for end in range(n - 1, 0, -1):             # kökü sona at: O(n log n)
        arr[0], arr[end] = arr[end], arr[0]
        sift_down(0, end)
    return arr


def lower_bound(sorted_items: Sequence[Any], target: Any, key: KeyFn = None) -> int:
    """İlk ``key(x) >= target`` indeksi. O(log n)."""
    key = key or (lambda x: x)
    lo, hi = 0, len(sorted_items)
    while lo < hi:
        mid = (lo + hi) // 2
        if key(sorted_items[mid]) < target:
            lo = mid + 1
        else:
            hi = mid
    return lo


def upper_bound(sorted_items: Sequence[Any], target: Any, key: KeyFn = None) -> int:
    """İlk ``key(x) > target`` indeksi (yarıçap kesimi için). O(log n)."""
    key = key or (lambda x: x)
    lo, hi = 0, len(sorted_items)
    while lo < hi:
        mid = (lo + hi) // 2
        if key(sorted_items[mid]) <= target:
            lo = mid + 1
        else:
            hi = mid
    return lo


def binary_search(sorted_items: Sequence[Any], target: Any, key: KeyFn = None) -> int:
    """Sıralı dizide hedefin ilk indeksi, yoksa -1. Zaman O(log n), uzay O(1)."""
    key = key or (lambda x: x)
    i = lower_bound(sorted_items, target, key)
    return i if i < len(sorted_items) and key(sorted_items[i]) == target else -1

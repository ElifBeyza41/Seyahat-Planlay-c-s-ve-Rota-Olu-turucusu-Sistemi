"""Sıfırdan yazılmış veri yapıları: AVL Ağacı, Trie, Stack, Queue.

Karmaşıklık özeti (n = eleman sayısı, L = kelime uzunluğu):

| Yapı  | İşlem            | Zaman        | Ek Uzay |
|-------|------------------|--------------|---------|
| AVL   | insert/search/delete | O(log n) | O(log n) özyineleme yığını |
| Trie  | insert/search/delete | O(L)     | O(L)    |
| Stack | push / pop / peek    | O(1)*    | O(1)    |
| Queue | enqueue / dequeue    | O(1)     | O(1)    |
(*push amortize O(1), Python listesi kullanıldığı için.)
"""
from __future__ import annotations

from typing import Any, Iterator, List, Optional, Tuple


def normalize(text: str) -> str:
    """Türkçe karakterlere duyarlı küçük harfe çevirme (İ/I sorunu)."""
    return text.strip().replace("İ", "i").replace("I", "ı").lower()


# --------------------------------------------------------------------------
# AVL AĞACI
# --------------------------------------------------------------------------
class _AVLNode:
    __slots__ = ("key", "values", "left", "right", "height")

    def __init__(self, key: str, value: Any):
        self.key = key
        self.values: List[Any] = [value]   # aynı isimli mekanlar için
        self.left: Optional["_AVLNode"] = None
        self.right: Optional["_AVLNode"] = None
        self.height = 1


class AVLTree:
    """Kendini dengeleyen ikili arama ağacı (Adelson-Velsky & Landis).

    Her düğümde |yükseklik(sol) - yükseklik(sağ)| <= 1 korunur; ihlalde
    tek/çift rotasyon yapılır. Anahtarlar ``normalize`` edilmiş mekan adlarıdır.
    """

    def __init__(self) -> None:
        self._root: Optional[_AVLNode] = None
        self._size = 0

    def __len__(self) -> int:
        return self._size

    @property
    def height(self) -> int:
        return self._h(self._root)

    # ---- yardımcılar ----
    @staticmethod
    def _h(n: Optional[_AVLNode]) -> int:
        return n.height if n else 0

    def _update(self, n: _AVLNode) -> None:
        n.height = 1 + max(self._h(n.left), self._h(n.right))

    def _balance(self, n: Optional[_AVLNode]) -> int:
        return self._h(n.left) - self._h(n.right) if n else 0

    def _rot_right(self, y: _AVLNode) -> _AVLNode:
        x = y.left
        y.left, x.right = x.right, y
        self._update(y); self._update(x)
        return x

    def _rot_left(self, x: _AVLNode) -> _AVLNode:
        y = x.right
        x.right, y.left = y.left, x
        self._update(x); self._update(y)
        return y

    def _rebalance(self, n: _AVLNode) -> _AVLNode:
        self._update(n)
        b = self._balance(n)
        if b > 1:                                   # sol ağır
            if self._balance(n.left) < 0:           # Left-Right
                n.left = self._rot_left(n.left)
            return self._rot_right(n)
        if b < -1:                                  # sağ ağır
            if self._balance(n.right) > 0:          # Right-Left
                n.right = self._rot_right(n.right)
            return self._rot_left(n)
        return n

    # ---- insert ----
    def insert(self, key: str, value: Any) -> None:
        """O(log n): anahtarı ekler; varsa değeri mevcut düğüme ekler."""
        self._root = self._insert(self._root, normalize(key), value)

    def _insert(self, node, key, value):
        if node is None:
            self._size += 1
            return _AVLNode(key, value)
        if key < node.key:
            node.left = self._insert(node.left, key, value)
        elif key > node.key:
            node.right = self._insert(node.right, key, value)
        else:
            if value not in node.values:
                node.values.append(value)
            return node
        return self._rebalance(node)

    # ---- search ----
    def search(self, key: str) -> List[Any]:
        """O(log n): tam eşleşen anahtarın değer listesini döndürür."""
        key, node = normalize(key), self._root
        while node:
            if key < node.key:
                node = node.left
            elif key > node.key:
                node = node.right
            else:
                return list(node.values)
        return []

    def prefix_search(self, prefix: str) -> List[Any]:
        """O(log n + k): ``prefix`` ile başlayan anahtarların değerleri (sıralı)."""
        prefix = normalize(prefix)
        out: List[Any] = []
        self._collect(self._root, prefix, prefix + "\uffff", out)
        return out

    def _collect(self, node, lo, hi, out):
        if node is None:
            return
        if lo < node.key:
            self._collect(node.left, lo, hi, out)
        if node.key.startswith(lo):
            out.extend(node.values)
        if node.key < hi:
            self._collect(node.right, lo, hi, out)

    # ---- delete ----
    def delete(self, key: str) -> bool:
        """O(log n): anahtarı siler; silindiyse True."""
        before = self._size
        self._root = self._delete(self._root, normalize(key))
        return self._size < before

    def _delete(self, node, key):
        if node is None:
            return None
        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            self._size -= 1
            if node.left is None:
                return node.right
            if node.right is None:
                return node.left
            succ = node.right                       # in-order ardıl
            while succ.left:
                succ = succ.left
            node.key, node.values = succ.key, succ.values
            node.right = self._delete_min(node.right)
        return self._rebalance(node)

    def _delete_min(self, node):
        if node.left is None:
            return node.right
        node.left = self._delete_min(node.left)
        return self._rebalance(node)

    def in_order(self) -> Iterator[Tuple[str, List[Any]]]:
        """O(n): (anahtar, değerler) çiftlerini alfabetik verir."""
        def walk(n):
            if n:
                yield from walk(n.left)
                yield n.key, list(n.values)
                yield from walk(n.right)
        return walk(self._root)


# --------------------------------------------------------------------------
# TRIE
# --------------------------------------------------------------------------
class _TrieNode:
    __slots__ = ("children", "is_end", "values")

    def __init__(self) -> None:
        self.children: dict = {}
        self.is_end = False
        self.values: List[Any] = []


class Trie:
    """Önek ağacı: otomatik tamamlama (autocomplete) için kullanılır."""

    def __init__(self) -> None:
        self._root = _TrieNode()
        self._count = 0

    def __len__(self) -> int:
        return self._count

    def insert(self, word: str, value: Any = None) -> None:
        """O(L): kelimeyi ve ilişkili değeri ekler."""
        node = self._root
        for ch in normalize(word):
            node = node.children.setdefault(ch, _TrieNode())
        if not node.is_end:
            node.is_end = True
            self._count += 1
        if value is not None and value not in node.values:
            node.values.append(value)

    def _find(self, prefix: str) -> Optional[_TrieNode]:
        node = self._root
        for ch in normalize(prefix):
            node = node.children.get(ch)
            if node is None:
                return None
        return node

    def search(self, word: str) -> bool:
        """O(L): kelime tam olarak var mı?"""
        node = self._find(word)
        return bool(node and node.is_end)

    def starts_with(self, prefix: str) -> bool:
        """O(L): bu önekle başlayan kelime var mı?"""
        return self._find(prefix) is not None

    def autocomplete(self, prefix: str, limit: int = 10) -> List[Tuple[str, List[Any]]]:
        """O(L + k): önekle başlayan kelimeleri alfabetik (kelime, değerler) verir."""
        start = self._find(prefix)
        if start is None:
            return []
        base, results = normalize(prefix), []
        stack = [(start, base)]
        while stack and len(results) < limit:
            node, word = stack.pop()
            if node.is_end:
                results.append((word, list(node.values)))
            for ch in sorted(node.children, reverse=True):
                stack.append((node.children[ch], word + ch))
        return results

    def delete(self, word: str) -> bool:
        """O(L): kelimeyi siler, artık kullanılmayan düğümleri budar."""
        word = normalize(word)

        def _del(node: _TrieNode, i: int) -> bool:
            if i == len(word):
                if not node.is_end:
                    return False
                node.is_end, node.values = False, []
                self._count -= 1
                return True
            child = node.children.get(word[i])
            if child is None:
                return False
            removed = _del(child, i + 1)
            if removed and not child.is_end and not child.children:
                del node.children[word[i]]
            return removed

        return _del(self._root, 0)


# --------------------------------------------------------------------------
# STACK (Undo / Redo)
# --------------------------------------------------------------------------
class Stack:
    """LIFO yığın. Undo/Redo geçmişini tutmak için kullanılır."""

    def __init__(self) -> None:
        self._items: List[Any] = []

    def __len__(self) -> int:
        return len(self._items)

    def is_empty(self) -> bool:
        return not self._items

    def push(self, item: Any) -> None:
        """O(1) amortize."""
        self._items.append(item)

    def pop(self) -> Any:
        """O(1)."""
        if self.is_empty():
            raise IndexError("Stack boş")
        return self._items.pop()

    def peek(self) -> Any:
        """O(1)."""
        if self.is_empty():
            raise IndexError("Stack boş")
        return self._items[-1]

    def clear(self) -> None:
        self._items.clear()


# --------------------------------------------------------------------------
# QUEUE (Rota sırası)
# --------------------------------------------------------------------------
class _QNode:
    __slots__ = ("value", "next")

    def __init__(self, value: Any):
        self.value, self.next = value, None


class Queue:
    """FIFO kuyruk (bağlı liste). Ziyaret edilecek durakların sırasını tutar."""

    def __init__(self) -> None:
        self._head: Optional[_QNode] = None
        self._tail: Optional[_QNode] = None
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def is_empty(self) -> bool:
        return self._size == 0

    def enqueue(self, item: Any) -> None:
        """O(1): sona ekler."""
        node = _QNode(item)
        if self._tail:
            self._tail.next = node
        else:
            self._head = node
        self._tail = node
        self._size += 1

    def dequeue(self) -> Any:
        """O(1): baştan çıkarır."""
        if self._head is None:
            raise IndexError("Queue boş")
        node = self._head
        self._head = node.next
        if self._head is None:
            self._tail = None
        self._size -= 1
        return node.value

    def peek(self) -> Any:
        if self._head is None:
            raise IndexError("Queue boş")
        return self._head.value

    def to_list(self) -> List[Any]:
        """O(n): sıradaki elemanların kopyası."""
        out, cur = [], self._head
        while cur:
            out.append(cur.value)
            cur = cur.next
        return out

    def clear(self) -> None:
        self._head = self._tail = None
        self._size = 0

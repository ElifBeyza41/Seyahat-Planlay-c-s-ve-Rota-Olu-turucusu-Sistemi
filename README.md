# Akıllı Seyahat ve Rota Planlama Sistemi (Travel Planner)

Python 3.10+ · Tkinter · Harici bağımlılık yok.

```bash
python main.py          # GUI
python main.py --demo   # konsol gösterimi
```

## Mimari (katmanlar)

| Modül | Sorumluluk |
|---|---|
| `models.py` | `Location`, `Route`, `RoutePlan` (veri sınıfları) |
| `data_structures.py` | AVL Ağacı, Trie, Stack, Queue (sıfırdan) |
| `algorithms.py` | Quicksort, Mergesort, Heapsort, Binary Search, Haversine |
| `graph.py` | Graf, Dijkstra, A* |
| `storage.py` | JSON (mekan + rota) ve CSV (mekan) G/Ç |
| `services.py` | `PlannerService` (Facade): arama, filtre, sıralama, rota, Undo/Redo |
| `gui.py` | Tkinter arayüzü + Canvas harita |

Veri yapılarının projedeki yeri: **AVL** → tam isim araması · **Trie** → otomatik tamamlama ·
**Stack** → Undo/Redo · **Queue** → durak ziyaret sırası · **Binary Search** → yarıçap kesimi ·
**Dijkstra/A\*** → duraklar arası en kısa yol.

## Karmaşıklık Analizi

n: eleman sayısı, L: kelime uzunluğu, k: sonuç sayısı, V/E: düğüm/kenar sayısı

| Yapı | İşlem | Zaman | Uzay |
|---|---|---|---|
| AVL Ağacı | Insert | O(log n) | O(1) ek (özyineleme O(log n)) |
| AVL Ağacı | Search | O(log n) | O(1) |
| AVL Ağacı | Delete | O(log n) | O(log n) özyineleme |
| AVL Ağacı | Prefix search | O(log n + k) | O(k) |
| Trie | Insert | O(L) | O(L) |
| Trie | Search / Delete | O(L) | O(1) / O(L) |
| Trie | Autocomplete | O(L + k·L) | O(k·L) |
| Stack | Push | O(1) amortize | O(1) |
| Stack | Pop / Peek | O(1) | O(1) |
| Queue (bağlı liste) | Enqueue | O(1) | O(1) |
| Queue (bağlı liste) | Dequeue | O(1) | O(1) |
| Quicksort | Sıralama | Ort. O(n log n), en kötü O(n²) | O(log n) |
| Mergesort | Sıralama | O(n log n) | O(n) |
| Heapsort | Sıralama | O(n log n) | O(1) |
| Binary Search | Arama | O(log n) | O(1) |
| Dijkstra (min-heap) | En kısa yol | O((V+E) log V) | O(V) |
| A* | En kısa yol | En kötü O(E log V), pratikte daha hızlı | O(V) |

Toplam yapı uzayı: AVL O(n), Trie O(toplam karakter), Graf O(V+E).
Yakın mekan sorgusu: O(n log n) sıralama + O(log n) Binary Search + O(n) tema filtresi.

## Kullanım notları
- Haritaya tıklayınca konum değişir; bir mekân işaretine tıklayınca bilgisi görünür.
- Arama kutusu Trie ile önek araması yapar (yarıçap yok sayılır).
- Rotalar `data/routes.json` içine kaydedilir; mekanlar `data/locations.json` (CSV içe/dışa aktarım `JsonStorage` içinde).
- Graf, her mekanı en yakın 4 komşusuna bağlar; kenar ağırlıkları Haversine km'dir. Gerçek yol verisi için `Graph.add_edge` ile OSM/API mesafeleri eklenebilir.

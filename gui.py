"""Tkinter arayüzü: harita (Canvas), filtreler, sıralama, rota yönetimi."""
from __future__ import annotations

import math
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from algorithms import haversine
from services import ALL_THEMES, PlannerService

THEME_COLORS = {
    "Tarihi Yerler": "#c0392b",
    "Deniz/Plaj Tatili": "#2980b9",
    "Doğa/Doğa Sporları": "#27ae60",
    "Kültürel": "#8e44ad",
}
CRITERIA = {"Mesafe": "distance", "Puan": "rating", "Popülerlik": "popularity"}
SORT_ALGOS = {"Quicksort": "quicksort", "Mergesort": "mergesort", "Heapsort": "heapsort"}
ROUTE_ALGOS = {"A*": "astar", "Dijkstra": "dijkstra"}
PAD = 45


class TravelPlannerApp(tk.Tk):
    """Ana pencere. İş mantığı için yalnızca ``PlannerService`` kullanır."""

    def __init__(self, service: PlannerService) -> None:
        super().__init__()
        self.title("Akıllı Seyahat ve Rota Planlama Sistemi")
        self.geometry("1300x780")
        self.minsize(1000, 620)
        self.service = service
        self.user = (41.0082, 28.9784)          # varsayılan: İstanbul
        self.results = []                        # [(mesafe, Location)]
        self.plan = None
        locs = service.all_locations()
        lats, lons = [l.lat for l in locs], [l.lon for l in locs]
        self._bounds = (min(lats), max(lats), min(lons), max(lons))
        self._build_ui()
        self.refresh_results()

    # ------------------------------------------------------------- arayüz
    def _build_ui(self) -> None:
        left = ttk.Frame(self, padding=8)
        left.pack(side="left", fill="y")
        self.canvas = tk.Canvas(self, bg="#eaf2f8", highlightthickness=0)
        self.canvas.pack(side="right", fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.redraw())
        self.canvas.bind("<Button-1>", self._on_click)

        self.lat_var = tk.StringVar(value=f"{self.user[0]:.4f}")
        self.lon_var = tk.StringVar(value=f"{self.user[1]:.4f}")
        self.radius_var = tk.StringVar(value="400")
        self.theme_var = tk.StringVar(value=ALL_THEMES)
        self.crit_var = tk.StringVar(value="Mesafe")
        self.sort_var = tk.StringVar(value="Mergesort")
        self.rt_var = tk.StringVar(value="A*")
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Haritaya tıklayarak konumunuzu seçin.")

        box = ttk.LabelFrame(left, text="Konum ve Filtreler", padding=6)
        box.pack(fill="x")
        rows = [
            ("Enlem", ttk.Entry(box, textvariable=self.lat_var, width=14)),
            ("Boylam", ttk.Entry(box, textvariable=self.lon_var, width=14)),
            ("Yarıçap (km)", ttk.Entry(box, textvariable=self.radius_var, width=14)),
            ("Tema", self._combo(box, self.theme_var, [ALL_THEMES] + self.service.themes())),
            ("Sırala", self._combo(box, self.crit_var, list(CRITERIA))),
            ("Algoritma", self._combo(box, self.sort_var, list(SORT_ALGOS))),
            ("Ara (Trie)", ttk.Entry(box, textvariable=self.search_var, width=14)),
        ]
        for r, (text, w) in enumerate(rows):
            ttk.Label(box, text=text).grid(row=r, column=0, sticky="w", pady=2)
            w.grid(row=r, column=1, sticky="ew", pady=2)
            if isinstance(w, ttk.Entry):
                w.bind("<Return>", lambda e: self._apply_position())
        self.search_var.trace_add("write", lambda *a: self.refresh_results())
        ttk.Button(box, text="Konumu Uygula", command=self._apply_position
                   ).grid(row=len(rows), column=0, columnspan=2, sticky="ew", pady=4)

        ttk.Label(left, text="Mekanlar").pack(anchor="w", pady=(8, 0))
        self.results_lb = tk.Listbox(left, height=11, width=52, exportselection=False)
        self.results_lb.pack(fill="x")
        ttk.Button(left, text="Rotaya Ekle ➜", command=self._add_selected).pack(fill="x", pady=2)

        ttk.Label(left, text="Rota (ziyaret sırası)").pack(anchor="w", pady=(6, 0))
        self.route_lb = tk.Listbox(left, height=8, width=52, exportselection=False)
        self.route_lb.pack(fill="x")

        bar = ttk.Frame(left)
        bar.pack(fill="x", pady=2)
        for text, cmd in [("Çıkar", self._remove_selected), ("⟲ Geri Al", self._undo),
                          ("⟳ Yinele", self._redo), ("Temizle", self._clear)]:
            ttk.Button(bar, text=text, command=cmd, width=11).pack(side="left", padx=1)
        bar2 = ttk.Frame(left)
        bar2.pack(fill="x", pady=2)
        ttk.Button(bar2, text="Sırayı Optimize Et", command=self._optimize).pack(side="left", padx=1)
        self._combo(bar2, self.rt_var, list(ROUTE_ALGOS), width=9).pack(side="left", padx=4)
        ttk.Button(bar2, text="Rotayı Hesapla", command=self._compute).pack(side="left", padx=1)
        bar3 = ttk.Frame(left)
        bar3.pack(fill="x", pady=2)
        ttk.Button(bar3, text="💾 Kaydet", command=self._save).pack(side="left", expand=True, fill="x", padx=1)
        ttk.Button(bar3, text="📂 Yükle", command=self._load).pack(side="left", expand=True, fill="x", padx=1)
        ttk.Label(left, textvariable=self.status_var, wraplength=380, foreground="#1a5276"
                  ).pack(fill="x", pady=6)

    def _combo(self, parent, var, values, width=14) -> ttk.Combobox:
        cb = ttk.Combobox(parent, textvariable=var, values=values, state="readonly", width=width)
        cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_results())
        return cb

    # --------------------------------------------------------- olay işleyiciler
    def _apply_position(self) -> None:
        try:
            lat, lon = float(self.lat_var.get()), float(self.lon_var.get())
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError
        except ValueError:
            messagebox.showerror("Hata", "Geçerli enlem (-90..90) ve boylam (-180..180) girin.")
            return
        self.user = (lat, lon)
        self.refresh_results()

    def refresh_results(self) -> None:
        lat, lon = self.user
        query = self.search_var.get().strip()
        crit, algo = CRITERIA[self.crit_var.get()], SORT_ALGOS[self.sort_var.get()]
        if query:
            pairs = [(haversine(lat, lon, l.lat, l.lon), l) for l in self.service.search(query)]
            self.results = self.service.rank(pairs, crit, algo)
        else:
            try:
                radius = float(self.radius_var.get())
            except ValueError:
                radius = 400.0
            self.results = self.service.nearby(lat, lon, radius, self.theme_var.get(), crit, algo)
        self.results_lb.delete(0, "end")
        for d, l in self.results:
            self.results_lb.insert("end", f"{l.name}  |  {l.theme.split('/')[0]}  |  "
                                          f"{d:.0f} km  |  ★{l.rating}  |  {l.popularity}")
        self.redraw()

    def _refresh_route_list(self) -> None:
        self.route_lb.delete(0, "end")
        for i, l in enumerate(self.service.stops(), 1):
            self.route_lb.insert("end", f"{i}. {l.name}")

    def _route_changed(self, msg: str = "") -> None:
        self.plan = None
        self._refresh_route_list()
        self.redraw()
        self.status_var.set(msg or f"Rotada {len(self.service.stops())} durak var.")

    def _add_selected(self) -> None:
        sel = self.results_lb.curselection()
        if not sel:
            return
        loc = self.results[sel[0]][1]
        if self.service.add_stop(loc.id):
            self._route_changed(f"'{loc.name}' rotaya eklendi.")
        else:
            self.status_var.set(f"'{loc.name}' zaten rotada.")

    def _remove_selected(self) -> None:
        sel = self.route_lb.curselection()
        if sel and self.service.remove_stop(self.service.stops()[sel[0]].id):
            self._route_changed()

    def _undo(self) -> None:
        self._route_changed("Geri alındı." if self.service.undo() else "Geri alınacak işlem yok.")

    def _redo(self) -> None:
        self._route_changed("Yinelendi." if self.service.redo() else "Yinelenecek işlem yok.")

    def _clear(self) -> None:
        self.service.clear_route()
        self._route_changed("Rota temizlendi.")

    def _optimize(self) -> None:
        self.service.optimize_order(self.user)
        self._route_changed("Durak sırası optimize edildi.")

    def _compute(self) -> None:
        stops = self.service.stops()
        if len(stops) < 1:
            messagebox.showinfo("Bilgi", "Önce rotaya durak ekleyin.")
            return
        self.plan = self.service.compute_route(ROUTE_ALGOS[self.rt_var.get()])
        first = haversine(*self.user, stops[0].lat, stops[0].lon)
        self.status_var.set(f"Rota ({self.rt_var.get()}): {self.plan.total_km:.1f} km  "
                            f"(+ konumdan ilk durağa {first:.1f} km kuş uçuşu)")
        self.redraw()

    def _save(self) -> None:
        if not self.service.stops():
            messagebox.showinfo("Bilgi", "Kaydedilecek rota boş.")
            return
        name = simpledialog.askstring("Rotayı Kaydet", "Rota adı:", parent=self)
        if name and name.strip():
            r = self.service.save_route(name.strip(), self.theme_var.get())
            self.status_var.set(f"'{r.name}' kaydedildi ({r.total_km} km).")

    def _load(self) -> None:
        names = self.service.saved_route_names()
        if not names:
            messagebox.showinfo("Bilgi", "Kayıtlı rota yok.")
            return
        name = simpledialog.askstring("Rota Yükle", "Kayıtlı rotalar:\n" + "\n".join(names)
                                      + "\n\nYüklenecek rota adı:", parent=self)
        if name and self.service.load_route(name.strip()):
            self._route_changed(f"'{name.strip()}' yüklendi.")
        elif name:
            messagebox.showerror("Hata", "Rota bulunamadı.")

    # --------------------------------------------------------------- harita
    def _project(self, lat: float, lon: float):
        w, h = max(self.canvas.winfo_width(), 200), max(self.canvas.winfo_height(), 200)
        a, b, c, d = self._bounds
        x = PAD + (lon - c) / (d - c) * (w - 2 * PAD)
        y = PAD + (b - lat) / (b - a) * (h - 2 * PAD)
        return x, y

    def _unproject(self, x: float, y: float):
        w, h = max(self.canvas.winfo_width(), 200), max(self.canvas.winfo_height(), 200)
        a, b, c, d = self._bounds
        return b - (y - PAD) / (h - 2 * PAD) * (b - a), c + (x - PAD) / (w - 2 * PAD) * (d - c)

    def _on_click(self, event) -> None:
        near = min(self.service.all_locations(),
                   key=lambda l: math.dist(self._project(l.lat, l.lon), (event.x, event.y)))
        if math.dist(self._project(near.lat, near.lon), (event.x, event.y)) < 10:
            self.status_var.set(f"{near.name} — {near.theme} — ★{near.rating}: {near.description}")
            for i, (_, l) in enumerate(self.results):
                if l.id == near.id:
                    self.results_lb.selection_clear(0, "end")
                    self.results_lb.selection_set(i)
                    self.results_lb.see(i)
            return
        lat, lon = self._unproject(event.x, event.y)
        self.user = (lat, lon)
        self.lat_var.set(f"{lat:.4f}")
        self.lon_var.set(f"{lon:.4f}")
        self.refresh_results()

    def redraw(self) -> None:
        c = self.canvas
        c.delete("all")
        shown = {l.id for _, l in self.results}
        for l in self.service.all_locations():          # filtre dışı: soluk nokta
            if l.id not in shown:
                x, y = self._project(l.lat, l.lon)
                c.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#b2babb", outline="")
        ulat, ulon = self.user
        if not self.search_var.get().strip():           # yarıçap dairesi
            try:
                r = float(self.radius_var.get())
                dlat = r / 111.0
                dlon = r / (111.0 * max(math.cos(math.radians(ulat)), 0.1))
                x1, y1 = self._project(ulat + dlat, ulon - dlon)
                x2, y2 = self._project(ulat - dlat, ulon + dlon)
                c.create_oval(x1, y1, x2, y2, outline="#e74c3c", dash=(4, 4))
            except ValueError:
                pass
        if self.plan and len(self.plan.path_ids) > 1:    # hesaplanmış yol
            pts = []
            for i in self.plan.path_ids:
                l = self.service.locations[i]
                pts.extend(self._project(l.lat, l.lon))
            c.create_line(*pts, fill="#f39c12", width=3, arrow="last")
        for _, l in self.results:
            x, y = self._project(l.lat, l.lon)
            c.create_oval(x - 6, y - 6, x + 6, y + 6, fill=THEME_COLORS.get(l.theme, "#555"),
                          outline="white", width=1.5)
        for i, l in enumerate(self.service.stops(), 1):  # rota durakları
            x, y = self._project(l.lat, l.lon)
            c.create_oval(x - 11, y - 11, x + 11, y + 11, outline="#f39c12", width=2)
            c.create_text(x, y - 20, text=f"{i}. {l.name}", font=("Segoe UI", 9, "bold"))
        ux, uy = self._project(ulat, ulon)
        c.create_polygon(ux, uy - 10, ux - 8, uy + 6, ux + 8, uy + 6, fill="#e74c3c", outline="white")
        for i, (name, col) in enumerate(THEME_COLORS.items()):   # gösterge
            c.create_oval(12, 14 + i * 20, 22, 24 + i * 20, fill=col, outline="")
            c.create_text(30, 19 + i * 20, text=name, anchor="w", font=("Segoe UI", 9))

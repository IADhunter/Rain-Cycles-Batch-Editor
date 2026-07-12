import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from copy import deepcopy
import re

CANVAS_W = 1366
CANVAS_H = 768
HANDLE = 6
SCROLLBAR_W = 16
DUP_OFFSET = 20

COLORS = {
    "teal": "#0f6e56",
    "coral": "#993c1d",
    "purple": "#3c3489",
    "gray": "#444441",
    "pink": "#72243e",
    "scroll_track": "#7a2e12",
    "text_square": "#0a7a7a",
}

TYPE_COLOR = {
    "frame": "teal",
    "button": "gray",
    "label": "pink",
    "entry": "text_square",
    "scroll": "coral",
    "switch": "pink",
}

# which edges move for each resize handle
HANDLE_DEFS = {
    "e": {"right": True},
    "w": {"left": True},
    "s": {"bottom": True},
    "n": {"top": True},
    "se": {"right": True, "bottom": True},
    "sw": {"left": True, "bottom": True},
    "ne": {"right": True, "top": True},
    "nw": {"left": True, "top": True},
}

DEFAULT_ITEMS = [
    {"id": "frame_palette_header", "x": 40, "y": 112, "w": 416, "h": 40, "c": "teal"},
    {"id": "frame_pa", "x": 40, "y": 160, "w": 200, "h": 104, "c": "teal"},
    {"id": "ent_pa_new", "x": 10, "y": 40, "w": 120, "h": 28, "c": "text_square", "parent": "frame_pa"},
    {"id": "frame_fa", "x": 256, "y": 160, "w": 200, "h": 104, "c": "teal"},
    {"id": "ent_fa_new", "x": 10, "y": 40, "w": 120, "h": 28, "c": "text_square", "parent": "frame_fa"},
    {"id": "ent_fade_opacity", "x": 140, "y": 40, "w": 50, "h": 28, "c": "text_square", "parent": "frame_fa"},
    {"id": "btn_add_b1", "x": 40, "y": 272, "w": 200, "h": 32, "c": "teal"},
    {"id": "scroll_b1", "x": 40, "y": 344, "w": 184, "h": 208, "c": "coral"},
    {"id": "btn_clear_b1", "x": 40, "y": 560, "w": 200, "h": 24, "c": "teal"},
    {"id": "btn_add_b2", "x": 256, "y": 272, "w": 200, "h": 32, "c": "teal"},
    {"id": "frame_fb_op", "x": 256, "y": 304, "w": 200, "h": 32, "c": "teal"},
    {"id": "ent_fade_b_opacity", "x": 140, "y": 4, "w": 50, "h": 22, "c": "text_square", "parent": "frame_fb_op"},
    {"id": "scroll_b2", "x": 256, "y": 344, "w": 184, "h": 208, "c": "coral"},
    {"id": "btn_clear_b2", "x": 256, "y": 560, "w": 200, "h": 24, "c": "teal"},
    {"id": "frame_rain_header", "x": 472, "y": 112, "w": 240, "h": 40, "c": "purple"},
    {"id": "frame_rain_controls", "x": 472, "y": 160, "w": 240, "h": 176, "c": "purple"},
    {"id": "ent_rain_type", "x": 90, "y": 45, "w": 131, "h": 28, "c": "text_square", "parent": "frame_rain_controls"},
    {"id": "ent_rain_view", "x": 90, "y": 75, "w": 131, "h": 28, "c": "text_square", "parent": "frame_rain_controls"},
    {"id": "ent_rain_tint_1", "x": 90, "y": 105, "w": 64, "h": 28, "c": "text_square", "parent": "frame_rain_controls"},
    {"id": "ent_rain_tint_2", "x": 157, "y": 105, "w": 64, "h": 28, "c": "text_square", "parent": "frame_rain_controls"},
    {"id": "frame_ambient_header", "x": 728, "y": 112, "w": 232, "h": 40, "c": "purple"},
    {"id": "frame_ambient_controls", "x": 728, "y": 160, "w": 232, "h": 176, "c": "purple"},
    {"id": "ent_decal_mult", "x": 155, "y": 15, "w": 65, "h": 28, "c": "text_square", "parent": "frame_ambient_controls"},
    {"id": "ent_light_mult", "x": 155, "y": 55, "w": 65, "h": 28, "c": "text_square", "parent": "frame_ambient_controls"},
    {"id": "ent_grime_mult", "x": 155, "y": 95, "w": 65, "h": 28, "c": "text_square", "parent": "frame_ambient_controls"},
    {"id": "ent_clouds_mult", "x": 155, "y": 135, "w": 65, "h": 28, "c": "text_square", "parent": "frame_ambient_controls"},
    {"id": "console_log", "x": 728, "y": 488, "w": 232, "h": 32, "c": "gray"},
    {"id": "btn_input", "x": 728, "y": 536, "w": 112, "h": 32, "c": "gray"},
    {"id": "btn_output", "x": 848, "y": 536, "w": 112, "h": 32, "c": "gray"},
    {"id": "btn_generate", "x": 728, "y": 584, "w": 232, "h": 48, "c": "gray"},
    {"id": "credits_label", "x": 10, "y": 720, "w": 140, "h": 24, "c": "gray"},
]


PLACE_RE = re.compile(
    r'self\.(?P<name>\w+)\.place\(\s*x=(?P<x>-?\d+)\s*,\s*y=(?P<y>-?\d+)\s*\)\s*'
    r'#\s*(?:parent=(?P<parent>\w+)\s+)?width=(?P<w>\d+)\s+height=(?P<h>\d+)'
)


def _guess_color(name, has_parent):
    if has_parent:
        return "text_square"
    n = name.lower()
    if "scroll" in n:
        return "coral"
    if n.startswith("frame_rain") or n.startswith("frame_ambient"):
        return "purple"
    if n.startswith("frame"):
        return "teal"
    if n.startswith("btn") or "button" in n:
        return "gray"
    if n.startswith("sw_") or "switch" in n:
        return "pink"
    if n.startswith("ent_") or "entry" in n:
        return "text_square"
    return "gray"


def parse_preset_text(text):
    """Finds every 'self.name.place(x=.., y=..)  # [parent=X] width=W height=H'
    occurrence anywhere in the text, regardless of line breaks."""
    entries = []
    for m in PLACE_RE.finditer(text):
        entries.append({
            "id": m.group("name"),
            "x": int(m.group("x")),
            "y": int(m.group("y")),
            "w": int(m.group("w")),
            "h": int(m.group("h")),
            "parent": m.group("parent"),
        })
    return entries


def _is_scroll(it):
    return it.get("c") == "coral" or "scroll" in it["id"]


def _visual_w(it):
    return it["w"] + (SCROLLBAR_W if _is_scroll(it) else 0)


class LayoutEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RWSBE - Editor visual de interfaz")
        self.geometry("1200x800")
        self.configure(bg="#1e1e1e")

        self.items = deepcopy(DEFAULT_ITEMS)
        self.selected_ids = set()
        self.history = []
        self.history_index = -1
        self.counter = 1
        self.canvas_ids = {}
        self._syncing = False
        self._drag_start = None
        self._drag_origin = {}
        self._resize_start = None
        self.zoom_scale = 1.0
        self.snap_grid_size = 0
        self._axis_lock = None

        self._build_toolbar()
        self._build_main_area()
        self._build_output()

        self.bind_all("<Control-z>", lambda e: self.undo())
        self.bind_all("<Control-Z>", lambda e: self.redo())
        self.bind_all("<Control-Shift-Z>", lambda e: self.redo())
        self.bind_all("<Control-Shift-z>", lambda e: self.redo())
        self.bind_all("<Control-d>", lambda e: self.duplicate_selected())
        self.bind_all("<Control-D>", lambda e: self.duplicate_selected())
        self.bind_all("<Delete>", self._on_delete_key)
        self.bind_all("<BackSpace>", self._on_delete_key)

        self.push_history()
        self.render()

        self.canvas.xview_moveto(0.5)
        self.canvas.yview_moveto(0.5)

    @property
    def selected_id(self):
        """Convenience accessor for code paths that only make sense for a
        single selected item (panel editing, renaming, resize). Returns
        None when zero or more than one item is selected."""
        if len(self.selected_ids) == 1:
            return next(iter(self.selected_ids))
        return None

    def _build_toolbar(self):
        bar = tk.Frame(self, bg="#141414")
        bar.pack(side="top", fill="x")

        self.type_var = tk.StringVar(value="frame")
        combo = ttk.Combobox(bar, textvariable=self.type_var, state="readonly", width=16,
                              values=["frame", "button", "label", "entry", "scroll", "switch"])
        combo.pack(side="left", padx=6, pady=6)

        tk.Button(bar, text="+ Agregar", command=self.add_item).pack(side="left", padx=4)
        tk.Button(bar, text="Duplicar (Ctrl+D)", command=self.duplicate_selected).pack(side="left", padx=4)
        tk.Button(bar, text="Eliminar seleccionado", command=self.delete_selected,
                  fg="#f88").pack(side="left", padx=4)
        tk.Button(bar, text="Deshacer (Ctrl+Z)", command=self.undo).pack(side="left", padx=4)
        tk.Button(bar, text="Rehacer (Ctrl+Shift+Z)", command=self.redo).pack(side="left", padx=4)
        tk.Button(bar, text="Copiar coordenadas", command=self.copy_output).pack(side="left", padx=4)
        tk.Button(bar, text="Exportar .txt", command=self.export_preset).pack(side="left", padx=4)
        tk.Button(bar, text="Importar .txt", command=self.import_preset).pack(side="left", padx=4)

        tk.Label(bar, text="Grid:", bg="#141414", fg="#999").pack(side="left", padx=(10, 2))
        self.grid_var = tk.IntVar(value=0)
        self.grid_scale = tk.Scale(bar, from_=0, to=100, orient="horizontal", length=100,
                                    variable=self.grid_var, bg="#141414", fg="#999",
                                    highlightthickness=0, troughcolor="#333",
                                    command=self._on_grid_change, showvalue=False)
        self.grid_scale.pack(side="left", padx=2)
        self.grid_label = tk.Label(bar, text="0", bg="#141414", fg="#999", width=3)
        self.grid_label.pack(side="left", padx=(0, 4))
        self.grid_scale.bind("<MouseWheel>", self._on_grid_wheel)
        self.grid_scale.bind("<Button-4>", self._on_grid_wheel)
        self.grid_scale.bind("<Button-5>", self._on_grid_wheel)

        tk.Label(bar, text="Click: seleccionar/mover | Ctrl+Click: multi-selección | Ctrl+D: duplicar | "
                          "Bordes: redimensionar | Rueda: zoom | Click central: pan | Shift: eje fijo",
                 bg="#141414", fg="#999").pack(side="left", padx=12)

    def _build_main_area(self):
        main = tk.Frame(self, bg="#1e1e1e")
        main.pack(side="top", fill="both", expand=True)

        canvas_frame = tk.Frame(main, bg="#1e1e1e")
        canvas_frame.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(
            canvas_frame, bg="#2b2b2b",
            scrollregion=(-5000, -5000, 5000, 5000),
            xscrollincrement=1, yscrollincrement=1
        )
        vbar = tk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        hbar = tk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)

        self.canvas.bind("<ButtonPress-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

        self.canvas.bind("<ButtonPress-2>", self._on_pan_start)
        self.canvas.bind("<B2-Motion>", self._on_pan_move)
        self.canvas.bind("<ButtonRelease-2>", self._on_pan_end)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_start)
        self.canvas.bind("<B3-Motion>", self._on_pan_move)
        self.canvas.bind("<ButtonRelease-3>", self._on_pan_end)

        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)

        panel = tk.Frame(main, bg="#1e1e1e", width=220)
        panel.pack(side="right", fill="y")
        panel.pack_propagate(False)

        tk.Label(panel, text="Elemento seleccionado", bg="#1e1e1e", fg="#ccc",
                 font=("Segoe UI", 10, "bold")).pack(pady=(10, 6))

        self.name_var = tk.StringVar()
        self.x_var = tk.StringVar()
        self.y_var = tk.StringVar()
        self.w_var = tk.StringVar()
        self.h_var = tk.StringVar()

        name_row = tk.Frame(panel, bg="#1e1e1e")
        name_row.pack(fill="x", padx=10, pady=4)
        tk.Label(name_row, text="Nombre", bg="#1e1e1e", fg="#999", width=8, anchor="w").pack(side="left")
        name_entry = tk.Entry(name_row, textvariable=self.name_var, bg="#2d2d2d", fg="#eaeaea",
                               insertbackground="#eaeaea")
        name_entry.pack(side="left", fill="x", expand=True)
        name_entry.bind("<Return>", self._apply_name)
        name_entry.bind("<FocusOut>", self._apply_name)

        for label, var, key in [("x", self.x_var, "x"), ("y", self.y_var, "y"),
                                 ("w", self.w_var, "w"), ("h", self.h_var, "h")]:
            row = tk.Frame(panel, bg="#1e1e1e")
            row.pack(fill="x", padx=10, pady=4)
            tk.Label(row, text=label, bg="#1e1e1e", fg="#999", width=8, anchor="w").pack(side="left")
            entry = tk.Entry(row, textvariable=var, bg="#2d2d2d", fg="#eaeaea", insertbackground="#eaeaea")
            entry.pack(side="left", fill="x", expand=True)
            var.trace_add("write", lambda *a, k=key: self._on_field_change(k))
            entry.bind("<FocusOut>", lambda e: self.push_history())
            entry.bind("<Return>", lambda e: self.push_history())

        self.multi_label = tk.Label(panel, text="", bg="#1e1e1e", fg="#4da3ff", wraplength=200, justify="left")
        self.multi_label.pack(fill="x", padx=10, pady=(10, 4))

    def _build_output(self):
        # kept as a no-op stub: text is generated on demand for export/copy,
        # no visible panel needed since exporting goes straight to a file.
        pass

    def snapshot(self):
        return deepcopy(self.items)

    def push_history(self):
        self.history = self.history[: self.history_index + 1]
        self.history.append(self.snapshot())
        self.history_index = len(self.history) - 1

    def undo(self):
        if self.history_index <= 0:
            return
        self.history_index -= 1
        self.items = deepcopy(self.history[self.history_index])
        self.render()

    def redo(self):
        if self.history_index >= len(self.history) - 1:
            return
        self.history_index += 1
        self.items = deepcopy(self.history[self.history_index])
        self.render()

    def find_item(self, item_id):
        for it in self.items:
            if it["id"] == item_id:
                return it
        return None

    def _unique_id(self, base_id):
        existing = {it["id"] for it in self.items}
        candidate = f"{base_id}_copy"
        n = 1
        while candidate in existing:
            n += 1
            candidate = f"{base_id}_copy{n}"
        return candidate

    def add_item(self):
        t = self.type_var.get()
        new_id = f"{t}_{self.counter}"
        self.counter += 1
        w = 100 if t == "label" else 150
        h = 24 if t == "label" else 40

        parent_id = None
        if t == "entry" and self.selected_id:
            selected = self.find_item(self.selected_id)
            if selected and "parent" not in selected:
                parent_id = self.selected_id
                w = 80
                h = 28

        item = {"id": new_id, "x": 400, "y": 250, "w": w, "h": h, "c": TYPE_COLOR.get(t, "gray")}
        if parent_id:
            item["parent"] = parent_id
            parent = self.find_item(parent_id)
            if parent:
                item["x"] = min(10, parent["w"] - w)
                item["y"] = min(10, parent["h"] - h)

        if parent_id:
            parent_idx = next((i for i, it in enumerate(self.items) if it["id"] == parent_id), -1)
            if parent_idx >= 0:
                self.items.insert(parent_idx + 1, item)
            else:
                self.items.append(item)
        else:
            self.items.append(item)

        self.selected_ids = {new_id}
        self.push_history()
        self.render()

    def duplicate_selected(self):
        if not self.selected_ids:
            return

        # duplicating a frame also duplicates its children automatically,
        # even if they weren't individually selected
        ids_to_dup = set(self.selected_ids)
        for it in self.items:
            if it.get("parent") in self.selected_ids:
                ids_to_dup.add(it["id"])

        id_map = {old_id: self._unique_id(old_id) for old_id in ids_to_dup}

        new_items = []
        new_selection = set()
        for it in self.items:
            if it["id"] not in ids_to_dup:
                continue
            new_it = deepcopy(it)
            new_it["id"] = id_map[it["id"]]

            if "parent" in it:
                parent_also_dup = it["parent"] in self.selected_ids
                if parent_also_dup:
                    # keep the same relative position inside the (also duplicated) parent
                    new_it["parent"] = id_map[it["parent"]]
                else:
                    # duplicated on its own: stays in the original parent, offset a bit
                    new_it["parent"] = it["parent"]
                    parent_obj = self.find_item(it["parent"])
                    nx = it["x"] + DUP_OFFSET // 2
                    ny = it["y"] + DUP_OFFSET // 2
                    if parent_obj:
                        nx = min(nx, parent_obj["w"] - it["w"])
                        ny = min(ny, parent_obj["h"] - it["h"])
                    new_it["x"] = max(0, nx)
                    new_it["y"] = max(0, ny)
            else:
                new_it["x"] = max(0, min(CANVAS_W - it["w"], it["x"] + DUP_OFFSET))
                new_it["y"] = max(0, min(CANVAS_H - it["h"], it["y"] + DUP_OFFSET))

            new_items.append(new_it)
            new_selection.add(new_it["id"])

        self.items.extend(new_items)
        self.selected_ids = new_selection
        self.push_history()
        self.render()

    def delete_selected(self):
        if not self.selected_ids:
            return
        to_delete = set()
        for sid in self.selected_ids:
            to_delete.add(sid)
            for it in self.items:
                if it.get("parent") == sid:
                    to_delete.add(it["id"])
        self.items = [it for it in self.items if it["id"] not in to_delete]
        self.selected_ids = set()
        self.push_history()
        self.render()

    def _on_delete_key(self, event):
        focused = self.focus_get()
        if isinstance(focused, tk.Entry):
            return
        self.delete_selected()

    def copy_output(self):
        self.clipboard_clear()
        self.clipboard_append("\n".join(self._generate_lines()))

    def _generate_lines(self):
        lines = []
        for it in self.items:
            if "parent" in it:
                line = f'self.{it["id"]}.place(x={it["x"]}, y={it["y"]})   # parent={it["parent"]} width={it["w"]} height={it["h"]}'
            else:
                line = f'self.{it["id"]}.place(x={it["x"]}, y={it["y"]})   # width={it["w"]} height={it["h"]}'
            lines.append(line)
        return lines

    def update_output(self):
        pass  # no visible panel anymore; lines are generated on demand (see _generate_lines)

    def export_preset(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivo de texto", "*.txt"), ("Todos los archivos", "*.*")],
            title="Guardar preset de posiciones",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(self._generate_lines()))
        except OSError as e:
            messagebox.showerror("Exportar", f"No se pudo guardar el archivo:\n{e}")
            return
        messagebox.showinfo("Exportar", f"Preset guardado en:\n{path}")

    def import_preset(self):
        path = filedialog.askopenfilename(
            filetypes=[("Archivo de texto", "*.txt"), ("Todos los archivos", "*.*")],
            title="Importar preset de posiciones",
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except OSError as e:
            messagebox.showerror("Importar", f"No se pudo leer el archivo:\n{e}")
            return
        self._apply_preset_text(text)

    def _apply_preset_text(self, text):
        parsed = parse_preset_text(text)
        if not parsed:
            messagebox.showerror(
                "Importar",
                "No se encontraron líneas con el formato esperado:\n"
                "self.nombre.place(x=.., y=..)   # [parent=X] width=W height=H",
            )
            return

        roots = [p for p in parsed if not p["parent"]]
        children_map = {}
        for p in parsed:
            if p["parent"]:
                children_map.setdefault(p["parent"], []).append(p)

        new_items = []
        seen_parents = set()
        for r in roots:
            new_items.append({
                "id": r["id"], "x": r["x"], "y": r["y"], "w": r["w"], "h": r["h"],
                "c": _guess_color(r["id"], False),
            })
            seen_parents.add(r["id"])
            for c in children_map.get(r["id"], []):
                new_items.append({
                    "id": c["id"], "x": c["x"], "y": c["y"], "w": c["w"], "h": c["h"],
                    "c": _guess_color(c["id"], True), "parent": c["parent"],
                })

        # children whose declared parent wasn't found among the roots (edge case)
        for p in parsed:
            if p["parent"] and p["parent"] not in seen_parents:
                new_items.append({
                    "id": p["id"], "x": p["x"], "y": p["y"], "w": p["w"], "h": p["h"],
                    "c": _guess_color(p["id"], True), "parent": p["parent"],
                })

        self.items = new_items
        self.selected_ids = set()
        self.push_history()
        self.render()
        messagebox.showinfo("Importar", f"Se cargaron {len(new_items)} elementos.")

    def update_panel(self):
        it = self.find_item(self.selected_id)
        self._syncing = True
        if not it:
            self.name_var.set("")
            self.x_var.set("")
            self.y_var.set("")
            self.w_var.set("")
            self.h_var.set("")
        else:
            self.name_var.set(it["id"])
            self.x_var.set(str(it["x"]))
            self.y_var.set(str(it["y"]))
            self.w_var.set(str(it["w"]))
            self.h_var.set(str(it["h"]))
        self._syncing = False

        if len(self.selected_ids) > 1:
            self.multi_label.config(text=f"{len(self.selected_ids)} elementos seleccionados\n(muévelos juntos arrastrando)")
        else:
            self.multi_label.config(text="")

    def _apply_name(self, event):
        it = self.find_item(self.selected_id)
        if not it:
            return
        new_name = self.name_var.get().strip()
        if new_name and new_name != it["id"]:
            old_id = it["id"]
            it["id"] = new_name
            for child in self.items:
                if child.get("parent") == old_id:
                    child["parent"] = new_name
            if old_id in self.selected_ids:
                self.selected_ids.discard(old_id)
                self.selected_ids.add(new_name)
            self.push_history()
            self.render()

    def _on_field_change(self, key):
        if self._syncing:
            return
        it = self.find_item(self.selected_id)
        if not it:
            return
        var_map = {"x": self.x_var, "y": self.y_var, "w": self.w_var, "h": self.h_var}
        raw = var_map[key].get()
        try:
            val = int(raw)
        except ValueError:
            return

        val = self._snap(val)

        if "parent" in it and key in ("x", "y", "w", "h"):
            parent = self.find_item(it["parent"])
            if parent:
                if key == "x":
                    val = max(0, min(val, parent["w"] - it["w"]))
                elif key == "y":
                    val = max(0, min(val, parent["h"] - it["h"]))
                elif key == "w":
                    val = max(10, min(val, parent["w"] - it["x"]))
                elif key == "h":
                    val = max(10, min(val, parent["h"] - it["y"]))
        else:
            val = max(0, val) if key in ("x", "y") else max(10, val)

        it[key] = val
        self._move_canvas_item(it)
        if "parent" not in it:
            for child in self.items:
                if child.get("parent") == it["id"]:
                    self._move_canvas_item(child)
        self.update_output()

    def _zoomed(self, val):
        return val * self.zoom_scale

    def _unzoomed(self, val):
        return val / self.zoom_scale

    def _snap(self, val):
        if self.snap_grid_size <= 0:
            return val
        return round(val / self.snap_grid_size) * self.snap_grid_size

    def _on_grid_change(self, val):
        self.snap_grid_size = int(val)
        if hasattr(self, 'grid_label'):
            self.grid_label.config(text=str(self.snap_grid_size))
        self.render()

    def _on_grid_wheel(self, event):
        current = self.grid_var.get()
        if event.num == 4 or event.delta > 0:
            new_val = min(100, current + 1)
        else:
            new_val = max(0, current - 1)
        self.grid_scale.set(new_val)
        self._on_grid_change(new_val)
        return "break"

    def _on_pan_start(self, event):
        self.canvas.scan_mark(event.x, event.y)
        self.canvas.config(cursor="fleur")

    def _on_pan_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _on_pan_end(self, event):
        self.canvas.config(cursor="")

    def _on_mousewheel(self, event):
        if event.num == 4 or event.delta > 0:
            factor = 1.1
        else:
            factor = 0.9

        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        logical_x = self._unzoomed(cx)
        logical_y = self._unzoomed(cy)

        self.zoom_scale *= factor
        self.zoom_scale = max(0.1, min(5.0, self.zoom_scale))

        self.render()

        new_cx = self._zoomed(logical_x)
        new_cy = self._zoomed(logical_y)
        cur_x = self.canvas.canvasx(0)
        cur_y = self.canvas.canvasy(0)
        dx = (new_cx - event.x) - cur_x
        dy = (new_cy - event.y) - cur_y
        self.canvas.xview_scroll(int(dx), "units")
        self.canvas.yview_scroll(int(dy), "units")

    def render(self):
        xscroll = self.canvas.xview()
        yscroll = self.canvas.yview()

        self.canvas.delete("all")
        self.canvas_ids = {}

        self._draw_window_frame()

        for gx in range(0, CANVAS_W + 1, 20):
            self.canvas.create_line(self._zoomed(gx), self._zoomed(0), self._zoomed(gx), self._zoomed(CANVAS_H), fill="#3a3a3a")
        for gy in range(0, CANVAS_H + 1, 20):
            self.canvas.create_line(self._zoomed(0), self._zoomed(gy), self._zoomed(CANVAS_W), self._zoomed(gy), fill="#3a3a3a")

        if self.snap_grid_size > 0:
            g = self.snap_grid_size
            grid_color = "#ffffff"
            for gx in range(0, CANVAS_W + 1, g):
                self.canvas.create_line(self._zoomed(gx), self._zoomed(0), self._zoomed(gx), self._zoomed(CANVAS_H), fill=grid_color, width=1)
            for gy in range(0, CANVAS_H + 1, g):
                self.canvas.create_line(self._zoomed(0), self._zoomed(gy), self._zoomed(CANVAS_W), self._zoomed(gy), fill=grid_color, width=1)

        for it in self.items:
            self._draw_item(it)

        self.update_output()
        self.update_panel()

        self.canvas.xview_moveto(xscroll[0])
        self.canvas.yview_moveto(yscroll[0])

    def _draw_window_frame(self):
        x0 = self._zoomed(0)
        y0 = self._zoomed(0)
        x1 = self._zoomed(CANVAS_W)
        y1 = self._zoomed(CANVAS_H)
        self.canvas.create_rectangle(
            x0, y0, x1, y1,
            outline="#ff3333",
            width=max(1, int(2 * self.zoom_scale)),
            dash=(max(3, int(6 * self.zoom_scale)), max(2, int(4 * self.zoom_scale))),
            fill="",
            tags=("window_frame",),
        )
        label_size = max(6, int(10 * self.zoom_scale))
        self.canvas.create_text(
            x0 + self._zoomed(6), y0 + self._zoomed(6),
            text=f"Ventana: {CANVAS_W}x{CANVAS_H}",
            fill="#ff3333",
            font=("Segoe UI", label_size, "bold"),
            anchor="nw",
            tags=("window_frame",),
        )
        corner_len = self._zoomed(20)
        corner_w = max(1, int(2 * self.zoom_scale))
        corners = [
            (x0, y0, x0 + corner_len, y0, x0, y0, x0, y0 + corner_len),
            (x1, y0, x1 - corner_len, y0, x1, y0, x1, y0 + corner_len),
            (x0, y1, x0 + corner_len, y1, x0, y1, x0, y1 - corner_len),
            (x1, y1, x1 - corner_len, y1, x1, y1, x1, y1 - corner_len),
        ]
        for x0l, y0l, x1l, y1l, x0r, y0r, x1r, y1r in corners:
            self.canvas.create_line(x0l, y0l, x1l, y1l, fill="#ff3333", width=corner_w, tags=("window_frame",))
            self.canvas.create_line(x0r, y0r, x1r, y1r, fill="#ff3333", width=corner_w, tags=("window_frame",))

    @staticmethod
    def _handle_rect(x0, y0, x1, y1, hs, mode):
        """Returns the handle's rectangle, always fully INSIDE the item's
        bounding box (flush with the edge it controls, never protruding)."""
        mid_x = (x0 + x1) / 2
        mid_y = (y0 + y1) / 2
        if mode == "nw":
            return x0, y0, x0 + hs, y0 + hs
        if mode == "ne":
            return x1 - hs, y0, x1, y0 + hs
        if mode == "sw":
            return x0, y1 - hs, x0 + hs, y1
        if mode == "se":
            return x1 - hs, y1 - hs, x1, y1
        if mode == "n":
            return mid_x - hs, y0, mid_x + hs, y0 + hs
        if mode == "s":
            return mid_x - hs, y1 - hs, mid_x + hs, y1
        if mode == "w":
            return x0, mid_y - hs, x0 + hs, mid_y + hs
        if mode == "e":
            return x1 - hs, mid_y - hs, x1, mid_y + hs
        return x0, y0, x0 + hs, y0 + hs

    def _draw_item(self, it):
        fill = COLORS.get(it["c"], "#444441")
        is_selected = it["id"] in self.selected_ids
        show_handles = is_selected and len(self.selected_ids) == 1
        outline = "#4da3ff" if is_selected else "#666666"
        width = 3 if is_selected else 1

        abs_x, abs_y = self._abs_pos(it)
        x0 = self._zoomed(abs_x)
        y0 = self._zoomed(abs_y)
        x1 = self._zoomed(abs_x + it["w"])
        y1 = self._zoomed(abs_y + it["h"])
        vw = self._zoomed(_visual_w(it))
        right = x0 + vw

        rect = self.canvas.create_rectangle(
            x0, y0, x1, y1, fill=fill, outline=outline, width=width,
            tags=("item", f"id:{it['id']}"),
        )
        text_size = max(1, int(8 * self.zoom_scale))
        text = self.canvas.create_text(
            (x0 + x1) / 2, (y0 + y1) / 2, text=it["id"], fill="white",
            font=("Segoe UI", text_size), tags=("item", f"id:{it['id']}"),
        )
        ids = {"rect": rect, "text": text}

        if _is_scroll(it):
            sb = self.canvas.create_rectangle(
                x1, y0, right, y1, fill=COLORS["scroll_track"], outline=outline, width=width,
                tags=("item", f"id:{it['id']}")
            )
            ids["scroll_track"] = sb

        if show_handles:
            hs = max(4, self._zoomed(HANDLE))
            has_parent = "parent" in it
            modes = ["e"] if has_parent else ["n", "s", "e", "w", "ne", "nw", "se", "sw"]
            for mode in modes:
                hx0, hy0, hx1, hy1 = self._handle_rect(x0, y0, right, y1, hs, mode)
                color = "#ffcc00" if len(mode) == 2 else "#4da3ff"
                hid = self.canvas.create_rectangle(
                    hx0, hy0, hx1, hy1, fill=color, outline="",
                    tags=("handle", f"mode:{mode}", f"id:{it['id']}"),
                )
                ids[f"handle_{mode}"] = hid

        self.canvas_ids[it["id"]] = ids

    def _move_canvas_item(self, it):
        ids = self.canvas_ids.get(it["id"])
        if not ids:
            return
        abs_x, abs_y = self._abs_pos(it)
        x0 = self._zoomed(abs_x)
        y0 = self._zoomed(abs_y)
        x1 = self._zoomed(abs_x + it["w"])
        y1 = self._zoomed(abs_y + it["h"])
        vw = self._zoomed(_visual_w(it))
        right = x0 + vw
        self.canvas.coords(ids["rect"], x0, y0, x1, y1)
        self.canvas.coords(ids["text"], (x0 + x1) / 2, (y0 + y1) / 2)
        if "scroll_track" in ids:
            self.canvas.coords(ids["scroll_track"], x1, y0, right, y1)

        hs = max(4, self._zoomed(HANDLE))
        for key in ids:
            if key.startswith("handle_"):
                mode = key[len("handle_"):]
                hx0, hy0, hx1, hy1 = self._handle_rect(x0, y0, right, y1, hs, mode)
                self.canvas.coords(ids[key], hx0, hy0, hx1, hy1)

    def _abs_pos(self, it):
        x, y = it["x"], it["y"]
        if "parent" in it:
            parent = self.find_item(it["parent"])
            if parent:
                px, py = self._abs_pos(parent)
                x += px
                y += py
        return x, y

    @staticmethod
    def _tag_item_id(tags):
        for t in tags:
            if t.startswith("id:"):
                return t[3:]
        return None

    @staticmethod
    def _tag_handle_mode(tags):
        for t in tags:
            if t.startswith("mode:"):
                return t[5:]
        return None

    def _on_canvas_click(self, event):
        ctrl = bool(event.state & 0x0004)
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        hits = self.canvas.find_overlapping(x - 1, y - 1, x + 1, y + 1)
        item_id = None
        handle_mode = None
        for h in reversed(hits):
            tags = self.canvas.gettags(h)
            if "handle" in tags:
                item_id = self._tag_item_id(tags)
                handle_mode = self._tag_handle_mode(tags)
                break
            if "item" in tags:
                item_id = self._tag_item_id(tags)
                break

        if item_id is None:
            if not ctrl and self.selected_ids:
                self.selected_ids = set()
                self.render()
            return

        if handle_mode:
            if self.selected_ids != {item_id}:
                self.selected_ids = {item_id}
                self.render()
            self._start_resize(event, item_id, handle_mode)
            return

        if ctrl:
            if item_id in self.selected_ids:
                self.selected_ids.discard(item_id)
            else:
                self.selected_ids.add(item_id)
            self.render()
            return

        if item_id not in self.selected_ids:
            self.selected_ids = {item_id}
            self.render()

        self._start_move(event)

    def _start_move(self, event):
        self._drag_start = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        self._axis_lock = None
        self._drag_origin = {}
        for iid in self.selected_ids:
            it = self.find_item(iid)
            if it:
                self._drag_origin[iid] = (it["x"], it["y"])
        self._resize_start = None

    def _start_resize(self, event, item_id, mode):
        it = self.find_item(item_id)
        if not it:
            return
        self._resize_start = (
            self.canvas.canvasx(event.x), self.canvas.canvasy(event.y),
            it["x"], it["y"], it["w"], it["h"],
            mode, item_id,
        )
        self._drag_start = None
        self._drag_origin = {}

    def _on_canvas_drag(self, event):
        if self._drag_start is not None:
            self._do_move(event)
        elif self._resize_start is not None:
            self._do_resize(event)

    def _do_move(self, event):
        if self._drag_start is None or not self._drag_origin:
            return
        sx, sy = self._drag_start
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        dx = self._unzoomed(cx - sx)
        dy = self._unzoomed(cy - sy)

        if event.state & 0x1:
            if self._axis_lock is None:
                if abs(dx) > abs(dy):
                    self._axis_lock = "x"
                elif abs(dy) > abs(dx):
                    self._axis_lock = "y"
            if self._axis_lock == "x":
                dy = 0
            elif self._axis_lock == "y":
                dx = 0
        else:
            self._axis_lock = None

        for iid, (ox, oy) in self._drag_origin.items():
            it = self.find_item(iid)
            if not it:
                continue

            if "parent" in it:
                parent = self.find_item(it["parent"])
                if parent:
                    new_x = self._snap(round(ox + dx))
                    new_y = self._snap(round(oy + dy))
                    it["x"] = max(0, min(new_x, parent["w"] - it["w"]))
                    it["y"] = max(0, min(new_y, parent["h"] - it["h"]))
                else:
                    it["x"] = max(0, self._snap(round(ox + dx)))
                    it["y"] = max(0, self._snap(round(oy + dy)))
            else:
                it["x"] = max(0, self._snap(round(ox + dx)))
                it["y"] = max(0, self._snap(round(oy + dy)))

            self._move_canvas_item(it)
            if "parent" not in it:
                for child in self.items:
                    if child.get("parent") == it["id"]:
                        self._move_canvas_item(child)

        self.update_panel()

    def _do_resize(self, event):
        if self._resize_start is None:
            return
        sx, sy, ox, oy, ow, oh, mode, item_id = self._resize_start
        it = self.find_item(item_id)
        if not it:
            return

        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        dx = self._unzoomed(cx - sx)
        dy = self._unzoomed(cy - sy)

        flags = HANDLE_DEFS[mode]
        x0, y0, x1, y1 = ox, oy, ox + ow, oy + oh
        new_x0, new_y0, new_x1, new_y1 = x0, y0, x1, y1

        if flags.get("right"):
            new_x1 = x1 + dx
        if flags.get("left"):
            new_x0 = x0 + dx
        if flags.get("bottom"):
            new_y1 = y1 + dy
        if flags.get("top"):
            new_y0 = y0 + dy

        if flags.get("left") or flags.get("right"):
            new_w = max(20, self._snap(round(new_x1 - new_x0)))
        else:
            new_w = ow
        if flags.get("top") or flags.get("bottom"):
            new_h = max(16, self._snap(round(new_y1 - new_y0)))
        else:
            new_h = oh

        new_x = x1 - new_w if flags.get("left") else x0
        new_y = y1 - new_h if flags.get("top") else y0

        if "parent" in it:
            # children only ever expose the "e" handle: width-only resize
            parent = self.find_item(it["parent"])
            if parent:
                new_w = min(new_w, parent["w"] - it["x"])
            new_x = it["x"]
            new_y = it["y"]
            new_h = oh

        it["x"] = max(0, round(new_x))
        it["y"] = max(0, round(new_y))
        it["w"] = new_w
        it["h"] = new_h

        self._move_canvas_item(it)
        self.update_panel()

    def _on_canvas_release(self, event):
        moved = bool(self._drag_origin) or self._resize_start is not None
        self._drag_start = None
        self._drag_origin = {}
        self._resize_start = None
        self._axis_lock = None
        if moved:
            self.push_history()


if __name__ == "__main__":
    app = LayoutEditor()
    app.mainloop()

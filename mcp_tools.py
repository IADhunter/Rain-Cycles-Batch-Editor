"""RCBE MCP tools — read-only + preview.

Pure functions used by mcp_server.py. They read the editor's `input/` folder
and never write anything. The transformation itself is delegated to
`core_logic.process_line_by_line`, so the MCP layer only adapts structured
rules to the existing engine.
"""

import difflib
import json
import os

import core_logic as core

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# RESOLUCIÓN DE RUTAS / FICHEROS
# ============================================================
def _input_dir(input_dir=None):
    d = input_dir or os.environ.get("RCBE_INPUT_DIR") or os.path.join(BASE_DIR, "input")
    return os.path.abspath(d)


def _txt_files(input_dir):
    if not os.path.isdir(input_dir):
        return []
    return sorted(
        f for f in os.listdir(input_dir)
        if f.lower().endswith(".txt") and os.path.isfile(os.path.join(input_dir, f))
    )


def _safe_path(input_dir, name):
    """Confina el nombre al directorio de entrada (sin traversal ni subrutas)."""
    base = os.path.basename(str(name))
    if base != str(name) or not base.lower().endswith(".txt"):
        raise ValueError(f"nombre de fichero no válido: {name!r}")
    path = os.path.join(input_dir, base)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"no existe en input/: {base}")
    return base, path


def _read_lines(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.readlines()


# ============================================================
# PARSEO RESUMIDO DE UN SETTING
# ============================================================
_PALETTE_KEYS = ("Palette", "TerrainPalette", "FadePalette", "TerrainFadePalette")


def _summarize(name, lines):
    template = None
    palettes = {}
    tags = None

    for line in lines:
        s = line.strip()
        if s.startswith("Template:"):
            template = s.split(":", 1)[1].strip()
        elif s.startswith("RainCycles:"):
            tags = core._parse_raincycles_tags(s)
        else:
            for key in _PALETTE_KEYS:
                if s.startswith(key + ":"):
                    value = s.split(":", 1)[1].strip()
                    # Las fade palettes llevan coma + opacidades; el id es lo 1º.
                    if key.startswith("Fade") or key.startswith("TerrainFade"):
                        value = value.split(",")[0].strip()
                    palettes[key] = value

    return {
        "file": name,
        "lines": len(lines),
        "template": template,
        "palette": palettes.get("Palette"),
        "terrain_palette": palettes.get("TerrainPalette"),
        "fade_palette": palettes.get("FadePalette"),
        "terrain_fade_palette": palettes.get("TerrainFadePalette"),
        "rain_cycles": tags,
        "has_vanilla_view": core._has_vanilla_view_effect(lines),
    }


def _raw_relevant_lines(lines):
    out = {}
    for line in lines:
        s = line.strip()
        if (s.startswith("RainCycles:") or s.startswith("Effects:")
                or s.startswith("Template:") or s.startswith("EffectColorA:")
                or s.startswith("EffectColorB:")):
            out.setdefault(s.split(":", 1)[0], []).append(s)
    return out


def _has_effect(input_lines, effect_name):
    """True si la línea Effects: contiene una entrada '<effect_name>-...'."""
    prefix = effect_name + "-"
    for line in input_lines:
        s = line.strip()
        if s.startswith("Effects:"):
            body = s[len("Effects:"):].strip()
            for entry in body.split(","):
                if entry.strip().startswith(prefix):
                    return True
    return False


# ============================================================
# ADAPTADOR rules -> process_line_by_line
# ============================================================
def build_core_args(rules):
    rules = rules or {}
    te = rules.get("terrain_effects") or {}
    rc = rules.get("rain_cycles") or {}
    tpl = rules.get("template") or {}
    eca = rules.get("effect_color_a") or {}
    ecb = rules.get("effect_color_b") or {}
    bkg = rules.get("bkg") or {}

    return [
        rules.get("palette") or {},
        rules.get("fade_palette") or {}, _num(rules.get("fade_opacity", 1.0)),
        rules.get("terrain_palette") or {},
        rules.get("terrain_fade_palette") or {}, _num(rules.get("terrain_fade_opacity", 1.0)),
        _num(rules.get("decal", 1.0)), _num(rules.get("light", 1.0)),
        _num(rules.get("grime", 1.0)), _num(rules.get("clouds", 1.0)),
        _num(te.get("light", 1.0)), _num(te.get("stain_amount", 1.0)),
        _num(te.get("stain_brightness", 1.0)), _num(te.get("stain_height", 1.0)),
        _num(te.get("waves", 1.0)), _num(te.get("grain", 1.0)),
        _num(te.get("sky_fade", 1.0)),
        bool(rc.get("enabled", False)), rc.get("type"), rc.get("view"), rc.get("tint"),
        tpl.get("replace") or {}, tpl.get("create"),
        bool(eca.get("enabled", False)), _num(eca.get("h", 1.0)), _num(eca.get("s", 1.0)),
        _num(eca.get("v", 1.0)), bool(eca.get("only", False)),
        bool(ecb.get("enabled", False)), _num(ecb.get("h", 1.0)), _num(ecb.get("s", 1.0)),
        _num(ecb.get("v", 1.0)), bool(ecb.get("only", False)),
        bool(bkg.get("enabled", False)), bkg.get("mod"), bkg.get("sky"),
        bkg.get("fog"), bkg.get("sun"), bool(bkg.get("only_view", False)),
        bkg.get("view"),
    ]


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 1.0


# ============================================================
# HERRAMIENTAS (solo lectura + preview)
# ============================================================
def list_settings(input_dir=None):
    d = _input_dir(input_dir)
    files = _txt_files(d)
    return {
        "input_dir": d,
        "count": len(files),
        "settings": [_summarize(name, _read_lines(os.path.join(d, name))) for name in files],
    }


def get_setting(file, input_dir=None):
    d = _input_dir(input_dir)
    name, path = _safe_path(d, file)
    lines = _read_lines(path)
    summary = _summarize(name, lines)
    summary["relevant_lines"] = _raw_relevant_lines(lines)
    return summary


def list_vanilla_views():
    return {
        "note": "Vanilla room effects that create a BackgroundScene 'view'. "
                "Mod ViewType: AboveCloudsView/PinkSky->ACV/PSV, RoofTopView->RTV, "
                "Outer/Inner Outer Rim View->ORV, Ancient Urban View->AUV. "
                "Downpour adds none. Watcher names contain spaces.",
        "effects": list(core.VIEW_EFFECTS),
    }


def rules_reference():
    return {
        "structure": {
            "palette": {"old_id": "new_id"},
            "fade_palette": {"old_id": "new_id"},
            "fade_opacity": 1.0,
            "terrain_palette": {"old_id": "new_id"},
            "terrain_fade_palette": {"old_id": "new_id"},
            "terrain_fade_opacity": 1.0,
            "decal": 1.0, "light": 1.0, "grime": 1.0, "clouds": 1.0,
            "terrain_effects": {"light": 1.0, "stain_amount": 1.0, "stain_brightness": 1.0,
                                "stain_height": 1.0, "waves": 1.0, "grain": 1.0, "sky_fade": 1.0},
            "rain_cycles": {"enabled": False, "type": "Blend", "view": "ACV", "tint": None},
            "template": {"replace": {"old": "new"}, "create": None},
            "effect_color_a": {"enabled": False, "h": 1.0, "s": 1.0, "v": 1.0, "only": False},
            "effect_color_b": {"enabled": False, "h": 1.0, "s": 1.0, "v": 1.0, "only": False},
            "bkg": {"enabled": False, "mod": "", "sky": "", "fog": "", "sun": "",
                "only_view": False, "view": ""},
        },
        "notes": [
            "Only keys you send are applied; omitted keys keep their defaults.",
            "bkg needs mod+sky; emits <Mod:mod,sky[,sun[,fog]]> inside RainCycles:.",
            "bkg.only_view (GUI: Only Effect View) restricts to settings whose Effects: has a vanilla view effect; "
        "bkg.view (full name or ACV/RTV/PSV/ORV/AUV, case-insensitive) narrows it to that specific effect; "
        "it only applies when bkg.only_view is true.",
            "rain_cycles.type=Vanilla removes the RainCycles line.",
            "rain_cycles is a partial update: omitted type/view/tint preserve the existing tag; "
            "use view=\"None\" or tint=\"\" to clear it.",
            "Multipliers use 1.0 = unchanged, 0.5 = 50%.",
        ],
    }


def preview_rules(rules, files=None, name_contains=None, input_dir=None, max_diff_chars=20000):
    d = _input_dir(input_dir)

    if files:
        targets = [_safe_path(d, f)[0] for f in files]
    else:
        targets = _txt_files(d)
        if name_contains:
            needle = str(name_contains).lower()
            targets = [f for f in targets if needle in f.lower()]

    args = build_core_args(rules)
    diffs = []
    changed = 0

    for name in targets:
        path = os.path.join(d, name)
        lines = _read_lines(path)
        result = core.process_line_by_line(lines, *args)

        # Comparación semántica: el motor normaliza espacios finales (p.ej. la
        # coma de "Effects: ... , ") incluso sin reglas; eso no es un cambio real.
        orig = [l.rstrip() for l in lines]
        new = [l.rstrip() for l in result]
        is_changed = orig != new
        if is_changed:
            changed += 1

        diff_text = "\n".join(difflib.unified_diff(orig, new, fromfile=name, tofile=name, lineterm=""))
        if len(diff_text) > max_diff_chars:
            diff_text = diff_text[:max_diff_chars] + f"\n... (truncado a {max_diff_chars} chars)"

        diffs.append({"file": name, "changed": is_changed, "diff": diff_text})

    return {
        "input_dir": d,
        "files_scanned": len(targets),
        "files_changed": changed,
        "files_unchanged": len(targets) - changed,
        "diffs": diffs,
    }


def generate(rules, files=None, name_contains=None, input_dir=None, output_dir=None):
    """Aplica las reglas y escribe los resultados en output/.

    Espeja el comportamiento de la GUI: lee input/*.txt con utf-8/errors=ignore
    y escribe en output/ con utf-8 (el newline por defecto preserva CRLF en
    Windows). Solo escribe dentro de output/; no toca input/.
    """
    src = _input_dir(input_dir)
    dst = output_dir or os.environ.get("RCBE_OUTPUT_DIR") or os.path.join(BASE_DIR, "output")
    dst = os.path.abspath(dst)
    os.makedirs(dst, exist_ok=True)

    if files:
        targets = [_safe_path(src, f)[0] for f in files]
    else:
        targets = _txt_files(src)
        if name_contains:
            needle = str(name_contains).lower()
            targets = [f for f in targets if needle in f.lower()]

    args = build_core_args(rules)
    records = []
    changed = 0

    for name in targets:
        lines = _read_lines(os.path.join(src, name))
        result = core.process_line_by_line(lines, *args)

        newline = core.detect_newline(os.path.join(src, name))
        core.write_setting_lines(os.path.join(dst, name), result, newline)

        is_changed = [l.rstrip() for l in lines] != [l.rstrip() for l in result]
        if is_changed:
            changed += 1
        records.append({
            "file": name,
            "changed": is_changed,
            "lines_in": len(lines),
            "lines_out": len(result),
        })

    return {
        "input_dir": src,
        "output_dir": dst,
        "files_written": len(targets),
        "files_changed": changed,
        "files_unchanged": len(targets) - changed,
        "files": records,
    }

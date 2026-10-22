import os


# Orden canónico de las líneas de settings según RoomSettings.Save() del juego.
# Solo incluye las líneas que el juego escribe. RainCycles (mod) siempre va al final.
SETTINGS_ORDER = [
    "Template",
    "DangerType",
    "CeilingDrips",
    "RainIntensity",
    "RumbleIntensity",
    "WaveSpeed",
    "WaveLength",
    "WaveAmplitude",
    "SecondWaveLength",
    "SecondWaveAmplitude",
    "Clouds",
    "Grime",
    "BkgDroneVolume",
    "BkgDroneNoThreatVolume",
    "RandomItemDensity",
    "RandomItemSpearChance",
    "WaterReflectionAlpha",
    "Palette",
    "EffectColorA",
    "EffectColorB",
    "TerrainLight",
    "TerrainStainAmount",
    "TerrainStainBrightness",
    "TerrainStainHeight",
    "TerrainWaves",
    "TerrainEdgeRadius",
    "TerrainGooHeight",
    "TerrainGrain",
    "TerrainDepth",
    "TerrainSkyFade",
    "TerrainPalette",
    "Effects",
    "PlacedObjects",
    "AmbientSounds",
    "Triggers",
    "FadePalette",
    "TerrainFadePalette",
    "RoomSpecificScriptActive",
    "WetTerrain",
]


# Efectos de sala vanilla que crean un "view" (BackgroundScene) en Rain World.
VIEW_EFFECTS = [
    "AboveCloudsView",
    "PinkSky",
    "RoofTopView",
    "Outer Rim View",
    "Inner Outer Rim View",
    "Ancient Urban View",
]

# Alias de la UI (View: ACV/RTV/PSV/ORV/AUV). ORV agrupa dos efectos vanilla.
VIEW_EFFECT_ALIASES = {
    "acv": ["AboveCloudsView"],
    "rtv": ["RoofTopView"],
    "psv": ["PinkSky"],
    "orv": ["Outer Rim View", "Inner Outer Rim View"],
    "auv": ["Ancient Urban View"],
}


def _resolve_view_effects(name):
    name = (name or "").strip()
    if not name:
        return list(VIEW_EFFECTS)
    key = name.lower()
    if key in VIEW_EFFECT_ALIASES:
        return list(VIEW_EFFECT_ALIASES[key])
    for effect in VIEW_EFFECTS:
        if key == effect.lower():
            return [effect]
    return []


def _get_line_setting_name(line):
    clean = line.strip()
    if ":" in clean:
        name = clean.split(":", 1)[0].strip()
        if name in SETTINGS_ORDER:
            return name
    return None


def _find_insert_position(new_lines, setting_name):
    if setting_name not in SETTINGS_ORDER:
        return len(new_lines)
    target_idx = SETTINGS_ORDER.index(setting_name)
    last_before = -1
    for i, line in enumerate(new_lines):
        name = _get_line_setting_name(line)
        if name is not None and name in SETTINGS_ORDER:
            idx = SETTINGS_ORDER.index(name)
            if idx < target_idx:
                last_before = i
    return last_before + 1


def _multiply_opacities(opacity_parts, factor):
    result = []
    for raw in opacity_parts:
        raw = raw.strip()
        try:
            val = float(raw)
            result.append(str(round(val * factor, 7)))
        except (ValueError, TypeError):
            result.append(raw)
    return result


def _multiply_effect_color(entry, h_mult, s_mult, v_mult):
    parts = entry.split("-", 2)
    if len(parts) < 3:
        return entry
    prefix = parts[0]  # ModifyEffectColorA o ModifyEffectColorB
    coords = parts[2]  # x-y

    hsv_str = parts[1]  # H,S,V
    hsv_vals = hsv_str.split(",")
    if len(hsv_vals) < 3:
        return entry

    try:
        h = float(hsv_vals[0])
        s = float(hsv_vals[1])
        v = float(hsv_vals[2])
    except (ValueError, TypeError):
        return entry

    h_new = round(h * h_mult, 7)
    s_new = round(s * s_mult, 7)
    v_new = round(v * v_mult, 7)

    return f"{prefix}-{h_new},{s_new},{v_new}-{coords}"


def _has_vanilla_view_effect(input_lines, only_effect=None):
    names = _resolve_view_effects(only_effect) if only_effect else VIEW_EFFECTS
    if not names:
        return False
    for line in input_lines:
        clean = line.strip()
        if not clean.startswith("Effects:"):
            continue
        entries = clean[len("Effects:"):].split(", ")
        for entry in entries:
            entry = entry.strip()
            for name in names:
                if entry == name or entry.startswith(name + "-"):
                    return True
        return False
    return False


def _parse_raincycles_tags(line):
    tags = {}
    content = line.strip()
    pos = 0
    while pos < len(content):
        start = content.find("<", pos)
        if start < 0:
            break
        end = content.find(">", start)
        if end < 0:
            break
        segment = content[start + 1:end]
        if ":" in segment:
            key, value = segment.split(":", 1)
            tags[key.strip()] = value.strip()
        pos = end + 1
    return tags


def _mod_before_tint(line):
    mod = line.find("<Mod:")
    if mod < 0:
        return False
    tint = line.find("<Tint:")
    return tint < 0 or mod < tint


def _build_bkg_tag(mod, sky, sun, fog):
    mod = (mod or "").strip()
    sky = (sky or "").strip()
    sun = (sun or "").strip()
    fog = (fog or "").strip()

    if not mod or not sky:
        return None

    parts = [mod, sky]
    if sun:
        parts.append(sun)
    elif fog:
        parts.append("")
    if fog:
        parts.append(fog)
    return ",".join(parts)


def _build_raincycles_line(rain_type, rain_view, rain_tint, bkg=None, mod_first=False):
    if not rain_type or rain_type == "Vanilla":
        return None

    parts = [f"<Type:{rain_type}>"]

    if rain_view and rain_view != "None":
        parts.append(f"<View:{rain_view}>")
        if mod_first:
            if bkg:
                parts.append(f"<Mod:{bkg}>")
            if rain_tint:
                parts.append(f"<Tint:{rain_tint}>")
        else:
            if rain_tint:
                parts.append(f"<Tint:{rain_tint}>")
            if bkg:
                parts.append(f"<Mod:{bkg}>")

    return "RainCycles: " + "".join(parts) + "\n"


def detect_newline(path):
    """Devuelve el estilo de salto de línea original del fichero."""
    with open(path, "rb") as f:
        raw = f.read()
    if b"\r\n" in raw:
        return "\r\n"
    if b"\r" in raw:
        return "\r"
    return "\n"


def write_setting_lines(path, lines, newline):

    text = "".join(lines)
    if newline != "\n":
        text = text.replace("\n", newline)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def process_line_by_line(
    input_lines,
    # --- Main Palette (SOLO reemplazo, nunca se crea desde cero) ---
    rules_main,             # Dict: {old_palette: new_palette}

    # --- Fade Palette (SOLO reemplazo, nunca se crea desde cero) ---
    rules_fade,             # Dict: {old_fade: new_fade}
    fade_b_opacity,         # Float/Str: multiplicador de opacidad

    # --- Terrain Palette (SOLO reemplazo, nunca se crea desde cero) ---
    rules_terrain_main,     # Dict: {old_terrain_palette: new_terrain_palette}

    # --- Terrain Fade Palette (SOLO reemplazo, nunca se crea desde cero) ---
    rules_terrain_fade,     # Dict: {old_terrain_fade: new_terrain_fade}
    terrain_fade_b_opacity, # Float/Str: multiplicador de opacidad

    # --- Room Control: Ambient multipliers ---
    decal_mult,             # Float
    light_mult,             # Float
    grime_mult,             # Float
    clouds_mult,            # Float

    # --- Room Control: Terrain Effects multipliers ---
    terrain_light_mult=1.0,             # Float -> TerrainLight
    terrain_stain_amount_mult=1.0,      # Float -> TerrainStainAmount
    terrain_stain_brightness_mult=1.0,  # Float -> TerrainStainBrightness
    terrain_stain_height_mult=1.0,      # Float -> TerrainStainHeight
    terrain_waves_mult=1.0,             # Float -> TerrainWaves
    terrain_grain_mult=1.0,             # Float -> TerrainGrain
    terrain_sky_fade_mult=1.0,          # Float -> TerrainSkyFade

    # --- Room Control: Rain Cycles ---
    rain_enabled=False,     # Bool: switch principal
    rain_type=None,         # Str: Blend / Static / Vanilla
    rain_view=None,         # Str: ACV / RTV / PSV / ORV / AUV / None
    rain_tint=None,         # Str: "#FFFFFF #131920" (o solo uno de los dos)

    # --- Template (reemplaza el valor existente) ---
    rules_template=None,    # Dict: {old_template: new_template}
    template_create=None,   # Str: valor para crear Template si no existe

    # --- Modify Effect Color A ---
    modify_effect_a_enabled=False,   # Bool: switch principal
    effect_a_h_mult=1.0,             # Float: multiplicador H
    effect_a_s_mult=1.0,             # Float: multiplicador S
    effect_a_v_mult=1.0,             # Float: multiplicador V
    only_effect_a=False,             # Bool: solo si EffectColorA existe

    # --- Modify Effect Color B ---
    modify_effect_b_enabled=False,   # Bool: switch principal
    effect_b_h_mult=1.0,             # Float: multiplicador H
    effect_b_s_mult=1.0,             # Float: multiplicador S
    effect_b_v_mult=1.0,             # Float: multiplicador V
    only_effect_b=False,             # Bool: solo si EffectColorB existe

    # --- Bkg / Images (tag <Mod:mod,sky[,sun,fog]> dentro de RainCycles:) ---
    bkg_enabled=False,               # Bool: activo si hay mod+sky
    bkg_mod=None,                    # Str: id/nombre del mod
    bkg_sky=None,                    # Str
    bkg_fog=None,                    # Str
    bkg_sun=None,                    # Str
    bkg_only_view=False,             # Bool: solo en settings con view vanilla
    bkg_view=None                    # Str: efecto vanilla concreto (nombre o alias)
):
    new_lines = []
    found_palette = False
    found_fade = False
    found_terrain_palette = False
    found_terrain_fade = False
    found_rain = False
    found_template = False
    found_effects = False
    found_effect_color_a = False
    found_effect_color_b = False

    try:
        f_b_op_factor = float(fade_b_opacity)
    except (TypeError, ValueError):
        f_b_op_factor = 1.0

    try:
        t_fb_op_factor = float(terrain_fade_b_opacity)
    except (TypeError, ValueError):
        t_fb_op_factor = 1.0

    bkg_tag = _build_bkg_tag(bkg_mod, bkg_sky, bkg_sun, bkg_fog) if bkg_enabled else None
    effect_filter = bkg_view if bkg_only_view else None
    apply_bkg = bkg_tag is not None and (
        not bkg_only_view or _has_vanilla_view_effect(input_lines, effect_filter))

    for line in input_lines:
        clean_line = line.strip()
        skip_line = False

        # --- MODULE: TEMPLATE (reemplaza el valor existente) ---
        if clean_line.startswith("Template:"):
            found_template = True
            if rules_template:
                val = clean_line.split(":", 1)[1].strip()
                if val in rules_template:
                    line = f"Template: {rules_template[val]}\n"

        # --- MODULE: MAIN PALETTE ---
        elif clean_line.startswith("Palette:"):
            found_palette = True
            val = clean_line.split(":", 1)[1].strip()
            if val in rules_main:
                line = f"Palette: {rules_main[val]}\n"

        # --- MODULE: TERRAIN PALETTE (solo reemplazo) ---
        elif clean_line.startswith("TerrainPalette:"):
            found_terrain_palette = True
            val = clean_line.split(":", 1)[1].strip()
            if val in rules_terrain_main:
                line = f"TerrainPalette: {rules_terrain_main[val]}\n"

        # --- MODULE: FADE PALETTE (solo reemplazo, multiplica TODAS las opacidades) ---
        elif clean_line.startswith("FadePalette:"):
            found_fade = True
            body = clean_line.split(":", 1)[1].strip()
            parts = body.split(",")
            orig_id = parts[0].strip()
            opac_parts = parts[1:]

            if orig_id in rules_fade and (rules_fade[orig_id] != orig_id or f_b_op_factor != 1.0):
                new_id = rules_fade[orig_id]
                new_opac = _multiply_opacities(opac_parts, f_b_op_factor)
                line = f"FadePalette: {new_id}, {', '.join(new_opac)}\n"
            elif f_b_op_factor != 1.0:
                new_opac = _multiply_opacities(opac_parts, f_b_op_factor)
                line = f"FadePalette: {orig_id}, {', '.join(new_opac)}\n"

        # --- MODULE: TERRAIN FADE PALETTE (solo reemplazo, multiplica TODAS las opacidades) ---
        elif clean_line.startswith("TerrainFadePalette:"):
            found_terrain_fade = True
            body = clean_line.split(":", 1)[1].strip()
            parts = body.split(",")
            orig_id = parts[0].strip()
            opac_parts = parts[1:]

            if orig_id in rules_terrain_fade and (rules_terrain_fade[orig_id] != orig_id or t_fb_op_factor != 1.0):
                new_id = rules_terrain_fade[orig_id]
                new_opac = _multiply_opacities(opac_parts, t_fb_op_factor)
                line = f"TerrainFadePalette: {new_id}, {', '.join(new_opac)}\n"
            elif t_fb_op_factor != 1.0:
                new_opac = _multiply_opacities(opac_parts, t_fb_op_factor)
                line = f"TerrainFadePalette: {orig_id}, {', '.join(new_opac)}\n"

        # --- MODULE: GRIME & CLOUDS ---
        elif clean_line.startswith("Grime:"):
            if grime_mult != 1.0:
                try:
                    val = float(clean_line.split(":", 1)[1].strip())
                    line = f"Grime: {round(val * grime_mult, 7)}\n"
                except (ValueError, IndexError):
                    pass

        elif clean_line.startswith("Clouds:"):
            if clouds_mult != 1.0:
                try:
                    val = float(clean_line.split(":", 1)[1].strip())
                    line = f"Clouds: {round(val * clouds_mult, 7)}\n"
                except (ValueError, IndexError):
                    pass

        # --- MODULE: TERRAIN EFFECTS (multiplicadores escalares) ---
        elif clean_line.startswith("TerrainLight:"):
            if terrain_light_mult != 1.0:
                try:
                    val = float(clean_line.split(":", 1)[1].strip())
                    line = f"TerrainLight: {round(val * terrain_light_mult, 7)}\n"
                except (ValueError, IndexError):
                    pass

        elif clean_line.startswith("TerrainStainAmount:"):
            if terrain_stain_amount_mult != 1.0:
                try:
                    val = float(clean_line.split(":", 1)[1].strip())
                    line = f"TerrainStainAmount: {round(val * terrain_stain_amount_mult, 7)}\n"
                except (ValueError, IndexError):
                    pass

        elif clean_line.startswith("TerrainStainBrightness:"):
            if terrain_stain_brightness_mult != 1.0:
                try:
                    val = float(clean_line.split(":", 1)[1].strip())
                    line = f"TerrainStainBrightness: {round(val * terrain_stain_brightness_mult, 7)}\n"
                except (ValueError, IndexError):
                    pass

        elif clean_line.startswith("TerrainStainHeight:"):
            if terrain_stain_height_mult != 1.0:
                try:
                    val = float(clean_line.split(":", 1)[1].strip())
                    line = f"TerrainStainHeight: {round(val * terrain_stain_height_mult, 7)}\n"
                except (ValueError, IndexError):
                    pass

        elif clean_line.startswith("TerrainWaves:"):
            if terrain_waves_mult != 1.0:
                try:
                    val = float(clean_line.split(":", 1)[1].strip())
                    line = f"TerrainWaves: {round(val * terrain_waves_mult, 7)}\n"
                except (ValueError, IndexError):
                    pass

        elif clean_line.startswith("TerrainGrain:"):
            if terrain_grain_mult != 1.0:
                try:
                    val = float(clean_line.split(":", 1)[1].strip())
                    line = f"TerrainGrain: {round(val * terrain_grain_mult, 7)}\n"
                except (ValueError, IndexError):
                    pass

        elif clean_line.startswith("TerrainSkyFade:"):
            if terrain_sky_fade_mult != 1.0:
                try:
                    val = float(clean_line.split(":", 1)[1].strip())
                    line = f"TerrainSkyFade: {round(val * terrain_sky_fade_mult, 7)}\n"
                except (ValueError, IndexError):
                    pass

        # --- MODULE: RAIN CYCLES (+ BKG) ---
        elif clean_line.startswith("RainCycles:"):
            found_rain = True
            tags = _parse_raincycles_tags(clean_line)

            if rain_enabled:
                new_type = rain_type if rain_type is not None else tags.get("Type")
                new_view = rain_view if rain_view is not None else tags.get("View")
                new_tint = rain_tint if rain_tint is not None else tags.get("Tint")
            else:
                new_type = tags.get("Type")
                new_view = tags.get("View")
                new_tint = tags.get("Tint")

            # El bkg existente se conserva salvo que el módulo lo sobreescriba.
            new_bkg = tags.get("Mod")
            if apply_bkg:
                new_bkg = bkg_tag

            if rain_enabled or (apply_bkg and new_type and new_view):
                new_line = _build_raincycles_line(new_type, new_view, new_tint, new_bkg,
                                                  _mod_before_tint(clean_line))
                if new_line is None:
                    skip_line = True
                elif new_line != line:
                    line = new_line
            # Si no, la línea original queda intacta.

        # --- MODULE: EFFECT COLOR A/B (detectar existencia) ---
        elif clean_line.startswith("EffectColorA:"):
            found_effect_color_a = True
        elif clean_line.startswith("EffectColorB:"):
            found_effect_color_b = True

        # --- MODULE: EFFECTS (ModifyEffectColor A/B) ---
        elif clean_line.startswith("Effects:"):
            found_effects = True
            effects_header = "Effects: "
            body = clean_line.replace(effects_header, "").strip().rstrip(",")
            entries = [e.strip() for e in body.split(", ") if e.strip()]

            # Buscar entradas existentes
            entry_a = None
            entry_b = None
            other_entries = []
            for entry in entries:
                if entry.startswith("ModifyEffectColorA-"):
                    entry_a = entry
                elif entry.startswith("ModifyEffectColorB-"):
                    entry_b = entry
                else:
                    other_entries.append(entry)

            # Procesar Effect Color A
            if modify_effect_a_enabled:
                create_a = not only_effect_a or found_effect_color_a
                if create_a:
                    if entry_a:
                        # Ya existe → multiplicar valores
                        entry_a = _multiply_effect_color(entry_a, effect_a_h_mult, effect_a_s_mult, effect_a_v_mult)
                    else:
                        # No existe → crear con defaults y multiplicar
                        h = round(0 * effect_a_h_mult, 7)
                        s = round(0.5 * effect_a_s_mult, 7)
                        v = round(0.5 * effect_a_v_mult, 7)
                        entry_a = f"ModifyEffectColorA-{h},{s},{v}-30-30"

            # Procesar Effect Color B
            if modify_effect_b_enabled:
                create_b = not only_effect_b or found_effect_color_b
                if create_b:
                    if entry_b:
                        # Ya existe → multiplicar valores
                        entry_b = _multiply_effect_color(entry_b, effect_b_h_mult, effect_b_s_mult, effect_b_v_mult)
                    else:
                        # No existe → crear con defaults y multiplicar
                        h = round(0 * effect_b_h_mult, 7)
                        s = round(0.5 * effect_b_s_mult, 7)
                        v = round(0.5 * effect_b_v_mult, 7)
                        entry_b = f"ModifyEffectColorB-{h},{s},{v}-40-40"

            if modify_effect_a_enabled or modify_effect_b_enabled:
                final_entries = other_entries[:]
                if entry_a:
                    final_entries.append(entry_a)
                if entry_b:
                    final_entries.append(entry_b)

                if final_entries:
                    rebuilt = effects_header + ", ".join(final_entries) + ",\n"
                else:
                    rebuilt = "Effects: \n"
                if rebuilt != line:
                    line = rebuilt

        # --- MODULE: PLACED OBJECTS (Decals & Lights) ---
        elif clean_line.startswith("PlacedObjects:"):
            if decal_mult != 1.0 or light_mult != 1.0:
                header_prefix = "PlacedObjects: "
                content = clean_line.replace(header_prefix, "")
                had_trailing_comma = content.rstrip().endswith(",")
                objects = content.split(",")
                processed_objects = []
                modified = False

                for obj in objects:
                    if not obj.strip():
                        continue

                    # Sub-Module: CustomDecals
                    if "CustomDecal" in obj and decal_mult != 1.0:
                        d_parts = obj.split("~")
                        if len(d_parts) > 19:
                            for i in [12, 14, 16, 18]:
                                try:
                                    d_parts[i] = str(round(float(d_parts[i]) * decal_mult, 7))
                                    modified = True
                                except (ValueError, IndexError):
                                    pass
                            obj = "~".join(d_parts)

                    # Sub-Module: LightSources
                    elif "LightSource" in obj and light_mult != 1.0:
                        l_parts = obj.split("~")
                        try:
                            header = l_parts[0].split("><")
                            header[-1] = str(round(float(header[-1]) * light_mult, 7))
                            l_parts[0] = "><".join(header)
                            obj = "~".join(l_parts)
                            modified = True
                        except (ValueError, IndexError):
                            pass

                    processed_objects.append(obj)

                if modified:
                    line = header_prefix + ",".join(processed_objects)
                    if had_trailing_comma:
                        line += ","
                    line += "\n"

        if not skip_line:
            new_lines.append(line)

    # Eliminar líneas vacías al final
    while new_lines and not new_lines[-1].strip():
        new_lines.pop()

    if not found_rain and rain_enabled:
        new_line = _build_raincycles_line(rain_type, rain_view, rain_tint,
                                          bkg_tag if apply_bkg else None)
        if new_line is not None:
            if new_lines and not new_lines[-1].endswith('\n'):
                new_lines[-1] += '\n'
            new_lines.append(new_line)

    if not found_effects:
        entries_to_create = []
        if modify_effect_a_enabled:
            create_a = not only_effect_a or found_effect_color_a
            if create_a:
                h = round(0 * effect_a_h_mult, 7)
                s = round(0.5 * effect_a_s_mult, 7)
                v = round(0.5 * effect_a_v_mult, 7)
                entries_to_create.append(f"ModifyEffectColorA-{h},{s},{v}-30-30")
        if modify_effect_b_enabled:
            create_b = not only_effect_b or found_effect_color_b
            if create_b:
                h = round(0 * effect_b_h_mult, 7)
                s = round(0.5 * effect_b_s_mult, 7)
                v = round(0.5 * effect_b_v_mult, 7)
                entries_to_create.append(f"ModifyEffectColorB-{h},{s},{v}-40-40")
        if entries_to_create:
            if new_lines and not new_lines[-1].endswith('\n'):
                new_lines[-1] += '\n'
            effects_line = "Effects: " + ", ".join(entries_to_create) + ",\n"
            pos = _find_insert_position(new_lines, "Effects")
            new_lines.insert(pos, effects_line)

    if not found_template and template_create:
        new_lines.insert(0, f"Template: {template_create}\n")

    for i, line in enumerate(new_lines):
        stripped = line.strip()
        if stripped.startswith("Effects:") and stripped[len("Effects:"):].strip() and not stripped.endswith(","):
            new_lines[i] = line.rstrip("\n").rstrip() + ",\n"

    return new_lines

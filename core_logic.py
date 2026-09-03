import os


def _multiply_opacities(opacity_parts, factor):
    """Multiplica cada valor de opacidad de una lista por un factor, preservando
    los valores que no se puedan convertir a float tal como vinieron."""
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
    """Multiplica los valores HSV de una entrada ModifyEffectColor.
    Formato: ModifyEffectColorX-H,S,V-x-y
    Devuelve la entrada con los valores multiplicados."""
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


def _build_raincycles_line(rain_type, rain_view, rain_tint):
    """Construye la línea RainCycles según Type/View/Tint.
    Devuelve None si la línea debe eliminarse (Vanilla o sin type)."""
    if not rain_type or rain_type == "Vanilla":
        return None

    parts = [f"<Type:{rain_type}>"]

    if rain_view and rain_view != "None":
        parts.append(f"<View:{rain_view}>")
        if rain_tint:
            parts.append(f"<Tint:{rain_tint}>")

    return "RainCycles:" + "".join(parts) + "\n"


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
    only_effect_b=False              # Bool: solo si EffectColorB existe
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

            if orig_id in rules_fade:
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

            if orig_id in rules_terrain_fade:
                new_id = rules_terrain_fade[orig_id]
                new_opac = _multiply_opacities(opac_parts, t_fb_op_factor)
                line = f"TerrainFadePalette: {new_id}, {', '.join(new_opac)}\n"
            elif t_fb_op_factor != 1.0:
                new_opac = _multiply_opacities(opac_parts, t_fb_op_factor)
                line = f"TerrainFadePalette: {orig_id}, {', '.join(new_opac)}\n"

        # --- MODULE: GRIME & CLOUDS ---
        elif clean_line.startswith("Grime:"):
            try:
                val = float(clean_line.split(":", 1)[1].strip())
                line = f"Grime: {round(val * grime_mult, 7)}\n"
            except (ValueError, IndexError):
                pass

        elif clean_line.startswith("Clouds:"):
            try:
                val = float(clean_line.split(":", 1)[1].strip())
                line = f"Clouds: {round(val * clouds_mult, 7)}\n"
            except (ValueError, IndexError):
                pass

        # --- MODULE: TERRAIN EFFECTS (multiplicadores escalares) ---
        elif clean_line.startswith("TerrainLight:"):
            try:
                val = float(clean_line.split(":", 1)[1].strip())
                line = f"TerrainLight: {round(val * terrain_light_mult, 7)}\n"
            except (ValueError, IndexError):
                pass

        elif clean_line.startswith("TerrainStainAmount:"):
            try:
                val = float(clean_line.split(":", 1)[1].strip())
                line = f"TerrainStainAmount: {round(val * terrain_stain_amount_mult, 7)}\n"
            except (ValueError, IndexError):
                pass

        elif clean_line.startswith("TerrainStainBrightness:"):
            try:
                val = float(clean_line.split(":", 1)[1].strip())
                line = f"TerrainStainBrightness: {round(val * terrain_stain_brightness_mult, 7)}\n"
            except (ValueError, IndexError):
                pass

        elif clean_line.startswith("TerrainStainHeight:"):
            try:
                val = float(clean_line.split(":", 1)[1].strip())
                line = f"TerrainStainHeight: {round(val * terrain_stain_height_mult, 7)}\n"
            except (ValueError, IndexError):
                pass

        elif clean_line.startswith("TerrainWaves:"):
            try:
                val = float(clean_line.split(":", 1)[1].strip())
                line = f"TerrainWaves: {round(val * terrain_waves_mult, 7)}\n"
            except (ValueError, IndexError):
                pass

        elif clean_line.startswith("TerrainGrain:"):
            try:
                val = float(clean_line.split(":", 1)[1].strip())
                line = f"TerrainGrain: {round(val * terrain_grain_mult, 7)}\n"
            except (ValueError, IndexError):
                pass

        elif clean_line.startswith("TerrainSkyFade:"):
            try:
                val = float(clean_line.split(":", 1)[1].strip())
                line = f"TerrainSkyFade: {round(val * terrain_sky_fade_mult, 7)}\n"
            except (ValueError, IndexError):
                pass

        # --- MODULE: RAIN CYCLES ---
        elif clean_line.startswith("RainCycles:"):
            found_rain = True
            if rain_enabled:
                new_line = _build_raincycles_line(rain_type, rain_view, rain_tint)
                if new_line is None:
                    skip_line = True
                else:
                    line = new_line
            # Si el switch está apagado, la línea original queda intacta.

        # --- MODULE: EFFECT COLOR A/B (detectar existencia) ---
        elif clean_line.startswith("EffectColorA:"):
            found_effect_color_a = True
        elif clean_line.startswith("EffectColorB:"):
            found_effect_color_b = True

        # --- MODULE: EFFECTS (ModifyEffectColor A/B) ---
        elif clean_line.startswith("Effects:"):
            found_effects = True
            effects_header = "Effects: "
            body = clean_line.replace(effects_header, "").strip()
            entries = [e.strip() for e in body.split(",") if e.strip()]

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

            # Reconstruir línea Effects
            final_entries = other_entries[:]
            if entry_a:
                final_entries.append(entry_a)
            if entry_b:
                final_entries.append(entry_b)

            if final_entries:
                line = effects_header + ", ".join(final_entries) + ",\n"
            else:
                line = "Effects: \n"

        # --- MODULE: PLACED OBJECTS (Decals & Lights) ---
        elif clean_line.startswith("PlacedObjects:"):
            header_prefix = "PlacedObjects: "
            content = clean_line.replace(header_prefix, "")
            objects = content.split(",")
            processed_objects = []

            for obj in objects:
                if not obj.strip():
                    continue

                # Sub-Module: CustomDecals
                if "CustomDecal" in obj:
                    d_parts = obj.split("~")
                    if len(d_parts) > 19:
                        for i in [12, 14, 16, 18]:
                            try:
                                d_parts[i] = str(round(float(d_parts[i]) * decal_mult, 7))
                            except (ValueError, IndexError):
                                pass
                        obj = "~".join(d_parts)

                # Sub-Module: LightSources
                elif "LightSource" in obj:
                    l_parts = obj.split("~")
                    try:
                        header = l_parts[0].split("><")
                        header[-1] = str(round(float(header[-1]) * light_mult, 7))
                        l_parts[0] = "><".join(header)
                        obj = "~".join(l_parts)
                    except (ValueError, IndexError):
                        pass

                processed_objects.append(obj)
            line = header_prefix + ",".join(processed_objects) + "\n"

        if not skip_line:
            new_lines.append(line)

    # Eliminar líneas vacías al final
    while new_lines and not new_lines[-1].strip():
        new_lines.pop()

    # --- AÑADIR PARÁMETROS FALTANTES AL FINAL ---
    # NOTA: de forma definitiva, ningún parámetro se crea desde cero.
    # Palette, FadePalette, TerrainPalette y TerrainFadePalette solo se
    # editan/reemplazan si ya existen en el setting original.

    # RainCycles (si está habilitado, tiene Type y no existía en el original)
    if not found_rain and rain_enabled:
        new_line = _build_raincycles_line(rain_type, rain_view, rain_tint)
        if new_line is not None:
            if new_lines and not new_lines[-1].endswith('\n'):
                new_lines[-1] += '\n'
            new_lines.append(new_line)

    # Effects (si no existía la línea pero necesitamos crear ModifyEffectColor)
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
            new_lines.append("Effects: " + ", ".join(entries_to_create) + ",\n")

    # Template (si template_create está definido y no existía en el original)
    if not found_template and template_create:
        new_lines.insert(0, f"Template: {template_create}\n")

    return new_lines

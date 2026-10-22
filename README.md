# Rain-Cycles-Batch-Editor

![Interface Preview](https://github.com/IADhunter/Rain-Cycles-Batch-Editor/blob/main/Screenshot.png)

**RCBE** is a tool designed for the batch editing of Rain World room configuration files (`settings.txt`).

Its main purpose is to facilitate the integration of regions into the [Rain Cycles](https://github.com/IADhunter/Rain-Cycles) mod, providing an easy way to create multiple dynamic states across several settings at once. It is the successor to [Rain-World-State-Batch-Editor](https://github.com/IADhunter/Rain-World-State-Batch-Editor), significantly improving and expanding its capabilities.

The goal is to edit files in batches while respecting the logic and artistic intent of each room. The tool **only replaces existing parameters**; it does not create new parameters from scratch (except for RainCycles and ModifyEffectColor, which can be added if they do not exist).

## Features

### Palettes

* **Main Palette:** Changes all palettes declared in a list to another (Example: Palette 0 to 14). It will search all settings for those with `Palette: 0` and change them to `14`. You can add as many options as you need.
* **Fade Palette:** Works the same as Main Palette for fade palettes, with an additional opacity multiplier that affects all opacity values of the palette.

### Terrain

* **Terrain Palette:** Replaces specific terrain palettes.
* **Terrain Fade Palette:** Replaces specific terrain fade palettes with opacity multiplier.

### Multiplicative Effects

This section uses a **decimal percentage system** (where `1` is the normal value, `0.5` is 50%, etc.).

* **Decals:** Decals in Rain World have **4 separate opacity modules**. RCBE recognizes this and **multiplies each of the 4 modules individually** by the declared percentage.
  - *Example:* If you apply `0.5` (50%), a decal with opacities `[1, 0.8, 0.4, 0]` will become `[0.5, 0.4, 0.2, 0]`. This ensures that the original depth and artistic decision are maintained, without leveling all values to the same point.

* **Light Sources:** Light sources have a single intensity setting. The tool scales this value to dim or enhance the global lighting of the room.
* **Grime and Clouds:** Intensity control for environmental grime and clouds. Allows for massive adjustment of these values so the atmosphere matches the new state (e.g., darker clouds for night states).

* **Terrain Effects:** Intensity control for the following terrain effects:
  - TerrainLight
  - TerrainStainAmount
  - TerrainStainBrightness
  - TerrainStainHeight
  - TerrainWaves
  - TerrainGrain
  - TerrainSkyFade

### Rain Cycles

* Full control of the `RainCycles:` line with options for:
  - **Type:** Blend, Static, Vanilla (Vanilla removes the line), Keep (preserve the existing type)
  - **View:** ACV, RTV, PSV, ORV, AUV, None, Keep (preserve the existing view)
  - **Tint:** Two separate fields for hexadecimal colors (e.g. #FFFFFF #131920). **Empty = keep** the existing tint; check **Clear** to remove it.
* These controls are disabled until **Enable RainCycles** is on; the switch is the master gate for the whole line.
* If the line does not exist and the switch is enabled, it is automatically created at the end of the file (when Type is not Keep).
* Line format: `RainCycles: <Type:Blend><View:ACV><Tint:#FFFFFF #131920><Mod:mod,sky>`. When rewriting, the relative order of `<Mod>` and `<Tint>` is preserved.
* Via MCP, `rain_cycles` is a **partial update**: omitted `type`/`view`/`tint` preserve the existing tag; use `view: "None"` or `tint: ""` to clear it. So "change Static to Blend" keeps the original view and tint.

### Background image (Bkg)

* Batch-writes the `Bkg` tag of the `RainCycles:` line: `<Mod:mod,sky[,sun[,fog]]>`, which sets the background illustration per room/state.
* The image tag uses four text fields: **Mod** (mod id / `modinfo.json` name), **Sky**, **Fog** and **Sun** (PNG filenames inside `<mod>/Illustrations/`, without extension). The tag is only applied when **Mod** and **Sky** are both filled; **Sun**/**Fog** are optional (and only meaningful on the `PSV` view).
* **Only Effect View:** when enabled, the tag is written only to settings whose `Effects:` line contains a vanilla view effect: `AboveCloudsView`, `PinkSky`, `RoofTopView`, `Outer Rim View`, `Inner Outer Rim View`, `Ancient Urban View`. It can only be enabled while **Enable RainCycles** is on, and it is turned off automatically when RainCycles is disabled.
* **Effect:** field next to **Only Effect View**, default `AboveCloudsView`. Clear it to accept any of the six; otherwise only settings with that specific effect qualify. Accepts the full name or the alias (`ACV`, `RTV`, `PSV`, `ORV`, `AUV`; `ORV` covers both Outer Rim views), case-insensitive. The field is disabled while **Only Effect View** is off; an unrecognized name is rejected with an error.
* The tag is inserted/updated inside the existing `RainCycles:` line without altering `Type`, `View` or `Tint`; a pre-existing `Bkg` tag is preserved unless the fields above override it.

### Template

* Batch replacement of the `Template:` field. Add rows with the old value and the new value to replace it across all files.
* If the line does not exist and a new value is provided, it is automatically created at the beginning of the file.

### Modify Effect Color A / B

* Multipliers for the HSV (Hue, Saturation, Value) values of `ModifyEffectColorA` and `ModifyEffectColorB` entries inside the `Effects:` line.
* Each section has:
  - **Enable:** Master switch to activate the section.
  - **H / S / V:** Multipliers (where `1` is no change, `0.5` is 50%, etc.).
  - **Only Effect A/B:** When enabled, only creates the entry if the corresponding `EffectColorA:` or `EffectColorB:` line exists in the settings file.
* If the entry already exists, the multipliers are applied to the current values.
* If the entry does not exist, it is created at the end of the `Effects:` line with default values (`H:0, S:0.5, V:0.5`) and then multiplied.

## Usage Instructions

1. Place the original `settings.txt` files in the **input** folder.
2. Run the tool and configure the changes in the interface.
3. The edited files will appear in the **output** folder.

*The tool is non-destructive; your files in the input folder will always remain intact. However, it is always recommended to have a backup in case something goes wrong.*

*Only the lines targeted by active rules are rewritten. Every other line is preserved byte-for-byte, including numeric precision, trailing commas, trailing whitespace and the original line endings (CRLF/LF) (a multiplier of `1.0` is a true no-op). The only deliberate normalization is the required trailing comma on the `Effects:` line: if it is missing, it is added.*

## MCP server (AI agents)

`mcp_server.py` exposes the editor as an **MCP server** (stdio, JSON-RPC 2.0, **no dependencies** — stdlib only, works with any Python 3.8+). Inspection and preview are read-only; writing to `output/` requires the explicit `generate` tool.

**Tools:**

| Tool | Purpose |
|---|---|
| `list_settings` | List every `.txt` in `input/` with a summary (template, palettes, `RainCycles` tags, has vanilla view effect). |
| `get_setting` | Full summary + relevant raw lines (`RainCycles`, `Effects`, `Template`, `EffectColorA/B`). |
| `preview_rules` | Apply rules in-memory and return unified diffs per file **without writing**. Supports `files` and `name_contains` filters. |
| `generate` | Apply rules and **write** the results to `output/` (same behaviour as the GUI). Never modifies `input/`. |
| `list_vanilla_views` | The six vanilla view effects used by `Only Effect View` / `bkg.view`. |
| `rules_reference` | Rules object structure, defaults and notes. |

The rules object mirrors the GUI sections (`palette`, `fade_palette`, `terrain_palette`, multiplicative effects, `rain_cycles`, `template`, `effect_color_a/b`, `bkg`). Omitted keys keep their defaults. Diffs compare semantically (trailing whitespace ignored). In `bkg`, `only_view` (GUI: **Only Effect View**) requires a vanilla view effect and `view` narrows it to one effect (full name or `ACV`/`RTV`/`PSV`/`ORV`/`AUV`, case-insensitive; empty = any; the GUI default is `AboveCloudsView`). `view` only has effect when `only_view` is true.

**Client config (Claude Desktop / Cursor / opencode):**

```json
{
  "mcpServers": {
    "rcbe": {
      "command": "python",
      "args": ["D:\\Documentos\\Rain Cycles Mod\\Rain-Cycles-Batch-Editor\\mcp_server.py"]
    }
  }
}
```

The server reads `<editor>/input` by default; override with the `RCBE_INPUT_DIR` env var or the `input_dir` argument. File arguments are confined to that folder (no path traversal). `preview_rules` never writes; `generate` writes only inside `output/` (override with `RCBE_OUTPUT_DIR` or `output_dir`).

## Compilation (For Developers)

If you wish to generate the executable from the source code, make sure you have the dependencies installed (`customtkinter`, `Pillow`) and use the following command:

```bash
python -m PyInstaller --noconfirm --onefile --windowed --add-data "background.jpg;." --add-data "icon.ico;." --icon "icon.ico" main.py

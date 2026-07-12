# Rain-Cycles-Batch-Editor

![Interface Preview](https://github.com/IADhunter/Rain-Cycles-Batch-Editor/blob/main/Screenshot.png)

**RCBE** is a tool designed for the batch editing of Rain World room configuration files (`settings.txt`).

Its main purpose is to facilitate the integration of regions into the [Rain Cycles](https://github.com/IADhunter/Rain-Cycles) mod, providing an easy way to create multiple dynamic states across several settings at once. It is the successor to [Rain-World-State-Batch-Editor](https://github.com/IADhunter/Rain-World-State-Batch-Editor), significantly improving and expanding its capabilities.

The goal is to edit files in batches while respecting the logic and artistic intent of each room. The tool **only replaces existing parameters**; it does not create new parameters from scratch (except for RainCycles, which can be added if it does not exist).

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
  - **Type:** Blend, Static, Vanilla (Vanilla removes the line)
  - **View:** ACV, RTV, PSV, ORV, AUV, None
  - **Tint:** Two separate fields for hexadecimal colors (e.g. #FFFFFF #131920)
* If the line does not exist and the switch is enabled, it is automatically created at the end of the file.

### Template

* Direct editing of the `Template:` field in the configuration file.

## Usage Instructions

1. Place the original `settings.txt` files in the **input** folder.
2. Run the tool and configure the changes in the interface.
3. The edited files will appear in the **output** folder.

*The tool is non-destructive; your files in the input folder will always remain intact. However, it is always recommended to have a backup in case something goes wrong.*

## Compilation (For Developers)

If you wish to generate the executable from the source code, make sure you have the dependencies installed (`customtkinter`, `Pillow`) and use the following command:

```bash
python -m PyInstaller --noconfirm --onefile --windowed --add-data "background.jpg;internal" --icon "icon.ico" main.py

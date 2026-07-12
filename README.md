# Rain-World-State-Batch-Editor

![Interface Preview](UI.png)
background image official art by Del Northern edited :)

**RWSBE** is a tool designed for the bulk editing of Rain World room configuration files (`settings.txt`).

This tool was born from a real technical need: to facilitate the implementation of multiple regional states for a mod currently under development, which allows handling several states for the same room using suffixes (e.g., `su_73_settings_1.txt`, `_2.txt`, etc.). Instead of manually editing hundreds of files for each state, RWSBE automates the process in seconds.

The goal is to edit files in batches while respecting the logic and artistic intent of each room.

##  Features

###  Palettes (Main & Fade)

* **Main Palette A:** Writes a palette to all settings that **do not have** a declared `Palette:`. If one is already declared, the tool ignores it and skips to section B.
* **Main Palette B:** Changes all palettes declared in a list to another (Example: Palette 0 to 14). It will search all settings for those with `Palette: 0` and change them to `14`. You can add as many options as you need.
* **Fade Palette A:** Works the same as Main Palette A, allowing you to choose the opacity of the Fade Palette. It is only applied if it doesn't already exist in the code.
* **Fade Palette B:** Works the same as Main Palette B for fade palettes, maintaining the already established opacity unless changed using the decimal percentage method below.

###  Effects & Intensity

This section uses a **decimal percentage system** (where `1` is the normal value, `0.5` is 50%, etc.).

* **Decals:** Decals in Rain World have **4 separate opacity modules**. RWSBE recognizes this and **multiplies each of the 4 modules individually** by the declared percentage.
* *Example:* If you apply `0.5` (50%), a decal with opacities `[1, 0.8, 0.4, 0]` will become `[0.5, 0.4, 0.2, 0]`. This ensures that the original depth and artistic decision are maintained, without leveling all values to the same point.


* **Light Sources:** Light sources have a single intensity setting. The tool scales this value to dim or enhance the global lighting of the room.
* **Grime & Clouds:** Intensity control for environmental grime and clouds. Allows for massive adjustment of these values so the atmosphere matches the new state (e.g., darker clouds for night states).

##  Usage Instructions

1. Place the original `settings.txt` files in the **input** folder.
2. Run the tool and configure the changes in the interface.
3. The edited files will appear in the **output** folder.

*The tool is non-destructive; your files in the input folder will always remain intact. However, it is always recommended to have a backup in case something goes wrong.*

##  Compilation (For Developers)

If you wish to generate the executable from the source code, make sure you have the dependencies installed (`customtkinter`, `Pillow`) and use the following command:

```bash
python -m PyInstaller --noconfirm --onefile --windowed --add-data "background.jpg;internal" --icon "icon.ico" main.py

```

##  Development Note

In this project, the logic was iterated with the help of Gemini AI to transform a manual process of more than 4 hours into an automated task of a few seconds. It is designed to be compatible with custom regions, making it easier for any modder to create dynamic states safely.

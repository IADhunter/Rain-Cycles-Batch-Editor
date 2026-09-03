import customtkinter as ctk
from PIL import Image, ImageTk
import os
import sys
import core_logic as core

def get_resource_path(relative_path):
    """Obtiene la ruta correcta tanto en desarrollo como en ejecutable"""
    if getattr(sys, 'frozen', False):
        # Cuando está compilado como .exe
        base_path = sys._MEIPASS
    else:
        # Cuando se ejecuta como script
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)

def get_external_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

class RuleRow(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", corner_radius=0, **kwargs)
        self.entry_old = ctk.CTkEntry(self, width=66, height=22, corner_radius=0)
        self.entry_old.pack(side="left", padx=2)
        ctk.CTkLabel(self, text="To").pack(side="left", padx=2)
        self.entry_new = ctk.CTkEntry(self, width=66, height=22, corner_radius=0)
        self.entry_new.pack(side="left", padx=2)
        self.btn_del = ctk.CTkButton(self, text="-", width=24, height=22,
                                     fg_color="#4a4a5a", corner_radius=0, command=self.destroy)
        self.btn_del.pack(side="left", padx=5)


class TemplateRuleRow(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", corner_radius=0, **kwargs)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        self.entry_old = ctk.CTkEntry(self, width=180, height=22, corner_radius=0)
        self.entry_old.grid(row=0, column=0, sticky="ew", padx=4, pady=(2, 1))

        self.entry_new = ctk.CTkEntry(self, width=180, height=22, corner_radius=0)
        self.entry_new.grid(row=1, column=0, sticky="ew", padx=4, pady=(1, 2))

        self.btn_del = ctk.CTkButton(self, text="-", width=24, height=22,
                                     fg_color="#4a4a5a", corner_radius=0, command=self.destroy)
        self.btn_del.grid(row=0, column=1, padx=(2, 4), pady=(2, 0), sticky="n")

class RCBEApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ===== CONFIGURACIÓN DE VENTANA =====
        self.title("RCBE - Rain Cycles Batch Editor")
        self.geometry("1366x768")
        self.resizable(True, True)
        self.minsize(1366, 768)

        # ===== ICONO (corregido para .exe) =====
        try:
            import ctypes
            icon_path = get_resource_path("icon.ico")
            if os.path.exists(icon_path):
                # Establecer AppUserModelID para Windows 10/11
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("RCBE")
                self.iconbitmap(icon_path)
        except Exception:
            pass

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # ===== VARIABLES DE INSTANCIA =====
        self.app_dir = get_external_path()
        self.input_path = os.path.join(self.app_dir, "input")
        self.output_path = os.path.join(self.app_dir, "output")

        for folder in [self.input_path, self.output_path]:
            if not os.path.exists(folder):
                os.makedirs(folder)

        self.bg_path = get_resource_path("background.jpg")

        # Registros de reglas
        self.rows_main_b = []
        self.rows_fade_b = []
        self.rows_terrain_main_b = []
        self.rows_terrain_fade_b = []
        self.rows_template = []

        # RainCycles
        self.rain_type_options = ["Blend", "Static", "Vanilla"]
        self.rain_type_index = 0
        self.rain_view_options = ["ACV", "RTV", "PSV", "ORV", "AUV", "None"]
        self.rain_view_index = 0

        # Centro del diseño original (1366 / 2)
        self._center_x = 683

        # ===== FONDO =====
        self.bg_original = None
        self.bg_label = None
        self.setup_background()

        # ===== UI =====
        self.init_ui_elements()

        # ===== REDIMENSIONAMIENTO (solo fondo) =====
        self.bind("<Configure>", self.on_resize)

    # ==================================================================
    #  HELPERS DE POSICIONAMIENTO
    # ==================================================================
    def _place(self, widget, base_x, base_y, anchor="nw"):
        """Coloca un widget usando relx=0.5 (centro de ventana) con un offset
        fijo, igual que el título. Así todo se centra automáticamente."""
        offset_x = base_x - self._center_x
        widget.place(relx=0.5, x=offset_x, y=base_y, anchor=anchor)

    # ==================================================================
    #  BACKGROUND
    # ==================================================================
    def setup_background(self):
        try:
            if os.path.exists(self.bg_path):
                self.bg_original = Image.open(self.bg_path)
                self.bg_label = ctk.CTkLabel(self, text="")
                self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                self.update_background()
        except Exception as e:
            print(f"Error loading background: {e}")

    def update_background(self):
        if self.bg_original is None or self.bg_label is None:
            return
        try:
            width = self.winfo_width()
            height = self.winfo_height()
            if width <= 1 or height <= 1:
                return
            img_width, img_height = self.bg_original.size
            ratio = max(width / img_width, height / img_height)
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            scaled = self.bg_original.resize((new_width, new_height), Image.Resampling.NEAREST)
            left = (new_width - width) // 2
            top = (new_height - height) // 2
            right = left + width
            bottom = top + height
            cropped = scaled.crop((left, top, right, bottom))
            self.bg_photo = ImageTk.PhotoImage(cropped)
            self.bg_label.configure(image=self.bg_photo)
        except Exception:
            pass

    def on_resize(self, event):
        if event.widget is not self:
            return
        self.update_background()

    # ==================================================================
    #  UI
    # ==================================================================
    def init_ui_elements(self):
        # ==================== TÍTULO ====================
        self.frame_title = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color="#212d5d", width=500)
        ctk.CTkLabel(self.frame_title, text="Rain Cycles Batch Editor",
                    font=("Trebuchet MS", 32, "bold")).place(relx=0.5, y=25, anchor="center")
        self._place(self.frame_title, 683, 10, anchor="n")

        # ==================== PALETTE CONTROL ====================
        self.frame_palette_header = ctk.CTkFrame(self, width=432, height=40, corner_radius=0, fg_color="#212d5d")
        ctk.CTkLabel(self.frame_palette_header, text="Palette Control",
                    font=("Trebuchet MS", 20, "bold")).place(x=10, y=5)
        self._place(self.frame_palette_header, 40, 90)

        # --- Palette B ---
        self.btn_add_b1 = ctk.CTkButton(self, text="+ palette", width=208, height=28,
                                       corner_radius=0, fg_color="#455f8b",
                                       command=lambda: self.add_rule_row(self.scroll_b1, self.rows_main_b))
        self._place(self.btn_add_b1, 40, 138)

        self.scroll_b1 = ctk.CTkScrollableFrame(self, width=192, height=140, corner_radius=0, fg_color="#2a2a32")
        self._place(self.scroll_b1, 40, 170)

        self.btn_clear_b1 = ctk.CTkButton(self, text="Clear", width=208, height=22,
                                         fg_color="#343844", hover_color="#4a5060",
                                         corner_radius=0, command=lambda: self.clear_rules(self.rows_main_b))
        self._place(self.btn_clear_b1, 40, 375)

        # --- Fade Palette ---
        self.btn_add_b2 = ctk.CTkButton(self, text="+ fade pal", width=98, height=28,
                                       corner_radius=0, fg_color="#455f8b",
                                       command=lambda: self.add_rule_row(self.scroll_b2, self.rows_fade_b))
        self._place(self.btn_add_b2, 264, 138)

        self.frame_fb_op = ctk.CTkFrame(self, width=108, height=28, corner_radius=0, fg_color="#3a3a4a")
        ctk.CTkLabel(self.frame_fb_op, text="Op:", font=("Trebuchet MS", 11)).place(x=4, y=2)
        self.ent_fade_b_opacity = ctk.CTkEntry(self.frame_fb_op, width=65, height=22, corner_radius=0)
        self.ent_fade_b_opacity.insert(0, "1.0")
        self.ent_fade_b_opacity.place(x=36, y=2)
        self._place(self.frame_fb_op, 364, 138)

        self.scroll_b2 = ctk.CTkScrollableFrame(self, width=192, height=140, corner_radius=0, fg_color="#2a2a32")
        self._place(self.scroll_b2, 264, 170)

        self.btn_clear_b2 = ctk.CTkButton(self, text="Clear", width=208, height=22,
                                         fg_color="#343844", hover_color="#4a5060",
                                         corner_radius=0, command=lambda: self.clear_rules(self.rows_fade_b))
        self._place(self.btn_clear_b2, 264, 375)

        # ==================== ROOM CONTROL ====================
        self.frame_room_header = ctk.CTkFrame(self, width=356, height=40, corner_radius=0, fg_color="#212d5d")
        ctk.CTkLabel(self.frame_room_header, text="Room Control",
                    font=("Trebuchet MS", 20, "bold")).place(x=10, y=5)
        self._place(self.frame_room_header, 504, 90)

        self.frame_ambient_controls = ctk.CTkFrame(self, width=356, height=400, corner_radius=0, fg_color="#2d2d3d")
        self._place(self.frame_ambient_controls, 504, 140)

        # Ambient multipliers
        ctk.CTkLabel(self.frame_ambient_controls, text="Grime:").place(x=15, y=24)
        self.ent_grime_mult = ctk.CTkEntry(self.frame_ambient_controls, width=65, height=24, corner_radius=0)
        self.ent_grime_mult.insert(0, "1.0")
        self.ent_grime_mult.place(x=104, y=20)

        ctk.CTkLabel(self.frame_ambient_controls, text="LightSource:").place(x=15, y=52)
        self.ent_light_mult = ctk.CTkEntry(self.frame_ambient_controls, width=65, height=24, corner_radius=0)
        self.ent_light_mult.insert(0, "1.0")
        self.ent_light_mult.place(x=104, y=48)

        ctk.CTkLabel(self.frame_ambient_controls, text="Clouds:").place(x=15, y=80)
        self.ent_clouds_mult = ctk.CTkEntry(self.frame_ambient_controls, width=65, height=24, corner_radius=0)
        self.ent_clouds_mult.insert(0, "1.0")
        self.ent_clouds_mult.place(x=104, y=76)

        ctk.CTkLabel(self.frame_ambient_controls, text="Decal:").place(x=15, y=108)
        self.ent_decal_mult = ctk.CTkEntry(self.frame_ambient_controls, width=65, height=24, corner_radius=0)
        self.ent_decal_mult.insert(0, "1.0")
        self.ent_decal_mult.place(x=104, y=104)

        # Terrain Effects
        ctk.CTkLabel(self.frame_ambient_controls, text="T.Light:").place(x=185, y=24)
        self.ent_terrain_light_mult = ctk.CTkEntry(self.frame_ambient_controls, width=65, height=24, corner_radius=0)
        self.ent_terrain_light_mult.insert(0, "1.0")
        self.ent_terrain_light_mult.place(x=280, y=20)

        ctk.CTkLabel(self.frame_ambient_controls, text="T.StainAmt:").place(x=185, y=52)
        self.ent_terrain_stain_amount_mult = ctk.CTkEntry(self.frame_ambient_controls, width=65, height=24, corner_radius=0)
        self.ent_terrain_stain_amount_mult.insert(0, "1.0")
        self.ent_terrain_stain_amount_mult.place(x=280, y=48)

        ctk.CTkLabel(self.frame_ambient_controls, text="T.StainBrt:").place(x=185, y=80)
        self.ent_terrain_stain_brightness_mult = ctk.CTkEntry(self.frame_ambient_controls, width=65, height=24, corner_radius=0)
        self.ent_terrain_stain_brightness_mult.insert(0, "1.0")
        self.ent_terrain_stain_brightness_mult.place(x=280, y=76)

        ctk.CTkLabel(self.frame_ambient_controls, text="T.StainH:").place(x=185, y=108)
        self.ent_terrain_stain_height_mult = ctk.CTkEntry(self.frame_ambient_controls, width=65, height=24, corner_radius=0)
        self.ent_terrain_stain_height_mult.insert(0, "1.0")
        self.ent_terrain_stain_height_mult.place(x=280, y=104)

        ctk.CTkLabel(self.frame_ambient_controls, text="T.Waves:").place(x=185, y=136)
        self.ent_terrain_waves_mult = ctk.CTkEntry(self.frame_ambient_controls, width=65, height=24, corner_radius=0)
        self.ent_terrain_waves_mult.insert(0, "1.0")
        self.ent_terrain_waves_mult.place(x=280, y=132)

        ctk.CTkLabel(self.frame_ambient_controls, text="T.Grain:").place(x=185, y=164)
        self.ent_terrain_grain_mult = ctk.CTkEntry(self.frame_ambient_controls, width=65, height=24, corner_radius=0)
        self.ent_terrain_grain_mult.insert(0, "1.0")
        self.ent_terrain_grain_mult.place(x=280, y=160)

        ctk.CTkLabel(self.frame_ambient_controls, text="T.SkyFade:").place(x=185, y=192)
        self.ent_terrain_sky_fade_mult = ctk.CTkEntry(self.frame_ambient_controls, width=65, height=24, corner_radius=0)
        self.ent_terrain_sky_fade_mult.insert(0, "1.0")
        self.ent_terrain_sky_fade_mult.place(x=280, y=188)

        # Rain Cycles
        self.sw_rain_cycles = ctk.CTkSwitch(self.frame_ambient_controls, text="Enable RainCycles",
                                           progress_color="#212d5d")
        self.sw_rain_cycles.place(x=15, y=228)

        ctk.CTkLabel(self.frame_ambient_controls, text="Type:").place(x=15, y=260)
        self.btn_type_prev = ctk.CTkButton(self.frame_ambient_controls, text="◀", width=28, height=26,
                                          corner_radius=0, fg_color="#455f8b",
                                          command=lambda: self.cycle_rain_type(-1))
        self.btn_type_prev.place(x=213, y=256)
        self.lbl_rain_type = ctk.CTkLabel(self.frame_ambient_controls, text=self.rain_type_options[0],
                                         width=65, height=26, fg_color="#1a1a22", corner_radius=0)
        self.lbl_rain_type.place(x=246, y=256)
        self.btn_type_next = ctk.CTkButton(self.frame_ambient_controls, text="▶", width=28, height=26,
                                          corner_radius=0, fg_color="#455f8b",
                                          command=lambda: self.cycle_rain_type(1))
        self.btn_type_next.place(x=316, y=256)

        ctk.CTkLabel(self.frame_ambient_controls, text="View:").place(x=15, y=290)
        self.btn_view_prev = ctk.CTkButton(self.frame_ambient_controls, text="◀", width=28, height=26,
                                          corner_radius=0, fg_color="#455f8b",
                                          command=lambda: self.cycle_rain_view(-1))
        self.btn_view_prev.place(x=213, y=286)
        self.lbl_rain_view = ctk.CTkLabel(self.frame_ambient_controls, text=self.rain_view_options[0],
                                         width=65, height=26, fg_color="#1a1a22", corner_radius=0)
        self.lbl_rain_view.place(x=246, y=286)
        self.btn_view_next = ctk.CTkButton(self.frame_ambient_controls, text="▶", width=28, height=26,
                                          corner_radius=0, fg_color="#455f8b",
                                          command=lambda: self.cycle_rain_view(1))
        self.btn_view_next.place(x=316, y=286)

        ctk.CTkLabel(self.frame_ambient_controls, text="Tint:").place(x=15, y=320)
        self.ent_rain_tint_1 = ctk.CTkEntry(self.frame_ambient_controls, width=64, height=26,
                                           corner_radius=0, placeholder_text="#FFFFFF")
        self.ent_rain_tint_1.place(x=213, y=316)
        self.ent_rain_tint_2 = ctk.CTkEntry(self.frame_ambient_controls, width=64, height=26,
                                           corner_radius=0, placeholder_text="#131920")
        self.ent_rain_tint_2.place(x=280, y=316)

        # ==================== TERRAIN CONTROL ====================
        self.frame_terrain_header = ctk.CTkFrame(self, width=432, height=40, corner_radius=0, fg_color="#212d5d")
        ctk.CTkLabel(self.frame_terrain_header, text="Terrain Control",
                    font=("Trebuchet MS", 20, "bold")).place(x=10, y=5)
        self._place(self.frame_terrain_header, 892, 90)

        # Terrain Palette B
        self.btn_add_terrain_b1 = ctk.CTkButton(self, text="+ T palette", width=208, height=28,
                                       corner_radius=0, fg_color="#455f8b",
                                       command=lambda: self.add_rule_row(self.scroll_terrain_b1, self.rows_terrain_main_b))
        self._place(self.btn_add_terrain_b1, 892, 138)

        self.scroll_terrain_b1 = ctk.CTkScrollableFrame(self, width=192, height=140, corner_radius=0, fg_color="#2a2a32")
        self._place(self.scroll_terrain_b1, 892, 170)

        self.btn_clear_terrain_b1 = ctk.CTkButton(self, text="Clear", width=208, height=22,
                                         fg_color="#343844", hover_color="#4a5060",
                                         corner_radius=0, command=lambda: self.clear_rules(self.rows_terrain_main_b))
        self._place(self.btn_clear_terrain_b1, 892, 375)

        # Terrain Fade Palette
        self.btn_add_terrain_b2 = ctk.CTkButton(self, text="+ T fade pal", width=98, height=28,
                                       corner_radius=0, fg_color="#455f8b",
                                       command=lambda: self.add_rule_row(self.scroll_terrain_b2, self.rows_terrain_fade_b))
        self._place(self.btn_add_terrain_b2, 1116, 138)

        self.frame_terrain_fb_op = ctk.CTkFrame(self, width=108, height=28, corner_radius=0, fg_color="#3a3a4a")
        ctk.CTkLabel(self.frame_terrain_fb_op, text="Op:", font=("Trebuchet MS", 11)).place(x=4, y=2)
        self.ent_terrain_fade_b_opacity = ctk.CTkEntry(self.frame_terrain_fb_op, width=65, height=22, corner_radius=0)
        self.ent_terrain_fade_b_opacity.insert(0, "1.0")
        self.ent_terrain_fade_b_opacity.place(x=36, y=2)
        self._place(self.frame_terrain_fb_op, 1216, 138)

        self.scroll_terrain_b2 = ctk.CTkScrollableFrame(self, width=192, height=140, corner_radius=0, fg_color="#2a2a32")
        self._place(self.scroll_terrain_b2, 1116, 170)

        self.btn_clear_terrain_b2 = ctk.CTkButton(self, text="Clear", width=208, height=22,
                                         fg_color="#343844", hover_color="#4a5060",
                                         corner_radius=0, command=lambda: self.clear_rules(self.rows_terrain_fade_b))
        self._place(self.btn_clear_terrain_b2, 1116, 375)

        # ==================== TEMPLATE ====================
        self.frame_template_header = ctk.CTkFrame(self, width=432, height=40, corner_radius=0, fg_color="#212d5d")
        ctk.CTkLabel(self.frame_template_header, text="Template",
                    font=("Trebuchet MS", 20, "bold")).place(x=10, y=5)
        self._place(self.frame_template_header, 40, 410)

        self.btn_add_template = ctk.CTkButton(self, text="+ template", width=208, height=28,
                                       corner_radius=0, fg_color="#455f8b",
                                       command=lambda: self.add_template_row(self.scroll_template, self.rows_template))
        self._place(self.btn_add_template, 40, 460)

        self.scroll_template = ctk.CTkScrollableFrame(self, width=416, height=100, corner_radius=0, fg_color="#2a2a32")
        self._place(self.scroll_template, 40, 495)

        self.btn_clear_template = ctk.CTkButton(self, text="Clear", width=208, height=22,
                                         fg_color="#343844", hover_color="#4a5060",
                                         corner_radius=0, command=lambda: self.clear_rules(self.rows_template))
        self._place(self.btn_clear_template, 264, 460)

        # ==================== MODIFY EFFECT COLOR A ====================
        self.frame_effect_color_a_header = ctk.CTkFrame(self, width=208, height=40, corner_radius=0, fg_color="#212d5d")
        ctk.CTkLabel(self.frame_effect_color_a_header, text="Modify Effect Color A",
                    font=("Trebuchet MS", 17, "bold")).place(x=10, y=6)
        self._place(self.frame_effect_color_a_header, 892, 410)

        self.frame_effect_color_a = ctk.CTkFrame(self, width=208, height=160, corner_radius=0, fg_color="#2d2d3d")
        self._place(self.frame_effect_color_a, 892, 455)

        self.sw_modify_effect_a = ctk.CTkSwitch(self.frame_effect_color_a, text="Enable",
                                            progress_color="#212d5d")
        self.sw_modify_effect_a.place(x=15, y=8)

        ctk.CTkLabel(self.frame_effect_color_a, text="H:").place(x=15, y=40)
        self.ent_eca_h = ctk.CTkEntry(self.frame_effect_color_a, width=60, height=24, corner_radius=0)
        self.ent_eca_h.insert(0, "1.0")
        self.ent_eca_h.place(x=80, y=37)

        ctk.CTkLabel(self.frame_effect_color_a, text="S:").place(x=15, y=72)
        self.ent_eca_s = ctk.CTkEntry(self.frame_effect_color_a, width=60, height=24, corner_radius=0)
        self.ent_eca_s.insert(0, "1.0")
        self.ent_eca_s.place(x=80, y=69)

        ctk.CTkLabel(self.frame_effect_color_a, text="V:").place(x=15, y=104)
        self.ent_eca_v = ctk.CTkEntry(self.frame_effect_color_a, width=60, height=24, corner_radius=0)
        self.ent_eca_v.insert(0, "1.0")
        self.ent_eca_v.place(x=80, y=101)

        self.sw_only_effect_a = ctk.CTkSwitch(self.frame_effect_color_a, text="Only Effect A",
                                            progress_color="#212d5d")
        self.sw_only_effect_a.place(x=15, y=132)

        # ==================== MODIFY EFFECT COLOR B ====================
        self.frame_effect_color_b_header = ctk.CTkFrame(self, width=208, height=40, corner_radius=0, fg_color="#212d5d")
        ctk.CTkLabel(self.frame_effect_color_b_header, text="Modify Effect Color B",
                    font=("Trebuchet MS", 17, "bold")).place(x=10, y=6)
        self._place(self.frame_effect_color_b_header, 1116, 410)

        self.frame_effect_color_b = ctk.CTkFrame(self, width=208, height=160, corner_radius=0, fg_color="#2d2d3d")
        self._place(self.frame_effect_color_b, 1116, 455)

        self.sw_modify_effect_b = ctk.CTkSwitch(self.frame_effect_color_b, text="Enable",
                                            progress_color="#212d5d")
        self.sw_modify_effect_b.place(x=15, y=8)

        ctk.CTkLabel(self.frame_effect_color_b, text="H:").place(x=15, y=40)
        self.ent_ecb_h = ctk.CTkEntry(self.frame_effect_color_b, width=60, height=24, corner_radius=0)
        self.ent_ecb_h.insert(0, "1.0")
        self.ent_ecb_h.place(x=80, y=37)

        ctk.CTkLabel(self.frame_effect_color_b, text="S:").place(x=15, y=72)
        self.ent_ecb_s = ctk.CTkEntry(self.frame_effect_color_b, width=60, height=24, corner_radius=0)
        self.ent_ecb_s.insert(0, "1.0")
        self.ent_ecb_s.place(x=80, y=69)

        ctk.CTkLabel(self.frame_effect_color_b, text="V:").place(x=15, y=104)
        self.ent_ecb_v = ctk.CTkEntry(self.frame_effect_color_b, width=60, height=24, corner_radius=0)
        self.ent_ecb_v.insert(0, "1.0")
        self.ent_ecb_v.place(x=80, y=101)

        self.sw_only_effect_b = ctk.CTkSwitch(self.frame_effect_color_b, text="Only Effect B",
                                            progress_color="#212d5d")
        self.sw_only_effect_b.place(x=15, y=132)

        # ==================== CONSOLE & BUTTONS ====================
        self.console_log = ctk.CTkLabel(self, text="🍉 Init 🍉", font=("Trebuchet MS", 15),
                                        width=240, height=32, text_color="#aaaaaa",
                                        fg_color="#1a1a22", corner_radius=0)
        self._place(self.console_log, 563, 570)

        self.btn_input = ctk.CTkButton(self, text="input", width=112, height=32, corner_radius=0,
                                       fg_color="#455f8b", command=lambda: os.startfile(self.input_path))
        self._place(self.btn_input, 563, 610)

        self.btn_output = ctk.CTkButton(self, text="output", width=112, height=32, corner_radius=0,
                                        fg_color="#455f8b", command=lambda: os.startfile(self.output_path))
        self._place(self.btn_output, 691, 610)

        self.btn_generate = ctk.CTkButton(self, text="Generate", width=240, height=44, corner_radius=0,
                                          font=("Trebuchet MS", 18, "bold"), fg_color="#212d5d",
                                          command=self.run_process)
        self._place(self.btn_generate, 563, 650)

        self.credits_label = ctk.CTkLabel(self, text="By IADhunter", font=("Trebuchet MS", 12),
                    text_color="#aaaaaa", width=120, height=20)
        self._place(self.credits_label, 40, 60)

    # ==================================================================
    #  HELPERS
    # ==================================================================
    def add_rule_row(self, scroll_target, registry):
        new_row = RuleRow(scroll_target)
        new_row.pack(pady=2, fill="x")
        registry.append(new_row)

    def add_template_row(self, scroll_target, registry):
        new_row = TemplateRuleRow(scroll_target)
        new_row.pack(pady=2, fill="x")
        registry.append(new_row)

    def clear_rules(self, registry):
        for row in registry:
            if row.winfo_exists():
                row.destroy()
        registry.clear()

    def cycle_rain_type(self, direction):
        self.rain_type_index = (self.rain_type_index + direction) % len(self.rain_type_options)
        self.lbl_rain_type.configure(text=self.rain_type_options[self.rain_type_index])

    def cycle_rain_view(self, direction):
        self.rain_view_index = (self.rain_view_index + direction) % len(self.rain_view_options)
        self.lbl_rain_view.configure(text=self.rain_view_options[self.rain_view_index])

    @staticmethod
    def _tint_value(entry):
        val = entry.get().strip()
        if not val or val.lower() == "none":
            return None
        return val

    # ==================================================================
    #  PROCESS
    # ==================================================================
    def run_process(self):
        try:
            d_mult = float(self.ent_decal_mult.get())
            l_mult = float(self.ent_light_mult.get())
            g_mult = float(self.ent_grime_mult.get())
            c_mult = float(self.ent_clouds_mult.get())
            fb_opacity = self.ent_fade_b_opacity.get().strip()
            terrain_fb_opacity = self.ent_terrain_fade_b_opacity.get().strip()

            t_light_mult = float(self.ent_terrain_light_mult.get())
            t_stain_amount_mult = float(self.ent_terrain_stain_amount_mult.get())
            t_stain_brightness_mult = float(self.ent_terrain_stain_brightness_mult.get())
            t_stain_height_mult = float(self.ent_terrain_stain_height_mult.get())
            t_waves_mult = float(self.ent_terrain_waves_mult.get())
            t_grain_mult = float(self.ent_terrain_grain_mult.get())
            t_sky_fade_mult = float(self.ent_terrain_sky_fade_mult.get())

            rules_main = {r.entry_old.get().strip(): r.entry_new.get().strip()
                         for r in self.rows_main_b if r.winfo_exists() and r.entry_old.get().strip()}
            rules_fade = {r.entry_old.get().strip(): r.entry_new.get().strip()
                         for r in self.rows_fade_b if r.winfo_exists() and r.entry_old.get().strip()}
            rules_terrain_main = {r.entry_old.get().strip(): r.entry_new.get().strip()
                         for r in self.rows_terrain_main_b if r.winfo_exists() and r.entry_old.get().strip()}
            rules_terrain_fade = {r.entry_old.get().strip(): r.entry_new.get().strip()
                         for r in self.rows_terrain_fade_b if r.winfo_exists() and r.entry_old.get().strip()}
            rules_template = {r.entry_old.get().strip(): r.entry_new.get().strip()
                         for r in self.rows_template if r.winfo_exists() and r.entry_old.get().strip()}

            template_create = None
            for r in self.rows_template:
                if r.winfo_exists() and not r.entry_old.get().strip() and r.entry_new.get().strip():
                    template_create = r.entry_new.get().strip()
                    break

            rain_enabled = bool(self.sw_rain_cycles.get())
            rain_type = self.rain_type_options[self.rain_type_index]
            rain_view = self.rain_view_options[self.rain_view_index]

            tint_1 = self._tint_value(self.ent_rain_tint_1)
            tint_2 = self._tint_value(self.ent_rain_tint_2)
            if tint_1 and tint_2:
                rain_tint = f"{tint_1} {tint_2}"
            elif tint_1:
                rain_tint = tint_1
            elif tint_2:
                rain_tint = tint_2
            else:
                rain_tint = None

            # Modify Effect Color A/B
            modify_effect_a_enabled = bool(self.sw_modify_effect_a.get())
            effect_a_h_mult = float(self.ent_eca_h.get())
            effect_a_s_mult = float(self.ent_eca_s.get())
            effect_a_v_mult = float(self.ent_eca_v.get())
            only_effect_a = bool(self.sw_only_effect_a.get())

            modify_effect_b_enabled = bool(self.sw_modify_effect_b.get())
            effect_b_h_mult = float(self.ent_ecb_h.get())
            effect_b_s_mult = float(self.ent_ecb_s.get())
            effect_b_v_mult = float(self.ent_ecb_v.get())
            only_effect_b = bool(self.sw_only_effect_b.get())

            target_files = [f for f in os.listdir(self.input_path) if f.endswith(".txt")]
            processed = 0

            for file_name in target_files:
                with open(os.path.join(self.input_path, file_name), 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

                result = core.process_line_by_line(
                    lines,
                    rules_main,
                    rules_fade, fb_opacity,
                    rules_terrain_main,
                    rules_terrain_fade, terrain_fb_opacity,
                    d_mult, l_mult, g_mult, c_mult,
                    t_light_mult, t_stain_amount_mult, t_stain_brightness_mult,
                    t_stain_height_mult, t_waves_mult, t_grain_mult, t_sky_fade_mult,
                    rain_enabled, rain_type, rain_view, rain_tint,
                    rules_template, template_create,
                    modify_effect_a_enabled, effect_a_h_mult, effect_a_s_mult, effect_a_v_mult, only_effect_a,
                    modify_effect_b_enabled, effect_b_h_mult, effect_b_s_mult, effect_b_v_mult, only_effect_b
                )

                with open(os.path.join(self.output_path, file_name), 'w', encoding='utf-8') as f:
                    f.writelines(result)
                processed += 1

            self.console_log.configure(text=f"🍉 Success: {processed} Settings 🍉", text_color="green")
        except Exception as e:
            self.console_log.configure(text=f"Error: {e}", text_color="red")

if __name__ == "__main__":
    app = RCBEApp()
    app.mainloop()
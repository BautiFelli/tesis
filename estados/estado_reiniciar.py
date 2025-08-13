import time
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from estados.estado_base import EstadoBase

# ... (resto igual)

class EstadoReiniciar(EstadoBase):
    def __init__(self, machine):
        super().__init__(machine)
        self.start_time = time.time()
        self.bg_color = (20, 21, 24)
        self.restart_btn_path = "assets/restart.jpg"
        self.duracion = 9999  # Queda hasta que se reinicie
        self.frase = "bueno, ya me aburriste. chau"
        # No definimos self.indicacion acá

        # Guardá el último afiche generado para mostrarlo (opcional)
        if hasattr(machine, "afiches_generados") and machine.afiches_generados:
            self.ultimo_afiche = machine.afiches_generados[-1]["img"]
        else:
            self.ultimo_afiche = None

        try:
            self.font_frase = ImageFont.truetype("arial.ttf", 54)
            self.font_indicacion = ImageFont.truetype("verdana.ttf", 36)
        except:
            self.font_frase = ImageFont.load_default()
            self.font_indicacion = ImageFont.load_default()

    def run(self):
        canvas_w, canvas_h = 864, 1536  # VERTICAL
        img = Image.new("RGB", (canvas_w, canvas_h), self.bg_color)
        draw = ImageDraw.Draw(img)

        # --- Frase principal ---
        frase = self.frase
        bbox = self.font_frase.getbbox(frase)
        frase_w = bbox[2] - bbox[0]
        x_frase = (canvas_w - frase_w) // 2
        y_frase = int(canvas_h * 0.13)
        draw.text((x_frase, y_frase), frase, font=self.font_frase, fill=(255,255,255))

        # --- Último afiche generado ---
        if self.ultimo_afiche is not None:
            afiche_max_w = int(canvas_w * 0.7)
            afiche_max_h = int(canvas_h * 0.38)
            img_w, img_h = self.ultimo_afiche.size
            scale = min(afiche_max_w / img_w, afiche_max_h / img_h, 1.0)
            new_size = (int(img_w * scale), int(img_h * scale))
            afiche_resized = self.ultimo_afiche.resize(new_size)
            x_afiche = (canvas_w - new_size[0]) // 2
            y_afiche = int(canvas_h * 0.27)
            img.paste(afiche_resized, (x_afiche, y_afiche))

        # --- Botón Restart (centro inferior) ---
        try:
            btn_img = Image.open(self.restart_btn_path).convert("RGBA")
        except:
            btn_img = Image.new("RGBA", (130, 130), (120, 120, 120, 255))  # Placeholder gris

        btn_size = 250
        btn_img = btn_img.resize((btn_size, btn_size), Image.LANCZOS)
        x_btn = (canvas_w - btn_size) // 2
        y_btn = int(canvas_h * 0.84)
        img.paste(btn_img, (x_btn, y_btn), btn_img)

        # Escribí la R encima, centrada
        try:
            font_R = ImageFont.truetype(r"C:\Users\bautista\AppData\Local\Microsoft\Windows\Fonts\MYRIADPRO-BOLD.OTF", 66)
        except:
            font_R = ImageFont.load_default()
        draw = ImageDraw.Draw(img)
        bbox_R = font_R.getbbox("R")
        w_R = bbox_R[2] - bbox_R[0]
        h_R = bbox_R[3] - bbox_R[1]
        r_x = x_btn + (btn_size - w_R) // 2
        r_y = y_btn + (btn_size - h_R) // 2
        draw.text((r_x, r_y), "R", font=font_R, fill=(30,30,30), stroke_width=2, stroke_fill=(255,255,255))

        frame = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
        frame_rotated = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        return frame_rotated

    def handle_key(self, key):
        if key in [ord('r'), ord('R')]:
            from estados.estado_inicio import EstadoInicio
            self.machine.change_state(EstadoInicio(self.machine))


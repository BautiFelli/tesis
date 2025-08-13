from estados.estado_base import EstadoBase
import cv2
import numpy as np
import time
import random
from PIL import Image, ImageDraw, ImageFont
from utilidades.utils import fill_and_center

FRASES_MEME = [
    "cringe",
    "-1000 de aura",
    "PEDILO",
    "normie",
    "boomer"
]

class EstadoMeme(EstadoBase):
    def __init__(self, machine):
        super().__init__(machine)
        self.start_time = time.time()
        self.capturado = False
        self.frame_meme = None

        # Elegí frase evitando la última
        frases_posibles = [f for f in FRASES_MEME if f != getattr(machine, 'ultima_frase_meme', None)]
        if not frases_posibles:
            frases_posibles = FRASES_MEME  # Si estaban todas usadas, permití todas
        self.frase = random.choice(frases_posibles)
        machine.ultima_frase_meme = self.frase  # Guardá la última frase usada

    def run(self):
        cap = self.machine.cap

        # --- CONFIGURACIÓN DEL CANVAS ---
        canvas_h, canvas_w = 864, 1536  # vertical (portrait)
        marco = 18  # grosor del marco negro

        if not self.capturado:
            ret, frame = cap.read()
            if not ret:
                frame = 255 * np.ones((canvas_h, canvas_w, 3), dtype=np.uint8)
            else:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                frame = fill_and_center(frame, canvas_w - 2*marco, canvas_h - 2*marco)
            self.frame_meme = frame.copy()
            self.capturado = True

        # Ya está el screenshot del tamaño justo para el área interna del marco
        screenshot = self.frame_meme

        # Armar canvas blanco y colocar screenshot
        canvas = np.ones((canvas_h, canvas_w, 3), dtype=np.uint8) * 255
        canvas[marco:canvas_h-marco, marco:canvas_w-marco] = screenshot

        # Dibujar marco negro alrededor del screenshot
        cv2.rectangle(canvas, (marco, marco), (canvas_w-marco, canvas_h-marco), (0,0,0), marco)

        # --- TEXTO MEME VERTICAL ---
        pil_img = Image.fromarray(canvas)
        frase = self.frase.upper()

        try:
            font = ImageFont.truetype("impact.ttf", int(canvas_h * 0.11))
        except:
            try:
                font = ImageFont.truetype("arialbd.ttf", int(canvas_h * 0.11))
            except:
                font = ImageFont.load_default()

        bbox = font.getbbox(frase)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        extra_margin = 128
        canvas_text_w = text_w + extra_margin
        canvas_text_h = text_h + extra_margin

        text_img = Image.new("RGBA", (canvas_text_w, canvas_text_h), (0,0,0,0))
        draw = ImageDraw.Draw(text_img)
        x_draw = (canvas_text_w - text_w) // 2
        y_draw = (canvas_text_h - text_h) // 2
        draw.text((x_draw, y_draw), frase, font=font, fill="white", stroke_width=16, stroke_fill="black")

        text_img_rotated = text_img.rotate(-90, expand=True)
        bbox_rotated = text_img_rotated.getbbox()
        text_img_rotated = text_img_rotated.crop(bbox_rotated)

        pos_x = 30
        pos_y = (canvas_h - text_img_rotated.height) // 2

        pil_img.paste(text_img_rotated, (pos_x, pos_y), text_img_rotated)
        canvas_final = np.array(pil_img)

        if time.time() - self.start_time > 7.0:
            from estados.estado_experiencia import EstadoExperiencia
            self.machine.change_state(EstadoExperiencia(self.machine))
        return canvas_final

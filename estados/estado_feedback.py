from estados.estado_base import EstadoBase
import cv2
import numpy as np
import time
import random
from PIL import Image, ImageDraw, ImageFont
from utilidades.utils import fill_and_center

class EstadoFeedback(EstadoBase):
    def __init__(self, machine, feedback):
        super().__init__(machine)
        self.feedback = feedback
        self.start_time = time.time()
        self.feedback_str = random.choice(feedback) if feedback else "..."
        self.color_feedback = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )


    def run(self):
        cap = self.machine.cap
        canvas_h, canvas_w = 864, 1536  # vertical

        ret, frame = cap.read()
        if not ret:
            frame = 255 * np.ones((canvas_h, canvas_w, 3), dtype=np.uint8)
        else:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            frame = fill_and_center(frame, canvas_w, canvas_h)

        # --- TEXTO VERTICAL tipo faja ---
        pil_img = Image.fromarray(frame)
        frase = self.feedback_str

        # CALCULAR TAMAÑO DE FUENTE SEGÚN EL ANCHO DEL CANVAS (NO ALTO)
        font_size = int(canvas_w * 0.04)  # 7% del ancho, ajustá a gusto
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()

        # Medir y renderizar texto
        bbox = font.getbbox(frase)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        extra_margin = 80
        canvas_text_w = text_w + extra_margin
        canvas_text_h = text_h + extra_margin
        text_img = Image.new("RGBA", (canvas_text_w, canvas_text_h), (0,0,0,0))
        draw = ImageDraw.Draw(text_img)
        x_draw = (canvas_text_w - text_w) // 2
        y_draw = (canvas_text_h - text_h) // 2
        draw.text((x_draw, y_draw), frase, font=font, fill=self.color_feedback, stroke_width=3, stroke_fill=(0, 0, 0,))


        # Rotar -90° para texto vertical tipo faja
        text_img_rotated = text_img.rotate(-90, expand=True)
        bbox_rotated = text_img_rotated.getbbox()
        text_img_rotated = text_img_rotated.crop(bbox_rotated)

        # Pegarlo a la izquierda, centrado vertical
        pos_x = 30
        pos_y = (canvas_h - text_img_rotated.height) // 2
        pil_img.paste(text_img_rotated, (pos_x, pos_y), text_img_rotated)

        frame = np.array(pil_img)

        # Siguiente estado tras 7 segundos
        if time.time() - self.start_time > 4.0:
            from estados.estado_meme import EstadoMeme
            self.machine.change_state(EstadoMeme(self.machine))
        return frame

from estados.estado_base import EstadoBase
from preguntas.preguntas import preguntas_opciones_feedback, obtener_siguiente_pregunta
from utilidades.utils import generar_fondo_pixelado
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
import random

from estados.estado_base import EstadoBase

class EstadoInicio(EstadoBase):
    def __init__(self, machine):
        super().__init__(machine)
        self.ultima_pregunta_mostrada = None
        self.pregunta_actual_data = obtener_siguiente_pregunta(preguntas_opciones_feedback, self.ultima_pregunta_mostrada)
        self.pregunta_actual = self.pregunta_actual_data["pregunta"]
        self.opciones_actuales = self.pregunta_actual_data["opciones"]
        self.feedback_base_para_experiencia = []
        self.fondo_pixelado = generar_fondo_pixelado(864, 1536).convert("RGB")
        

    def run(self):
        # Renderiza la pregunta y las opciones en pantalla
        canvas_w, canvas_h = 864, 1536
        img_pil =self.fondo_pixelado.copy()  # O "RGBA" si querés transparencia, pero para esto con RGB va bien
        draw = ImageDraw.Draw(img_pil)

        try:
            fuente_pregunta = ImageFont.truetype("verdanab.ttf", int(canvas_w * 0.09))
        except:
            fuente_pregunta = ImageFont.load_default()
        try:
            fuente_opcion = ImageFont.truetype("trebucbd.ttf", int(canvas_w * 0.055))
        except:
            fuente_opcion = ImageFont.load_default()

        import textwrap
        pregunta_lines = textwrap.wrap(self.pregunta_actual, width=16)
        pregunta_y = int(canvas_h * 0.10)
        for line in pregunta_lines:
            pregunta_bbox = draw.textbbox((0, 0), line, font=fuente_pregunta)
            pregunta_x = (canvas_w - (pregunta_bbox[2] - pregunta_bbox[0])) // 2
            draw.text((pregunta_x, pregunta_y), line, font=fuente_pregunta, fill=(0, 0, 0))
            pregunta_y += pregunta_bbox[3] - pregunta_bbox[1] + 12

        for i, opcion in enumerate(self.opciones_actuales):
            opcion_txt = f"{i+1}. {opcion}"
            opcion_bbox = draw.textbbox((0, 0), opcion_txt, font=fuente_opcion)
            opcion_x = (canvas_w - (opcion_bbox[2] - opcion_bbox[0])) // 2
            opcion_y = int(canvas_h * 0.35) + i * int(canvas_h * 0.13)
            draw.text((opcion_x, opcion_y), opcion_txt, font=fuente_opcion, fill=(0, 0, 0))

        frame = cv2.cvtColor(np.asarray(img_pil), cv2.COLOR_RGB2BGR)
        frame_rotated = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        return frame_rotated

    def handle_key(self, key):
        # Toma la respuesta del usuario con las teclas 1-4
        if key in [ord('1'), ord('2'), ord('3'), ord('4')]:
            idx = int(chr(key)) - 1
            if 0 <= idx < len(self.opciones_actuales):
                respuesta_usuario = self.opciones_actuales[idx]
                feedback = self.pregunta_actual_data["feedback"].get(respuesta_usuario, [])
                from estados.estado_feedback import EstadoFeedback
                self.machine.change_state(EstadoFeedback(self.machine, feedback))


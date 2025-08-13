import time
import random
import numpy as np
import cv2
from assets.frases_virales import lista_frases_virales
from assets.afiche import generar_afiche_popart
from estados.estado_base import EstadoBase

class EstadoFinal(EstadoBase):
    def __init__(self, machine, ultimo_frame):
        super().__init__(machine)
        self.start_time = time.time()
        self.duracion = 5  # Segundos que se muestra el afiche antes de pasar a EstadoViral
        self.ultimo_frame = ultimo_frame  # Debe ser un PIL Image (o np.array, convertí si hace falta)
        self.afiche_generado = None

    def run(self):
       

        # --- Convertí screenshot a RGB sí o sí, para evitar mezcla de colores ---
        if hasattr(self.ultimo_frame, "mode") and self.ultimo_frame.mode != "RGB":
            screenshot_rgb = self.ultimo_frame.convert("RGB")
        else:
            screenshot_rgb = self.ultimo_frame

        # Sólo generá el afiche una vez
        if self.afiche_generado is None:
            frase = random.choice(lista_frases_virales)
            self.afiche_generado = generar_afiche_popart(screenshot_rgb, frase)
            if not hasattr(self.machine, "afiches_generados"):
                self.machine.afiches_generados = []
            self.machine.afiches_generados.append({"img": self.afiche_generado, "frase": frase})

        # Convertí PIL a numpy y a BGR para OpenCV
        frame = np.array(self.afiche_generado)
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame_rotated = cv2.rotate(frame_bgr, cv2.ROTATE_90_CLOCKWISE)

        # Cambio de estado a EstadoViral tras X segundos
        if time.time() - self.start_time > self.duracion:
            from estados.estado_viral import EstadoViral
            self.machine.change_state(EstadoViral(self.machine))

        return frame_rotated



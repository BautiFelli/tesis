from estados.estado_base import EstadoBase
import cv2
import numpy as np
import time
import random
from PIL import Image, ImageDraw, ImageFont

from efectos.efectos import (
    aplicar_zoom_region,
    aplicar_split_face_desordenado,
    aplicar_liquido_region,
    aplicar_blur_region,
    aplicar_pixelate_region,
    generar_estiramiento
)

from utilidades.utils import (
    fill_and_center,
    detectar_sonrisa,
    detectar_serio,
    elegir_posicion_fuera_de_cara_y_elementos,
    cargar_imagenes_desde_carpeta,
    seleccionar_imagen_aleatoria,
    generar_texto_vertical,
    overlay_boca_sonrisa
)
from assets.frasesReacciones import frases_serio, frases_sonrisa, frases_teclado

FUENTES_MEME = [
    "impact.ttf",
    "comicbd.ttf",
    "arialbd.ttf"
]

class EstadoExperiencia(EstadoBase):
    def __init__(self, machine):
        super().__init__(machine)
        self.start_time = time.time()
        self.last_emotion = None
        self.frases_a_mostrar = []
        self.zona_prohibida = None
        self.ultimo_refresh = 0
        self.intervalo_refresh = 3.5
        self.ultimo_estiramiento_params = None

        self.color_sonrisa = (
            random.randint(80, 255),
            random.randint(20, 120),
            random.randint(120, 255),
            100   # alpha (ajustalo)
        )
        self.frase_teclado_actual = None
        self.momento_tecla = 0
        self.pos_teclado_actual = None
        self.text_img_teclado = None
        self.frases_teclado_activas = []
        self.tiempo_mostrar_teclado = 2.5

        self.ultimo_efecto_time = 0
        self.efecto_actual = None
        self.ultimo_centro_cara = None
        self.umbral_movimiento = 300

        # --- Para imágenes de experiencia ---
        self.todas_las_imagenes_data = cargar_imagenes_desde_carpeta("imagenes", cantidad=69)
        self.imagenes_maximas = 30
        self.imagenes_experiencia = []
        self.imagenes_mostradas = 0
        self.tiempo_inicio_imagenes = None
        self.prox_tiempo_imagen = 3
        self.intervalo_imagen_min = 3.5
        self.intervalo_imagen_max = 3.5
        self.sonriendo = False
        self.cara_detectada = False
        self.last_frame = None
        
    def inicializar_imagenes_experiencia(self, canvas_w, canvas_h, zona_prohibida):
        self.imagenes_experiencia = []
        posiciones_usadas = []
        for _ in range(self.imagenes_maximas):
            img_obj, img_id = seleccionar_imagen_aleatoria(
                self.todas_las_imagenes_data,
                self.machine.historial_imagenes_global,
                len(self.todas_las_imagenes_data)
            )
            if img_obj is None:
                continue
            img_obj_final = self.limitar_tamano(img_obj).rotate(0, expand=True)
            pos = elegir_posicion_fuera_de_cara_y_elementos(
                canvas_w, canvas_h, zona_prohibida, img_obj_final, posiciones_usadas
            )
            # Si no encontró lugar tras max_reintentos, busca SOLO evitar zona prohibida
            if pos is None:
                img_w, img_h = img_obj_final.size
                x0, y0, x1, y1 = zona_prohibida
                encontrado = False
                for _ in range(200):  # más intentos para evitar la zona prohibida
                    x = random.randint(0, max(0, canvas_w - img_w))
                    y = random.randint(0, max(0, canvas_h - img_h))
                    # chequea que NO toque la zona prohibida
                    if (x + img_w < x0 or x > x1 or y + img_h < y0 or y > y1):
                        pos = (x, y)
                        encontrado = True
                        break
                if not encontrado:
                    # Último recurso: pone en cualquier lado (puede tapar todo, muy raro)
                    pos = (
                        random.randint(0, max(0, canvas_w - img_w)),
                        random.randint(0, max(0, canvas_h - img_h))
                    )
            posiciones_usadas.append((pos[0], pos[1], img_obj_final.size[0], img_obj_final.size[1]))
            self.imagenes_experiencia.append((img_obj_final, pos, img_id))

        self.imagenes_mostradas = 0
        self.tiempo_inicio_imagenes = time.time()
        self.prox_tiempo_imagen = 5 + random.uniform(self.intervalo_imagen_min, self.intervalo_imagen_max)

    def limitar_tamano(self, imagen, max_size=280):
        w, h = imagen.size
        if w > max_size or h > max_size:
            escala = min(max_size / w, max_size / h)
            nuevo_tam = (int(w * escala), int(h * escala))
            return imagen.resize(nuevo_tam, Image.LANCZOS)
        return imagen

    def run(self):
        ahora = time.time()
        cap = self.machine.cap
        face_mesh = self.machine.face_mesh
        tiempo_transcurrido = time.time() - self.start_time
        aplicar_efectos = tiempo_transcurrido < 40.0 

        canvas_h, canvas_w = 864, 1536  # VERTICAL
        ret, frame = cap.read()
        if not ret:
            frame = 255 * np.ones((canvas_h, canvas_w, 3), dtype=np.uint8)
        else:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            frame = fill_and_center(frame, canvas_w, canvas_h)

        # --- Detección facial y flag de cara ---
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(img_rgb)
        zona_prohibida = self.zona_prohibida
        centro_cara_actual = None

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                lm = face_landmarks.landmark
                xs = [int(l.x * canvas_w) for l in lm]
                ys = [int(l.y * canvas_h) for l in lm]
                x0, x1 = max(min(xs) - 50, 0), min(max(xs) + 70, canvas_w)
                y0, y1 = max(min(ys) - 50, 0), min(max(ys) + 70, canvas_h)
                zona_prohibida = (x0, y0, x1, y1)
                centro_cara_actual = ((x0 + x1) // 2, (y0 + y1) // 2)
                self.zona_prohibida = zona_prohibida
                self.cara_detectada = True
                break
        else:
            self.cara_detectada = False

        # ------ ACÁ VA LA LÓGICA PARA RECOLOCAR SÓLO SI SE MUEVE ------
        recolocar = False
        if not hasattr(self, "ultimo_centro_cara") or self.ultimo_centro_cara is None or centro_cara_actual is None:
            self.ultimo_centro_cara = centro_cara_actual
            recolocar = True
        elif centro_cara_actual is not None and self.ultimo_centro_cara is not None:
            dx = centro_cara_actual[0] - self.ultimo_centro_cara[0]
            dy = centro_cara_actual[1] - self.ultimo_centro_cara[1]
            dist = (dx ** 2 + dy ** 2) ** 0.5
            if dist > getattr(self, "umbral_movimiento", 60):  # Ajustá el umbral si querés más sensible
                recolocar = True
                self.ultimo_centro_cara = centro_cara_actual

        # SOLO actualizar imágenes si hay cara Y SIEMPRE SI SE MUEVE
        if self.cara_detectada and recolocar and self.imagenes_experiencia and self.imagenes_mostradas > 0:
            posiciones_usadas = []
            nuevas_posiciones = []
            for img_obj, _, img_id in self.imagenes_experiencia[:self.imagenes_mostradas]:
                # PROBÁ MÁS REINTENTOS SI QUERÉS MAYOR SEGURIDAD
                nueva_pos = elegir_posicion_fuera_de_cara_y_elementos(
                    canvas_w, canvas_h, self.zona_prohibida, img_obj, posiciones_usadas, max_reintentos=250
                )
                if nueva_pos is None:
                    # Si NO encuentra lugar, poné la imagen en el rincón superior izquierdo o donde te guste, pero no sobre la cara
                    # Ejemplo: justo abajo del canvas, medio afuera
                    nueva_pos = (30, canvas_h - img_obj.height - 30)
                posiciones_usadas.append((nueva_pos[0], nueva_pos[1], img_obj.width, img_obj.height))
                nuevas_posiciones.append((img_obj, nueva_pos, img_id))
            # Actualizá solo los que ya están mostrándose
            for i in range(self.imagenes_mostradas):
                self.imagenes_experiencia[i] = nuevas_posiciones[i]

        if self.cara_detectada and not self.imagenes_experiencia and self.zona_prohibida is not None:
            self.inicializar_imagenes_experiencia(canvas_w, canvas_h, self.zona_prohibida)

        if self.cara_detectada and self.tiempo_inicio_imagenes is None:
            self.tiempo_inicio_imagenes = time.time()
        tiempo_actual = time.time() - self.tiempo_inicio_imagenes if self.tiempo_inicio_imagenes else 0
        if self.cara_detectada and (self.imagenes_mostradas < self.imagenes_maximas) and (tiempo_actual >= self.prox_tiempo_imagen):
            self.imagenes_mostradas += 1
            self.prox_tiempo_imagen += random.uniform(self.intervalo_imagen_min, self.intervalo_imagen_max)

        # --- PIL para composición visual
        pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")

        # Solo procesar emociones, efectos y frases si hay cara
        if self.cara_detectada and results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                lm = face_landmarks.landmark
                xs = [int(l.x * canvas_w) for l in lm]
                ys = [int(l.y * canvas_h) for l in lm]
                x0, x1 = max(min(xs) - 70, 0), min(max(xs) + 70, canvas_w)
                y0, y1 = max(min(ys) - 70, 0), min(max(ys) + 70, canvas_h)
                zona_prohibida = (x0, y0, x1, y1)

                # --- EMOCIONES ---
                if detectar_sonrisa(face_landmarks, frame.shape):
                    new_emotion = "sonrisa"
                    emotion_frases = frases_sonrisa
                    boca_indices = [
                        61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308,
                        324, 318, 402, 317, 14, 87, 178, 88, 95, 185, 40, 39, 37, 0,
                        267, 269, 270, 409, 415, 310, 311, 312, 13, 82, 81, 42, 183, 78
                    ]
                    puntos_boca = [
                        (int(face_landmarks.landmark[i].x * canvas_w), int(face_landmarks.landmark[i].y * canvas_h))
                        for i in boca_indices
                    ]
                    pil_img = overlay_boca_sonrisa(pil_img, puntos_boca, color=self.color_sonrisa)

                elif detectar_serio(face_landmarks, frame.shape):
                    new_emotion = "serio"
                    emotion_frases = frases_serio
                else:
                    new_emotion = None

                nueva_sonrisa = detectar_sonrisa(face_landmarks, frame.shape)
                if not hasattr(self, "sonriendo"):
                    self.sonriendo = False
                if nueva_sonrisa and not self.sonriendo and self.imagenes_mostradas < self.imagenes_maximas:
                    self.imagenes_mostradas += 1
                    self.prox_tiempo_imagen = tiempo_actual + random.uniform(self.intervalo_imagen_min, self.intervalo_imagen_max)
                self.sonriendo = nueva_sonrisa

                # --- EFECTOS VISUALES SOBRE LA CARA ---
                # --- EFECTOS VISUALES SOBRE LA CARA ---
                ex, ey, ew, eh = x0, y0, x1 - x0, y1 - y0
                from utilidades.utils import get_ojos_region, get_boca_region, get_nariz_region
                min_size = 50

                if aplicar_efectos:  # SOLO aplicar efectos si NO pasaron los 40s
                    if self.efecto_actual == aplicar_pixelate_region:
                        lado = random.choice(["derecho", "izquierdo"])
                        ex, ey, ew, eh = get_ojos_region(face_landmarks, canvas_w, canvas_h, lado)
                        if ew < min_size:
                            ex = max(ex - (min_size - ew) // 2, 0)
                            ew = min_size
                        if eh < min_size:
                            ey = max(ey - (min_size - eh) // 2, 0)
                            eh = min_size
                    elif self.efecto_actual == aplicar_blur_region:
                        ex, ey, ew, eh = get_nariz_region(face_landmarks, canvas_w, canvas_h)
                        if ew < min_size:
                            ex = max(ex - (min_size - ew) // 2, 0)
                            ew = min_size
                        if eh < min_size:
                            ey = max(ey - (min_size - eh) // 2, 0)
                            eh = min_size

                    ahora = time.time()
                    efectos_funciones = [
                        aplicar_zoom_region,
                        aplicar_split_face_desordenado,
                        aplicar_liquido_region,
                        aplicar_blur_region,
                        aplicar_pixelate_region,
                        generar_estiramiento
                    ]

                    if not hasattr(self, "estiramiento_params"):
                        self.estiramiento_params = None

                    if (self.efecto_actual is None) or (ahora - getattr(self, "ultimo_efecto_time", 0) > 4.0):
                        self.efecto_actual = random.choice(efectos_funciones)
                        self.ultimo_efecto_time = ahora
                       
                        if self.efecto_actual == aplicar_liquido_region:
                            self.lado_liquido = random.choice(["izquierda", "derecha"])
                        else:
                            self.lado_liquido = None
                        
                        # Solo cuando toca estiramiento, generá los params UNA vez
                        if self.efecto_actual.__name__ == "generar_estiramiento":
                            self.estiramiento_params = {
                                "horizontal": random.choice([True, False]),
                                "fuerza": random.uniform(1.18, 1.6)
                            }
                        else:
                            self.estiramiento_params = None

                    # Si querés hacer que el pixel/blur sea solo de un ojo o boca, acá ajustás
                    # 1. Inicializá frame_np SOLO una vez:
                    frame_np = np.array(pil_img)

                    # 2. Aplica el efecto SEGÚN cuál es:
                    if self.efecto_actual == aplicar_pixelate_region:
                        frame_np = aplicar_pixelate_region(frame_np, ex, ey, ew, eh, pixel_size=12)
                    elif self.efecto_actual == aplicar_liquido_region:
                        # Usá el lado que ya está guardado
                        lado = getattr(self, "lado_liquido", "izquierda")
                        if lado == "derecha":
                            ex_liq = ex + ew // 2
                            ew_liq = ew // 2
                        else:
                            ex_liq = ex
                            ew_liq = ew // 2
                        frame_np = self.efecto_actual(frame_np, ex_liq, ey, ew_liq, eh)
                    elif self.efecto_actual.__name__ == "generar_estiramiento":
                        params = getattr(self, "estiramiento_params", None)
                        if params is None:
                            params = {"horizontal": True, "fuerza": 1.3}
                        frame_np = self.efecto_actual(frame_np, ex, ey, ew, eh, params)
                    else:
                        # Otros efectos normales
                        frame_np = self.efecto_actual(frame_np, ex, ey, ew, eh)

                    pil_img = Image.fromarray(frame_np).convert("RGBA")

                # Si NO hay que aplicar efectos, NO hagas nada a la cara!


                # FRASES por emoción (igual que antes)
                if (
                    (new_emotion != self.last_emotion) or
                    (ahora - getattr(self, 'ultimo_refresh', 0) > getattr(self, 'intervalo_refresh', 2.5))
                ) and new_emotion and zona_prohibida is not None:
                    self.last_emotion = new_emotion
                    self.ultimo_refresh = ahora
                    self.frases_a_mostrar = []
                    frases = random.sample(emotion_frases, min(2, len(emotion_frases)))
                    posiciones_usadas = [
                        (x, y, img_obj.width, img_obj.height)
                        for img_obj, (x, y), _ in self.imagenes_experiencia[:self.imagenes_mostradas]
                    ]
                    for frase in frases:
                        font_path = random.choice(FUENTES_MEME)
                        color = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
                        text_img_rotated = generar_texto_vertical(frase, canvas_w, font_path=font_path, color=color, stroke=random.randint(0,5))
                        pos = elegir_posicion_fuera_de_cara_y_elementos(
                            canvas_w, canvas_h, zona_prohibida, text_img_rotated, posiciones_usadas
                        )
                        if pos is not None:
                            self.frases_a_mostrar.append((text_img_rotated, pos))
                            posiciones_usadas.append((pos[0], pos[1], text_img_rotated.width, text_img_rotated.height))

        # 6. Pegado de imágenes ROTADAS -90º
        for i in range(self.imagenes_mostradas):
            if i < len(self.imagenes_experiencia):
                img_obj, (x, y), img_id = self.imagenes_experiencia[i]
                rotated_img = self.limitar_tamano(img_obj).rotate(-90, expand=True)
                pil_img.paste(rotated_img, (x, y), rotated_img)

        # 7. Pegado de frases de reacción (después de imágenes)
        for text_img_rotated, (x, y) in getattr(self, "frases_a_mostrar", []):
            pil_img.paste(text_img_rotated, (x, y), text_img_rotated)

        # 8. Pegado de frases por teclado (si las usás)
        ahora = time.time()
        nuevas_frases_teclado = []
        for text_img, (x, y), t0 in getattr(self, "frases_teclado_activas", []):
            if ahora - t0 < self.tiempo_mostrar_teclado:
                pil_img.paste(text_img, (x, y), text_img)
                nuevas_frases_teclado.append((text_img, (x, y), t0))
        self.frases_teclado_activas = nuevas_frases_teclado

        # 9. Convertir a frame BGR para OpenCV
        frame = cv2.cvtColor(np.asarray(pil_img), cv2.COLOR_RGB2BGR)

        ids_mostrados = [img_id for _, _, img_id in self.imagenes_experiencia[:self.imagenes_mostradas]]
        for img_id in ids_mostrados:
            if img_id not in self.machine.historial_imagenes_global:
                self.machine.historial_imagenes_global.append(img_id)
        while len(self.machine.historial_imagenes_global) > 2 * self.imagenes_maximas:
            self.machine.historial_imagenes_global.pop(0)

        # 10. Estado final
        if time.time() - self.start_time > 40.0:
            from estados.estado_final import EstadoFinal

            # Tomá un frame limpio de cámara y orientalo como siempre
            ret, frame_clean = cap.read()
            if ret:
                frame_clean = cv2.rotate(frame_clean, cv2.ROTATE_90_CLOCKWISE)
                frame_clean = fill_and_center(frame_clean, canvas_w, canvas_h)
            else:
                frame_clean = frame  # Usá el frame actual si la cámara falla

            # Generá el frame final SIN efectos en la cara pero con overlays
            pil_frame_final = self.generar_frame_final(frame_clean, results, canvas_w, canvas_h)

            self.machine.change_state(EstadoFinal(self.machine, pil_frame_final))


        # --- CONGELADO VISUAL SI NO HAY CARA ---
        if not self.cara_detectada:
            if self.last_frame is not None:
                return self.last_frame
            else:
                self.last_frame = frame
                return frame
        else:
            self.last_frame = frame

        return frame

    def generar_frame_final(self, frame_base, resultados_face, canvas_w, canvas_h):
        """Genera el frame final sin efectos de cara, pero con frases e imágenes."""
        # Usá el último frame ya orientado y rescalado
        pil_img = Image.fromarray(cv2.cvtColor(frame_base, cv2.COLOR_BGR2RGB)).convert("RGBA")

        # Pegá imágenes y frases normalmente (igual que el final de tu run)
        for i in range(self.imagenes_mostradas):
            if i < len(self.imagenes_experiencia):
                img_obj, (x, y), img_id = self.imagenes_experiencia[i]
                rotated_img = self.limitar_tamano(img_obj).rotate(-90, expand=True)
                pil_img.paste(rotated_img, (x, y), rotated_img)

        for text_img_rotated, (x, y) in getattr(self, "frases_a_mostrar", []):
            pil_img.paste(text_img_rotated, (x, y), text_img_rotated)

        nuevas_frases_teclado = []
        ahora = time.time()
        for text_img, (x, y), t0 in getattr(self, "frases_teclado_activas", []):
            if ahora - t0 < self.tiempo_mostrar_teclado:
                pil_img.paste(text_img, (x, y), text_img)
                nuevas_frases_teclado.append((text_img, (x, y), t0))
        self.frases_teclado_activas = nuevas_frases_teclado

        # Convertí a PIL RGB (sin canal alfa)
        pil_frame_final = pil_img.convert("RGB")
        return pil_frame_final
    
    def reaccionar_tecla(self):
        frase = random.choice(frases_teclado)
        canvas_w, canvas_h = 1536, 864
        font_size = int(canvas_w * 0.055)
        font_path = r"C:\Users\bautista\AppData\Local\Microsoft\Windows\Fonts\MYRIADPRO-BOLD.OTF"
        color = (random.randint(0,100), 0, 0)
        from utilidades.utils import generar_texto_vertical
        text_img_rotated = generar_texto_vertical(frase, canvas_w, font_path=font_path, color=color, stroke=0)
        zona_prohibida = self.zona_prohibida if self.zona_prohibida is not None else (0,0,0,0)
        posiciones_usadas = [
            (x, y, img_obj.width, img_obj.height)
            for img_obj, (x, y), _ in self.imagenes_experiencia[:self.imagenes_mostradas]
        ]
        pos = elegir_posicion_fuera_de_cara_y_elementos(canvas_w, canvas_h, zona_prohibida, text_img_rotated, posiciones_usadas)
        if pos is not None:
            x, y = pos
        else:
            x, y = 60, (canvas_h - text_img_rotated.height) // 2
        self.frases_teclado_activas.append((text_img_rotated, (x, y), time.time()))

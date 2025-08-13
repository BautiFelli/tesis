import os
import random
import numpy as np
import cv2
import numpy as np
import math
from PIL import Image, ImageDraw
import random
from PIL import Image, ImageDraw, ImageFont


def crop_horizontal_to_portrait(frame, portrait_width=864, portrait_height=1536):
    h, w, _ = frame.shape
    scale = portrait_height / h
    new_w = int(w * scale)
    resized = cv2.resize(frame, (new_w, portrait_height))
    if new_w > portrait_width:
        x_start = (new_w - portrait_width) // 2
        cropped = resized[:, x_start:x_start+portrait_width]
    else:
        cropped = resized
    return cropped

def intersecan_rectangulos(rect1, rect2):
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2
    r1_x2, r1_y2 = x1 + w1, y1 + h1
    r2_x2, r2_y2 = x2 + w2, y2 + h2
    if x1 >= r2_x2 or x2 >= r1_x2:
        return False
    if y1 >= r2_y2 or y2 >= r1_y2:
        return False
    return True

def posicion_valida(cx_rostro, cy_rostro, tint_mask_ampliada, frame_width, frame_height, elem_width, elem_height, existing_elements, intentos=300, margen_separacion=20):
    if elem_width >= frame_width or elem_height >= frame_height:
        return None, None
    h_mask, w_mask = tint_mask_ampliada.shape
    for _ in range(intentos):
        x = random.randint(0, frame_width - elem_width)
        y = random.randint(0, frame_height - elem_height)
        x1_mask = max(0, x)
        y1_mask = max(0, y)
        x2_mask = min(w_mask, x + elem_width)
        y2_mask = min(h_mask, y + elem_height)
        if x2_mask <= x1_mask or y2_mask <= y1_mask:
            continue
        mask_region = tint_mask_ampliada[y1_mask:y2_mask, x1_mask:x2_mask]
        if np.any(mask_region):
            continue
        overlap = False
        for other in existing_elements:
            if (abs(x - other['x']) < other['width'] + margen_separacion) and (abs(y - other['y']) < other['height'] + margen_separacion):
                overlap = True
                break
        if overlap:
            continue
        return x, y
    return None, None




def fill_and_center(frame, output_w, output_h):
    h, w = frame.shape[:2]
    scale = max(output_w / w, output_h / h)  # Ahora usa max, no min
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized = cv2.resize(frame, (new_w, new_h))
    # Cropeo para que quede exactamente en el centro
    x0 = (new_w - output_w) // 2
    y0 = (new_h - output_h) // 2
    cropped = resized[y0:y0+output_h, x0:x0+output_w]
    return cropped
def distancia(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def detectar_sonrisa(face_landmarks, frame_shape):
    h, w = frame_shape[:2]

    # Landmarks para la boca (Mediapipe):
    # Esquinas de la boca: 61 (izq), 291 (der)
    # Centro boca arriba: 13, centro boca abajo: 14

    lm = face_landmarks.landmark

    izquierda = int(lm[61].x * w), int(lm[61].y * h)
    derecha = int(lm[291].x * w), int(lm[291].y * h)
    arriba = int(lm[13].x * w), int(lm[13].y * h)
    abajo = int(lm[14].x * w), int(lm[14].y * h)

    ancho_boca = distancia(izquierda, derecha)
    alto_boca = distancia(arriba, abajo)

    # Relación: boca ancha y relativamente abierta => sonrisa
    ratio = ancho_boca / (alto_boca + 1e-6)  # +1e-6 para evitar división por cero

    # Ajustá el threshold para tu cámara/condiciones
    return ratio > 2.2 and alto_boca > 22

def detectar_serio(face_landmarks, frame_shape):
    h, w = frame_shape[:2]
    lm = face_landmarks.landmark
    izquierda = int(lm[61].x * w), int(lm[61].y * h)
    derecha = int(lm[291].x * w), int(lm[291].y * h)
    arriba = int(lm[13].x * w), int(lm[13].y * h)
    abajo = int(lm[14].x * w), int(lm[14].y * h)
    ancho_boca = distancia(izquierda, derecha)
    alto_boca = distancia(arriba, abajo)
    ratio = ancho_boca / (alto_boca + 1e-6)
    # Threshold inverso: boca más cerrada y menos "ancha"
    return ratio < 1.8 or alto_boca < 15
import random

def elegir_posicion_fuera_de_cara_y_elementos(canvas_w, canvas_h, zona_prohibida, img_obj, posiciones_usadas, max_reintentos=80):
    # img_obj puede estar ya rotada y redimensionada acá
    img_w, img_h = img_obj.size
    x0, y0, x1, y1 = zona_prohibida
    w_ok = canvas_w - img_w
    h_ok = canvas_h - img_h
    if w_ok < 1 or h_ok < 1:
        return None
    for _ in range(max_reintentos):
        x = random.randint(0, w_ok)
        y = random.randint(0, h_ok)
        # No pisa zona prohibida
        no_pisa_cara = (x + img_w < x0 or x > x1 or y + img_h < y0 or y > y1)
        # No pisa otras imágenes/textos (chequea todos los usados hasta ahora)
        no_pisa_otro = all(
            (x + img_w < px or x > px + pw or y + img_h < py or y > py + ph)
            for (px, py, pw, ph) in posiciones_usadas
        )
        if no_pisa_cara and no_pisa_otro:
            return x, y
    # Si no encuentra espacio, arrincona en 30,30 igual (rara vez pasa)
    return None




def generar_fondo_pixelado(w=1536, h=864, block_size=32):
    base_color = (200, 215, 230)
    img = Image.new("RGB", (w, h), base_color)
    draw = ImageDraw.Draw(img)

    paleta = [
        (235, 250, 255),
        (220, 200, 255),
        (180, 210, 240),
        (205, 230, 220),
        (255, 240, 200),
        (210, 240, 200),
        (210, 210, 255),
        (255, 225, 240),
        (230, 240, 210)
    ]

    for y in range(0, h, block_size):
        for x in range(0, w, block_size):
            if random.random() < 0.55:
                color = random.choice(paleta)
                color = tuple(min(255, max(0, c + random.randint(-14, 14))) for c in color)
                draw.rectangle([x, y, x+block_size-1, y+block_size-1], fill=color)

    return img

def generar_texto_vertical(frase, canvas_w, font_path=None, font_size=None, color=None, stroke=0):
    if font_size is None:
        font_size = int(canvas_w * 0.035)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()
    text = frase
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    extra_margin = 80
    canvas_text_w = text_w + extra_margin
    canvas_text_h = text_h + extra_margin
    text_img = Image.new("RGBA", (canvas_text_w, canvas_text_h), (0,0,0,0))
    draw = ImageDraw.Draw(text_img)
    x_draw = (canvas_text_w - text_w) // 2
    y_draw = (canvas_text_h - text_h) // 2
    if color is None:
        color = (255,255,255)
    draw.text((x_draw, y_draw), text, font=font, fill=color)
    text_img_rotated = text_img.rotate(-90, expand=True)
    bbox_rotated = text_img_rotated.getbbox()
    text_img_rotated = text_img_rotated.crop(bbox_rotated)
    return text_img_rotated

# assets/efectos_visuales.py
from PIL import Image, ImageDraw

def overlay_boca_sonrisa(pil_img, puntos_boca, color=(0,255,0,65)):
    overlay = Image.new("RGBA", pil_img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    if len(puntos_boca) > 3:
        draw.polygon(puntos_boca, fill=color)
    return Image.alpha_composite(pil_img.convert("RGBA"), overlay)

def overlay_fruncir_ceja(pil_img, puntos_ceja, color=(255,0,0,40)):
    overlay = Image.new("RGBA", pil_img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    if len(puntos_ceja) > 2:
        draw.line(puntos_ceja, fill=color, width=12)
    return Image.alpha_composite(pil_img.convert("RGBA"), overlay)

# ...otros overlays/effects visuales
def get_ojos_region(face_landmarks, canvas_w, canvas_h, lado=None):
    # Si no se pasa lado, elegí random
    if lado is None:
        lado = random.choice(["izquierdo", "derecho"])
    indices = [33, 133, 159, 145, 153, 154, 155, 133] if lado == "derecho" else [362, 263, 387, 373, 380, 381, 382, 362]
    xs = [int(face_landmarks.landmark[i].x * canvas_w) for i in indices]
    ys = [int(face_landmarks.landmark[i].y * canvas_h) for i in indices]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    return x0, y0, x1 - x0, y1 - y0

def get_boca_region(face_landmarks, canvas_w, canvas_h):
    indices = [78, 308, 13, 14, 17, 0, 87, 317, 82, 312]
    xs = [int(face_landmarks.landmark[i].x * canvas_w) for i in indices]
    ys = [int(face_landmarks.landmark[i].y * canvas_h) for i in indices]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    return x0, y0, x1 - x0, y1 - y0

def cargar_imagenes_desde_carpeta(ruta_carpeta, cantidad=69, extension="png"):
    imagenes_data = []
    for i in range(cantidad):
        nombre = f"{i}.{extension}"
        ruta = os.path.join(ruta_carpeta, nombre)
        if os.path.exists(ruta):
            img_obj = Image.open(ruta).convert("RGBA")
            imagenes_data.append({"id": i, "img_obj": img_obj})
    return imagenes_data

def seleccionar_imagen_aleatoria(todas_las_imagenes_data, historial_recientes, historial_size):
    if not todas_las_imagenes_data:
        return None, None
    candidatas_disponibles = [img_data for img_data in todas_las_imagenes_data if img_data["id"] not in historial_recientes]
    if candidatas_disponibles:
        seleccionada = random.choice(candidatas_disponibles)
    else:
        seleccionada = random.choice(todas_las_imagenes_data)
    historial_recientes.append(seleccionada["id"])
    if len(historial_recientes) > historial_size:
        historial_recientes.pop(0)
    return seleccionada["img_obj"], seleccionada["id"]

def get_nariz_region(face_landmarks, canvas_w, canvas_h):
    indices = [1, 2, 98, 327, 195, 4, 5]
    xs = [int(face_landmarks.landmark[i].x * canvas_w) for i in indices]
    ys = [int(face_landmarks.landmark[i].y * canvas_h) for i in indices]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    return x0, y0, x1 - x0, y1 - y0


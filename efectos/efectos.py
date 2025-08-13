import cv2
import numpy as np
import math
import random

def aplicar_zoom_region(img, ex, ey, ew, eh):
    h, w = img.shape[:2]
    zx, zy = max(ex, 0), max(ey, 0)
    zw, zh = min(ew, w - zx), min(eh, h - zy)
    if zw < 5 or zh < 5:
        return img
    region = img[zy:zy+zh, zx:zx+zw].copy()
    zoom = 1.3
    new_w, new_h = int(zw * zoom), int(zh * zoom)
    region_zoom = cv2.resize(region, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    crop_x = (new_w - zw) // 2
    crop_y = (new_h - zh) // 2
    region_zoom = region_zoom[crop_y:crop_y+zh, crop_x:crop_x+zw]
    img[zy:zy+zh, zx:zx+zw] = region_zoom
    return img
    


def aplicar_liquido_region(frame, x, y, w, h, intensidad=6):
    x = max(0, x)
    y = max(0, y)
    w = min(w, frame.shape[1] - x)
    h = min(h, frame.shape[0] - y)
    sub_img = frame[y:y+h, x:x+w].copy()

    if w > 10 and h > 10:
        # Efecto liquido simple: onda senoidal en X
        for i in range(h):
            offset = int(intensidad * np.sin(2 * np.pi * i / 32))
            sub_img[i] = np.roll(sub_img[i], offset, axis=0)
        frame[y:y+h, x:x+w] = sub_img
    return frame

def aplicar_blur_region(frame, x, y, w, h, blur_ksize=51):
    x = max(0, x)
    y = max(0, y)
    w = min(w, frame.shape[1] - x)
    h = min(h, frame.shape[0] - y)
    sub_img = frame[y:y+h, x:x+w]
    if w > 2 and h > 2:
        blurred = cv2.GaussianBlur(sub_img, (blur_ksize, blur_ksize), 0)
        frame[y:y+h, x:x+w] = blurred
    return frame


def aplicar_split_face_desordenado(frame, ex, ey, ew, eh):
    region = frame[ey:ey+eh, ex:ex+ew].copy()
    h, w = region.shape[:2]
    mitad = w // 2
    # Ajusta las mitades por si el ancho es impar
    left = region[:, :mitad].copy()
    right = region[:, mitad:].copy()
    # Hace el swap solo sobre el tamaño más chico
    min_w = min(left.shape[1], right.shape[1])
    region[:, :min_w] = right[:, :min_w]
    region[:, min_w:min_w*2] = left[:, :min_w]
    # Pega de vuelta
    frame[ey:ey+eh, ex:ex+min_w] = region[:, :min_w]
    frame[ey:ey+eh, ex+min_w:ex+min_w*2] = region[:, min_w:min_w*2]
    return frame



def aplicar_pixelate_region(frame, x, y, w, h, pixel_size=12):
    # Clampeá los valores para evitar salirte del frame
    x = max(0, x)
    y = max(0, y)
    w = min(w, frame.shape[1] - x)
    h = min(h, frame.shape[0] - y)
    sub_img = frame[y:y+h, x:x+w]

    # Solo pixelar si el recorte tiene tamaño suficiente
    if sub_img.shape[0] > 2 and sub_img.shape[1] > 2:
        # Bajá la resolución
        small = cv2.resize(sub_img, (max(1, w // pixel_size), max(1, h // pixel_size)), interpolation=cv2.INTER_LINEAR)
        # Subí la resolución (esto es el pixelado!)
        pixelated = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
        frame[y:y+h, x:x+w] = pixelated
    return frame    # frame: np.ndarray BGR, lo paso a PIL
    #pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")

    if face_landmarks is None:
        return frame  # si no hay landmarks, devolvé igual

    # Indices landmarks
    ojo_indices = [33, 133, 159, 145, 153, 154, 155, 133]
    boca_indices = [78, 308, 13, 14, 17, 0, 87, 317, 82, 312]

    def get_bbox(indices):
        xs = [int(face_landmarks.landmark[i].x * canvas_w) for i in indices]
        ys = [int(face_landmarks.landmark[i].y * canvas_h) for i in indices]
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        return x0, y0, x1, y1

    ojo_box = get_bbox(ojo_indices)
    boca_box = get_bbox(boca_indices)
    ojo_img = pil_img.crop(ojo_box)
    boca_img = pil_img.crop(boca_box)

    boca_resized = boca_img.resize((ojo_box[2]-ojo_box[0], ojo_box[3]-ojo_box[1]))
    ojo_resized  = ojo_img.resize((boca_box[2]-boca_box[0], boca_box[3]-boca_box[1]))

    img_out = pil_img.copy()
    img_out.paste(boca_resized, (ojo_box[0], ojo_box[1]))
    img_out.paste(ojo_resized,  (boca_box[0], boca_box[1]))

    # Devolvé a np.ndarray BGR
    return cv2.cvtColor(np.array(img_out), cv2.COLOR_RGBA2BGR)


def detectar_sonrisa(face_landmarks, frame_width, frame_height, umbral_mar=0.42, umbral_ancho_boca=50):
    if not face_landmarks:
        return False
    left = face_landmarks.landmark[61]
    right = face_landmarks.landmark[291]
    top = face_landmarks.landmark[13]
    bottom = face_landmarks.landmark[14]
    dist_h = math.hypot((right.x - left.x) * frame_width, (right.y - left.y) * frame_height)
    dist_v = math.hypot((top.x - bottom.x) * frame_width, (top.y - bottom.y) * frame_height)
    if dist_h == 0:
        return False
    mar = dist_v / dist_h
    return mar < umbral_mar and dist_h > umbral_ancho_boca
# Colocá aquí tus funciones de efectos (zoom, blur, pixelate, etc)

def generar_estiramiento(frame_np, ex, ey, ew, eh, params):
    """
    Estira la región de la cara horizontal o verticalmente, según params.
    - frame_np: imagen numpy (H, W, 3)
    - ex, ey, ew, eh: bounding box de la ROI
    - params: dict con 'horizontal' (bool) y 'fuerza' (float)
    Devuelve frame_np con la región estirada.
    """
    # Seguridad en límites
    H, W = frame_np.shape[:2]
    ex = max(0, min(ex, W-1))
    ey = max(0, min(ey, H-1))
    ew = max(10, min(ew, W-ex))
    eh = max(10, min(eh, H-ey))
    
    roi = frame_np[ey:ey+eh, ex:ex+ew].copy()

    if params.get("horizontal", True):
        new_w = max(1, int(ew * params.get("fuerza", 1.35)))
        new_h = eh
    else:
        new_w = ew
        new_h = max(1, int(eh * params.get("fuerza", 1.35)))
    
    roi_estirada = cv2.resize(roi, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    
    # Si se pasa del tamaño original, recortá al canvas
    paste_x = max(0, ex - (new_w - ew) // 2)
    paste_y = max(0, ey - (new_h - eh) // 2)
    end_x = min(paste_x + new_w, W)
    end_y = min(paste_y + new_h, H)
    roi_crop = roi_estirada[:end_y-paste_y, :end_x-paste_x]

    # Pegalo de vuelta
    frame_result = frame_np.copy()
    frame_result[paste_y:end_y, paste_x:end_x] = roi_crop
    return frame_result

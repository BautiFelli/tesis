import os
import random
from PIL import Image, ImageDraw, ImageFont

FONDO_PATH = "assets/fondos"
FONT_PATH = r"C:\Users\bautista\AppData\Local\Microsoft\Windows\Fonts\Futura Bold.otf"

def generar_afiche_popart(screenshot, frase):
    

    # Paso seguro: convertí screenshot a RGB y "aplaná" por si tiene canal alfa residual
    if screenshot.mode != "RGB":
        screenshot = screenshot.convert("RGB")
    

    # Fondo SIEMPRE a RGB puro, sin canal alfa ni nada
    fondos = [f for f in os.listdir(FONDO_PATH) if f.endswith(".png")]
    fondo_file = random.choice(fondos)
    fondo = Image.open(os.path.join(FONDO_PATH, fondo_file))
    if fondo.mode != "RGB":
        fondo = fondo.convert("RGB")
    

    # Resizing screenshot
    w, h = fondo.size
    max_ancho = int(w * 0.72)
    max_alto = int(h * 0.65)
    if screenshot.width > screenshot.height:
        screenshot = screenshot.rotate(90, expand=True)
    escala = min(max_ancho / screenshot.width, max_alto / screenshot.height, 1.0)
    nuevo_tam = (int(screenshot.width * escala), int(screenshot.height * escala))
    screenshot = screenshot.resize(nuevo_tam, Image.LANCZOS)
    

    x_img = (w - screenshot.width) // 2
    y_img = int(h * 0.09)

    # Pegado seguro (sin máscara)
    fondo.paste(screenshot, (x_img, y_img))
    

    # Texto
    draw = ImageDraw.Draw(fondo)
    font_size = int(w * 0.08)
    min_margin = int(w * 0.08)  # margen mínimo a los costados

    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except:
        font = ImageFont.load_default()

    # Si la frase es DEMASIADO larga, reducí el tamaño hasta que entre
    frase_upper = frase.upper()
    font_size = int(w * 0.08)
    min_margin = int(w * 0.08)
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except:
        font = ImageFont.load_default()
    
    # Medida precisa con getbbox
    bbox = font.getbbox(frase_upper)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    max_text_w = w - 2 * min_margin

    while text_w > max_text_w and font_size > 12:
        font_size -= 2
        try:
            font = ImageFont.truetype(FONT_PATH, font_size)
        except:
            font = ImageFont.load_default()
        bbox = font.getbbox(frase_upper)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

    x_text = (w - text_w) // 2
    y_text = y_img + screenshot.height + int(h * 0.045)
    if y_text + text_h > h - int(h * 0.02):
        y_text = h - text_h - int(h * 0.02)

    # OPCIONAL DEBUG: dibujá un fondo amarillo para ver el área exacta
    # draw.rectangle([x_text, y_text, x_text + text_w, y_text + text_h], fill=(255,255,128))

    draw.text((x_text, y_text), frase_upper, font=font, fill=(255,255,255))

    
    return fondo.convert("RGB")

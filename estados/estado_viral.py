import time
import tempfile
import numpy as np
import cv2
from PIL import Image
import qrcode
from mastodon import Mastodon
from estados.estado_base import EstadoBase
from estados.estado_reiniciar import EstadoReiniciar

class EstadoViral(EstadoBase):
    def __init__(self, machine):
        super().__init__(machine)
        self.start_time = time.time()
        self.duracion = 10 # segundos que se muestra el QR antes de reiniciar
        self.qr_img = None
        self.posteado = False

        # Generar QR de inmediato
        self.qr_img = self.generar_pantalla_qr(1536, 864, "https://mastodon.social/@viralArtimanias")

    def generar_pantalla_qr(self, canvas_w, canvas_h, url):
        # Tamaño máximo posible del QR, manteniendo cuadrado
        max_qr_size = int(min(canvas_w, canvas_h) * 0.8)  # 80% del lado menor
        
        qr = qrcode.QRCode(
            version=3,
            box_size=10,
            border=4
        )
        qr.add_data(url)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="white", back_color="black").convert("RGB")

        # Escalar manteniendo cuadrado
        qr_img = qr_img.resize((max_qr_size, max_qr_size), Image.NEAREST)

        # Fondo negro del tamaño del canvas
        fondo = Image.new("RGB", (canvas_w, canvas_h), (0, 0, 0))

        # Centrar QR sin deformar
        x = (canvas_w - qr_img.width) // 2
        y = (canvas_h - qr_img.height) // 2
        fondo.paste(qr_img, (x, y))

        return fondo

    def post_to_mastodon(self, image_pil, text_caption):
        mastodon = Mastodon(
            access_token="76dY6u-k6VMlUEeTpk83p6Hl6GGzaW-3HhYQVjDZLHs",
            api_base_url="https://mastodon.social"
        )
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
            image_pil.save(tmpfile.name, format="PNG")
            media = mastodon.media_post(tmpfile.name, mime_type="image/png")
        mastodon.status_post(text_caption, media_ids=[media["id"]])

    def run(self):
        # Publicar en Mastodon solo una vez
        if not self.posteado and hasattr(self.machine, "afiches_generados") and self.machine.afiches_generados:
            afiche_data = self.machine.afiches_generados[-1]
            try:
                self.post_to_mastodon(afiche_data["img"], afiche_data["frase"])
            except Exception as e:
                print(f"Error publicando en Mastodon: {e}")
            self.posteado = True

        # Mostrar QR en pantalla
        frame = np.array(self.qr_img)
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame_rotated = cv2.rotate(frame_bgr, cv2.ROTATE_90_CLOCKWISE)

        # Pasar a EstadoReiniciar después de self.duracion segundos
        if time.time() - self.start_time > self.duracion:
            self.machine.change_state(EstadoReiniciar(self.machine))

        return frame_rotated

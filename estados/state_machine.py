import cv2
import mediapipe as mp
from estados.estado_inicio import EstadoInicio

from estados.estado_base import EstadoBase

class StateMachine:
    def __init__(self):
        self.running = True
        # --- Inicialización global de cámara y FaceMesh ---
        self.cap = cv2.VideoCapture(0)
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1, refine_landmarks=True
        )
        # --- Estado inicial ---
        self.state = EstadoInicio(self)
        self.window_initialized = False  # Para fullscreen solo una vez
        
        self.ultima_frase_meme = None
        
        self.historial_imagenes_global = []
        self.afiches_generados = []  

    def change_state(self, new_state):
        self.state = new_state

    def stop(self):
        self.running = False
    def run(self):
        while self.running:
            frame = self.state.run()
            if frame is not None:
                if not self.window_initialized:
                    cv2.namedWindow("Face Paint Demo", cv2.WND_PROP_FULLSCREEN)
                    cv2.setWindowProperty("Face Paint Demo", cv2.WINDOW_FULLSCREEN, 1)
                    self.window_initialized = True
                cv2.imshow("Face Paint Demo", frame)
                key = cv2.waitKey(1)
                self.state.handle_key(key)

                # Si el estado actual es EstadoExperiencia, llamá al método reaccionar_tecla para mostrar la frase
                from estados.estado_experiencia import EstadoExperiencia
                if isinstance(self.state, EstadoExperiencia):
                    # Ignoramos teclas especiales como -1 (sin tecla presionada)
                    if key not in [-1, 255]:  
                        self.state.reaccionar_tecla()
                # --- SOLO permití ESC en EstadoReiniciar ---
                from estados.estado_reiniciar import EstadoReiniciar
                if isinstance(self.state, EstadoReiniciar) and key == 27:
                    self.stop()
                    break
        # --- Liberar recursos ---
        self.cap.release()
        cv2.destroyAllWindows()
        self.face_mesh.close()

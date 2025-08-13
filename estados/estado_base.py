# estados/estado_base.py

class EstadoBase:
    def __init__(self, machine):
        self.machine = machine  # Referencia a la StateMachine principal

    def run(self):
        """
        Debe ser sobreescrito por cada estado.
        Ejecuta la lógica principal del estado.
        Retorna el frame que debe mostrarse en pantalla.
        """
        raise NotImplementedError

    def handle_key(self, key):
        """
        Método opcional para manejar teclas o eventos.
        Por defecto no hace nada.
        """
        pass

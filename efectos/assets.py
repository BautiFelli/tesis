import random

def obtener_zonas_cara(cx, cy, radio):
    return [
        ('ojo_izq', (cx - radio // 2, cy - radio // 3, radio // 2, radio // 2)),
        ('ojo_der', (cx + radio // 6, cy - radio // 3, radio // 2, radio // 2)),
        ('boca', (cx - radio // 4, cy + radio // 5, radio // 2, radio // 3)),
        ('frente', (cx - radio // 4, cy - radio // 2, radio // 2, radio // 3)),
    ]

def elegir_dos_zonas_distintas(zonas):
    z1 = random.choice(zonas)
    z2 = random.choice([z for z in zonas if z != z1])
    return z1, z2

def elegir_una_zona(zonas):
    return random.choice(zonas)
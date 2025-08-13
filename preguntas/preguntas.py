import random

preguntas_opciones_feedback = [
    {
        "pregunta": "¿Que buscas hoy?",
        "opciones": ["Divertirme/reírme", "Inspirarme", "Pasar el rato", "Nada en especial"],
        "feedback": {
            "Divertirme/reírme": ["yo me divierto con vos", "yo me voy a reir de vos", "vos sos el show"],
            "Inspirarme": ["", "chamuyerx sos", "linda, genix del arte"],
            "Pasar el rato": ["sos aburrido", "que bodrio"],
            "Nada en especial": ["nada especial, como vos", "tibix", "sos un plomo"]
        }
    },
    {
        "pregunta": "¿Qué esperas encontrar aca?",
        "opciones": ["Algo piola", "Vine a ver que onda", "Nada especial/nada bueno", "Nada"],
        "feedback": {
            "Algo piola": ["mira que bohemix", "ai que intelectual", "pretenciosx"],
            "Vine a ver que onda": ["venis a boludear", "te la jugaste, buenisimo"],
            "Nada especial/nada bueno": ["que fantasma", "nada bueno, como vos", "bajate un poco ", "claro, se te nota"],
            "Nada": ["ah re, banana", "ortiva mal", "nada pensas, como siempre"]
        }
    },
    {
        "pregunta": "¿Cómo andas hoy?",
        "opciones": ["Bien/Joya", "Tranqui", "Cansado/Bajón", "Meh/no sé"],
        "feedback": {
            "Bien/Joya": ["como te mentis eh", "no te vas a sentir bien aca"],
            "Tranqui": ["hasta ahora, espera", "que buena onda che"],
            "Cansado/Bajón": ["qué pesadx", "pobrecitx"],
            "Meh/no sé": ["sos re bala", "sacate la paja, dale"]
        }
    },
    {
        "pregunta": "¿Te copa la muestra?",
        "opciones": ["Sí", "No", "Mas o menos", "Me aburre"],
        "feedback": {
            "Sí": ["sos re COOL", "mira que cultx", "como te haces el snob"],
            "No": ["yo me voy a copar por vos", "mas rancix que vos no hay igual"],
            "Mas o menos": ["bien tibix", "gris, como vos"],
            "Me aburre": ["a ver si la levantas vos", "vos me aburris a mi", "que delicadx sos"]
        }
    }
]

def obtener_siguiente_pregunta(preguntas_disponibles, ultima_pregunta):
    preguntas_filtradas = [p for p in preguntas_disponibles if p["pregunta"] != ultima_pregunta]
    if not preguntas_filtradas:
        return random.choice(preguntas_disponibles)
    return random.choice(preguntas_filtradas)

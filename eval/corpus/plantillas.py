"""Plantillas de texto natural, por categoria, para el corpus de eval.

Cada plantilla es una lista de "partes": strings literales (texto que no
es PII) intercalados con tuplas `(tipo, valor)` (un tramo que SI es una
entidad sensible). `armar_muestra` concatena las partes y calcula el
`inicio`/`fin` de cada entidad AL MISMO TIEMPO que arma el texto -- nunca
con `texto.find(valor)` despues del hecho, porque si un valor apareciera
dos veces (o fuera substring de otro) el `find` podria encontrar la
posicion equivocada. Concatenar y contar sobre la marcha no tiene ese
problema: la posicion es exacta por construccion.
"""

import random

from faker import Faker

from eval.corpus import valores

TIPOS_CON_GENERADOR = {
    "NIT": valores.generar_nit,
    "RUT": valores.generar_rut,
    "CUIT_CUIL": valores.generar_cuit_cuil,
    "CURP": valores.generar_curp,
    "TARJETA_CREDITO": valores.generar_tarjeta_credito,
    "EMAIL": valores.generar_email,
    "TELEFONO": valores.generar_telefono,
    "NOMBRE_PERSONA": valores.generar_nombre_persona,
}

# Locale al que pertenece cada tipo de documento pais-especifico. Los tipos
# que no dependen de un pais (tarjeta, email, telefono, nombre) rotan entre
# todos los locales en español disponibles -- eso se decide en generar.py.
LOCALE_POR_TIPO_PAIS = {
    "NIT": "es_CO",
    "RUT": "es_CL",
    "CUIT_CUIL": "es_AR",
    "CURP": "es_MX",
}

TIPOS_SIN_PAIS_FIJO = ["TARJETA_CREDITO", "EMAIL", "TELEFONO", "NOMBRE_PERSONA"]


def armar_muestra(partes: list) -> tuple[str, list[dict]]:
    trozos_texto = []
    entidades = []
    cursor = 0
    for parte in partes:
        if isinstance(parte, tuple):
            tipo, valor = parte
            entidades.append(
                {"tipo": tipo, "inicio": cursor, "fin": cursor + len(valor), "valor": valor}
            )
            trozos_texto.append(valor)
            cursor += len(valor)
        else:
            trozos_texto.append(parte)
            cursor += len(parte)
    return "".join(trozos_texto), entidades


# ---------------------------------------------------------------------------
# Positivos claros: PII inequivoca en contexto natural.
# ---------------------------------------------------------------------------

_PLANTILLAS_POSITIVO_NIT = [
    lambda v: ["Buenas, mi NIT es ", ("NIT", v), " y necesito la factura electronica del pedido."],
    lambda v: ["Para el contrato, el NIT de la empresa es ", ("NIT", v), ", quedo atento."],
    lambda v: ["Adjunto el NIT ", ("NIT", v), " para que lo validen en el sistema tributario."],
    lambda v: ["¿Podrian confirmar si el NIT ", ("NIT", v), " ya esta registrado con ustedes?"],
]

_PLANTILLAS_POSITIVO_RUT = [
    lambda v: ["Mi RUT es ", ("RUT", v), ", lo necesito para la boleta electronica."],
    lambda v: ["El RUT de la empresa proveedora es ", ("RUT", v), ", por si lo requieren."],
    lambda v: ["Quedo con el RUT ", ("RUT", v), " registrado para el tramite del SII."],
    lambda v: ["Perdon, me equivoque: el RUT correcto es ", ("RUT", v), "."],
]

_PLANTILLAS_POSITIVO_CUIT_CUIL = [
    lambda v: ["El CUIT de la empresa es ", ("CUIT_CUIL", v), ", para la factura A."],
    lambda v: ["Mi CUIL es ", ("CUIT_CUIL", v), ", lo pueden usar para el recibo de sueldo."],
    lambda v: ["Confirmo el CUIT/CUIL ", ("CUIT_CUIL", v), " para el alta en AFIP."],
    lambda v: ["Necesito facturar a nombre del CUIT ", ("CUIT_CUIL", v), "."],
]

_PLANTILLAS_POSITIVO_CURP = [
    lambda v: ["Mi CURP es ", ("CURP", v), ", la necesito para el tramite del IMSS."],
    lambda v: ["Adjunto la CURP ", ("CURP", v), " para completar el registro."],
    lambda v: ["¿La CURP ", ("CURP", v), " ya quedo asociada a mi expediente?"],
    lambda v: ["Para la beca necesitan mi CURP: ", ("CURP", v), "."],
]

_PLANTILLAS_POSITIVO_TARJETA = [
    lambda v: ["Para pagar, mi numero de tarjeta es ", ("TARJETA_CREDITO", v), "."],
    lambda v: [
        "La tarjeta con la que quiero pagar termina distinto, es la ",
        ("TARJETA_CREDITO", v),
        ".",
    ],
    lambda v: ["Registren la tarjeta ", ("TARJETA_CREDITO", v), " como metodo de pago principal."],
    lambda v: ["Tuve un cargo raro en la tarjeta ", ("TARJETA_CREDITO", v), ", ¿pueden revisar?"],
]

_PLANTILLAS_POSITIVO_EMAIL = [
    lambda v: ["Mi correo es ", ("EMAIL", v), ", enviame la confirmacion ahi."],
    lambda v: ["Pueden escribirme a ", ("EMAIL", v), " con el resultado."],
    lambda v: ["El correo de contacto que dejaron es ", ("EMAIL", v), "."],
    lambda v: ["Actualiza mi correo registrado a ", ("EMAIL", v), ", por favor."],
]

_PLANTILLAS_POSITIVO_TELEFONO = [
    lambda v: ["Mi numero es ", ("TELEFONO", v), ", llamame cuando puedas."],
    lambda v: ["Pueden contactarme al ", ("TELEFONO", v), " despues de las 5pm."],
    lambda v: ["El telefono de emergencia que dejo es ", ("TELEFONO", v), "."],
    lambda v: ["Cambie de numero, el nuevo es ", ("TELEFONO", v), "."],
]

_PLANTILLAS_POSITIVO_NOMBRE = [
    lambda v: [
        "Hola, mi nombre es ",
        ("NOMBRE_PERSONA", v),
        " y tengo una consulta sobre mi pedido.",
    ],
    lambda v: ["El titular de la cuenta es ", ("NOMBRE_PERSONA", v), "."],
    lambda v: ["Quien firma el contrato es ", ("NOMBRE_PERSONA", v), ", por si necesitan el dato."],
    lambda v: ["Buenas tardes, habla ", ("NOMBRE_PERSONA", v), ", quisiera agendar una cita."],
]

_PLANTILLAS_POSITIVO_POR_TIPO = {
    "NIT": _PLANTILLAS_POSITIVO_NIT,
    "RUT": _PLANTILLAS_POSITIVO_RUT,
    "CUIT_CUIL": _PLANTILLAS_POSITIVO_CUIT_CUIL,
    "CURP": _PLANTILLAS_POSITIVO_CURP,
    "TARJETA_CREDITO": _PLANTILLAS_POSITIVO_TARJETA,
    "EMAIL": _PLANTILLAS_POSITIVO_EMAIL,
    "TELEFONO": _PLANTILLAS_POSITIVO_TELEFONO,
    "NOMBRE_PERSONA": _PLANTILLAS_POSITIVO_NOMBRE,
}


def generar_positivo_claro(tipo: str, fake: Faker) -> tuple[str, list[dict]]:
    valor = TIPOS_CON_GENERADOR[tipo](fake)
    plantilla = random.choice(_PLANTILLAS_POSITIVO_POR_TIPO[tipo])
    return armar_muestra(plantilla(valor))


# ---------------------------------------------------------------------------
# Negativos claros: texto sin ninguna PII.
# ---------------------------------------------------------------------------

_TEMAS_NEGATIVO_CLARO = [
    "¿Cual es la capital de Australia?",
    "Explicame la diferencia entre TCP y UDP con un ejemplo sencillo.",
    "Necesito una receta rapida de pasta para hoy en la noche.",
    "¿Como configuro un webhook en un repositorio de GitHub?",
    "Resume en tres puntos el ultimo informe trimestral de la empresa.",
    "¿Que libros recomiendas sobre arquitectura de software?",
    "Escribeme un correo formal para posponer una reunion de equipo.",
    "¿Cual es la mejor forma de aprender a tocar guitarra desde cero?",
    "Traduce esta frase al ingles: 'el proyecto sigue en construccion'.",
    "¿Que diferencia hay entre precision y recall en un modelo de clasificacion?",
    "Dame ideas para el nombre de un podcast sobre tecnologia y sociedad.",
    "¿Como se calcula el interes compuesto de un prestamo a tres años?",
    "Necesito un resumen del ultimo partido de la seleccion, no lo pude ver.",
    "¿Que plantas de interior sobreviven mejor con poca luz?",
    "Ayudame a planear un itinerario de tres dias en la costa.",
    "¿Cual es la version estable mas reciente de Python?",
    "Explica que es una arquitectura de microservicios en terminos simples.",
    "¿Que ejercicios recomiendas para el dolor de espalda baja?",
    "Escribeme un poema corto sobre el otoño.",
    "¿Como comprimo un archivo .tar.gz desde la terminal?",
]


def generar_negativo_claro(_fake: Faker) -> tuple[str, list[dict]]:
    texto = random.choice(_TEMAS_NEGATIVO_CLARO)
    return armar_muestra([texto])


# ---------------------------------------------------------------------------
# Negativos dificiles: lo que causa over-redaction. Numeros con formato de
# documento que NO son un documento de una persona, nombres de producto o
# empresa que se parecen a nombres propios.
# ---------------------------------------------------------------------------

_PLANTILLAS_NEGATIVO_DIFICIL = [
    lambda _fake: [
        "El numero de seguimiento del envio es ",
        f"{random.randint(100000000, 999999999)}-{random.randint(0,9)}",
        ", puedes rastrearlo en la pagina del transportista.",
    ],
    lambda _fake: [
        "El codigo de referencia de la orden de compra es ",
        f"{random.randint(10000000, 99999999)}-{random.choice('0123456789K')}",
        ".",
    ],
    lambda _fake: [
        "Lanzamos el nuevo producto ",
        random.choice(["Apollo", "Mercurio", "Vertice", "Nimbus", "Kairos"]),
        " la semana pasada, las ventas van bien.",
    ],
    lambda _fake: [
        "La empresa ",
        random.choice(["Andina Soluciones S.A.S.", "Norte Digital Ltda.", "Vertex Consultores"]),
        " nos hizo una propuesta interesante para el proyecto.",
    ],
    lambda _fake: [
        "El numero de ticket de soporte es #",
        str(random.randint(100000, 999999)),
        ", quedo pendiente de respuesta.",
    ],
    lambda _fake: [
        "La version del sistema que estamos corriendo es ",
        f"{random.randint(1,9)}.{random.randint(0,20)}.{random.randint(0,99)}",
        ", antes de actualizar hagamos el backup.",
    ],
    lambda _fake: [
        "El codigo postal de la bodega es ",
        str(random.randint(10000, 99999)),
        ", esta en la zona industrial.",
    ],
    lambda _fake: [
        "El folio interno del documento es ",
        f"F-{random.randint(1000,9999)}-{random.randint(0,9)}",
        ", archivalo con los demas de este mes.",
    ],
]


def generar_negativo_dificil(fake: Faker) -> tuple[str, list[dict]]:
    plantilla = random.choice(_PLANTILLAS_NEGATIVO_DIFICIL)
    return armar_muestra(plantilla(fake))


# ---------------------------------------------------------------------------
# Casos borde: PII en tablas, JSON, codigo, URLs.
# ---------------------------------------------------------------------------


def _caso_borde_tabla(tipo: str, valor: str) -> list:
    return [
        "| Campo | Valor |\n|---|---|\n| ",
        "Documento" if tipo != "NOMBRE_PERSONA" else "Titular",
        " | ",
        (tipo, valor),
        " |\n",
    ]


def _caso_borde_json(tipo: str, valor: str) -> list:
    clave = {
        "NIT": "nit",
        "RUT": "rut",
        "CUIT_CUIL": "cuit",
        "CURP": "curp",
        "TARJETA_CREDITO": "numero_tarjeta",
        "EMAIL": "correo",
        "TELEFONO": "telefono",
        "NOMBRE_PERSONA": "nombre",
    }[tipo]
    return ['{"', clave, '": "', (tipo, valor), '"}']


def _caso_borde_codigo(tipo: str, valor: str) -> list:
    return ['```python\ncliente = {\n    "', tipo.lower(), '": "', (tipo, valor), '",\n}\n```']


def _caso_borde_url(tipo: str, valor: str) -> list:
    return [
        "Revisa el registro en https://portal.interno.example.com/clientes?documento=",
        (tipo, valor),
        "&formato=json",
    ]


_CASOS_BORDE = [_caso_borde_tabla, _caso_borde_json, _caso_borde_codigo, _caso_borde_url]


def generar_caso_borde(tipo: str, fake: Faker) -> tuple[str, list[dict]]:
    valor = TIPOS_CON_GENERADOR[tipo](fake)
    constructor = random.choice(_CASOS_BORDE)
    return armar_muestra(constructor(tipo, valor))


# ---------------------------------------------------------------------------
# Multi-entidad: varias entidades del mismo tipo, o la misma entidad repetida.
# ---------------------------------------------------------------------------


def generar_multi_entidad_distinta(fake: Faker) -> tuple[str, list[dict]]:
    """Dos entidades del MISMO tipo, con valores distintos."""
    tipo = random.choice(list(TIPOS_CON_GENERADOR))
    valor_1 = TIPOS_CON_GENERADOR[tipo](fake)
    valor_2 = TIPOS_CON_GENERADOR[tipo](fake)
    etiqueta = "Documento" if tipo != "NOMBRE_PERSONA" else "Nombre"
    partes = [
        f"El titular original es {etiqueta.lower()} ",
        (tipo, valor_1),
        ", pero el nuevo titular es ",
        (tipo, valor_2),
        ". Actualicen el registro con ambos datos.",
    ]
    return armar_muestra(partes)


def generar_multi_entidad_repetida(fake: Faker) -> tuple[str, list[dict]]:
    """La MISMA entidad aparece dos veces en el texto -- ambas apariciones
    deben quedar etiquetadas, con sus propios offsets (no la misma posicion)."""
    tipo = random.choice(list(TIPOS_CON_GENERADOR))
    valor = TIPOS_CON_GENERADOR[tipo](fake)
    partes = [
        "Para confirmar, el dato que les envie antes es ",
        (tipo, valor),
        ". Repito por si no llego bien: ",
        (tipo, valor),
        ". Gracias por confirmar.",
    ]
    return armar_muestra(partes)


def generar_multi_entidad(fake: Faker) -> tuple[str, list[dict]]:
    generador = random.choice([generar_multi_entidad_distinta, generar_multi_entidad_repetida])
    return generador(fake)


# ---------------------------------------------------------------------------
# Ingles: subconjunto pequeño, mismo espiritu que los positivos en español.
# ---------------------------------------------------------------------------

_PLANTILLAS_INGLES_POR_TIPO = {
    "EMAIL": [
        lambda v: ["You can reach me at ", ("EMAIL", v), ", I'll reply within a day."],
        lambda v: ["Please update my contact email to ", ("EMAIL", v), "."],
    ],
    "TELEFONO": [
        lambda v: ["My phone number is ", ("TELEFONO", v), ", call anytime after 6pm."],
        lambda v: ["You can text me at ", ("TELEFONO", v), " if that's easier."],
    ],
    "NOMBRE_PERSONA": [
        lambda v: [
            "Hi, my name is ",
            ("NOMBRE_PERSONA", v),
            " and I have a question about my order.",
        ],
        lambda v: ["The account holder is ", ("NOMBRE_PERSONA", v), "."],
    ],
    "TARJETA_CREDITO": [
        lambda v: ["Please charge the card ", ("TARJETA_CREDITO", v), " for this month's invoice."],
        lambda v: ["I'd like to update my payment method to card ", ("TARJETA_CREDITO", v), "."],
    ],
}


TIPOS_CON_PLANTILLA_INGLES = list(_PLANTILLAS_INGLES_POR_TIPO)


def generar_ingles(tipo: str, fake: Faker) -> tuple[str, list[dict]]:
    valor = TIPOS_CON_GENERADOR[tipo](fake)
    plantilla = random.choice(_PLANTILLAS_INGLES_POR_TIPO[tipo])
    return armar_muestra(plantilla(valor))

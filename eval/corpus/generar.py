"""Genera eval/corpus/corpus.jsonl: el corpus etiquetado de TICKET-201.

Determinista: misma semilla, mismo corpus, siempre. Eso importa porque
`docs/metrics-log.md` va a comparar metricas ANTES/DESPUES de cambios en
fases futuras contra este mismo corpus -- si el corpus cambiara solo por
correr el generador de nuevo (o por una version distinta de Faker), esas
comparaciones dejarian de tener sentido.

Para regenerar (por ejemplo, si se agregan mas plantillas):

    python -m eval.corpus.generar

Esto SOBREESCRIBE eval/corpus/corpus.jsonl. El archivo resultante se
comitea al repo -- es el artefacto congelado el que usan los tests y el
arnes, no el generador.
"""

import itertools
import json
import random
from pathlib import Path

from faker import Faker

from eval.corpus import plantillas

SEMILLA = 20260211  # fecha arbitraria fija -- documentada para poder reproducirla a mano
LOCALES_ES = ["es_CO", "es_MX", "es_AR", "es_CL", "es_ES"]
RUTA_SALIDA = Path(__file__).parent / "corpus.jsonl"

TIPOS = list(plantillas.TIPOS_CON_GENERADOR)

CONTEO_POSITIVOS_POR_TIPO = {
    "NIT": 13,
    "RUT": 13,
    "CUIT_CUIL": 13,
    "CURP": 13,
    "TARJETA_CREDITO": 12,
    "EMAIL": 12,
    "TELEFONO": 12,
    "NOMBRE_PERSONA": 12,
}
TOTAL_NEGATIVOS_CLAROS = 50
TOTAL_NEGATIVOS_DIFICILES = 50
TOTAL_CASOS_BORDE = 40
TOTAL_MULTI_ENTIDAD = 40
TOTAL_INGLES = 20


class _Contador:
    """Numera las muestras de forma secuencial y estable para construir el `id`.

    Una clase minima en vez de una funcion con `nonlocal`: el estado (el
    contador) y la operacion que lo usa (armar el id) quedan juntos, sin
    depender de una variable capturada por closure.
    """

    def __init__(self) -> None:
        self._siguiente = 0

    def siguiente_id(self, categoria: str, tipo: str) -> str:
        self._siguiente += 1
        return f"{categoria}-{tipo.lower()}-{self._siguiente:04d}"


def generar_corpus() -> list[dict]:
    # Dos generadores de aleatoriedad distintos, dos semillas que fijar:
    # Faker.seed() solo controla lo que produce Faker (nombres, emails,
    # telefonos...); valores.py y plantillas.py llaman ademas al modulo
    # `random` de Python directamente (para el digito verificador y para
    # elegir plantilla), y ese generador global es independiente del de
    # Faker -- sin esta segunda linea, el corpus no era reproducible (se
    # detecto regenerandolo dos veces y comparando el archivo resultante).
    random.seed(SEMILLA)
    Faker.seed(SEMILLA)
    fakers = {locale: Faker(locale) for locale in [*LOCALES_ES, "en_US"]}
    rotador_locales = itertools.cycle(LOCALES_ES)
    contador = _Contador()
    muestras = []

    def agregar(categoria: str, tipo: str, locale: str, texto: str, entidades: list[dict]) -> None:
        muestras.append(
            {
                "id": contador.siguiente_id(categoria, tipo),
                "texto": texto,
                "categoria": categoria,
                "locale": locale,
                "entidades": entidades,
            }
        )

    for tipo, cantidad in CONTEO_POSITIVOS_POR_TIPO.items():
        locale_fijo = plantillas.LOCALE_POR_TIPO_PAIS.get(tipo)
        for _ in range(cantidad):
            locale = locale_fijo or next(rotador_locales)
            texto, entidades = plantillas.generar_positivo_claro(tipo, fakers[locale])
            agregar("positivo_claro", tipo, locale, texto, entidades)

    for _ in range(TOTAL_NEGATIVOS_CLAROS):
        locale = next(rotador_locales)
        texto, entidades = plantillas.generar_negativo_claro(fakers[locale])
        agregar("negativo_claro", "ninguno", locale, texto, entidades)

    for _ in range(TOTAL_NEGATIVOS_DIFICILES):
        locale = next(rotador_locales)
        texto, entidades = plantillas.generar_negativo_dificil(fakers[locale])
        agregar("negativo_dificil", "ninguno", locale, texto, entidades)

    for i in range(TOTAL_CASOS_BORDE):
        tipo = TIPOS[i % len(TIPOS)]
        locale = plantillas.LOCALE_POR_TIPO_PAIS.get(tipo) or next(rotador_locales)
        texto, entidades = plantillas.generar_caso_borde(tipo, fakers[locale])
        agregar("caso_borde", tipo, locale, texto, entidades)

    for _ in range(TOTAL_MULTI_ENTIDAD):
        locale = next(rotador_locales)
        texto, entidades = plantillas.generar_multi_entidad(fakers[locale])
        agregar("multi_entidad", "vario", locale, texto, entidades)

    tipos_ingles = plantillas.TIPOS_CON_PLANTILLA_INGLES
    for i in range(TOTAL_INGLES):
        tipo = tipos_ingles[i % len(tipos_ingles)]
        texto, entidades = plantillas.generar_ingles(tipo, fakers["en_US"])
        agregar("ingles", tipo, "en_US", texto, entidades)

    return muestras


def escribir_corpus(muestras: list[dict], ruta: Path = RUTA_SALIDA) -> None:
    with ruta.open("w", encoding="utf-8") as archivo:
        for muestra in muestras:
            archivo.write(json.dumps(muestra, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    muestras = generar_corpus()
    escribir_corpus(muestras)
    print(f"Generadas {len(muestras)} muestras en {RUTA_SALIDA}")

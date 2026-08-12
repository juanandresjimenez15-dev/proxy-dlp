"""Test de TICKET-202: el arnes de medicion mismo, con resultados conocidos.

"Un arnes con un bug te miente durante todo el proyecto" (PLAN.md). Se
prueba con tres detectores de juguete cuyo comportamiento se conoce de
antemano, sobre un set de muestras chico y a mano (no el corpus real de
300 -- asi el resultado esperado se puede calcular en la cabeza y
verificar exacto, sin depender de que el corpus no cambie).
"""

import pytest

from eval.harness.metricas import percentil
from eval.harness.run import correr_arnes

MUESTRAS_JUGUETE = [
    {
        "id": "m1",
        "texto": "Mi NIT es 900123456-7, gracias.",
        "categoria": "positivo_claro",
        "locale": "es_CO",
        "entidades": [{"tipo": "NIT", "inicio": 10, "fin": 21, "valor": "900123456-7"}],
    },
    {
        "id": "m2",
        "texto": "Hola, ¿como estas hoy?",
        "categoria": "negativo_claro",
        "locale": "es_CO",
        "entidades": [],
    },
    {
        "id": "m3",
        "texto": "El codigo de seguimiento es 555444333-2.",
        "categoria": "negativo_dificil",
        "locale": "es_CO",
        "entidades": [],
    },
    {
        "id": "m4",
        "texto": "El folio interno es F-1234-5.",
        "categoria": "negativo_dificil",
        "locale": "es_CO",
        "entidades": [],
    },
    {
        "id": "m5",
        "texto": "Mi correo es a@example.com, el de mi hermana es b@example.com.",
        "categoria": "multi_entidad",
        "locale": "es_CO",
        "entidades": [
            {"tipo": "EMAIL", "inicio": 11, "fin": 26, "valor": "a@example.com"},
            {"tipo": "EMAIL", "inicio": 44, "fin": 59, "valor": "b@example.com"},
        ],
    },
    {
        "id": "m6",
        "texto": "Mi correo es c@example.com.",
        "categoria": "positivo_claro",
        "locale": "es_CO",
        "entidades": [{"tipo": "EMAIL", "inicio": 12, "fin": 26, "valor": "c@example.com"}],
    },
]

TOTAL_ENTIDADES_REALES = 4  # 1 (m1) + 0 + 0 + 0 + 2 (m5) + 1 (m6)
TOTAL_NEGATIVOS_DIFICILES = 2  # m3, m4


def _mapa_texto_a_entidades() -> dict[str, list[dict]]:
    return {muestra["texto"]: muestra["entidades"] for muestra in MUESTRAS_JUGUETE}


def _detector_perfecto(texto: str) -> list[dict]:
    return _mapa_texto_a_entidades()[texto]


def _detector_que_no_detecta_nada(_texto: str) -> list[dict]:
    return []


def _detector_que_marca_todo(texto: str) -> list[dict]:
    # Un solo span "comodin" que cubre el texto completo -- por diseno de
    # las muestras de juguete, ninguna entidad real empieza en 0 y termina
    # en len(texto), asi que este span NUNCA coincide exactamente con una
    # entidad real: fuerza precision y recall a 0 de forma predecible.
    return [{"tipo": "COMODIN", "inicio": 0, "fin": len(texto)}]


@pytest.mark.unit
def test_detector_perfecto_da_metricas_perfectas():
    resultado = correr_arnes(_detector_perfecto, MUESTRAS_JUGUETE)

    assert resultado["global"] == {
        "tp": TOTAL_ENTIDADES_REALES,
        "fp": 0,
        "fn": 0,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0,
    }
    assert resultado["over_redaction"] == 0.0
    assert resultado["por_tipo"]["NIT"]["tp"] == 1
    assert resultado["por_tipo"]["EMAIL"]["tp"] == 3


@pytest.mark.unit
def test_detector_que_no_detecta_nada():
    resultado = correr_arnes(_detector_que_no_detecta_nada, MUESTRAS_JUGUETE)

    assert resultado["global"] == {
        "tp": 0,
        "fp": 0,
        "fn": TOTAL_ENTIDADES_REALES,
        "precision": 1.0,  # convencion documentada en metricas.py: sin predicciones, precision 1.0
        "recall": 0.0,
        "f1": 0.0,
    }
    assert resultado["over_redaction"] == 0.0


@pytest.mark.unit
def test_detector_que_marca_todo():
    resultado = correr_arnes(_detector_que_marca_todo, MUESTRAS_JUGUETE)

    assert resultado["global"] == {
        "tp": 0,
        "fp": len(MUESTRAS_JUGUETE),  # una prediccion equivocada por muestra
        "fn": TOTAL_ENTIDADES_REALES,
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
    }
    # Marca TODO, asi que los dos negativos dificiles quedan marcados: 100%.
    assert resultado["over_redaction"] == 1.0


@pytest.mark.unit
def test_percentil_con_valores_conocidos():
    valores = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert percentil(valores, 0) == 10.0
    assert percentil(valores, 50) == 30.0
    assert percentil(valores, 100) == 50.0


@pytest.mark.unit
def test_percentil_de_lista_vacia_es_cero():
    assert percentil([], 50) == 0.0


@pytest.mark.unit
def test_arnes_mide_latencia_no_negativa():
    resultado = correr_arnes(_detector_perfecto, MUESTRAS_JUGUETE)
    for percentil_nombre in ("p50", "p95", "p99"):
        assert resultado["latencia_segundos"][percentil_nombre] >= 0.0

"""Tests de TICKET-203: el baseline solo-regex.

No busca igualar las metricas del corpus completo (eso vive en
docs/metrics-log.md) -- verifica el comportamiento basico de cada patron
por separado, con ejemplos chicos y a mano, y los casos negativos
explicitos (texto vacio, texto sin nada de PII).
"""

import pytest

from eval.harness.baseline_regex import detectar


def _tipos_detectados(texto: str) -> set[str]:
    return {entidad["tipo"] for entidad in detectar(texto)}


@pytest.mark.unit
@pytest.mark.parametrize(
    ("texto", "tipo_esperado"),
    [
        ("Mi NIT es 900123456-7.", "NIT"),
        ("Mi RUT es 12345678-9.", "RUT"),
        ("El CUIT es 20-12345678-9.", "CUIT_CUIL"),
        ("La CURP es GOMJ800101HDFRRN09.", "CURP"),
        ("La tarjeta es 4532148803436467.", "TARJETA_CREDITO"),
        ("Mi correo es persona@example.com.", "EMAIL"),
        ("Llamame al +57 300 123 4567.", "TELEFONO"),
    ],
)
def test_detecta_cada_tipo_en_un_ejemplo_basico(texto, tipo_esperado):
    assert tipo_esperado in _tipos_detectados(texto)


@pytest.mark.unit
def test_no_detecta_nombre_de_persona():
    """Limitacion reconocida a proposito (ver docstring del modulo): un
    regex no tiene forma de reconocer un nombre. Este test documenta esa
    limitacion como comportamiento esperado, no como bug pendiente."""
    assert detectar("Hola, mi nombre es Juan Andres Jimenez.") == []


@pytest.mark.unit
def test_texto_sin_pii_no_devuelve_nada():
    assert detectar("¿Cual es la capital de Australia?") == []


@pytest.mark.unit
def test_texto_vacio_no_falla():
    assert detectar("") == []


@pytest.mark.unit
def test_cada_entidad_tiene_el_valor_correspondiente_al_span():
    texto = "Mi correo es persona@example.com, gracias."
    for entidad in detectar(texto):
        assert texto[entidad["inicio"] : entidad["fin"]] == entidad["valor"]

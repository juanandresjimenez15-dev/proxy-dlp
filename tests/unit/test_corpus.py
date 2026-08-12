"""Tests de TICKET-201: el corpus etiquetado mismo, no el detector.

"El instrumento de medicion tambien se testea" (CLAUDE.md, seccion 2.1) --
un corpus con offsets mal calculados miente durante toda la Fase 2 y la
Fase 3, porque el arnes (TICKET-202) va a confiar ciegamente en que
`texto[inicio:fin] == valor`. Este archivo es la unica linea de defensa
para eso.

No regenera el corpus (eso corre aparte, `python -m eval.corpus.generar`)
-- lee el archivo ya comiteado, que es el artefacto que usa el resto del
proyecto.
"""

import json
from pathlib import Path

import pytest

RUTA_CORPUS = Path(__file__).resolve().parents[2] / "eval" / "corpus" / "corpus.jsonl"

TIPOS_EN_ALCANCE = {
    "NIT",
    "RUT",
    "CUIT_CUIL",
    "CURP",
    "TARJETA_CREDITO",
    "EMAIL",
    "TELEFONO",
    "NOMBRE_PERSONA",
}


def _cargar_corpus() -> list[dict]:
    with RUTA_CORPUS.open(encoding="utf-8") as archivo:
        return [json.loads(linea) for linea in archivo]


@pytest.fixture(scope="module")
def corpus() -> list[dict]:
    return _cargar_corpus()


@pytest.mark.unit
def test_el_corpus_existe_y_no_esta_vacio(corpus):
    assert len(corpus) > 0


@pytest.mark.unit
def test_composicion_minima(corpus):
    # El ticket pide ~300 muestras como minimo, no como objetivo exacto.
    assert len(corpus) >= 300


@pytest.mark.unit
def test_ids_unicos(corpus):
    ids = [muestra["id"] for muestra in corpus]
    assert len(ids) == len(set(ids)), "hay ids repetidos en el corpus"


@pytest.mark.unit
def test_cada_muestra_tiene_los_campos_requeridos(corpus):
    campos_requeridos = {"id", "texto", "categoria", "locale", "entidades"}
    for muestra in corpus:
        assert campos_requeridos.issubset(muestra.keys()), muestra["id"]


@pytest.mark.unit
def test_los_spans_de_entidades_coinciden_con_el_texto(corpus):
    """El test central de este archivo: si esto falla, cualquier metrica
    calculada sobre el corpus (recall, precision, over-redaction) es sospechosa,
    porque el arnes compara posiciones, no solo valores (ver TICKET-202)."""
    for muestra in corpus:
        texto = muestra["texto"]
        for entidad in muestra["entidades"]:
            inicio, fin, valor = entidad["inicio"], entidad["fin"], entidad["valor"]
            fragmento = texto[inicio:fin]
            assert fragmento == valor, (
                f"{muestra['id']}: texto[{inicio}:{fin}] = {fragmento!r}, "
                f"pero la entidad dice valor={valor!r}"
            )


@pytest.mark.unit
def test_tipos_de_entidad_estan_dentro_del_alcance(corpus):
    """Ningun tipo fuera de la tabla de la seccion 5 de PLAN.md -- si aparece
    uno nuevo, es que se amplio el alcance sin la decision explicita que
    CLAUDE.md exige (seccion 2.2)."""
    tipos_presentes = {entidad["tipo"] for muestra in corpus for entidad in muestra["entidades"]}
    assert tipos_presentes.issubset(TIPOS_EN_ALCANCE)


@pytest.mark.unit
def test_los_ocho_tipos_del_alcance_tienen_al_menos_una_muestra(corpus):
    tipos_presentes = {entidad["tipo"] for muestra in corpus for entidad in muestra["entidades"]}
    faltantes = TIPOS_EN_ALCANCE - tipos_presentes
    assert not faltantes, f"tipos sin ninguna muestra en el corpus: {faltantes}"


@pytest.mark.unit
def test_categorias_esperadas_estan_representadas(corpus):
    categorias_esperadas = {
        "positivo_claro",
        "negativo_claro",
        "negativo_dificil",
        "caso_borde",
        "multi_entidad",
        "ingles",
    }
    categorias_presentes = {muestra["categoria"] for muestra in corpus}
    assert categorias_esperadas.issubset(categorias_presentes)


@pytest.mark.unit
def test_negativos_no_tienen_entidades_etiquetadas(corpus):
    for muestra in corpus:
        if muestra["categoria"] in ("negativo_claro", "negativo_dificil"):
            assert muestra["entidades"] == [], muestra["id"]


@pytest.mark.unit
def test_multi_entidad_tiene_mas_de_una_entidad(corpus):
    muestras_multi = [m for m in corpus if m["categoria"] == "multi_entidad"]
    assert muestras_multi, "no hay muestras de categoria multi_entidad"
    for muestra in muestras_multi:
        assert len(muestra["entidades"]) >= 2, muestra["id"]


@pytest.mark.unit
def test_hay_muestras_en_ingles(corpus):
    idioma_ingles = [m for m in corpus if m["categoria"] == "ingles"]
    assert len(idioma_ingles) > 0
    assert all(m["locale"] == "en_US" for m in idioma_ingles)

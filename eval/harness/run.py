"""Arnes de medicion: TICKET-202.

Corre un detector sobre el corpus etiquetado (TICKET-201) y calcula
precision/recall/F1 (global y por tipo de entidad), tasa de
over-redaction, y latencia p50/p95/p99. La logica de comparacion vive en
`metricas.py`, deliberadamente separada de este archivo, para poder
testearla sin depender de I/O ni de un detector real.

Todavia no existe un detector de verdad (eso empieza en TICKET-301, Fase
3) -- por eso `correr_arnes` recibe el detector como parametro en vez de
importarlo fijo: cualquier funcion con la forma `texto: str ->
list[dict]` sirve, incluidos los detectores de juguete que usan los
tests de este mismo ticket.

Uso desde la linea de comandos, una vez que exista un detector real:

    python -m eval.harness.run eval.harness.baseline_regex:detectar

`detector` es `modulo:funcion` -- se importa dinamicamente, asi que este
script no necesita cambiar cuando la Fase 3 agregue el detector real.
"""

import argparse
import importlib
import json
import time
from collections.abc import Callable
from pathlib import Path

from eval.harness import metricas

Detector = Callable[[str], list[dict]]

RUTA_CORPUS_POR_DEFECTO = Path(__file__).resolve().parents[1] / "corpus" / "corpus.jsonl"
RUTA_SALIDA_JSON = Path(__file__).parent / "ultimo_resultado.json"
RUTA_SALIDA_MD = Path(__file__).parent / "ultimo_resultado.md"


def cargar_corpus(ruta: Path = RUTA_CORPUS_POR_DEFECTO) -> list[dict]:
    with ruta.open(encoding="utf-8") as archivo:
        return [json.loads(linea) for linea in archivo]


def correr_arnes(detector: Detector, muestras: list[dict]) -> dict:
    predicciones: dict[str, list[dict]] = {}
    latencias: list[float] = []

    for muestra in muestras:
        inicio = time.perf_counter()
        predicciones[muestra["id"]] = detector(muestra["texto"])
        latencias.append(time.perf_counter() - inicio)

    conteos_por_tipo = metricas.calcular_conteos(muestras, predicciones)
    metricas_por_tipo = {
        tipo: metricas.precision_recall_f1(**conteo) for tipo, conteo in conteos_por_tipo.items()
    }

    tp_total = sum(c["tp"] for c in conteos_por_tipo.values())
    fp_total = sum(c["fp"] for c in conteos_por_tipo.values())
    fn_total = sum(c["fn"] for c in conteos_por_tipo.values())
    metricas_globales = metricas.precision_recall_f1(tp_total, fp_total, fn_total)

    return {
        "n_muestras": len(muestras),
        "global": metricas_globales,
        "por_tipo": metricas_por_tipo,
        "over_redaction": metricas.calcular_over_redaction(muestras, predicciones),
        "latencia_segundos": {
            "p50": metricas.percentil(latencias, 50),
            "p95": metricas.percentil(latencias, 95),
            "p99": metricas.percentil(latencias, 99),
        },
    }


def formatear_markdown(resultado: dict) -> str:
    lineas = [
        f"# Resultado del arnes ({resultado['n_muestras']} muestras)",
        "",
        "## Global",
        "",
        "| Precision | Recall | F1 | TP | FP | FN |",
        "|---|---|---|---|---|---|",
        (
            f"| {resultado['global']['precision']:.3f} "
            f"| {resultado['global']['recall']:.3f} "
            f"| {resultado['global']['f1']:.3f} "
            f"| {resultado['global']['tp']} "
            f"| {resultado['global']['fp']} "
            f"| {resultado['global']['fn']} |"
        ),
        "",
        "## Por tipo de entidad",
        "",
        "| Tipo | Precision | Recall | F1 | TP | FP | FN |",
        "|---|---|---|---|---|---|---|",
    ]
    for tipo, metrica in sorted(resultado["por_tipo"].items()):
        lineas.append(
            f"| {tipo} | {metrica['precision']:.3f} | {metrica['recall']:.3f} "
            f"| {metrica['f1']:.3f} | {metrica['tp']} | {metrica['fp']} | {metrica['fn']} |"
        )
    lineas += [
        "",
        "## Over-redaction y latencia",
        "",
        "| Over-redaction | Latencia p50 | Latencia p95 | Latencia p99 |",
        "|---|---|---|---|",
        (
            f"| {resultado['over_redaction']:.1%} "
            f"| {resultado['latencia_segundos']['p50'] * 1000:.2f} ms "
            f"| {resultado['latencia_segundos']['p95'] * 1000:.2f} ms "
            f"| {resultado['latencia_segundos']['p99'] * 1000:.2f} ms |"
        ),
        "",
    ]
    return "\n".join(lineas)


def escribir_resultado(
    resultado: dict, ruta_json: Path = RUTA_SALIDA_JSON, ruta_md: Path = RUTA_SALIDA_MD
) -> None:
    ruta_json.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    ruta_md.write_text(formatear_markdown(resultado), encoding="utf-8")


def _importar_detector(referencia: str) -> Detector:
    modulo_nombre, _separador, funcion_nombre = referencia.partition(":")
    if not _separador:
        raise ValueError(f"formato esperado 'modulo:funcion', recibido: {referencia!r}")
    modulo = importlib.import_module(modulo_nombre)
    return getattr(modulo, funcion_nombre)


def main() -> None:
    parser = argparse.ArgumentParser(description="Corre el arnes de medicion sobre el corpus.")
    parser.add_argument(
        "detector",
        help=(
            "referencia 'modulo:funcion' del detector a evaluar, "
            "ej. eval.harness.baseline_regex:detectar"
        ),
    )
    parser.add_argument("--corpus", type=Path, default=RUTA_CORPUS_POR_DEFECTO)
    args = parser.parse_args()

    detector = _importar_detector(args.detector)
    muestras = cargar_corpus(args.corpus)
    resultado = correr_arnes(detector, muestras)
    escribir_resultado(resultado)
    print(formatear_markdown(resultado))


if __name__ == "__main__":
    main()

"""Calculo de metricas del arnes: TICKET-202.

Todo aqui es logica PURA (nada de I/O, nada de llamar al detector) para
que se pueda testear con datos de juguete y resultados conocidos -- "el
instrumento de medicion tambien se testea" (CLAUDE.md, seccion 2.1).

Decision de diseno (confirmada explicitamente, no asumida): coincidencia
EXACTA de span. Una entidad predicha cuenta como acierto solo si su
`tipo`, `inicio` y `fin` son identicos a los de una entidad real -- un
detector que encuentra el NIT correcto pero con un espacio de mas en el
span cuenta como fallo. La alternativa (solapamiento con umbral) es mas
indulgente pero obliga a definir un umbral arbitrario y una logica de
emparejamiento greedy para no contar el mismo acierto dos veces; la
coincidencia exacta resuelve eso gratis, incluso el caso de dos entidades
del mismo tipo y valor en el mismo texto (categoria `multi_entidad`):
como sus posiciones son distintas, sus claves (tipo, inicio, fin) tambien
lo son, y no hay ambiguedad de cual predicha corresponde a cual real.
"""

from collections import defaultdict


def _clave(entidad: dict) -> tuple:
    return (entidad["tipo"], entidad["inicio"], entidad["fin"])


def comparar_entidades(
    entidades_reales: list[dict], entidades_predichas: list[dict]
) -> tuple[set[tuple], set[tuple], set[tuple]]:
    """Compara las entidades de UNA muestra. Devuelve (verdaderos_positivos,
    falsos_positivos, falsos_negativos), cada uno un set de claves
    `(tipo, inicio, fin)`.

    Usar un set (en vez de, por ejemplo, restar listas) es seguro porque
    dentro de una misma muestra dos entidades nunca pueden compartir
    exactamente la misma clave: el corpus las genera con un cursor que
    avanza estrictamente (ver `eval/corpus/plantillas.py::armar_muestra`),
    asi que dos entidades reales siempre tienen offsets distintos.
    """
    claves_reales = {_clave(e) for e in entidades_reales}
    claves_predichas = {_clave(e) for e in entidades_predichas}
    verdaderos_positivos = claves_reales & claves_predichas
    falsos_positivos = claves_predichas - claves_reales
    falsos_negativos = claves_reales - claves_predichas
    return verdaderos_positivos, falsos_positivos, falsos_negativos


def calcular_conteos(muestras: list[dict], predicciones: dict[str, list[dict]]) -> dict[str, dict]:
    """TP/FP/FN, desglosados por tipo de entidad, sumando sobre todas las muestras."""
    conteos = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    for muestra in muestras:
        verdaderos_positivos, falsos_positivos, falsos_negativos = comparar_entidades(
            muestra["entidades"], predicciones[muestra["id"]]
        )
        for tipo, _inicio, _fin in verdaderos_positivos:
            conteos[tipo]["tp"] += 1
        for tipo, _inicio, _fin in falsos_positivos:
            conteos[tipo]["fp"] += 1
        for tipo, _inicio, _fin in falsos_negativos:
            conteos[tipo]["fn"] += 1
    return dict(conteos)


def precision_recall_f1(tp: int, fp: int, fn: int) -> dict:
    """Convencion para los casos 0/0 (documentada, no accidental):

    - Precision sin ninguna prediccion (tp+fp == 0): 1.0. El detector no
      hizo ninguna afirmacion falsa -- vacuamente correcto, igual que un
      detector que nunca predice nada no "miente" sobre lo que no dijo.
    - Recall sin ninguna entidad real que encontrar (tp+fn == 0): 1.0, por
      la misma razon en espejo -- no se le paso nada por alto porque no
      habia nada que encontrar.
    - F1 es 0.0 solo si precision Y recall son 0 (evita dividir por cero
      cuando ambas convenciones de arriba no aplican).
    """
    precision = 1.0 if (tp + fp) == 0 else tp / (tp + fp)
    recall = 1.0 if (tp + fn) == 0 else tp / (tp + fn)
    f1 = 0.0 if (precision + recall) == 0 else 2 * precision * recall / (precision + recall)
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def calcular_over_redaction(muestras: list[dict], predicciones: dict[str, list[dict]]) -> float:
    """% de negativos dificiles donde el detector predijo AL MENOS una entidad.

    Metrica de primera clase (CLAUDE.md, seccion 6): no se deriva de
    precision/recall, se calcula aparte, sobre el subconjunto especifico
    de negativos dificiles -- ese es el subconjunto diseñado justamente
    para exponer over-redaction (ver eval/corpus/README.md).
    """
    negativos_dificiles = [m for m in muestras if m["categoria"] == "negativo_dificil"]
    if not negativos_dificiles:
        return 0.0
    marcados = sum(1 for m in negativos_dificiles if predicciones[m["id"]])
    return marcados / len(negativos_dificiles)


def percentil(valores: list[float], p: float) -> float:
    """Percentil `p` (0-100) de `valores`, con interpolacion lineal entre
    los dos valores ordenados mas cercanos -- el mismo metodo que usa
    numpy por defecto. `p=50` es la mediana, `p=99` es "peor caso salvo
    el 1% mas lento", que es la lectura que le importa a latencia.
    """
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    if len(ordenados) == 1:
        return ordenados[0]
    posicion = (p / 100) * (len(ordenados) - 1)
    indice_bajo = int(posicion)
    indice_alto = min(indice_bajo + 1, len(ordenados) - 1)
    fraccion = posicion - indice_bajo
    return ordenados[indice_bajo] + (ordenados[indice_alto] - ordenados[indice_bajo]) * fraccion

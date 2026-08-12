# Bitácora de métricas

Una entrada por cambio medible: fecha, fase, qué se cambió, la tabla de métricas antes/después, y una nota de qué sorprendió. Nunca se acepta "mejoró" sin un número al lado (CLAUDE.md, sección 2.1).

---

## 2026-08-11 — Fase 2 (TICKET-203) — Baseline solo-regex

**Cambio aplicado:** primera medición del proyecto. No hay "antes" — este es el punto de partida contra el que se va a comparar todo lo que venga en la Fase 3 (Presidio + reconocedores con checksum). Detector: `eval/harness/baseline_regex.py`, un patrón por tipo, sin NER y sin validación de dígito verificador.

**Corpus:** `eval/corpus/corpus.jsonl`, 300 muestras (TICKET-201).

### Global

| Precisión | Recall | F1 | Over-redaction |
|---|---|---|---|
| 0.521 | 0.825 | 0.639 | 30.0% |

### Por tipo de entidad

| Tipo | Precisión | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| EMAIL | 1.000 | 1.000 | 1.000 | 32 | 0 | 0 |
| CUIT_CUIL | 1.000 | 1.000 | 1.000 | 28 | 0 | 0 |
| CURP | 1.000 | 1.000 | 1.000 | 28 | 0 | 0 |
| TARJETA_CREDITO | 1.000 | 1.000 | 1.000 | 28 | 0 | 0 |
| NIT | 0.833 | 1.000 | 0.909 | 30 | 6 | 0 |
| RUT | 0.464 | 1.000 | 0.634 | 32 | 37 | 0 |
| TELEFONO | 0.126 | 0.769 | 0.216 | 20 | 139 | 6 |
| NOMBRE_PERSONA | 1.000 | 0.000 | 0.000 | 0 | 0 | 36 |

### Qué sorprendió

- **`NOMBRE_PERSONA` en 0.000 de recall no es un bug, es el resultado esperado.** Un regex no tiene ninguna forma de reconocer un nombre de persona — no hay patrón de caracteres que lo distinga de cualquier otra palabra capitalizada. Es exactamente por lo que la tabla de alcance (PLAN.md, sección 5) marca ese tipo como "NER, sin validación posible": la Fase 3 va a mover este número de 0 a algo real, y ese salto es la evidencia más clara de por qué Presidio (NER) hace falta y un baseline de regex no alcanza.
- **`TELEFONO` en 0.126 de precisión (139 falsos positivos) confirma, con un número, algo que el plan ya anticipaba** ("Teléfono: muchos falsos positivos, buen caso para medir over-redaction", PLAN.md sección 5). El patrón de teléfono es necesariamente laxo (cualquier corrida de 7 a 13 dígitos con separadores opcionales) porque los formatos varían mucho entre `es_CO`, `es_MX`, `es_AR`, `es_CL`, `es_ES` — y esa laxitud hace que también capture partes de NIT, RUT, CUIT/CUIL y tarjetas. No se ajustó el patrón para "verse mejor": el número feo es el punto — muestra por qué un dato de alta ambigüedad como el teléfono necesita más que regex.
- **37 falsos positivos de `RUT` — la mayoría no son error del patrón de RUT en sí, sino colisión con otros dos tipos.** El propio corpus tiene un negativo difícil diseñado a propósito con el mismo formato (`\d{7,8}-[dígito]`, un "código de referencia de orden de compra" que no es un documento — 9 de las 37). El resto (28) viene de que el tramo final de un CUIT/CUIL (`XX-XXXXXXXX-X`) es, en sí mismo, indistinguible por formato de un RUT (`XXXXXXXX-X`) — el patrón de RUT matchea el sufijo de casi cualquier CUIT válido. Un regex no tiene forma de saber que ese tramo "ya pertenece" a otra entidad más larga; eso es justo el tipo de ambigüedad que un validador de checksum (Fase 3) resuelve, porque el dígito verificador de RUT y el de CUIT usan fórmulas distintas.
- **Los 4 tipos con formato más rígido y sin overlap con otros patrones (EMAIL, CUIT_CUIL, CURP, TARJETA_CREDITO) dieron precisión y recall perfectos.** Tiene sentido: son los que menos se parecen entre sí y entre categorías del corpus. Es una señal de que el corpus (TICKET-201) está bien construido para estos tipos — si un regex simple ya los resuelve del todo, el corpus no tiene suficientes negativos difíciles *específicos* de esos tipos. Queda anotado como posible mejora futura del corpus si la Fase 3/8 lo necesita.

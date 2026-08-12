# Corpus etiquetado (TICKET-201)

300 muestras sintéticas, generadas de forma determinista, para medir el detector de PII de las fases 3-4. Ver `docs/adr/ADR-201-...md` (TICKET-203) para por qué este corpus existe *antes* que el detector.

## Cómo se generó

`python -m eval.corpus.generar` construye `corpus.jsonl` a partir de:

- **`valores.py`** — un generador por tipo de dato (NIT, RUT, CUIT/CUIL, CURP, tarjeta, email, teléfono, nombre). Genera el **formato** correcto de cada tipo (largo, separadores, estructura) usando `Faker` + `random`, pero **no garantiza que el dígito verificador sea matemáticamente válido**. Esa fórmula real, verificada contra la fuente oficial de cada país, es responsabilidad del reconocedor de `TICKET-303` (Fase 3) — decisión explícita para no adelantar ni duplicar ese trabajo (ver `docs/learning-log.md`, Fase 2).
- **`plantillas.py`** — frases naturales en español (y un subconjunto en inglés) donde se insertan esos valores, por categoría. Los offsets de cada entidad se calculan **mientras se concatena el texto**, nunca buscando el valor después con `texto.find(...)` — así no hay ambigüedad si un valor se repite o es substring de otro.
- **`generar.py`** — arma las 300 muestras (ver composición abajo) y escribe `corpus.jsonl`.

**Reproducible con semilla fija** (`SEMILLA = 20260211` en `generar.py`): correr el generador dos veces produce el mismo archivo, byte a byte. Esto importa porque `docs/metrics-log.md` compara métricas antes/después de cambios en fases futuras **contra este mismo corpus** — si cambiara solo por regenerarlo, esas comparaciones dejarían de tener sentido. Nota técnica: hay dos generadores de números aleatorios en juego (`Faker.seed()` para lo que produce Faker, `random.seed()` de Python para todo lo demás) — los dos se siembran, porque sembrar solo uno no alcanza (así se descubrió el bug la primera vez: dos ejecuciones daban corpus distintos).

El archivo `corpus.jsonl` generado **se comitea al repo** — es el artefacto congelado que usan los tests y el arnés, no el generador.

## Formato

Un objeto JSON por línea:

```json
{"id": "positivo_claro-nit-0001", "texto": "...", "categoria": "positivo_claro", "locale": "es_CO", "entidades": [{"tipo": "NIT", "inicio": 15, "fin": 26, "valor": "..."}]}
```

`inicio`/`fin` son offsets de caracter en `texto` (indexado como en Python); para toda entidad, `texto[inicio:fin] == valor` — invariante verificada por `tests/unit/test_corpus.py`.

## Qué cubre

| Categoría | Cantidad | Propósito |
|---|---|---|
| `positivo_claro` | 100 | PII inequívoca en contexto natural — ~12-13 por cada uno de los 8 tipos en alcance |
| `negativo_claro` | 50 | Texto de conversación típica sin ninguna PII |
| `negativo_dificil` | 50 | Lo que causa over-redaction: números con formato de documento que **no** son un documento de una persona (folios, tracking, versiones, códigos postales), nombres de producto/empresa |
| `caso_borde` | 40 | PII dentro de tablas markdown, JSON, bloques de código y URLs |
| `multi_entidad` | 40 | Dos entidades del mismo tipo con valores distintos, o la misma entidad repetida dos veces en el texto |
| `ingles` | 20 | Subconjunto pequeño para comparar el rendimiento español vs. inglés (D1) |

Locales: `es_CO`, `es_MX`, `es_AR`, `es_CL`, `es_ES` para el contenido en español (los tipos con país fijo — NIT, RUT, CUIT/CUIL, CURP — siempre usan el locale de su país; el resto rota entre los cinco), `en_US` para la categoría en inglés.

## Sesgos reconocidos

Publicados a propósito, no escondidos (D4):

- **Diversidad de plantillas limitada.** Cada tipo/categoría tiene entre 2 y 6 patrones de frase distintos; la variedad del corpus viene sobre todo de los valores aleatorios insertados (nombres, números, emails distintos en cada muestra), no de la estructura de la oración. Un corpus con más patrones de frase por tipo mediría mejor la robustez del detector ante fraseo variado — queda como mejora futura si el arnés muestra que el detector se sobreajusta a estas estructuras.
- **Ningún valor de documento con checksum tiene garantía de validez matemática.** Ni los "positivos claros" (podrían fallar un checksum real) ni los "negativos difíciles" (fallan casi con certeza, pero por azar, no por diseño explícito). Ver la sección "Cómo se generó" arriba.
- **Los negativos difíciles son los que un humano razonable escribiría, no un ataque adversarial dirigido.** La suite de red-team (Fase 8) es la que prueba evasión deliberada; este corpus mide el caso base.
- **`negativo_dificil` no incluye nombres de persona reales que coincidan con nombres de producto/marca** (el caso más difícil de over-redaction para el tipo `NOMBRE_PERSONA`, que no tiene validación posible). Es una categoría de negativo difícil genuina que falta — queda anotada aquí para no perderla de vista al revisar métricas de la Fase 3.
- **El subconjunto en inglés es pequeño (20 de 300)** y cubre solo 4 de los 8 tipos (los que no dependen de un documento específico de un país latinoamericano). Alcanza para *demostrar* el sesgo español/inglés (D1), no para medirlo con la misma precisión estadística que el español.

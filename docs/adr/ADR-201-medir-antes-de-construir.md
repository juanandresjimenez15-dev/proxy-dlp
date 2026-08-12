# ADR-201 — El arnés de medición se construye antes que el detector

## Contexto

El orden intuitivo para construir un sistema de detección de PII sería: primero el detector (Fase 3, Presidio + reconocedores), después medirlo. Es el orden en que la mayoría de los proyectos se hacen, y se siente natural — ¿cómo vas a medir algo que todavía no existe?

Este proyecto invierte ese orden a propósito: la Fase 2 (corpus + arnés) se construye completa, incluyendo un baseline medido, **antes** de escribir una sola línea del detector real.

## Decisión

El arnés de medición (`eval/harness/`) y el corpus etiquetado (`eval/corpus/`) existen y están probados antes de que exista Presidio, antes de que exista un solo `Recognizer`, antes de la Fase 3. El primer número que produce el arnés (TICKET-203) es un baseline solo-regex — deliberadamente simple, sin NER y sin validación de checksum — no el detector final.

## Consecuencias

- **"Mejoró la detección" deja de ser una opinión.** Sin este orden, la única forma de saber si un cambio de la Fase 3 ayudó es la intuición de quien lo escribió. Con el baseline ya medido (`docs/metrics-log.md`, entrada del 2026-08-11: recall 0.825, precisión 0.521, over-redaction 30.0%), cualquier cambio futuro se compara contra un número concreto, no contra una sensación. "Mejoró" pasa a significar `recall 0.825 → 0.94`, con la tabla al lado.
- **Define qué es "correcto" antes de intentar serlo.** Escribir el corpus obliga a decidir por adelantado: ¿qué cuenta como acierto? ¿coincidencia exacta de span o solapamiento? (ver `eval/harness/metricas.py`, decisión confirmada explícitamente en TICKET-202). ¿Qué es un "negativo difícil"? Tomar esas decisiones sin un detector de por medio evita el sesgo de diseñar el criterio de éxito *a la medida* del detector que ya se escribió — un error común y difícil de notar desde adentro.
- **El arnés y el corpus se testean sin la presión de que el detector real funcione.** `tests/unit/test_corpus.py` y `tests/unit/test_harness.py` ya prueban toda la tubería de medición con datos controlados (detectores de juguete, offsets conocidos) — cuando la Fase 3 conecte el detector real, cualquier número raro que salga es sospechoso del *detector*, no del instrumento que lo mide. Si el arnés se hubiera escrito después, un bug en cualquiera de los dos sería indistinguible del otro.
- **Ya se puede ver la forma del reporte final (D4) sin haber terminado el proyecto.** El baseline demuestra en la práctica lo que la tabla de alcance (PLAN.md, sección 5) predijo por escrito: `NOMBRE_PERSONA` necesita NER (recall 0.000 con regex puro) y `TELEFONO` produce muchos falsos positivos (precisión 0.126). Tener el número *antes* de construir el detector confirma que el plan de la Fase 3 ataca los problemas correctos, no problemas inventados.
- **Costo aceptado: dos entregas de trabajo "invisible" antes del primer resultado vistoso.** Construir un corpus de 300 muestras y un arnés con su propia suite de tests, sin que el detector todavía exista, no produce nada demostrable por sí solo (no hay "el proxy ahora detecta PII" que enseñar). Se acepta ese costo porque el valor no es el corpus ni el arnés en sí — es que todo lo que venga después queda respaldado por un número, no por una afirmación.

## Alternativas descartadas

- **Construir el detector primero y medirlo al final de la Fase 3** — el orden intuitivo, descartado porque es exactamente el que produce "mejoró la detección" sin poder decir cuánto, y porque el criterio de qué es un acierto terminaría diseñándose (consciente o inconscientemente) alrededor de lo que el detector ya sabe hacer.
- **Medir de forma informal sobre unos pocos ejemplos manuales, sin un corpus ni un arnés formal** — más rápido de armar, pero no sirve para comparar fases entre sí de forma reproducible, y no se testea a sí mismo — el riesgo exacto que señala CLAUDE.md sección 2.1 ("un arnés con un bug miente durante todo el proyecto").

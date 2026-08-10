# Registro de aprendizaje

Distinto de `metrics-log.md`: aqui no van numeros, van conceptos. Por cada fase: que era nuevo, que costo entender, que error se cometio y como se resolvio. Lo llena Juan, en el momento — la version escrita despues es una reconstruccion, no el aprendizaje real.

---

## Fase 0 — Setup e identidad de GitHub

**Que era nuevo:**

- La logica de `includeIf`, el alias SSH `github-personal` y la separacion identidad/autenticacion, en general se siguieron bien sobre la marcha.
- Lo que si costo un poco fue la estructura de carpetas del esqueleto (`app/`, `tests/`, `eval/`, `docs/`, `config/`) y para que sirve cada una — sobre todo la diferencia entre `tests/` (prueba que el codigo funcione) y `eval/` (mide que tan bien detecta), que a primera vista suenan parecidas pero son cosas distintas: una es correctitud, la otra es calidad de deteccion medida con numeros.

**Que costo entender:**

- Distinguir `tests/redteam/` de `eval/harness/`: ambas usan datos y ambas "evaluan" el sistema, pero una corre como test (pasa/falla, es parte del CI) y la otra corre como medicion (produce un numero de precision/recall, alimenta `metrics-log.md`).

**Que se decidio y por que:**

- N/A para esta fase — las decisiones tecnicas (no usar `gh`, hook de identidad, etc.) quedaron documentadas en los ADRs y en `CLAUDE.md` en vez de repetirse aqui.

---

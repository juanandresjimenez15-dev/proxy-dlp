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

## Fase 1 — Endpoint pass-through, manejo de fallos y concurrencia (TICKET-101/102/103)

**Que costo entender:**

- El orden de los bloques `except` en `upstream.py` me tenia confundido. `httpx.TimeoutException` es subclase de `httpx.RequestError`, y en Python el primer `except` cuyo tipo hace match con la excepcion es el que se ejecuta — no el mas especifico por defecto. Si el `except RequestError` generico fuera primero, atraparia tambien los timeouts y el bloque especifico de abajo nunca se ejecutaria. Por eso el mas especifico (`TimeoutException`) tiene que ir arriba.
- En el test de concurrencia (TICKET-103) crei que `asyncio.gather` devuelve los resultados en orden porque "los datos vienen limpios". No es asi: el orden de la lista de resultados es una garantia del API de `gather` en si misma — siempre devuelve los resultados en el mismo orden en que se le pasaron las corrutinas, sin importar en que orden terminaron por dentro. Esa garantia de orden es independiente de si hubo o no un cruce de datos: si hubiera una fuga entre requests, `gather` seguiria devolviendo la lista en la posicion correcta, pero el *contenido* de esa posicion seria el equivocado. Por eso el test compara `respuestas[indice]` contra `str(indice)`: confia en el orden de `gather` y verifica el contenido por separado.

**Que se decidio y por que:**

- **Por que el ADR-102 descarta reintentos automaticos:** en un proxy generico, reintentar ante un timeout es gratis — es la practica estandar de cualquier sistema distribuido. En `proxy-dlp` no lo es, porque cada llamada al upstream manda el payload completo, potencialmente con datos sensibles (antes de que exista deteccion en la Fase 3). Un reintento automatico significaria mandar ese mismo dato sensible una segunda vez a un sistema externo, sin que el cliente original lo haya decidido de nuevo. Por eso el proxy responde de inmediato con el error (502/504) y deja la decision de reintentar en manos del cliente original — si el dato se reenvia, es porque el cliente lo decidio con conocimiento, no porque el proxy lo repitio en silencio.
- **Por que el mensaje de error al cliente es generico:** las excepciones de `httpx` (timeout, conexion rechazada, etc.) pueden traer en su texto detalles de infraestructura interna — IP, host, puerto del upstream. Nunca se le pasa ese texto crudo al cliente; el mensaje que ve siempre es fijo y generico, y el detalle real solo queda disponible en el lado del servidor (log / `raise ... from exc`).
- **Por que ADR-103 elige `Depends` de FastAPI en vez de `contextvars` para el aislamiento por request:** hoy la cadena de llamadas es corta (el handler llama directo a la dependencia), asi que pasar el estado explicito por parametro es mas simple y mas facil de leer que el estado implicito de `contextvars`. Se reconsidera en la Fase 5 si la boveda termina necesitandose muy adentro de la logica de deteccion/normalizacion, donde pasarla a mano por cada firma se vuelva pesado.

---

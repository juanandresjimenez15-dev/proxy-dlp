# ADR-103 — Aislamiento por request via inyeccion de dependencias, no contextvars ni diccionarios globales

## Contexto

El backlog original describia la boveda (Fase 5) como "scoped a la sesion/request", sin definir que pasa cuando llegan requests simultaneas. `proxy-dlp` es single-tenant pero no es de un solo request a la vez: un proceso `uvicorn` atiende multiples requests concurrentes sobre el mismo event loop. Si el estado de un request (hoy: el `UpstreamClient`; desde la Fase 5: la boveda con PII real) vive en un lugar compartido entre corutinas, dos requests concurrentes pueden leer o pisar el estado del otro.

Ademas, "sesion" no es un concepto que este sistema tenga: no hay login, no hay cookies, no hay estado que sobreviva a un request. Por eso la decision de aislamiento es **por request**, nunca por sesion — la ambiguedad del backlog original queda resuelta aqui.

Habia que elegir el mecanismo tecnico para garantizar ese aislamiento, antes de que la Fase 5 le agregue datos sensibles de verdad.

## Decision

**Todo estado con alcance de request se construye dentro del ciclo de vida del request, nunca en una variable de modulo.** El mecanismo concreto es la inyeccion de dependencias de FastAPI (`Depends`), con las dependencias construidas de nuevo en cada llamada — nunca decoradas con `@lru_cache` ni cacheadas de ninguna forma.

Hoy esto ya se cumple para `get_upstream_client()`: cada request recibe su propia instancia de `UpstreamClient`, construida dentro de la funcion de la dependencia. Cuando la Fase 5 agregue la boveda, seguira el mismo patron: `get_vault()` (o el nombre que tenga) construye una boveda nueva y vacia en cada request, inyectada via `Depends`, nunca un diccionario a nivel de modulo indexado por algun id de request.

La unica excepcion deliberada es `get_settings()`, que si usa `@lru_cache`: la configuracion es de solo lectura, identica para todos los requests, y se lee una sola vez por proceso a proposito (arranca y falla temprano si falta una variable — TICKET-003). Cachear un dato inmutable no es un riesgo de aislamiento; cachear una boveda si lo seria.

## Consecuencias

- **Cero coordinacion manual.** No hay que generar un id de request, no hay que registrar ni borrar entradas de un diccionario, no hay riesgo de un id que colisiona o de una entrada que nunca se borra (memory leak). El ciclo de vida de la variable ya es exactamente el ciclo de vida del request: nace cuando FastAPI resuelve la dependencia, muere cuando la corutina del handler termina y Python la recolecta.
- **Nunca hace falta TTL para el request en si.** La regla de seguridad "la boveda se destruye al terminar la request, o al vencer el TTL" (CLAUDE.md, seccion 3) para el caso "al terminar" queda resuelta gratis por el alcance de la variable — no hay boveda que sobreviva al request salvo que alguien la guarde en algo con vida mas larga (lo cual esta prohibido por esta misma decision). El TTL como limite adicional (para requests que se cuelgan) sigue siendo responsabilidad de la Fase 5, no de este ticket.
- **Testeable sin trucos.** Reemplazar una dependencia en un test es una linea (`app.dependency_overrides[...] = ...`), tal como ya se usa en `test_proxy_passthrough.py` y `test_proxy_upstream_failures.py`. Un modelo basado en estado global séria mucho mas dificil de aislar entre tests.
- **Regla que se hereda a cada ticket futuro que toque estado compartido:** si un ticket nuevo necesita algo que "viva durante el request", la pregunta obligatoria es "¿esto se puede construir como una dependencia de FastAPI?". Si la respuesta es no, se vuelve a abrir este ADR, no se improvisa una alternativa en silencio.

## Alternativas descartadas

- **`contextvars.ContextVar`** — el mecanismo estandar de Python para estado implicito por-tarea-asincrona, que se propaga solo a traves de la cadena de llamadas sin pasarlo como parametro explicito. Es genuinamente util cuando el estado lo necesitan funciones muy profundas en la pila de llamadas y pasarlo a mano por cada firma de funcion se vuelve inmanejable. Se descarta **por ahora**: hoy la cadena de llamadas es corta (el handler y una o dos funciones mas), asi que pasar el estado explicito por parametro (lo que ya hace `Depends`) es mas simple y mas explicito de leer. Se reconsidera en la Fase 5 si la boveda termina necesitandose en funciones muy anidadas de deteccion/normalizacion donde pasarla a mano se vuelva ruidoso.
- **Diccionario global indexado por un id de request** (`_estado: dict[str, EstadoRequest] = {}`) — descartado por dos razones: (1) requiere generar el id y **limpiar** la entrada explicitamente al terminar, y un olvido ahi es un memory leak silencioso que crece con el trafico; (2) es exactamente el patron de "estado global mutable" que ya penó en la Fase 0 con `gh auth switch` (ver `docs/learning-log.md`, Fase 0) — funciona hasta que dos cosas concurrentes lo tocan a la vez y uno pisa al otro.
- **Middleware que adjunta estado a `request.state`** — tecnicamente tambien esta scoped al request (Starlette lo garantiza), y hubiera sido una alternativa razonable. Se descarta a favor de `Depends` porque `Depends` deja el estado explicito en la firma de la funcion (se ve en el tipo de que dependencias recibe el handler), mientras que `request.state.algo` es un atributo dinamico sin tipo ni contrato visible — mas dificil de verificar en revision de codigo o con un type checker.

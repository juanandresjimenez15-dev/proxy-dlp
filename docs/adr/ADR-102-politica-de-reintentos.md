# ADR-102 — Sin reintentos automaticos ante fallos del upstream

## Contexto

Cuando el proveedor upstream falla (timeout, no responde, error de conexion), la reaccion habitual de un cliente HTTP es reintentar automaticamente, a veces con backoff exponencial. Es una practica estandar en la mayoria de los sistemas distribuidos.

## Decision

`proxy-dlp` **no reintenta automaticamente** ninguna llamada al upstream. Ante `UpstreamTimeoutError` o `UpstreamUnavailableError`, el proxy responde de inmediato con un error claro (504 o 502) y deja que sea el cliente quien decida si reintentar.

## Consecuencias

- **Un reintento duplica el envio de datos sensibles.** Cada llamada al upstream manda el payload completo (potencialmente con PII, sobre todo antes de que exista deteccion en la Fase 3). Reintentar automaticamente significa que el mismo dato sensible viaja una segunda vez a un sistema externo, sin que el cliente original lo haya decidido de nuevo. En un proxy DLP, cuyo objetivo entero es minimizar la superficie de exposicion de esos datos, eso va en contra del proposito del proyecto.
- Cada intento adicional tambien es una entrada mas en los logs del proveedor externo (fuera de nuestro control) con el mismo contenido sensible — una segunda copia de algo que ya no se puede "desloguear" despues.
- **El cliente sigue teniendo la opcion de reintentar el mismo,** con conocimiento pleno de que lo esta haciendo. La diferencia importa: el cliente ya tomo la decision de enviar ese dato una vez; que el proxy la repita en silencio no es lo mismo que el cliente decidiendolo de nuevo.
- Como contrapartida, el sistema es menos resiliente a fallos transitorios del upstream (un timeout momentaneo que un reintento simple hubiera resuelto ahora se le devuelve al cliente como error). Se acepta ese costo porque, para este proyecto, la propiedad de seguridad pesa mas que la de disponibilidad — es la misma logica de fail-closed que rige el resto del sistema (ver glosario, PLAN.md).

## Alternativas descartadas

- **Reintentar automaticamente con backoff en 5xx/timeout** — descartado por la razon central de este ADR: duplica el envio de datos sensibles sin que el cliente lo decida.
- **Reintentar solo si la respuesta parcial confirma que el upstream nunca recibio el payload** (p. ej. un `ConnectError` antes de mandar nada) — tecnicamente mas seguro, pero con `httpx` no hay una garantia simple y confiable de "nunca llego a salir del socket"; distinguir eso con certeza agrega complejidad que no se justifica todavia. Queda como posible mejora futura si el proyecto llega a medir que los timeouts transitorios son un problema real.

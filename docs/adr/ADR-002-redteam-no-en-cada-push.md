# ADR-002 — El red-team no corre en cada push

## Contexto

El CI necesita dos tipos de verificacion muy distintos. Los tests `unit`/`integration` confirman que el sistema hace lo que se espera (contra el stub local, deterministico, gratis). El red-team hace lo contrario: se pone en el papel de un atacante e intenta romper el sistema contra un **modelo real**, no una respuesta fija — porque un ataque de inyeccion o de homoglifos solo prueba algo si el modelo del otro lado genera texto de verdad.

Correr eso en cada push tiene tres costos concretos:

1. **Dinero.** Un catalogo de 20+ ataques (`TICKET-801`) contra una API de pago significa 20+ llamadas reales por push. Con decenas de pushes al dia, se acumula sin limite.
2. **Tiempo.** El job `fast` existe para dar feedback en <2 minutos. Una llamada real a un LLM tarda segundos, no milisegundos; sumar 20+ llamadas en serie rompe ese presupuesto.
3. **No-determinismo.** Un modelo real no responde igual dos veces al mismo prompt. Si el red-team corriera en cada push, un fallo intermitente del modelo (no un bug real) pondria el CI en rojo — y la reaccion natural es empezar a ignorar los rojos, que es el mismo problema de confianza falsa que se queria evitar, en la direccion contraria.

## Decision

El job `redteam` corre solo manual (`workflow_dispatch`). El disparador nocturno (`schedule`) se activa recien en la Fase 8, cuando el catalogo de ataques exista de verdad — antes de eso, un cron nocturno solo generaria notificaciones de fallo sin ningun test real que correr.

Ademas: el red-team corre contra un **modelo local via Ollama** (modo compatible con la API de OpenAI), no contra un proveedor de pago. Esto es una decision explicita del proyecto, no un detalle tecnico: `proxy-dlp` es un proyecto de portafolio sin presupuesto de empresa detras, y la idea es poder aprender y experimentar sin gasto recurrente. Ollama resuelve esto sin sacrificar que el red-team siga siendo contra un sistema real y no-deterministico.

## Consecuencias

- **Existe una ventana de exposicion.** Entre un push que rompe una defensa (por ejemplo, el mapa de offsets de la Fase 4 dejando de reconocer homoglifos) y el momento en que alguien corre `redteam` a mano, el sistema puede tener una grieta activa sin que nadie lo sepa. Durante esa ventana, **el checkmark verde de `fast` no certifica que el sistema este protegido** — solo certifica que el comportamiento ya conocido no se rompio. Es una distincion importante para no leer mal el estado del repo.
- Cuando la Fase 8 active el cron nocturno, esa ventana queda acotada a un maximo de 24h en vez de "indefinida, depende de que alguien se acuerde de correrlo a mano".
- **Usar un modelo local pequeño en vez de uno de frontera es una limitacion real, no cosmetica.** Un modelo como Llama 3.2 1B es probablemente mas facil de enganar con ciertos ataques (y quiza mas dificil con otros, por ser menos capaz de seguir instrucciones complejas) que GPT-4 o Claude. Los resultados del red-team local no se trasladan 1:1 a lo que pasaria contra un modelo comercial. Esto se documenta como limitacion honesta (diferenciador D4), no se esconde.
- **Mas adelante, ya con el sistema maduro, se va a hacer una corrida puntual del red-team contra un modelo comercial real** (no local) — una sola vez, manual, controlada, para ver como se comparan los resultados frente a Ollama y documentar esa comparacion. No es parte del flujo recurrente ni del CI automatico; es una validacion de una sola vez, no una corrida periodica.
- **Este es un proyecto de portafolio para demostrar habilidad tecnica, no un sistema a nivel maximo de produccion.** Elegir un modelo local pequeño por defecto, en vez de infraestructura de nivel comercial, es una decision proporcional a ese objetivo — no una limitacion que haya que disculpar. El criterio del proyecto (ver PLAN.md) es que cada decision se pueda explicar y defender, no que cada pieza sea la version mas costosa o mas grande posible.

## Alternativas descartadas

- **Redteam en cada push** — descartado por los tres costos de la seccion de contexto (dinero, tiempo, no-determinismo erosionando la confianza en el CI).
- **API de pago con presupuesto limitado** — tecnicamente viable, pero descartada porque el objetivo explicito del proyecto es aprender sin gasto recurrente.
- **Activar el cron nocturno desde ahora** — descartado porque hoy no existe el catalogo de ataques (Fase 8); un cron sin tests reales que correr solo produce ruido sin senal.

# ADR-101 — Imitar el contrato de OpenAI en vez de inventar uno propio

## Contexto

El proxy necesita algun formato de peticion/respuesta HTTP. Habia dos caminos: disenar un formato propio (el que mas se ajuste "naturalmente" a lo que hace el proxy), o adoptar un formato que ya existe.

## Decision

Se imita el contrato de OpenAI para `/v1/chat/completions`: el mismo JSON de entrada (`model`, `messages`) y de salida (`choices[].message`) que usa su API real.

## Consecuencias

- **Portabilidad de proveedor sin tocar codigo.** Ya lo demostramos en la practica en `ADR-002`: el mismo proxy habla con Ollama local (para no gastar dinero) simplemente porque Ollama expone ese mismo contrato en modo compatible. El dia que se quiera comparar contra OpenAI real, o contra otro proveedor que tambien lo imite, es un cambio de `UPSTREAM_BASE_URL`, no una reescritura.
- **Legibilidad para quien evalua el proyecto.** El contrato de OpenAI es el que mas gente en el area ya conoce. Un evaluador no necesita leer documentacion propia para entender que hace el endpoint — ya sabe que es `/v1/chat/completions` en cuanto lo ve.
- **Costo de acoplamiento.** Si OpenAI cambia su contrato (agrega un campo, cambia una convencion), este proyecto hereda esa dependencia. Es un costo aceptado, no ignorado: el contrato de chat completions es estable desde hace tiempo y es, de facto, el estandar de la industria — varios proveedores lo imitan por la misma razon que este proyecto lo hace.

## Alternativas descartadas

- **Inventar un contrato propio** — descartado porque no aporta nada al problema que el proyecto resuelve (deteccion de PII), y le resta legibilidad y portabilidad sin ninguna ganancia a cambio.
- **Soportar varios contratos a la vez** (OpenAI y, por ejemplo, el de Anthropic) — descartado por ahora, consistente con el principio del proyecto de profundidad sobre amplitud (ver PLAN.md, seccion 5): un contrato bien soportado vale mas que dos a medias.

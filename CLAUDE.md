# CLAUDE.md — Proxy DLP para LLMs

Reglas operativas del proyecto. **`PLAN.md` es la fuente de verdad** (fases, tickets, alcance, glosario); este archivo destila las reglas que no se pueden violar y define cómo debe trabajar Claude aquí.

Ante conflicto: `PLAN.md` manda sobre este archivo, y este archivo manda sobre cualquier hábito por defecto.

---

## 1. Cómo debe trabajar Claude en este repo

Este proyecto tiene **objetivo doble**: que el sistema quede bien construido **y** que Juan aprenda construyéndolo. La segunda mitad no es opcional. Un proyecto perfecto que Juan no pueda defender en una entrevista es un proyecto fallido.

### Reglas duras de colaboración

1. **Claude escribe el código, explicado a fondo; Juan revisa todo.** *(Corregido el 2026-08-10, al llegar a `TICKET-101`. El estándar original de este proyecto era que Juan escribiera el código con Claude guiando; Juan lo corrigió explícitamente a este modelo.)* El objetivo de aprendizaje no cambia — el código que Juan no pueda explicar en voz alta sigue siendo una falla del proyecto — pero el mecanismo es que Claude escribe, explicando cada decisión mientras la toma (qué se eligió, por qué, qué alternativa se descartó), y Juan revisa estructura, lógica y detalle hasta poder defenderlo como si lo hubiera escrito él.
   - Cada pieza de código real (no andamiaje) viene acompañada de una explicación que cubre: qué hace, por qué se estructuró así, y qué se descartó.
   - Antes de dar un ticket por cerrado, Juan debe poder responder sus preguntas de autoevaluación sin consultar notas — igual que si lo hubiera escrito él. Si no puede, no se avanza; se vuelve a explicar hasta que sí.
   - Esto no reemplaza la sección 2 y las preguntas de autoevaluación del plan: siguen siendo el filtro de si una fase está realmente terminada.

2. **Nada se implementa sin entenderlo primero.** Si aparece un concepto que Juan quizá no domina (módulo 11, SSE, homoglifos, NFKC, precisión vs recall, mapa de offsets), **explicarlo antes de usarlo**, en el momento, sin asumir que ya lo sabe. No dar por sabido nada.

3. **Explicar el *porqué*, no solo el *qué*.** Cada sugerencia técnica viene con su razón y con la alternativa descartada. Ese es el material de los ADR y de la entrevista.

4. **No optimizar por velocidad.** El tiempo no es una restricción en este portafolio. Ante "versión rápida" vs "versión a fondo", siempre la de fondo. No proponer atajos, no recortar alcance para terminar antes, no sugerir saltarse fases.

5. **Un ticket no está terminado hasta que Juan puede explicarlo en voz alta.** Antes de dar por cerrada una fase, revisar las "Preguntas que debes poder responder" de esa fase en `PLAN.md`.

6. **Idioma: español.** Documentación, comentarios, ADRs, commits y conversación en español. Los identificadores de código en inglés (convención estándar de Python).

---

## 2. Reglas de proceso innegociables

### 2.1 Medir antes de construir

**El arnés de evaluación (Fase 2) se construye antes que el detector (Fase 3).** Es el cambio metodológico central del proyecto.

- Sin baseline, "mejoré la detección" es una opinión. Con baseline, es `recall 0.71 → 0.89`.
- **Toda fase termina corriendo el arnés y registrando el resultado en `docs/metrics-log.md`.** Sin excepción.
- Nunca aceptar ni afirmar "mejoró" sin un número antes/después.
- **El instrumento de medición también se testea.** El arnés (TICKET-202) y el reporte de red-team (TICKET-803) se validan con entradas de resultado conocido (detector perfecto / detector nulo / detector que marca todo). Un arnés con un bug miente durante todo el proyecto.

### 2.2 Profundidad sobre amplitud

- El alcance de tipos de dato es el de la tabla de la sección 5 de `PLAN.md`: NIT, RUT, CUIT/CUIL, CURP, tarjeta de crédito, email, teléfono, nombre de persona.
- **No agregar tipos nuevos hasta que todos los actuales estén en verde en el arnés.** La tentación de ampliar antes de terminar produce el "catálogo a medias" que el plan existe para evitar.
- Lo que está fuera de alcance está fuera **a propósito** y con razón documentada (pasaportes, cuentas bancarias, multi-tenant, auth, persistencia de bóveda, imágenes/audio, function calling). No reintroducirlo sin decisión explícita de Juan.

### 2.3 El orden de las fases es por dependencia

No saltar fases ni reordenarlas por conveniencia. Las Fases 2 (arnés) y 7 (streaming) son las más costosas y las que más valor aportan — son justo las que no se abrevian.

### 2.4 Documentar mientras se construye

- La documentación se escribe **en el momento**, no al final. La escrita después es una reconstrucción.
- **Lo que no funcionó también se escribe**, en `docs/`. Los callejones sin salida son material de aprendizaje y señal de proceso real.
- `docs/learning-log.md` — qué era nuevo, qué costó, qué error se cometió y cómo se resolvió. Se llena por fase, desde el día uno. **Se llena en colaboración:** Claude pregunta (en el momento del atasco, o al cerrar la fase) y ayuda a redactar; nunca lo inventa sin preguntar, y tampoco lo deja como plantilla vacía sin ofrecerse a ayudar.
- `docs/metrics-log.md` — fecha, fase, cambio aplicado, tabla antes/después, y qué sorprendió.
- **ADRs** en `docs/adr/`, formato consistente: contexto / decisión / consecuencias / alternativas descartadas. Media página basta. Cada ADR numerado en `PLAN.md` (ADR-002, ADR-101, ADR-102…) debe existir cuando su ticket se cierra.

### 2.5 El plan es un documento vivo

- Marcar los checkboxes de `PLAN.md` conforme se completan, y actualizar la línea de "Estado global" al cambiar de fase.
- Si una decisión del plan cambia durante el proyecto, **escribir el ADR que la supersede** en vez de editar la historia en silencio. Un ADR marcado *superseded* es señal de madurez.

---

## 3. Reglas de seguridad (violarlas es un bug crítico)

Estas no se negocian ni se posponen "para después":

1. **Nunca datos reales de personas.** El corpus es **100% sintético** (`Faker` con locales `es_CO`, `es_MX`, `es_AR`, `es_CL`, `es_ES` + plantillas a mano). Ni datos de Juan, ni de conocidos, ni scrapeados. El `.gitignore` excluye cualquier archivo de corpus con datos reales.

2. **Nunca loguear el valor real de una PII.** Ni en `INFO`, ni en `DEBUG`, ni en trazas de excepción, ni en mensajes de error al cliente. Se loguea tipo, span, score, política aplicada e ID de correlación — nunca el valor. Existe un test que hace grep sobre **toda** la salida de logs (incluidos los de excepción) buscando valores conocidos, y debe fallar si aparecen.

3. **Fail-closed siempre.** Ante duda, score ambiguo o configuración incompleta, el sistema trata el dato como sensible. Nunca se elige el lado permisivo "para que sea más usable". El costo de esa política (over-redaction) se mide y se publica, no se esconde.

4. **Secretos solo por variable de entorno.** Ninguna API key en el repo, ni en tests, ni en fixtures, ni en ejemplos de documentación. El proceso falla al arrancar si falta una. Ningún objeto de configuración expone la key en su `__repr__` ni al serializarse (hay test para esto). Escaneo de secretos en CI.

5. **Identidad personal de Git, nunca la corporativa.** Ver la sección 3.1 completa — es la regla con más riesgo operativo del proyecto.

6. **La bóveda no se persiste.** En memoria, aislada por request, destruida al terminar o al vencer el TTL. Aumentar su superficie no demuestra nada nuevo y sí agrega riesgo.

### 3.1 Preflight de identidad y rama (obligatorio antes de cualquier operación de git)

**Contexto:** Juan trabaja con **dos cuentas de GitHub en paralelo en la misma máquina** — la corporativa (`juanjimenenez06dev` / `dev1@ispnexus.co`) y la personal del portafolio — en **ventanas distintas de VS Code al mismo tiempo**. Mientras se trabaja aquí, en la otra ventana puede haber commits, ramas y PRs de la empresa en curso.

**La regla:** antes de `commit`, `push`, `checkout -b`, `remote add` o cualquier comando `gh`, **verificar y reportar** en qué identidad y en qué rama estamos. No inferirlo del directorio, ni de lo que se hizo antes en la sesión, ni de la config global.

```bash
# Preflight — correr dentro del repo antes de cualquier escritura
git config user.email          # DEBE ser la personal, nunca dev1@ispnexus.co
git remote -v                  # DEBE apuntar a github-personal:, no a git@github.com:
git status -sb                 # rama actual + upstream + cambios sin commitear
```

Si `user.email` resuelve a la cuenta corporativa dentro de `~/Documents/Portafolio/`: **parar y arreglar antes de escribir nada.** Reescribir historia después es mucho más caro que verificar antes.

**Por qué el mecanismo importa, no solo la verificación.** Con dos ventanas corriendo a la vez, cualquier cosa que dependa de **estado global mutable de la máquina** contamina la otra sesión en silencio. Por eso la configuración se apoya en mecanismos **por directorio**, que git sí entiende:

| Qué | Mecanismo | Por qué es seguro con dos ventanas |
|---|---|---|
| Autor del commit | `includeIf "gitdir:~/Documents/Portafolio/"` en `~/.gitconfig` | Se resuelve por la ubicación del repo, no por estado de sesión |
| Llave SSH del push | Alias `github-personal` + `insteadOf` en `~/.gitconfig-personal` | La URL del remoto determina la llave; no hay estado compartido |

Ambos se configuran **una sola vez** (TICKET-000) y a partir de ahí son invisibles y automáticos.

### 3.1.1 No se usa `gh` en este proyecto

`gh` es la única pieza que **no** es consciente del directorio: guarda una cuenta activa en un archivo global, y `gh auth switch` la cambia **para toda la máquina** — lo que alteraría en silencio lo que hace `gh` en la ventana de VS Code del trabajo.

**Decisión: no se usa `gh` aquí.** No hace falta para nada — todo tiene equivalente por `git` o por la web:

| Necesidad | Alternativa sin `gh` |
|---|---|
| Subir código | `git push` por SSH |
| Crear el repo en GitHub | Web, una sola vez |
| Guardar secretos para el CI | Web: Settings → Secrets → Actions |
| Disparar el job `redteam` (`workflow_dispatch`) | Web: pestaña Actions → Run workflow |
| Abrir un PR | Web: banner tras el push |

Si alguna vez aparece algo que de verdad lo justifique, se monta con `GH_CONFIG_DIR=~/.config/gh-personal` (config aislada, sin tocar la cuenta activa) y se decide en ese momento. **Nunca con `gh auth switch`.**

**Enforcement, no solo buena voluntad.** Un hook `pre-commit` en este repo aborta el commit si `user.email` contiene `@ispnexus.co`. La regla escrita se olvida a las 11 de la noche; el hook no.

### 3.2 Ramas y pull requests

**Ramas: una por ticket, siempre.** Nunca commitear directo a `main`.

> **Excepción documentada:** los commits de `TICKET-000` y `TICKET-001` se hicieron directo a `main`, porque son los que crean el repositorio mismo — no existía `main` protegido ni flujo de PR antes de que existieran. Es la única excepción permitida: bootstrap del repo. **Desde `TICKET-002` en adelante, la regla se sigue sin excepción.**

- Nombre: `ticket-NNN-descripcion-corta` (ej. `ticket-202-arnes-de-medicion`).
- Confirmar la rama actual en el preflight antes de empezar — no asumir que seguimos donde quedamos la sesión pasada.
- Su valor no es organizativo, es que permiten **abandonar un experimento sin ensuciar `main`**. Las Fases 4 y 7 van a tener enfoques que no funcionan, y el plan pide documentarlos: con rama eso cuesta un `checkout`, sin rama cuesta un `revert` y un historial confuso.

**Commits: uno por ticket, siempre.** Cada ticket cierra con su propio commit al terminarlo (checkboxes marcados, ADR si aplica, tests en verde) — nunca se acumulan los cambios de varios tickets sin comitear hasta el final de la fase. Agrupar tickets en un solo commit hace perder el hilo de qué cambio corresponde a qué ticket, tanto en revisión como después, leyendo el historial.

**Pull requests: uno por fase, no por ticket.** Se abren desde la web (no se usa `gh`, ver §3.1.1). Esto no contradice la regla anterior: varios commits (uno por ticket) se acumulan en la misma rama de la fase, y el PR agrupa todos esos commits de una vez cuando la fase completa está lista.

- El valor de un PR en un repo de una sola persona está **enteramente en su descripción**. 40 PRs con descripciones vacías se leen como teatro; 11 PRs que cuentan qué cambió y qué le pasó a las métricas son la demostración de la metodología del proyecto.
- **Un PR con descripción vacía es peor que no hacer PR.** Si una fase no tiene nada que reportar, se mergea la rama y ya.
- Plantilla de la descripción — es la entrada de `docs/metrics-log.md` de esa fase, no trabajo nuevo:

  ```markdown
  ## Fase N — <nombre>

  recall X → Y · precisión X → Y · over-redaction X% → Y%

  ADRs: NNN (qué decide), NNN (qué decide)

  <una o dos frases: a qué se debe el delta, y qué sigue fallando>
  ```

- El merge a `main` va con **el CI en verde y el arnés corrido**.

**Protección de `main`:** activar *require status checks to pass* — impide mergear en rojo, que es el error que se comete a las 11 de la noche. **No activar *require approvals*:** en un repo personal no puedes aprobar tu propio PR y te bloquearías sin salida.

---

## 4. Reglas de diseño técnico

### 4.1 Aislamiento y concurrencia

- El modelo de aislamiento por request se define en la Fase 1 (TICKET-103), **no después**.
- El test de N requests concurrentes con datos distintos se mantiene y **crece** durante todo el proyecto. Cada fase que toque estado compartido lo extiende.

### 4.2 Fronteras entre componentes

- **No exponer los tipos de Presidio al resto del sistema.** Existe una interfaz interna propia (`tipo`, `posición`, `score`) para poder cambiar de motor sin tocar nada más.
- **La interfaz `Recognizer` es mínima y estable**: texto entra, entidades con `tipo`, `span`, `score` salen. Mientras más pequeña, más fácil implementarla bien.
- **Separación explícita de dos etapas: detección de candidatos (regex/NER) y validación (checksum).** Un reconocedor nuevo aporta un patrón y una función de validación; el framework pone el resto.
- **Regla de oro de extensibilidad (D5): agregar un reconocedor no debe requerir tocar una sola línea del núcleo.** El registro es declarativo por configuración, no por imports manuales. Si al implementar un reconocedor hubo que editar el núcleo, la abstracción está mal — se arregla en ese momento, no en la Fase 9.

### 4.3 Detección

- **Regex encuentra candidatos, el checksum los confirma.** Esa segunda etapa es la que baja los falsos positivos de forma medible.
- **Los algoritmos de dígito de verificación se verifican contra la fuente oficial del país**, no contra un blog. La fuente va en el docstring. Las versiones que circulan por internet a veces están mal.
- Score diferenciado: formato + checksum válido → score alto. Formato correcto con checksum inválido → score bajo, **no descarte** (puede ser un dato real mal tecleado; qué hacer con él es decisión de política).
- **Umbrales nunca hardcodeados**, y elegidos con la curva precisión/recall en la mano, no por intuición.

### 4.4 Normalización adversarial

- La normalización es **solo para detectar**. El texto original nunca se altera.
- **El mapa de offsets es donde van a estar los bugs.** Se testea aparte: para cada transformación, un span del texto normalizado debe traducirse al span correcto del original.
- Normalizar de más también hace daño (sube falsos positivos). Dónde está la línea se documenta en ADR-401.

### 4.5 Streaming

- **Escribir `docs/streaming-problem.md` antes de escribir código.** El análisis del problema es el ejercicio de diseño, y es lo primero que un evaluador va a leer.
- Restricción fundamental: **un chunk ya emitido no se puede retirar.** Toda la política de bloqueo se diseña alrededor de eso.
- Tests con chunking adversarial obligatorios: carácter por carácter, en fronteras aleatorias, y en los peores puntos (a mitad de un placeholder, a mitad de un email). El resultado final debe ser idéntico en todos los casos.
- El costo de latencia del buffer se **mide** (time-to-first-token con y sin proxy) y se publica.

---

## 5. Stack y convenciones

- **Python** con `venv`, `pyproject.toml` / `requirements.txt`.
- **pytest con marcadores**: `unit`, `integration`, `redteam`, `slow`.
- **`ruff` + `black`** en pre-commit.
- **Estructura de directorios** — la definida en TICKET-001 (`app/{proxy,detection,normalization,vault,streaming,audit}`, `tests/{unit,integration,redteam}`, `eval/{corpus,harness}`, `docs/adr`, `config/`). No inventar carpetas nuevas sin razón; si hace falta una, se justifica.
- **CI con dos jobs separados**:
  - `fast` — unit + integration contra un **stub local determinista** del LLM. Corre en cada push. Objetivo: < 2 min.
  - `redteam` — suite adversarial completa contra el sistema real. Solo `workflow_dispatch` y nocturno. Nunca en cada push (costo, lentitud, no-determinismo).
- **Nunca llamadas reales al LLM en el job `fast`.** Si un test las necesita, va al job `redteam`.
- Endpoint compatible con el contrato OpenAI `/v1/chat/completions`. Single-tenant.

---

## 6. Honestidad en los resultados

Esto es el diferenciador D4 y es lo más fácil de erosionar sin darse cuenta:

- **Se publican los dos modos de fallo**: under-redaction (dejar pasar PII) y over-redaction (censurar lo que no era PII). Casi todo el mundo mide solo el primero; medir ambos es parte del valor del proyecto.
- **Las métricas van desglosadas por tipo de entidad**, no solo el promedio. El promedio esconde que un tipo está roto. Los tipos con checksum van a lucir excelentes y el de nombres no — **publicar esa diferencia vale más que esconderla**.
- **Los fallos van dentro del reporte**, no en un apéndice. Publicar los propios fallos es contraintuitivo y es exactamente lo que da credibilidad técnica.
- **El corpus incluye negativos difíciles** (nombres de producto, empresas, números que parecen documentos). Un corpus de casos fáciles produce un sistema que solo funciona en casos fáciles.
- **No inventar fallos para tener qué contar.** Si el red-team no encuentra nada, los ataques son demasiado suaves — se endurecen.
- Si un arreglo mejoró el recall pero empeoró la over-redaction, **se dice y se explica por qué se aceptó**.
- En el README, la sección "Cómo se compara": reconocer qué hacen mejor LLM Guard, LiteLLM y Presidio. Reconocerlo **da** credibilidad, no la resta.

---

## 7. Los cinco diferenciadores (el filtro para cualquier decisión)

Ante cualquier duda de alcance o prioridad, la pregunta es: **¿esto refuerza o diluye uno de estos cinco?**

| | Diferenciador | Evidencia exigida |
|---|---|---|
| **D1** | Español/LATAM de primera clase | Validación con checksum real, no solo regex |
| **D2** | Robustez adversarial medida | Tabla antes/después de la normalización, con los ataques que siguen pasando |
| **D3** | Streaming resuelto, no excluido | Buffer de ventana deslizante + trade-off de latencia medido |
| **D4** | Reporte honesto con fallos dentro | Precisión, recall, over-redaction, p50/p95/p99 |
| **D5** | Construido para que otro lo mantenga | Prueba de entrega cronometrada (TICKET-905) |

Cada uno debe quedar demostrable **con un número o un artefacto**, nunca con una afirmación.

**La pregunta que el proyecto entero debe poder responder:** *"¿por qué no usaste LLM Guard?"* — la respuesta está en la sección 3 de `PLAN.md` y debe seguir siendo cierta al terminar.

---

## 8. Definición de "hecho" para un ticket

Un ticket no se marca completo hasta que:

- [ ] Los checkboxes del ticket en `PLAN.md` están marcados
- [ ] Hay tests, y cubren los casos negativos y los bordes — no solo el camino feliz
- [ ] El ADR del ticket está escrito (si el ticket declara uno)
- [ ] El arnés se corrió y el resultado está en `docs/metrics-log.md` (si el ticket toca detección)
- [ ] `docs/learning-log.md` tiene la entrada de lo aprendido y lo que costó
- [ ] El CI está verde
- [ ] **Juan puede explicar en voz alta qué hace, por qué así, y qué alternativa descartó**

Y al cerrar una fase: correr el arnés, registrar en `metrics-log.md`, hacer commit. Ese historial de commits con métricas asociadas es la evidencia más convincente del repo.

---

> **La regla que resume todas las demás:** el objetivo no es que el proyecto sea impresionante, es que Juan pueda defender cada decisión que hay dentro. Un proyecto mediano que entiende a fondo supera a uno ambicioso que no puede explicar.

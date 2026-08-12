"""Baseline solo-regex: TICKET-203.

Detector minimo, SIN NER y SIN validacion de checksum -- una funcion
`detectar(texto) -> list[dict]` que corre un patron por tipo y devuelve
todos los matches. Sirve como PISO de referencia: cualquier mejora de la
Fase 3 (Presidio + reconocedores con checksum) se compara contra este
numero, no contra "cero" ni contra intuicion (ver ADR-201).

Limitaciones reconocidas a proposito (no bugs -- decisiones de alcance de
"el baseline mas simple que funciona"):

- **NOMBRE_PERSONA no tiene patron.** Los nombres de persona no tienen una
  forma reconocible por regex -- por eso la tabla de alcance (PLAN.md,
  seccion 5) dice "NER, sin validacion posible" para ese tipo. Este
  baseline reporta recall 0 ahi, honestamente, en vez de inventar un
  patron que no puede funcionar de verdad.
- **Ningun patron valida digito verificador.** Un NIT con formato correcto
  pero checksum invalido se marca igual que uno valido -- eso es
  justamente lo que TICKET-303 va a mejorar, y el numero de over-redaction
  de HOY es la vara con la que se mide esa mejora despues.
- **Los patrones no resuelven conflictos entre tipos.** Un mismo tramo de
  texto puede matchear el patron de mas de un tipo (por ejemplo, un
  numero largo que parece tarjeta y tambien telefono). Este baseline no
  elige "el mejor" tipo -- reporta todos los candidatos tal cual. La
  logica de elegir/descartar por confianza es la Fase 3 (TICKET-304).
"""

import re

_PATRONES: dict[str, re.Pattern] = {
    "NIT": re.compile(r"\b\d{9}-\d\b"),
    "RUT": re.compile(r"\b\d{7,8}-[\dkK]\b"),
    "CUIT_CUIL": re.compile(r"\b\d{2}-\d{8}-\d\b"),
    "CURP": re.compile(r"\b[A-Z]{4}\d{6}[HM][A-Z]{2}[A-Z]{3}[A-Z0-9]\d\b"),
    "TARJETA_CREDITO": re.compile(r"\b\d{13,16}\b"),
    "EMAIL": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "TELEFONO": re.compile(r"(?<!\d)\+?\(?\d{1,4}\)?(?:[\s.-]?\d){6,12}(?!\d)"),
}


def detectar(texto: str) -> list[dict]:
    entidades = []
    for tipo, patron in _PATRONES.items():
        for coincidencia in patron.finditer(texto):
            entidades.append(
                {
                    "tipo": tipo,
                    "inicio": coincidencia.start(),
                    "fin": coincidencia.end(),
                    "valor": coincidencia.group(),
                }
            )
    return entidades

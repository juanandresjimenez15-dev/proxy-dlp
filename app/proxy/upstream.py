"""Cliente que reenvia peticiones al proveedor upstream real.

Separado de app/proxy/main.py a proposito: la ruta HTTP no sabe COMO se
hace la llamada saliente, solo que existe algo con un metodo
`chat_completions`. Esa capa de indireccion es lo que permite reemplazar
el cliente real por uno falso en los tests unitarios, sin tocar la red
ni depender de una libreria de mocking (ver tests/unit/test_proxy_passthrough.py).
"""

from dataclasses import dataclass

import httpx


@dataclass
class UpstreamResponse:
    status_code: int
    content: bytes
    headers: dict[str, str]


class UpstreamError(Exception):
    """El proveedor no genero una respuesta HTTP normal.

    Distinto de un 4xx/5xx del proveedor -- eso SI es una respuesta
    normal y se propaga tal cual en UpstreamResponse. Esto es para
    cuando ni siquiera hubo respuesta: no se pudo hablar con el, o no
    contesto a tiempo. La ruta HTTP (main.py) traduce estas excepciones
    a un codigo de error informativo, sin filtrar el detalle interno
    (ver TICKET-102).
    """


class UpstreamTimeoutError(UpstreamError):
    """El proveedor no respondio dentro del timeout configurado."""


class UpstreamUnavailableError(UpstreamError):
    """No se pudo establecer conexion con el proveedor (DNS, red, conexion rechazada, etc.)."""


class UpstreamClient:
    """Reenvia el payload, sin modificarlo, al proveedor real."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout

    async def chat_completions(self, body: bytes) -> UpstreamResponse:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self._api_key}",
                    },
                )
        except httpx.TimeoutException as exc:
            # httpx.TimeoutException es subclase de httpx.RequestError, asi
            # que este except tiene que ir ANTES del mas general de abajo.
            raise UpstreamTimeoutError(f"El upstream no respondio en {self._timeout}s") from exc
        except httpx.RequestError as exc:
            raise UpstreamUnavailableError(
                "No se pudo establecer conexion con el upstream"
            ) from exc

        return UpstreamResponse(
            status_code=response.status_code,
            content=response.content,
            headers=dict(response.headers),
        )

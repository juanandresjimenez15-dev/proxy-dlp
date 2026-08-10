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


class UpstreamClient:
    """Reenvia el payload, sin modificarlo, al proveedor real."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout

    async def chat_completions(self, body: bytes) -> UpstreamResponse:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
            )
        return UpstreamResponse(
            status_code=response.status_code,
            content=response.content,
            headers=dict(response.headers),
        )

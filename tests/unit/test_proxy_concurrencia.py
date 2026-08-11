"""Test de TICKET-103: aislamiento de estado entre requests concurrentes.

Todavia no existe la boveda (eso es TICKET-501, Fase 5), asi que lo que
hay que probar hoy es el pass-through: N requests concurrentes con
payloads distintos, verificando que la respuesta que le llega a cada
cliente corresponde exactamente al payload que ESE cliente mando, nunca
al de otro. Este test se extiende en la Fase 5 para cubrir tambien la
boveda -- ver ADR-103.

No usa red real (marcador `unit`): ASGITransport corre la app FastAPI en
proceso, sin abrir un socket.
"""

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from app.proxy.main import app, get_upstream_client
from app.proxy.upstream import UpstreamResponse


class _UpstreamEcoConDelayInvertido:
    """Devuelve el mismo body que recibio, pero completa en orden INVERSO
    al de llegada: el primer request en llegar es el ultimo en responder.

    Es a proposito. Si `get_upstream_client()` compartiera estado entre
    requests (una variable de instancia, un dict a nivel de modulo), un
    bug de aislamiento podria pasar desapercibido si todo terminara en el
    mismo orden en que empezo -- el scheduling "por casualidad" no lo
    expondria. Forzando que terminen en desorden, cualquier cruce de datos
    entre requests se vuelve visible de forma determinista.
    """

    def __init__(self, total: int) -> None:
        self._total = total

    async def chat_completions(self, body: bytes) -> UpstreamResponse:
        indice = int(body.decode())
        await asyncio.sleep((self._total - indice) * 0.01)
        return UpstreamResponse(
            status_code=200,
            content=body,
            headers={"content-type": "text/plain"},
        )


async def _lanzar_requests_concurrentes(total: int) -> list:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await asyncio.gather(
            *(
                client.post("/v1/chat/completions", content=str(indice).encode())
                for indice in range(total)
            )
        )


@pytest.mark.unit
def test_n_requests_concurrentes_no_cruzan_datos():
    total = 10
    app.dependency_overrides[get_upstream_client] = lambda: _UpstreamEcoConDelayInvertido(total)
    try:
        respuestas = asyncio.run(_lanzar_requests_concurrentes(total))
    finally:
        app.dependency_overrides.clear()

    for indice, response in enumerate(respuestas):
        assert response.status_code == 200
        contenido_esperado = str(indice).encode()
        assert (
            response.content == contenido_esperado
        ), f"la respuesta {indice} trae datos de otro request: {response.content!r}"

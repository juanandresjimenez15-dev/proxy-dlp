"""Tests de TICKET-102: comportamiento del proxy cuando el upstream falla.

Tres cosas distintas, cada una con su propio test:
1. El upstream no responde a tiempo (timeout) -> 504, mensaje generico.
2. El upstream no se puede contactar -> 502, mensaje generico.
3. Un bug del PROXY (no del upstream) tampoco debe filtrar detalles
   internos al cliente -- distinto de los dos anteriores, que son fallos
   del proveedor.

Ninguno de estos tres es "el upstream respondio con un 4xx/5xx" -- ese
caso ya esta cubierto en test_proxy_passthrough.py::test_status_code_del_upstream_se_propaga,
porque ahi SI hubo una respuesta HTTP normal y se propaga tal cual.
"""

import pytest
from fastapi.testclient import TestClient

from app.proxy.main import app, get_upstream_client
from app.proxy.upstream import UpstreamResponse, UpstreamTimeoutError, UpstreamUnavailableError


class _UpstreamFalso:
    """Igual que en test_proxy_passthrough.py, pero tambien puede fallar a proposito."""

    def __init__(self) -> None:
        self.status_code = 200
        self.content = b'{"ok": true}'
        self.headers = {"content-type": "application/json"}
        self.exception_to_raise: Exception | None = None

    async def chat_completions(self, body: bytes) -> UpstreamResponse:
        if self.exception_to_raise is not None:
            raise self.exception_to_raise
        return UpstreamResponse(
            status_code=self.status_code,
            content=self.content,
            headers=self.headers,
        )


@pytest.fixture
def falso():
    instancia = _UpstreamFalso()
    app.dependency_overrides[get_upstream_client] = lambda: instancia
    yield instancia
    app.dependency_overrides.clear()


@pytest.mark.unit
def test_timeout_del_upstream_devuelve_504_sin_filtrar_detalle(falso):
    falso.exception_to_raise = UpstreamTimeoutError("detalle interno: timeout a los 30s")

    response = TestClient(app).post("/v1/chat/completions", content=b"{}")

    assert response.status_code == 504
    assert response.json()["error"]["type"] == "upstream_timeout"
    assert "detalle interno" not in response.text


@pytest.mark.unit
def test_upstream_inalcanzable_devuelve_502_sin_filtrar_detalle(falso):
    falso.exception_to_raise = UpstreamUnavailableError("detalle interno: DNS no resuelve")

    response = TestClient(app).post("/v1/chat/completions", content=b"{}")

    assert response.status_code == 502
    assert response.json()["error"]["type"] == "upstream_unavailable"
    assert "detalle interno" not in response.text


@pytest.mark.unit
def test_bug_del_proxy_tampoco_filtra_detalles_internos(falso):
    """Distincion clave del ticket: esto NO es un UpstreamError, es un bug
    de nuestro propio codigo. Debe tratarse distinto (Starlette lo
    convierte en 500 generico) pero con la misma garantia: nada interno
    llega al cliente."""
    falso.exception_to_raise = ValueError("un detalle interno que nunca deberia salir")

    client_sin_relanzar = TestClient(app, raise_server_exceptions=False)
    response = client_sin_relanzar.post("/v1/chat/completions", content=b"{}")

    assert response.status_code == 500
    assert "un detalle interno que nunca deberia salir" not in response.text

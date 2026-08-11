"""Tests unitarios del pass-through: sin red, con el upstream reemplazado.

TICKET-101: "con la llamada al LLM mockeada, verificar que el payload
sale byte-identico". Aqui no se mockea httpx -- se reemplaza el objeto
UpstreamClient completo via el mecanismo de dependencias de FastAPI, que
es justo lo que app/proxy/main.py fue disenado para permitir.
"""

import pytest
from fastapi.testclient import TestClient

from app.proxy.main import app, get_upstream_client
from app.proxy.upstream import UpstreamResponse


class _UpstreamFalso:
    """Reemplaza a UpstreamClient en los tests: no toca la red ni un modelo real."""

    def __init__(self) -> None:
        self.status_code = 200
        self.content = b'{"ok": true}'
        self.headers = {"content-type": "application/json"}
        self.received_body: bytes | None = None

    async def chat_completions(self, body: bytes) -> UpstreamResponse:
        self.received_body = body
        return UpstreamResponse(
            status_code=self.status_code,
            content=self.content,
            headers=self.headers,
        )


@pytest.fixture
def cliente_con_upstream_falso():
    falso = _UpstreamFalso()
    app.dependency_overrides[get_upstream_client] = lambda: falso
    yield TestClient(app), falso
    app.dependency_overrides.clear()


@pytest.mark.unit
def test_payload_sale_byte_identico(cliente_con_upstream_falso):
    client, falso = cliente_con_upstream_falso
    payload_original = b'{"model":"x","messages":[{"role":"user","content":"hola"}]}'

    client.post(
        "/v1/chat/completions",
        content=payload_original,
        headers={"Content-Type": "application/json"},
    )

    assert falso.received_body == payload_original


@pytest.mark.unit
def test_status_code_del_upstream_se_propaga(cliente_con_upstream_falso):
    client, falso = cliente_con_upstream_falso
    falso.status_code = 429  # ejemplo: el upstream aplico rate-limit

    response = client.post("/v1/chat/completions", content=b"{}")

    assert response.status_code == 429


@pytest.mark.unit
def test_headers_hop_by_hop_no_se_reenvian(cliente_con_upstream_falso):
    client, falso = cliente_con_upstream_falso
    falso.headers = {
        "content-type": "application/json",
        "connection": "keep-alive",
        "transfer-encoding": "chunked",
    }

    response = client.post("/v1/chat/completions", content=b"{}")

    assert "connection" not in response.headers
    assert "transfer-encoding" not in response.headers
    assert response.headers["content-type"] == "application/json"

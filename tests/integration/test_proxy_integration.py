"""Test de integracion: flujo completo del proxy contra el stub local del LLM.

A diferencia de tests/unit/test_proxy_passthrough.py, aqui SI hay una
llamada HTTP real -- solo que al stub determinista (tests/stubs/llm_stub.py),
nunca a un proveedor de verdad. Es lo que TICKET-002 llama "el job fast
no depende de la red externa, pero si prueba el flujo completo".
"""

import pytest
from fastapi.testclient import TestClient

from app.proxy.main import app, get_upstream_client
from app.proxy.upstream import UpstreamClient
from tests.stubs.llm_stub import RESPUESTA_FIJA, LLMStub


@pytest.mark.integration
def test_flujo_completo_contra_stub_local():
    with LLMStub() as stub:
        app.dependency_overrides[get_upstream_client] = lambda: UpstreamClient(
            base_url=stub.base_url,
            api_key="el-stub-no-valida-esto",
        )
        try:
            client = TestClient(app)
            response = client.post(
                "/v1/chat/completions",
                json={"model": "stub", "messages": [{"role": "user", "content": "hola"}]},
            )
        finally:
            app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == RESPUESTA_FIJA

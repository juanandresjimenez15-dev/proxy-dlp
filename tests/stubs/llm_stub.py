"""Stub local deterministico del proveedor LLM upstream.

Imita el endpoint POST /v1/chat/completions con una respuesta fija, para
que el job `fast` del CI y los tests de integracion no dependan de la red
ni de un proveedor real (ver TICKET-002, ADR-002).
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

RESPUESTA_FIJA = {
    "id": "chatcmpl-stub-0001",
    "object": "chat.completion",
    "created": 0,
    "model": "stub-modelo-determinista",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Respuesta fija del stub local, para tests deterministas.",
            },
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
}


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)  # el stub no lee el payload: siempre responde igual

        body = json.dumps(RESPUESTA_FIJA).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_args):  # silencia el logging por defecto a stdout
        pass


class LLMStub:
    """Servidor HTTP minimo y deterministico, para pruebas sin red externa."""

    def __init__(self, host: str = "127.0.0.1", port: int = 0):
        self._server = HTTPServer((host, port), _Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        host, port = self._server.server_address
        return f"http://{host}:{port}"

    def __enter__(self) -> "LLMStub":
        self._thread.start()
        return self

    def __exit__(self, *_exc_info):
        self._server.shutdown()
        self._server.server_close()


if __name__ == "__main__":
    with LLMStub(port=8081) as stub:
        print(f"Stub del LLM corriendo en {stub.base_url}/v1/chat/completions")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass

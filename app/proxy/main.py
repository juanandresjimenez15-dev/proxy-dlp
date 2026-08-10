"""Endpoint compatible con /v1/chat/completions de OpenAI.

Fase 1: proxy pass-through puro. Reenvia el payload al upstream sin
modificarlo -- todavia no hay deteccion de PII (eso empieza en la Fase 3).
Ver ADR-101 sobre por que se imita este contrato en vez de inventar uno
propio.
"""

from fastapi import Depends, FastAPI, Request, Response

from app.proxy.config import get_settings
from app.proxy.upstream import UpstreamClient

# Se lee y se valida al IMPORTAR este modulo, es decir, al arrancar el
# proceso -- no en el primer request. Si falta una variable de entorno
# requerida, el proceso ni siquiera llega a escuchar el puerto (TICKET-003:
# "el proceso falla al arrancar si falta una").
settings = get_settings()

app = FastAPI(title="proxy-dlp")

# Headers "hop-by-hop" (RFC 7230 seccion 6.1): describen UNA conexion HTTP
# especifica y nunca deben reenviarse a otra. Cliente->proxy y proxy->upstream
# son dos conexiones distintas. Reenviar estos tal cual produce respuestas
# corruptas -- por ejemplo, un Content-Length que ya no coincide con el
# cuerpo real una vez que el framework lo vuelve a armar.
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "content-length",
}


def get_upstream_client() -> UpstreamClient:
    """Dependencia de FastAPI: construye el cliente real.

    En los tests unitarios, se reemplaza por completo via
    `app.dependency_overrides[get_upstream_client] = ...` -- no hay que
    mockear httpx ni la red, solo cambiar que funcion devuelve esta.
    """
    return UpstreamClient(
        base_url=settings.upstream_base_url,
        api_key=settings.upstream_api_key.get_secret_value(),
    )


@app.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    upstream: UpstreamClient = Depends(get_upstream_client),
) -> Response:
    # request.body() da los bytes crudos, sin parsear. No usamos
    # request.json() porque parsear y volver a serializar puede cambiar
    # el texto (espacios, orden de llaves) -- y el requisito de esta fase
    # es que el payload salga BYTE-IDENTICO al que entro.
    body = await request.body()

    upstream_response = await upstream.chat_completions(body)

    response_headers = {
        key: value
        for key, value in upstream_response.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=response_headers,
    )

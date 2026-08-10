"""Configuracion del proxy, leida desde variables de entorno.

Nunca hardcodear secretos aqui. `UPSTREAM_API_KEY` usa `SecretStr`: pydantic
oculta su valor real en cualquier repr/log/serializacion por diseno del
tipo, no porque alguien se acuerde de ocultarlo (ver TICKET-003).
"""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    upstream_base_url: str
    upstream_api_key: SecretStr


@lru_cache
def get_settings() -> Settings:
    """Construye Settings una sola vez por proceso (los env vars no cambian en caliente)."""
    return Settings()  # type: ignore[call-arg]  # los valores vienen del entorno, no de aqui

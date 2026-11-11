import os


def _normalizar_url_do_banco(url: str) -> str:
    # Serviços como Neon e Render entregam "postgres://" ou "postgresql://".
    # O projeto usa o driver psycopg 3, que precisa de "postgresql+psycopg://".
    for prefixo in ("postgres://", "postgresql://"):
        if url.startswith(prefixo):
            return "postgresql+psycopg://" + url[len(prefixo):]
    return url


DATABASE_URL = _normalizar_url_do_banco(
    os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://gastos:gastos@localhost:5432/gastos",
    )
)

# Endereços do front-end que podem chamar a API (separados por vírgula)
CORS_ORIGINS = [
    origem.strip()
    for origem in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origem.strip()
]
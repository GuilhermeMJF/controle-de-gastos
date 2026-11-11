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

# Chave usada para assinar os tokens de login (JWT).
# Em produção, defina JWT_SECRET com um valor longo e aleatório.
JWT_SECRET_PADRAO = "chave-de-desenvolvimento-troque-antes-de-publicar"
JWT_SECRET = os.getenv("JWT_SECRET", JWT_SECRET_PADRAO)
JWT_EXPIRA_MINUTOS = int(os.getenv("JWT_EXPIRA_MINUTOS", str(60 * 24 * 7)))  # 7 dias

# Endereços do front-end que podem chamar a API (separados por vírgula)
CORS_ORIGINS = [
    origem.strip()
    for origem in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origem.strip()
]
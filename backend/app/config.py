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

JWT_SECRET_PADRAO = "chave-de-desenvolvimento-troque-antes-de-publicar"
JWT_SECRET = os.getenv("JWT_SECRET") or JWT_SECRET_PADRAO 
JWT_EXPIRA_MINUTOS = int(os.getenv("JWT_EXPIRA_MINUTOS", str(60 * 24 * 7)))  # 7 dias

# Endereços do front-end que podem chamar a API (separados por vírgula)
CORS_ORIGINS = [
    origem.strip()
    for origem in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origem.strip()
]
# Endereço do site, usado para montar o link de redefinição de senha.
# Se não for definido, usa o primeiro endereço de CORS_ORIGINS.
FRONTEND_URL = os.getenv("FRONTEND_URL", CORS_ORIGINS[0] if CORS_ORIGINS else "").rstrip("/")

# Envio de e-mails pelo Brevo (https://www.brevo.com).
# Sem BREVO_API_KEY, os e-mails não são enviados: o conteúdo aparece no log da API,
# o que é útil para testar no computador.
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE", "")
NOME_REMETENTE = os.getenv("NOME_REMETENTE", "Controle de Gastos")

# Quanto tempo o link de redefinição de senha vale
REDEFINICAO_EXPIRA_MINUTOS = int(os.getenv("REDEFINICAO_EXPIRA_MINUTOS", "30"))

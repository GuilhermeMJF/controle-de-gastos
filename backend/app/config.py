import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://gastos:gastos@localhost:5432/gastos",
)

# Endereços do front-end que podem chamar a API (separados por vírgula)
CORS_ORIGINS = [
    origem.strip()
    for origem in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origem.strip()
]

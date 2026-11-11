# 💰 Controle de Gastos

Aplicação web para registrar gastos pessoais e organizá-los por categoria. Você cadastra o que gastou, filtra por mês e categoria e vê, na hora, quanto saiu no período e para onde foi o dinheiro.

## ✨ Funcionalidades

- Cadastrar, editar e excluir gastos (descrição, valor, data e categoria)
- Filtrar gastos por mês e por categoria
- Total do período e participação de cada categoria no total
- Categorias padrão já criadas (Alimentação, Transporte, Moradia, Lazer, Saúde, Outros) e opção de criar novas com cor própria
- Validações na API: valor positivo com no máximo 2 casas decimais, categoria existente, nomes de categoria sem repetição e proteção contra excluir categoria em uso

## 🛠️ Tecnologias

| Camada | Tecnologia |
| --- | --- |
| Back-end | Python 3.12, FastAPI, SQLAlchemy 2, Pydantic 2 |
| Banco de dados | PostgreSQL 16 |
| Front-end | React 18 + Vite |
| Testes | Pytest |
| Ambiente | Docker e Docker Compose |

## 📁 Estrutura

```
controle-de-gastos/
├── backend/
│   ├── app/
│   │   ├── main.py          # cria a aplicação, CORS e categorias padrão
│   │   ├── config.py        # variáveis de ambiente
│   │   ├── database.py      # conexão com o banco
│   │   ├── models.py        # tabelas (SQLAlchemy)
│   │   ├── schemas.py       # validação de entrada e saída (Pydantic)
│   │   └── routers/         # rotas de categorias e gastos
│   └── tests/               # testes automatizados da API
├── frontend/
│   └── src/
│       ├── App.jsx          # tela principal
│       ├── api.js           # chamadas à API
│       └── components/      # formulário, lista, resumo e nova categoria
└── docker-compose.yml
```

## 🚀 Como rodar

### Opção 1: com Docker

Precisa ter o [Docker](https://www.docker.com/) instalado.

```bash
docker compose up --build
```

- Aplicação: http://localhost:5173
- API: http://localhost:8000
- Documentação interativa da API (Swagger): http://localhost:8000/docs

### Opção 2: sem Docker

Precisa de Python 3.12+, Node 20+ e um PostgreSQL rodando.

**1. Banco de dados**

Crie um banco e um usuário (os valores padrão são `gastos` / `gastos` / `gastos`):

```sql
CREATE USER gastos WITH PASSWORD 'gastos';
CREATE DATABASE gastos OWNER gastos;
```

**2. Back-end**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Para usar outro banco, defina a variável `DATABASE_URL`, por exemplo:
`postgresql+psycopg://usuario:senha@localhost:5432/meubanco`

**3. Front-end** (em outro terminal)

```bash
cd frontend
npm install
npm run dev
```

## 🧪 Testes

Os testes usam SQLite em memória, então não precisam do PostgreSQL:

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

## 🔌 Rotas da API

| Método | Rota | Descrição |
| --- | --- | --- |
| GET | `/categorias` | Lista as categorias |
| POST | `/categorias` | Cria uma categoria |
| PUT | `/categorias/{id}` | Atualiza uma categoria |
| DELETE | `/categorias/{id}` | Exclui uma categoria sem gastos |
| GET | `/gastos` | Lista gastos (filtros: `categoria_id`, `inicio`, `fim`) |
| GET | `/gastos/{id}` | Detalha um gasto |
| POST | `/gastos` | Cria um gasto |
| PUT | `/gastos/{id}` | Atualiza um gasto |
| DELETE | `/gastos/{id}` | Exclui um gasto |

Exemplo de gasto:

```json
{
  "descricao": "Mercado do mês",
  "valor": 432.9,
  "data": "2026-11-10",
  "categoria_id": 1
}
```

## 🗺️ Próximos passos

- [ ] Resumo mensal com gráfico de evolução
- [ ] Metas e limite de orçamento por categoria
- [ ] Login de usuários (cada pessoa vê só os próprios gastos)
- [ ] Migrações de banco com Alembic
- [ ] Deploy online (ex.: Render para a API e Vercel para o front)

## 👤 Autor

Feito por [Luiz Guilherme](https://github.com/GuilhermeMJF).

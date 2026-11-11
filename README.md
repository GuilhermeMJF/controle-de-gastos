# 💰 Controle de Gastos

Aplicação web para registrar gastos pessoais e organizá-los por categoria. Você cadastra o que gastou, filtra por mês e categoria e vê, na hora, quanto saiu no período e para onde foi o dinheiro.

## ✨ Funcionalidades

- Cadastro e login com e-mail e senha: cada pessoa vê só os próprios gastos
- Recuperação de senha por e-mail, com link que vale por 30 minutos
- Limite de gastos mensal, no total e por categoria, com barra que fica amarela a partir de 80% e vermelha ao estourar
- Cadastrar, editar e excluir gastos (descrição, valor, data e categoria)
- Filtrar gastos por mês e por categoria
- Total do período e participação de cada categoria no total
- Categorias padrão já criadas (Alimentação, Transporte, Moradia, Lazer, Saúde, Outros) e opção de criar novas com cor própria
- Validações na API: valor positivo com no máximo 2 casas decimais, categoria existente, nomes de categoria sem repetição e proteção contra excluir categoria em uso

## 🔐 Como funciona o login

- As senhas nunca são guardadas: o banco armazena só um hash **scrypt** com sal aleatório.
- Ao entrar, a API devolve um **token JWT** válido por 7 dias. O front-end envia esse token no cabeçalho `Authorization: Bearer ...` de cada pedido.
- Todas as rotas de gastos e categorias exigem login. Os gastos são separados por usuário; as categorias são compartilhadas entre todos.
- Login com e-mail inexistente e com senha errada dão a mesma resposta, para não revelar quais e-mails estão cadastrados.

### Esqueci minha senha

1. A pessoa informa o e-mail e recebe um link do tipo `https://site/?redefinir=<token>`.
2. O link vale por 30 minutos e só pode ser usado uma vez. O banco guarda só o hash do token, nunca o token em si.
3. Ao criar a nova senha, todos os logins abertos (em qualquer aparelho) são encerrados.
4. A resposta é sempre a mesma, exista o e-mail ou não, e um novo e-mail só sai depois de 2 minutos, para evitar spam.

Os e-mails são enviados pela API HTTP do [Brevo](https://www.brevo.com), porque o plano gratuito do Render bloqueia as portas SMTP. **Sem o Brevo configurado, o e-mail não é enviado: o conteúdo, com o link, aparece no terminal da API**, o que facilita testar no computador.

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
│   │   ├── seguranca.py     # hash de senha e tokens JWT
│   │   ├── dependencias.py  # descobre qual usuário está logado
│   │   ├── envio_email.py   # envio de e-mails pelo Brevo
│   │   └── routers/         # rotas de login, categorias e gastos
│   └── tests/               # testes automatizados da API
├── frontend/
│   └── src/
│       ├── App.jsx          # decide entre a tela de login e o painel
│       ├── api.js           # chamadas à API (envia o token)
│       ├── sessao.js        # guarda o login no navegador
│       └── components/      # login, nova senha, painel, formulário, lista, resumo e limites
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

Variáveis de ambiente da API:

| Variável | Para que serve |
| --- | --- |
| `DATABASE_URL` | Endereço do banco, ex.: `postgresql+psycopg://usuario:senha@localhost:5432/meubanco` |
| `JWT_SECRET` | Chave que assina os tokens de login. **Obrigatório em produção**, com um valor longo e aleatório |
| `CORS_ORIGINS` | Endereços do front-end que podem chamar a API, separados por vírgula |
| `FRONTEND_URL` | Endereço do site usado no link do e-mail. Se não for definido, usa o primeiro de `CORS_ORIGINS` |
| `BREVO_API_KEY` | Chave da API do Brevo, para enviar e-mails (opcional) |
| `EMAIL_REMETENTE` | E-mail verificado no Brevo que aparece como remetente (opcional) |

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

Com exceção do cadastro, do login e da recuperação de senha, todas as rotas exigem o cabeçalho `Authorization: Bearer <token>`.

| Método | Rota | Descrição |
| --- | --- | --- |
| POST | `/auth/cadastro` | Cria uma conta e já devolve o token |
| POST | `/auth/login` | Entra com e-mail e senha e devolve o token |
| GET | `/auth/me` | Mostra o usuário logado |
| POST | `/auth/esqueci-senha` | Envia o link de redefinição de senha por e-mail |
| POST | `/auth/redefinir-senha` | Cria a nova senha a partir do token do link |
| GET | `/categorias` | Lista as categorias |
| POST | `/categorias` | Cria uma categoria |
| PUT | `/categorias/{id}` | Atualiza uma categoria |
| DELETE | `/categorias/{id}` | Exclui uma categoria sem gastos |
| GET | `/gastos` | Lista os gastos do usuário logado (filtros: `categoria_id`, `inicio`, `fim`) |
| GET | `/gastos/{id}` | Detalha um gasto |
| POST | `/gastos` | Cria um gasto |
| PUT | `/gastos/{id}` | Atualiza um gasto |
| DELETE | `/gastos/{id}` | Exclui um gasto |
| GET | `/limites` | Lista os limites do usuário |
| PUT | `/limites/total` | Define (ou altera) o limite total do mês |
| DELETE | `/limites/total` | Remove o limite total |
| PUT | `/limites/categorias/{id}` | Define (ou altera) o limite de uma categoria |
| DELETE | `/limites/categorias/{id}` | Remove o limite de uma categoria |
| GET | `/limites/resumo?mes=AAAA-MM` | Quanto já foi gasto no mês em comparação com cada limite |

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
- [x] Limite de gastos mensal, no total e por categoria
- [x] Login de usuários (cada pessoa vê só os próprios gastos)
- [ ] Migrações de banco com Alembic
- [x] Deploy online (Neon para o banco, Render para a API e Vercel para o front)
- [x] Recuperação de senha por e-mail

Acesse o site:https://controle-de-gastos-psi-six.vercel.app/

## 👤 Autor

Feito por [Luiz Guilherme](https://github.com/GuilhermeMJF).

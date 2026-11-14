# Controle de Gastos

Site: https://controle-de-gastos-psi-six.vercel.app

Aplicação web para registrar gastos pessoais e organizá-los por categoria. Você cadastra o que gastou, filtra por mês e categoria e vê, na hora, quanto saiu no período e para onde foi o dinheiro.

## Funcionalidades

- Cadastro e login com e-mail e senha: cada pessoa vê só os próprios gastos
- Recuperação de senha por e-mail, com link que vale por 30 minutos
- Limite de gastos mensal, no total e por categoria, com barra que fica amarela a partir de 80% e vermelha ao estourar
- Gráfico dos últimos 6 meses, com a linha do limite total e clique para navegar entre os meses
- Cadastrar, editar e excluir gastos (descrição, valor, data e categoria)
- Filtrar gastos por mês e por categoria
- Total do período e participação de cada categoria no total
- Categorias padrão já criadas (Alimentação, Transporte, Moradia, Lazer, Saúde, Outros) e opção de criar novas com cor própria
- Validações na API: valor positivo com no máximo 2 casas decimais, categoria existente, nomes de categoria sem repetição e proteção contra excluir categoria em uso

## Como funciona o login

- As senhas nunca são guardadas: o banco armazena só um hash scrypt com sal aleatório.
- Ao entrar, a API devolve um token JWT válido por 7 dias. O front-end envia esse token no cabeçalho `Authorization: Bearer ...` de cada pedido.
- Todas as rotas de gastos e categorias exigem login. Cada pessoa vê só os próprios gastos, limites e categorias; as 6 categorias padrão aparecem para todos, mas ninguém pode alterá-las.
- Login com e-mail inexistente e com senha errada dão a mesma resposta, para não revelar quais e-mails estão cadastrados.
- Proteção contra força bruta: depois de 5 senhas erradas, o login da conta fica bloqueado por 15 minutos. Também há limites por IP para login, cadastro e pedidos de nova senha (a API responde 429).
- Em produção, a API se recusa a ligar sem a variável `JWT_SECRET`, para nunca usar a chave de desenvolvimento, que é pública.

### Esqueci minha senha

1. A pessoa informa o e-mail e recebe um link do tipo `https://site/?redefinir=<token>`.
2. O link vale por 30 minutos e só pode ser usado uma vez. O banco guarda só o hash do token, nunca o token em si.
3. Ao criar a nova senha, todos os logins abertos (em qualquer aparelho) são encerrados.
4. A resposta é sempre a mesma, exista o e-mail ou não, e um novo e-mail só sai depois de 2 minutos, para evitar spam.

Os e-mails são enviados pela API HTTP do [Brevo](https://www.brevo.com), porque o plano gratuito do Render bloqueia as portas SMTP. Sem o Brevo configurado, o e-mail não sai. O conteúdo, com o link, aparece no terminal da API, e isso facilita testar no computador.

## Tecnologias

- Back-end: Python 3.12, FastAPI, SQLAlchemy 2 e Pydantic 2
- Banco de dados: PostgreSQL 16
- Front-end: React 18, Vite, Recharts e ícones Lucide
- Testes: Pytest
- Ambiente: Docker e Docker Compose

## Estrutura

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
│   │   ├── limitador.py     # limite de tentativas (contra força bruta)
│   │   └── routers/         # rotas de login, categorias, gastos e limites
│   └── tests/               # testes automatizados da API
├── frontend/
│   └── src/
│       ├── App.jsx          # decide entre a tela de login e o painel
│       ├── api.js           # chamadas à API (envia o token)
│       ├── sessao.js        # guarda o login no navegador
│       └── components/      # login, nova senha, painel, formulário, lista, resumo, limites e gráfico
└── docker-compose.yml
```

## Como rodar localmente

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

#### 1. Banco de dados

Crie um banco e um usuário (os valores padrão são `gastos` / `gastos` / `gastos`):

```sql
CREATE USER gastos WITH PASSWORD 'gastos';
CREATE DATABASE gastos OWNER gastos;
```

#### 2. Back-end

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
| `JWT_SECRET` | Chave que assina os tokens de login. Obrigatória em produção, com um valor longo e aleatório |
| `CORS_ORIGINS` | Endereços do front-end que podem chamar a API, separados por vírgula |
| `FRONTEND_URL` | Endereço do site usado no link do e-mail. Se não for definido, usa o primeiro de `CORS_ORIGINS` |
| `BREVO_API_KEY` | Chave da API do Brevo, para enviar e-mails |
| `EMAIL_REMETENTE` | E-mail verificado no Brevo que aparece como remetente |

#### 3. Front-end

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

## Testes

Os testes usam SQLite em memória, então não precisam do PostgreSQL:

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

## Rotas da API

Todas as rotas, menos cadastro, login e recuperação de senha, exigem o cabeçalho `Authorization: Bearer <token>`.

| Método | Rota | Descrição |
| --- | --- | --- |
| POST | `/auth/cadastro` | Cria uma conta e já devolve o token |
| POST | `/auth/login` | Entra com e-mail e senha e devolve o token |
| GET | `/auth/me` | Mostra o usuário logado |
| POST | `/auth/esqueci-senha` | Envia o link de redefinição de senha por e-mail |
| POST | `/auth/redefinir-senha` | Cria a nova senha a partir do token do link |
| GET | `/categorias` | Lista as categorias padrão e as criadas pelo usuário |
| POST | `/categorias` | Cria uma categoria só para o usuário |
| PUT | `/categorias/{id}` | Atualiza uma categoria do usuário (as padrão não podem ser alteradas) |
| DELETE | `/categorias/{id}` | Exclui uma categoria do usuário que não tenha gastos |
| GET | `/gastos` | Lista os gastos do usuário logado (filtros: `categoria_id`, `inicio`, `fim`) |
| GET | `/gastos/{id}` | Detalha um gasto |
| POST | `/gastos` | Cria um gasto |
| PUT | `/gastos/{id}` | Atualiza um gasto |
| DELETE | `/gastos/{id}` | Exclui um gasto |
| GET | `/gastos/resumo-mensal?ate=AAAA-MM&meses=6` | Totais de cada mês, por categoria, para o gráfico |
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

## O que já foi feito

- [x] Resumo mensal com gráfico de evolução
- [x] Limite de gastos mensal, no total e por categoria
- [x] Login de usuários (cada pessoa vê só os próprios gastos)
- [x] Deploy online (Neon para o banco, Render para a API e Vercel para o front)
- [x] Recuperação de senha por e-mail

## Autor

Feito por [Luiz Guilherme](https://github.com/GuilhermeMJF).
import { EVENTO_SESSAO_EXPIRADA, tokenAtual } from "./sessao.js";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request(caminho, opcoes = {}) {
  const token = tokenAtual();
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  let resposta;
  try {
    resposta = await fetch(`${API_URL}${caminho}`, { ...opcoes, headers });
  } catch {
    throw new Error("Não foi possível conectar à API. Ela está rodando?");
  }

  // Token vencido ou inválido: avisa o App para voltar à tela de login
  if (resposta.status === 401 && token) {
    window.dispatchEvent(new Event(EVENTO_SESSAO_EXPIRADA));
    throw new Error("Sua sessão expirou. Entre novamente.");
  }

  if (!resposta.ok) {
    let mensagem = `Erro ${resposta.status}`;
    try {
      const corpo = await resposta.json();
      if (typeof corpo.detail === "string") {
        mensagem = corpo.detail;
      } else if (Array.isArray(corpo.detail)) {
        mensagem = corpo.detail.map(traduzirErroDeValidacao).join("; ");
      }
    } catch {
      // resposta sem JSON: mantém a mensagem genérica
    }
    throw new Error(mensagem);
  }

  return resposta.status === 204 ? null : resposta.json();
}

// Deixa as mensagens de validação mais amigáveis nos campos do login
function traduzirErroDeValidacao(erro) {
  const campo = erro.loc?.at(-1);
  if ((campo === "senha" || campo === "nova_senha") && erro.type === "string_too_short") {
    return "A senha precisa ter pelo menos 8 caracteres";
  }
  if (campo === "email") return "E-mail inválido";
  return erro.msg;
}

function comFiltros(caminho, filtros) {
  const params = new URLSearchParams();
  Object.entries(filtros).forEach(([chave, valor]) => {
    if (valor !== "" && valor != null) params.set(chave, valor);
  });
  const query = params.toString();
  return query ? `${caminho}?${query}` : caminho;
}

export const api = {
  cadastrar: (dados) =>
    request("/auth/cadastro", { method: "POST", body: JSON.stringify(dados) }),
  entrar: (dados) => request("/auth/login", { method: "POST", body: JSON.stringify(dados) }),
  esqueciSenha: (email) =>
    request("/auth/esqueci-senha", { method: "POST", body: JSON.stringify({ email }) }),
  redefinirSenha: (token, novaSenha) =>
    request("/auth/redefinir-senha", {
      method: "POST",
      body: JSON.stringify({ token, nova_senha: novaSenha }),
    }),

  listarCategorias: () => request("/categorias"),
  criarCategoria: (dados) =>
    request("/categorias", { method: "POST", body: JSON.stringify(dados) }),

  listarGastos: (filtros = {}) => request(comFiltros("/gastos", filtros)),
  criarGasto: (dados) =>
    request("/gastos", { method: "POST", body: JSON.stringify(dados) }),
  atualizarGasto: (id, dados) =>
    request(`/gastos/${id}`, { method: "PUT", body: JSON.stringify(dados) }),
  excluirGasto: (id) => request(`/gastos/${id}`, { method: "DELETE" }),
};

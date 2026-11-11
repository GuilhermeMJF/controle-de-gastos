const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request(caminho, opcoes = {}) {
  let resposta;
  try {
    resposta = await fetch(`${API_URL}${caminho}`, {
      headers: { "Content-Type": "application/json" },
      ...opcoes,
    });
  } catch {
    throw new Error("Não foi possível conectar à API. Ela está rodando?");
  }

  if (!resposta.ok) {
    let mensagem = `Erro ${resposta.status}`;
    try {
      const corpo = await resposta.json();
      if (typeof corpo.detail === "string") {
        mensagem = corpo.detail;
      } else if (Array.isArray(corpo.detail)) {
        mensagem = corpo.detail.map((erro) => erro.msg).join("; ");
      }
    } catch {
      // resposta sem JSON: mantém a mensagem genérica
    }
    throw new Error(mensagem);
  }

  return resposta.status === 204 ? null : resposta.json();
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

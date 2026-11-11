// Guarda o login no navegador, para a pessoa continuar logada ao recarregar a página.
const CHAVE = "controle-de-gastos:sessao";

export const EVENTO_SESSAO_EXPIRADA = "sessao-expirada";

export function lerSessao() {
  try {
    const salvo = localStorage.getItem(CHAVE);
    return salvo ? JSON.parse(salvo) : null;
  } catch {
    return null;
  }
}

export function salvarSessao(sessao) {
  try {
    localStorage.setItem(CHAVE, JSON.stringify(sessao));
  } catch {
    // Navegador sem armazenamento (ex.: modo privado): o login vale só até recarregar
  }
  sessaoEmMemoria = sessao;
}

export function limparSessao() {
  try {
    localStorage.removeItem(CHAVE);
  } catch {
    // nada a fazer
  }
  sessaoEmMemoria = null;
}

let sessaoEmMemoria = lerSessao();

export function tokenAtual() {
  return sessaoEmMemoria?.token ?? null;
}

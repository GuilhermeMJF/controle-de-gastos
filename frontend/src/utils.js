const formatadorMoeda = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

export function formatarMoeda(valor) {
  return formatadorMoeda.format(valor);
}

// "2026-11-10" -> "10/11/2026" (sem passar por Date, para não sofrer com fuso horário)
export function formatarData(dataIso) {
  return dataIso.split("-").reverse().join("/");
}

function doisDigitos(numero) {
  return String(numero).padStart(2, "0");
}

export function hojeIso() {
  const hoje = new Date();
  return `${hoje.getFullYear()}-${doisDigitos(hoje.getMonth() + 1)}-${doisDigitos(hoje.getDate())}`;
}

export function mesAtual() {
  return hojeIso().slice(0, 7);
}

// "2026-11" -> { inicio: "2026-11-01", fim: "2026-11-30" }
export function intervaloDoMes(mes) {
  if (!mes) return {};
  const [ano, numeroMes] = mes.split("-").map(Number);
  const ultimoDia = new Date(ano, numeroMes, 0).getDate();
  return { inicio: `${mes}-01`, fim: `${mes}-${doisDigitos(ultimoDia)}` };
}

// "2026-11" -> "novembro de 2026"
export function nomeDoMes(mes) {
  if (!mes) return "";
  const [ano, numeroMes] = mes.split("-").map(Number);
  return new Date(ano, numeroMes - 1, 1).toLocaleDateString("pt-BR", {
    month: "long",
    year: "numeric",
  });
}

import { formatarMoeda, nomeDoMes } from "../utils.js";

// Abaixo de 80%: normal. De 80% até 100%: alerta. Acima de 100%: estourado.
function estadoDoLimite(porcentagem) {
  if (porcentagem > 100) return "estourado";
  if (porcentagem >= 80) return "alerta";
  return "normal";
}

function textoDoRestante(situacao) {
  if (situacao.restante < 0) {
    return `Passou ${formatarMoeda(-situacao.restante)} do limite`;
  }
  if (situacao.restante === 0) return "Limite atingido";
  return `Faltam ${formatarMoeda(situacao.restante)}`;
}

function BarraDoLimite({ titulo, cor, situacao, destaque = false }) {
  const estado = estadoDoLimite(situacao.porcentagem);
  const largura = Math.min(situacao.porcentagem, 100);

  return (
    <li className={`limite ${destaque ? "limite-total" : ""}`}>
      <div className="limite-cabecalho">
        <span className="limite-titulo">
          {cor && <span className="marcador" style={{ background: cor }} />}
          {titulo}
        </span>
        <span className="limite-valores">
          {formatarMoeda(situacao.gasto)} de {formatarMoeda(situacao.limite)}
        </span>
      </div>
      <div
        className="barra-fundo"
        role="progressbar"
        aria-valuenow={Math.round(situacao.porcentagem)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${titulo}: ${Math.round(situacao.porcentagem)}% do limite`}
      >
        <div className={`barra barra-${estado}`} style={{ width: `${largura}%` }} />
      </div>
      <div className={`limite-rodape texto-${estado}`}>
        <span>{textoDoRestante(situacao)}</span>
        <span>{Math.round(situacao.porcentagem)}%</span>
      </div>
    </li>
  );
}

export default function LimitesMes({ mes, resumo, onEditar }) {
  const temLimites = resumo && (resumo.total || resumo.categorias.length > 0);

  return (
    <section className="limites">
      <div className="cartao-cabecalho">
        <h2>Limites de {nomeDoMes(mes)}</h2>
        <button type="button" className="link" onClick={onEditar}>
          {temLimites ? "Editar limites" : "Definir limites"}
        </button>
      </div>

      {!resumo ? (
        <p className="vazio">Carregando limites...</p>
      ) : !temLimites ? (
        <p className="vazio">
          Defina quanto você quer gastar por mês, no total ou em cada categoria, e acompanhe
          aqui quanto ainda falta.
        </p>
      ) : (
        <ul className="lista-limites">
          {resumo.total && (
            <BarraDoLimite titulo="Total do mês" situacao={resumo.total} destaque />
          )}
          {resumo.categorias.map((situacao) => (
            <BarraDoLimite
              key={situacao.categoria.id}
              titulo={situacao.categoria.nome}
              cor={situacao.categoria.cor}
              situacao={situacao}
            />
          ))}
        </ul>
      )}
    </section>
  );
}

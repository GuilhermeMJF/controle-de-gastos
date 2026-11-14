import { Pencil, Trash2 } from "lucide-react";
import { formatarData, formatarMoeda } from "../utils.js";

export default function ListaGastos({ gastos, carregando, onEditar, onExcluir }) {
  if (carregando) {
    return <p className="vazio">Carregando gastos...</p>;
  }

  if (gastos.length === 0) {
    return <p className="vazio">Nenhum gasto encontrado nesse período.</p>;
  }

  return (
    <ul className="lista">
      {gastos.map((gasto) => (
        <li key={gasto.id} className="item">
          <span className="marcador" style={{ background: gasto.categoria.cor }} />
          <div className="item-info">
            <strong>{gasto.descricao}</strong>
            <small>
              {formatarData(gasto.data)} · {gasto.categoria.nome}
            </small>
          </div>
          <span className="item-valor">{formatarMoeda(gasto.valor)}</span>
          <div className="item-acoes">
            <button
              type="button"
              className="icone"
              onClick={() => onEditar(gasto)}
              aria-label={`Editar ${gasto.descricao}`}
              title="Editar"
            >
              <Pencil size={16} aria-hidden="true" />
            </button>
            <button
              type="button"
              className="icone"
              onClick={() => onExcluir(gasto)}
              aria-label={`Excluir ${gasto.descricao}`}
              title="Excluir"
            >
              <Trash2 size={16} aria-hidden="true" />
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}

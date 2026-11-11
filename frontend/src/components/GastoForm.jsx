import { useState } from "react";
import { hojeIso } from "../utils.js";

function estadoInicial(gasto, categorias) {
  if (gasto) {
    return {
      descricao: gasto.descricao,
      valor: String(gasto.valor),
      data: gasto.data,
      categoria_id: String(gasto.categoria_id),
    };
  }
  return {
    descricao: "",
    valor: "",
    data: hojeIso(),
    categoria_id: categorias[0] ? String(categorias[0].id) : "",
  };
}

export default function GastoForm({ categorias, gastoEmEdicao, onSalvar, onCancelar }) {
  const [campos, setCampos] = useState(() => estadoInicial(gastoEmEdicao, categorias));
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");

  const editando = Boolean(gastoEmEdicao);

  function alterar(evento) {
    const { name, value } = evento.target;
    setCampos((atual) => ({ ...atual, [name]: value }));
  }

  async function enviar(evento) {
    evento.preventDefault();
    setErro("");
    setSalvando(true);
    try {
      await onSalvar({
        descricao: campos.descricao.trim(),
        valor: Number(campos.valor),
        data: campos.data,
        categoria_id: Number(campos.categoria_id),
      });
      if (!editando) {
        setCampos((atual) => ({ ...estadoInicial(null, categorias), categoria_id: atual.categoria_id }));
      }
    } catch (e) {
      setErro(e.message);
    } finally {
      setSalvando(false);
    }
  }

  return (
    <form className="cartao formulario" onSubmit={enviar}>
      <h2>{editando ? "Editar gasto" : "Novo gasto"}</h2>

      <label>
        Descrição
        <input
          name="descricao"
          value={campos.descricao}
          onChange={alterar}
          maxLength={120}
          placeholder="Ex.: Mercado do mês"
          required
        />
      </label>

      <div className="linha">
        <label>
          Valor (R$)
          <input
            name="valor"
            type="number"
            inputMode="decimal"
            min="0.01"
            step="0.01"
            value={campos.valor}
            onChange={alterar}
            placeholder="0,00"
            required
          />
        </label>

        <label>
          Data
          <input name="data" type="date" value={campos.data} onChange={alterar} required />
        </label>
      </div>

      <label>
        Categoria
        <select name="categoria_id" value={campos.categoria_id} onChange={alterar} required>
          {categorias.map((categoria) => (
            <option key={categoria.id} value={categoria.id}>
              {categoria.nome}
            </option>
          ))}
        </select>
      </label>

      {erro && <p className="erro">{erro}</p>}

      <div className="acoes">
        {editando && (
          <button type="button" className="secundario" onClick={onCancelar}>
            Cancelar
          </button>
        )}
        <button type="submit" disabled={salvando || categorias.length === 0}>
          {salvando ? "Salvando..." : editando ? "Salvar alterações" : "Adicionar gasto"}
        </button>
      </div>
    </form>
  );
}

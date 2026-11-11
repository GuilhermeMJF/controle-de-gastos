import { useState } from "react";

const TOTAL = "total";

// Monta { total: "3000", "4": "300", ... } a partir dos limites que vêm da API
function valoresIniciais(limites) {
  const valores = {};
  limites.forEach((limite) => {
    valores[limite.categoria_id ?? TOTAL] = String(limite.valor);
  });
  return valores;
}

export default function EditorLimites({ categorias, limites, onSalvar, onCancelar }) {
  const [originais] = useState(() => valoresIniciais(limites));
  const [valores, setValores] = useState(originais);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");

  function alterar(chave, valor) {
    setValores((atuais) => ({ ...atuais, [chave]: valor }));
  }

  async function enviar(evento) {
    evento.preventDefault();
    setErro("");

    // Só manda para a API o que mudou: valor novo → definir; campo apagado → remover
    const chaves = new Set([...Object.keys(originais), ...Object.keys(valores)]);
    const alteracoes = [];
    for (const chave of chaves) {
      const antes = originais[chave] ?? "";
      const depois = (valores[chave] ?? "").trim();
      const categoriaId = chave === TOTAL ? null : Number(chave);
      if (depois === "" && antes !== "") {
        alteracoes.push({ categoriaId, valor: null });
      } else if (depois !== "" && Number(depois) !== Number(antes)) {
        alteracoes.push({ categoriaId, valor: Number(depois) });
      }
    }

    setSalvando(true);
    try {
      await onSalvar(alteracoes);
    } catch (e) {
      setErro(e.message);
      setSalvando(false);
    }
  }

  function campo(chave, rotulo, cor) {
    return (
      <label key={chave} className="campo-limite">
        <span className="limite-titulo">
          {cor && <span className="marcador" style={{ background: cor }} />}
          {rotulo}
        </span>
        <input
          type="number"
          inputMode="decimal"
          min="0.01"
          step="0.01"
          placeholder="Sem limite"
          value={valores[chave] ?? ""}
          onChange={(e) => alterar(chave, e.target.value)}
        />
      </label>
    );
  }

  return (
    <form className="cartao formulario editor-limites" onSubmit={enviar}>
      <div className="cartao-cabecalho">
        <h2>Limites mensais</h2>
      </div>
      <p className="explicacao">
        Os limites valem para todos os meses até você mudar. Deixe em branco para não ter
        limite.
      </p>

      {campo(TOTAL, "Total do mês")}

      <p className="subtitulo">Por categoria</p>
      {categorias.map((categoria) => campo(String(categoria.id), categoria.nome, categoria.cor))}

      {erro && <p className="erro">{erro}</p>}

      <div className="acoes">
        <button type="button" className="secundario" onClick={onCancelar}>
          Cancelar
        </button>
        <button type="submit" disabled={salvando}>
          {salvando ? "Salvando..." : "Salvar limites"}
        </button>
      </div>
    </form>
  );
}

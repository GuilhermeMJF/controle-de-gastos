import { useState } from "react";

export default function NovaCategoria({ onCriar }) {
  const [aberto, setAberto] = useState(false);
  const [nome, setNome] = useState("");
  const [cor, setCor] = useState("#0ea5e9");
  const [erro, setErro] = useState("");

  async function enviar(evento) {
    evento.preventDefault();
    setErro("");
    try {
      await onCriar({ nome: nome.trim(), cor });
      setNome("");
      setAberto(false);
    } catch (e) {
      setErro(e.message);
    }
  }

  if (!aberto) {
    return (
      <button type="button" className="link" onClick={() => setAberto(true)}>
        + Nova categoria
      </button>
    );
  }

  return (
    <form className="cartao nova-categoria" onSubmit={enviar}>
      <div className="linha">
        <label>
          Nome
          <input
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            maxLength={50}
            placeholder="Ex.: Educação"
            required
            autoFocus
          />
        </label>
        <label className="campo-cor">
          Cor
          <input type="color" value={cor} onChange={(e) => setCor(e.target.value)} />
        </label>
      </div>
      {erro && <p className="erro">{erro}</p>}
      <div className="acoes">
        <button type="button" className="secundario" onClick={() => setAberto(false)}>
          Cancelar
        </button>
        <button type="submit">Criar categoria</button>
      </div>
    </form>
  );
}

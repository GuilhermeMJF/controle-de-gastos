import { useState } from "react";
import { api } from "../api.js";

export default function TelaRedefinirSenha({ token, onConcluir, onCancelar }) {
  const [novaSenha, setNovaSenha] = useState("");
  const [confirmacao, setConfirmacao] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState("");

  async function enviar(evento) {
    evento.preventDefault();
    setErro("");
    if (novaSenha !== confirmacao) {
      setErro("As duas senhas não são iguais");
      return;
    }
    setEnviando(true);
    try {
      const resposta = await api.redefinirSenha(token, novaSenha);
      onConcluir(resposta.mensagem);
    } catch (e) {
      setErro(e.message);
      setEnviando(false);
    }
  }

  return (
    <div className="tela-login">
      <header className="topo centralizado">
        <h1>💰 Controle de Gastos</h1>
        <p>Crie uma nova senha para a sua conta.</p>
      </header>

      <form className="cartao formulario" onSubmit={enviar}>
        <h2>Nova senha</h2>

        <label>
          Nova senha
          <input
            type="password"
            value={novaSenha}
            onChange={(e) => setNovaSenha(e.target.value)}
            minLength={8}
            maxLength={128}
            autoComplete="new-password"
            required
            autoFocus
          />
          <small className="dica">Mínimo de 8 caracteres</small>
        </label>

        <label>
          Repita a nova senha
          <input
            type="password"
            value={confirmacao}
            onChange={(e) => setConfirmacao(e.target.value)}
            minLength={8}
            maxLength={128}
            autoComplete="new-password"
            required
          />
        </label>

        {erro && <p className="erro">{erro}</p>}

        <button type="submit" disabled={enviando}>
          {enviando ? "Aguarde..." : "Salvar nova senha"}
        </button>

        <p className="alternar">
          <button type="button" className="link" onClick={onCancelar}>
            Voltar para o login
          </button>
        </p>
      </form>
    </div>
  );
}

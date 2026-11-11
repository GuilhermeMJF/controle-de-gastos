import { useState } from "react";
import { api } from "../api.js";

export default function TelaLogin({ onEntrar }) {
  const [modo, setModo] = useState("entrar"); // "entrar" ou "cadastrar"
  const [campos, setCampos] = useState({ nome: "", email: "", senha: "" });
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState("");

  const cadastrando = modo === "cadastrar";

  function alterar(evento) {
    const { name, value } = evento.target;
    setCampos((atual) => ({ ...atual, [name]: value }));
  }

  function trocarModo() {
    setModo(cadastrando ? "entrar" : "cadastrar");
    setErro("");
  }

  async function enviar(evento) {
    evento.preventDefault();
    setErro("");
    setEnviando(true);
    try {
      const resposta = cadastrando
        ? await api.cadastrar({
            nome: campos.nome.trim(),
            email: campos.email.trim(),
            senha: campos.senha,
          })
        : await api.entrar({ email: campos.email.trim(), senha: campos.senha });
      onEntrar({ token: resposta.access_token, usuario: resposta.usuario });
    } catch (e) {
      setErro(e.message);
      setEnviando(false);
    }
  }

  return (
    <div className="tela-login">
      <header className="topo centralizado">
        <h1>💰 Controle de Gastos</h1>
        <p>Registre seus gastos e veja para onde o dinheiro está indo.</p>
      </header>

      <form className="cartao formulario" onSubmit={enviar}>
        <h2>{cadastrando ? "Criar conta" : "Entrar"}</h2>

        {cadastrando && (
          <label>
            Nome
            <input
              name="nome"
              value={campos.nome}
              onChange={alterar}
              maxLength={80}
              autoComplete="name"
              required
              autoFocus
            />
          </label>
        )}

        <label>
          E-mail
          <input
            name="email"
            type="email"
            value={campos.email}
            onChange={alterar}
            maxLength={254}
            autoComplete="email"
            required
            autoFocus={!cadastrando}
          />
        </label>

        <label>
          Senha
          <input
            name="senha"
            type="password"
            value={campos.senha}
            onChange={alterar}
            minLength={cadastrando ? 8 : undefined}
            maxLength={128}
            autoComplete={cadastrando ? "new-password" : "current-password"}
            required
          />
          {cadastrando && <small className="dica">Mínimo de 8 caracteres</small>}
        </label>

        {erro && <p className="erro">{erro}</p>}

        <button type="submit" disabled={enviando}>
          {enviando ? "Aguarde..." : cadastrando ? "Criar conta" : "Entrar"}
        </button>

        <p className="alternar">
          {cadastrando ? "Já tem conta?" : "Ainda não tem conta?"}{" "}
          <button type="button" className="link" onClick={trocarModo}>
            {cadastrando ? "Entrar" : "Criar conta"}
          </button>
        </p>
      </form>
    </div>
  );
}

import { useState } from "react";
import { api } from "../api.js";

const TITULOS = {
  entrar: "Entrar",
  cadastrar: "Criar conta",
  esqueci: "Esqueci minha senha",
};

export default function TelaLogin({ onEntrar, mensagemInicial = "" }) {
  const [modo, setModo] = useState("entrar"); // "entrar", "cadastrar" ou "esqueci"
  const [campos, setCampos] = useState({ nome: "", email: "", senha: "" });
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState(mensagemInicial);

  const cadastrando = modo === "cadastrar";
  const esqueci = modo === "esqueci";

  function alterar(evento) {
    const { name, value } = evento.target;
    setCampos((atual) => ({ ...atual, [name]: value }));
  }

  function irPara(novoModo) {
    setModo(novoModo);
    setErro("");
    setSucesso("");
  }

  async function enviar(evento) {
    evento.preventDefault();
    setErro("");
    setSucesso("");
    setEnviando(true);
    try {
      if (esqueci) {
        const resposta = await api.esqueciSenha(campos.email.trim());
        setSucesso(resposta.mensagem);
        setEnviando(false);
        return;
      }
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

  let textoBotao = TITULOS[modo];
  if (esqueci) textoBotao = "Enviar link por e-mail";
  if (enviando) textoBotao = "Aguarde...";

  return (
    <div className="tela-login">
      <header className="topo centralizado">
        <h1>💰 Controle de Gastos</h1>
        <p>Registre seus gastos e veja para onde o dinheiro está indo.</p>
      </header>

      <form className="cartao formulario" onSubmit={enviar}>
        <h2>{TITULOS[modo]}</h2>

        {esqueci && (
          <p className="explicacao">
            Informe o e-mail da sua conta. Vamos enviar um link para você criar uma nova
            senha.
          </p>
        )}

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

        {!esqueci && (
          <label>
            <span className="rotulo-com-link">
              Senha
              {modo === "entrar" && (
                <button type="button" className="link" onClick={() => irPara("esqueci")}>
                  Esqueci minha senha
                </button>
              )}
            </span>
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
        )}

        {erro && <p className="erro">{erro}</p>}
        {sucesso && <p className="sucesso">{sucesso}</p>}

        <button type="submit" disabled={enviando}>
          {textoBotao}
        </button>

        <p className="alternar">
          {modo === "entrar" ? (
            <>
              Ainda não tem conta?{" "}
              <button type="button" className="link" onClick={() => irPara("cadastrar")}>
                Criar conta
              </button>
            </>
          ) : (
            <>
              {cadastrando ? "Já tem conta? " : "Lembrou a senha? "}
              <button type="button" className="link" onClick={() => irPara("entrar")}>
                Entrar
              </button>
            </>
          )}
        </p>
      </form>
    </div>
  );
}

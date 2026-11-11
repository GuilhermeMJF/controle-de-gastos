import { useEffect, useState } from "react";
import Painel from "./components/Painel.jsx";
import TelaLogin from "./components/TelaLogin.jsx";
import TelaRedefinirSenha from "./components/TelaRedefinirSenha.jsx";
import {
  EVENTO_SESSAO_EXPIRADA,
  lerSessao,
  limparSessao,
  salvarSessao,
} from "./sessao.js";

// Token que vem no link do e-mail: https://site/?redefinir=...
function lerTokenDaUrl() {
  return new URL(window.location.href).searchParams.get("redefinir");
}

// Tira o token da barra de endereço, para ele não ficar no histórico do navegador
function limparTokenDaUrl() {
  const url = new URL(window.location.href);
  if (!url.searchParams.has("redefinir")) return;
  url.searchParams.delete("redefinir");
  window.history.replaceState(null, "", url.pathname + url.search + url.hash);
}

export default function App() {
  const [sessao, setSessao] = useState(lerSessao);
  const [tokenRedefinicao, setTokenRedefinicao] = useState(lerTokenDaUrl);
  const [aviso, setAviso] = useState("");
  const [mensagemLogin, setMensagemLogin] = useState("");

  function entrar(novaSessao) {
    salvarSessao(novaSessao);
    setAviso("");
    setMensagemLogin("");
    setSessao(novaSessao);
  }

  function sair() {
    limparSessao();
    setSessao(null);
  }

  function senhaRedefinida(mensagem) {
    // A troca de senha encerra todos os logins, inclusive o deste aparelho
    limparSessao();
    setSessao(null);
    setTokenRedefinicao(null);
    setMensagemLogin(mensagem);
  }

  useEffect(() => {
    limparTokenDaUrl();
  }, []);

  // Se a API recusar o token (vencido ou inválido), volta para o login
  useEffect(() => {
    function aoExpirar() {
      limparSessao();
      setSessao(null);
      setAviso("Sua sessão expirou. Entre novamente.");
    }
    window.addEventListener(EVENTO_SESSAO_EXPIRADA, aoExpirar);
    return () => window.removeEventListener(EVENTO_SESSAO_EXPIRADA, aoExpirar);
  }, []);

  if (tokenRedefinicao) {
    return (
      <TelaRedefinirSenha
        token={tokenRedefinicao}
        onConcluir={senhaRedefinida}
        onCancelar={() => setTokenRedefinicao(null)}
      />
    );
  }

  if (!sessao) {
    return (
      <>
        {aviso && (
          <div className="aviso aviso-topo" role="status">
            {aviso}
          </div>
        )}
        {/* key: a mensagem de sucesso aparece de novo a cada troca de senha */}
        <TelaLogin key={mensagemLogin} onEntrar={entrar} mensagemInicial={mensagemLogin} />
      </>
    );
  }

  // key: ao trocar de conta, o painel começa do zero
  return <Painel key={sessao.usuario.id} usuario={sessao.usuario} onSair={sair} />;
}

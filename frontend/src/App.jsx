import { useEffect, useState } from "react";
import Painel from "./components/Painel.jsx";
import TelaLogin from "./components/TelaLogin.jsx";
import {
  EVENTO_SESSAO_EXPIRADA,
  lerSessao,
  limparSessao,
  salvarSessao,
} from "./sessao.js";

export default function App() {
  const [sessao, setSessao] = useState(lerSessao);
  const [aviso, setAviso] = useState("");

  function entrar(novaSessao) {
    salvarSessao(novaSessao);
    setAviso("");
    setSessao(novaSessao);
  }

  function sair() {
    limparSessao();
    setSessao(null);
  }

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

  if (!sessao) {
    return (
      <>
        {aviso && (
          <div className="aviso aviso-topo" role="status">
            {aviso}
          </div>
        )}
        <TelaLogin onEntrar={entrar} />
      </>
    );
  }

  // key: ao trocar de conta, o painel começa do zero
  return <Painel key={sessao.usuario.id} usuario={sessao.usuario} onSair={sair} />;
}

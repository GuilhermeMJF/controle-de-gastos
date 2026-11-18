import {
  ArrowLeft,
  KeyRound,
  Lock,
  LockOpen,
  LogOut,
  Pencil,
  Trash2,
  X,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { api } from "../api.js";
import { formatarData, nomeCurtoDoMes } from "../utils.js";

function VisaoGeral({ resumo }) {
  if (!resumo) return <p className="vazio">Carregando resumo...</p>;
  const maior = Math.max(1, ...resumo.contas_por_mes.map((m) => m.quantidade));

  return (
    <section className="admin-resumo">
      <div className="admin-numeros">
        <p>
          <span className="admin-numero">{resumo.total_contas}</span>
          contas criadas
        </p>
        <p>
          <span className="admin-numero">{resumo.contas_bloqueadas}</span>
          {resumo.contas_bloqueadas === 1 ? "conta bloqueada" : "contas bloqueadas"}
        </p>
      </div>
      <div>
        <h2>Contas novas por mês</h2>
        <ul className="admin-meses">
          {resumo.contas_por_mes.map((m) => (
            <li key={m.mes}>
              <span className="admin-mes">{nomeCurtoDoMes(m.mes)}</span>
              <div className="barra-fundo">
                <div
                  className="barra barra-normal"
                  style={{ width: `${(m.quantidade / maior) * 100}%` }}
                />
              </div>
              <span className="admin-qtd">{m.quantidade}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

function FormEdicao({ conta, onSalvar, onCancelar }) {
  const [nome, setNome] = useState(conta.nome);
  const [email, setEmail] = useState(conta.email);
  const [salvando, setSalvando] = useState(false);

  async function enviar(evento) {
    evento.preventDefault();
    setSalvando(true);
    const ok = await onSalvar({ nome: nome.trim(), email: email.trim() });
    if (!ok) setSalvando(false);
  }

  return (
    <form className="admin-edicao" onSubmit={enviar}>
      <label>
        Nome
        <input value={nome} onChange={(e) => setNome(e.target.value)} maxLength={80} required autoFocus />
      </label>
      <label>
        E-mail
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          maxLength={254}
          required
        />
      </label>
      <div className="acoes">
        <button type="button" className="secundario" onClick={onCancelar}>
          Cancelar
        </button>
        <button type="submit" disabled={salvando}>
          {salvando ? "Salvando..." : "Salvar alterações"}
        </button>
      </div>
    </form>
  );
}

function Acao({ icone: Icone, rotulo, onClick, perigo = false }) {
  return (
    <button
      type="button"
      className={`icone ${perigo ? "icone-perigo" : ""}`}
      onClick={onClick}
      aria-label={rotulo}
      title={rotulo}
    >
      <Icone size={16} aria-hidden="true" />
    </button>
  );
}

export default function TelaAdmin({ usuario, onVoltar }) {
  const [resumo, setResumo] = useState(null);
  const [contas, setContas] = useState(null);
  const [busca, setBusca] = useState("");
  const [editandoId, setEditandoId] = useState(null);
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState("");

  const carregar = useCallback(async (termo) => {
    try {
      const [novoResumo, lista] = await Promise.all([
        api.admin.resumo(),
        api.admin.listarContas(termo),
      ]);
      setResumo(novoResumo);
      setContas(lista);
    } catch (e) {
      setErro(e.message);
    }
  }, []);

  // Espera a pessoa parar de digitar antes de buscar
  useEffect(() => {
    const espera = setTimeout(() => carregar(busca), 300);
    return () => clearTimeout(espera);
  }, [busca, carregar]);

  async function executar(pergunta, acao, mensagem) {
    if (pergunta && !window.confirm(pergunta)) return false;
    setErro("");
    setSucesso("");
    try {
      const resposta = await acao();
      setSucesso(resposta?.mensagem ?? mensagem);
      await carregar(busca);
      return true;
    } catch (e) {
      setErro(e.message);
      return false;
    }
  }

  async function salvarEdicao(conta, dados) {
    const ok = await executar(null, () => api.admin.editarConta(conta.id, dados), "Conta atualizada.");
    if (ok) setEditandoId(null);
    return ok;
  }

  return (
    <div className="pagina">
      <header className="topo topo-logado">
        <div>
          <h1>Administração</h1>
          <p>Contas criadas no Controle de Gastos. Os gastos de cada pessoa não aparecem aqui.</p>
        </div>
        <button type="button" className="secundario com-icone" onClick={onVoltar}>
          <ArrowLeft size={16} aria-hidden="true" />
          Voltar ao painel
        </button>
      </header>

      {erro && (
        <div className="aviso" role="alert">
          {erro}
          <button type="button" className="icone" onClick={() => setErro("")} aria-label="Fechar aviso">
            <X size={16} aria-hidden="true" />
          </button>
        </div>
      )}
      {sucesso && (
        <p className="sucesso admin-sucesso" role="status">
          {sucesso}
        </p>
      )}

      <VisaoGeral resumo={resumo} />

      <section className="cartao admin-contas">
        <div className="cartao-cabecalho">
          <h2>Contas</h2>
        </div>
        <label className="admin-busca">
          Buscar por nome ou e-mail
          <input type="search" value={busca} onChange={(e) => setBusca(e.target.value)} maxLength={254} />
        </label>

        {!contas ? (
          <p className="vazio">Carregando contas...</p>
        ) : contas.length === 0 ? (
          <p className="vazio">Nenhuma conta encontrada{busca ? ` para "${busca}"` : ""}.</p>
        ) : (
          <ul className="lista">
            {contas.map((conta) =>
              editandoId === conta.id ? (
                <li key={conta.id} className="item">
                  <FormEdicao
                    conta={conta}
                    onSalvar={(dados) => salvarEdicao(conta, dados)}
                    onCancelar={() => setEditandoId(null)}
                  />
                </li>
              ) : (
                <li key={conta.id} className="item">
                  <div className="item-info">
                    <strong>
                      {conta.nome}
                      {conta.id === usuario.id && " (você)"}
                    </strong>
                    <small>{conta.email}</small>
                    <small>
                      Desde {formatarData(conta.criado_em.slice(0, 10))} ·{" "}
                      {conta.quantidade_gastos} {conta.quantidade_gastos === 1 ? "gasto" : "gastos"}
                    </small>
                  </div>
                  {conta.admin ? (
                    <span className="selo">Administrador</span>
                  ) : (
                    conta.bloqueado && <span className="selo selo-bloqueado">Bloqueada</span>
                  )}
                  <div className="item-acoes">
                    {!conta.admin && (
                      <Acao icone={Pencil} rotulo={`Editar ${conta.nome}`} onClick={() => setEditandoId(conta.id)} />
                    )}
                    <Acao
                      icone={LogOut}
                      rotulo={`Encerrar sessões de ${conta.nome}`}
                      onClick={() =>
                        executar(
                          `Encerrar todas as sessões de ${conta.nome}? A pessoa vai precisar entrar de novo.`,
                          () => api.admin.encerrarSessoes(conta.id)
                        )
                      }
                    />
                    {!conta.bloqueado && (
                      <Acao
                        icone={KeyRound}
                        rotulo={`Enviar link de nova senha para ${conta.nome}`}
                        onClick={() =>
                          executar(
                            `Enviar um link de nova senha para ${conta.email}?`,
                            () => api.admin.enviarLinkSenha(conta.id)
                          )
                        }
                      />
                    )}
                    {!conta.admin &&
                      (conta.bloqueado ? (
                        <Acao
                          icone={LockOpen}
                          rotulo={`Desbloquear ${conta.nome}`}
                          onClick={() =>
                            executar(
                              `Desbloquear a conta de ${conta.nome}?`,
                              () => api.admin.desbloquear(conta.id),
                              "Conta desbloqueada."
                            )
                          }
                        />
                      ) : (
                        <Acao
                          icone={Lock}
                          rotulo={`Bloquear ${conta.nome}`}
                          onClick={() =>
                            executar(
                              `Bloquear a conta de ${conta.nome}? A pessoa sai na hora e não consegue entrar até ser desbloqueada.`,
                              () => api.admin.bloquear(conta.id),
                              "Conta bloqueada."
                            )
                          }
                        />
                      ))}
                    {!conta.admin && (
                      <Acao
                        icone={Trash2}
                        perigo
                        rotulo={`Excluir ${conta.nome}`}
                        onClick={() =>
                          executar(
                            `Excluir a conta de ${conta.nome} (${conta.email})? Todos os gastos, limites e categorias dela serão apagados. Isso não pode ser desfeito.`,
                            () => api.admin.excluirConta(conta.id),
                            "Conta excluída."
                          )
                        }
                      />
                    )}
                  </div>
                </li>
              )
            )}
          </ul>
        )}
      </section>
    </div>
  );
}

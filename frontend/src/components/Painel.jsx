import { useCallback, useEffect, useState } from "react";
import { api } from "../api.js";
import { intervaloDoMes, mesAtual } from "../utils.js";
import EditorLimites from "./EditorLimites.jsx";
import GastoForm from "./GastoForm.jsx";
import GraficoMensal from "./GraficoMensal.jsx";
import LimitesMes from "./LimitesMes.jsx";
import ListaGastos from "./ListaGastos.jsx";
import NovaCategoria from "./NovaCategoria.jsx";
import ResumoCategorias from "./ResumoCategorias.jsx";

export default function Painel({ usuario, onSair }) {
  const [categorias, setCategorias] = useState([]);
  const [gastos, setGastos] = useState([]);
  const [mes, setMes] = useState(mesAtual());
  const [categoriaFiltro, setCategoriaFiltro] = useState("");
  const [gastoEmEdicao, setGastoEmEdicao] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");
  const [limites, setLimites] = useState([]);
  const [resumoLimites, setResumoLimites] = useState(null);
  const [editandoLimites, setEditandoLimites] = useState(false);
  const [resumoMensal, setResumoMensal] = useState(null);

  const carregarGastos = useCallback(async () => {
    setCarregando(true);
    try {
      const lista = await api.listarGastos({
        ...intervaloDoMes(mes),
        categoria_id: categoriaFiltro,
      });
      setGastos(lista);
      setErro("");
    } catch (e) {
      setErro(e.message);
    } finally {
      setCarregando(false);
    }
  }, [mes, categoriaFiltro]);

  // Limites definidos + quanto já foi gasto no mês escolhido.
  // Não depende do filtro de categoria: o limite sempre considera o mês inteiro.
  const carregarLimites = useCallback(async () => {
    if (!mes) return;
    try {
      const [lista, resumo] = await Promise.all([
        api.listarLimites(),
        api.resumoDosLimites(mes),
      ]);
      setLimites(lista);
      setResumoLimites(resumo);
    } catch (e) {
      setErro(e.message);
    }
  }, [mes]);

  // Totais dos últimos 6 meses para o gráfico (sempre até o mês atual)
  const carregarResumoMensal = useCallback(async () => {
    try {
      setResumoMensal(await api.resumoMensal(mesAtual(), 6));
    } catch (e) {
      setErro(e.message);
    }
  }, []);

  useEffect(() => {
    api.listarCategorias().then(setCategorias).catch((e) => setErro(e.message));
  }, []);

  useEffect(() => {
    carregarResumoMensal();
  }, [carregarResumoMensal]);

  useEffect(() => {
    carregarLimites();
  }, [carregarLimites]);

  useEffect(() => {
    carregarGastos();
  }, [carregarGastos]);

  async function salvarGasto(dados) {
    if (gastoEmEdicao) {
      await api.atualizarGasto(gastoEmEdicao.id, dados);
      setGastoEmEdicao(null);
    } else {
      await api.criarGasto(dados);
    }
    await Promise.all([carregarGastos(), carregarLimites(), carregarResumoMensal()]);
  }

  async function excluirGasto(gasto) {
    if (!window.confirm(`Excluir "${gasto.descricao}"?`)) return;
    try {
      await api.excluirGasto(gasto.id);
      if (gastoEmEdicao?.id === gasto.id) setGastoEmEdicao(null);
      await Promise.all([carregarGastos(), carregarLimites(), carregarResumoMensal()]);
    } catch (e) {
      setErro(e.message);
    }
  }

  async function salvarLimites(alteracoes) {
    for (const { categoriaId, valor } of alteracoes) {
      if (valor == null) {
        await api.removerLimite(categoriaId);
      } else {
        await api.definirLimite(categoriaId, valor);
      }
    }
    setEditandoLimites(false);
    await carregarLimites();
  }

  async function criarCategoria(dados) {
    const nova = await api.criarCategoria(dados);
    setCategorias((atuais) =>
      [...atuais, nova].sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"))
    );
  }

  return (
    <div className="pagina">
      <header className="topo topo-logado">
        <div>
          <h1>💰 Controle de Gastos</h1>
          <p>Olá, {usuario.nome.split(" ")[0]}! Veja para onde o seu dinheiro está indo.</p>
        </div>
        <button type="button" className="secundario" onClick={onSair}>
          Sair
        </button>
      </header>

      {erro && (
        <div className="aviso" role="alert">
          {erro}
          <button type="button" className="icone" onClick={() => setErro("")} title="Fechar">
            ✕
          </button>
        </div>
      )}

      <main className="grade">
        <aside className="coluna">
          <GastoForm
            key={gastoEmEdicao?.id ?? `novo-${categorias.length}`}
            categorias={categorias}
            gastoEmEdicao={gastoEmEdicao}
            onSalvar={salvarGasto}
            onCancelar={() => setGastoEmEdicao(null)}
          />
          <NovaCategoria onCriar={criarCategoria} />
        </aside>

        <section className="coluna">
          <div className="cartao filtros">
            <label>
              Mês
              <input type="month" value={mes} onChange={(e) => setMes(e.target.value)} />
            </label>
            <label>
              Categoria
              <select value={categoriaFiltro} onChange={(e) => setCategoriaFiltro(e.target.value)}>
                <option value="">Todas</option>
                {categorias.map((categoria) => (
                  <option key={categoria.id} value={categoria.id}>
                    {categoria.nome}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {editandoLimites ? (
            <EditorLimites
              categorias={categorias}
              limites={limites}
              onSalvar={salvarLimites}
              onCancelar={() => setEditandoLimites(false)}
            />
          ) : (
            mes && (
              <LimitesMes
                mes={mes}
                resumo={resumoLimites}
                onEditar={() => setEditandoLimites(true)}
              />
            )
          )}

          <ResumoCategorias gastos={gastos} />

          <div className="cartao">
            <h2>Gastos</h2>
            <ListaGastos
              gastos={gastos}
              carregando={carregando}
              onEditar={setGastoEmEdicao}
              onExcluir={excluirGasto}
            />
          </div>

          <GraficoMensal
            resumo={resumoMensal}
            mesSelecionado={mes}
            limiteTotal={limites.find((limite) => limite.categoria_id == null)?.valor ?? null}
            onSelecionarMes={setMes}
          />
        </section>
      </main>
    </div>
  );
}
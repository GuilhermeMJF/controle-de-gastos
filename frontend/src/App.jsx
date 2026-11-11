import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";
import GastoForm from "./components/GastoForm.jsx";
import ListaGastos from "./components/ListaGastos.jsx";
import NovaCategoria from "./components/NovaCategoria.jsx";
import ResumoCategorias from "./components/ResumoCategorias.jsx";
import { intervaloDoMes, mesAtual } from "./utils.js";

export default function App() {
  const [categorias, setCategorias] = useState([]);
  const [gastos, setGastos] = useState([]);
  const [mes, setMes] = useState(mesAtual());
  const [categoriaFiltro, setCategoriaFiltro] = useState("");
  const [gastoEmEdicao, setGastoEmEdicao] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");

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

  useEffect(() => {
    api.listarCategorias().then(setCategorias).catch((e) => setErro(e.message));
  }, []);

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
    await carregarGastos();
  }

  async function excluirGasto(gasto) {
    if (!window.confirm(`Excluir "${gasto.descricao}"?`)) return;
    try {
      await api.excluirGasto(gasto.id);
      if (gastoEmEdicao?.id === gasto.id) setGastoEmEdicao(null);
      await carregarGastos();
    } catch (e) {
      setErro(e.message);
    }
  }

  async function criarCategoria(dados) {
    const nova = await api.criarCategoria(dados);
    setCategorias((atuais) =>
      [...atuais, nova].sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"))
    );
  }

  return (
    <div className="pagina">
      <header className="topo">
        <h1>💰 Controle de Gastos</h1>
        <p>Registre seus gastos e veja para onde o dinheiro está indo.</p>
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
        </section>
      </main>
    </div>
  );
}

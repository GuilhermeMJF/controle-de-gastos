import { formatarMoeda } from "../utils.js";

export default function ResumoCategorias({ gastos }) {
  const total = gastos.reduce((soma, gasto) => soma + gasto.valor, 0);

  const porCategoria = Object.values(
    gastos.reduce((grupos, gasto) => {
      const { id, nome, cor } = gasto.categoria;
      grupos[id] ??= { id, nome, cor, total: 0 };
      grupos[id].total += gasto.valor;
      return grupos;
    }, {})
  ).sort((a, b) => b.total - a.total);

  return (
    <section className="cartao resumo">
      <p className="rotulo">Total no período</p>
      <p className="total">{formatarMoeda(total)}</p>

      {porCategoria.length > 0 && (
        <ul className="barras">
          {porCategoria.map((categoria) => {
            const porcentagem = total > 0 ? (categoria.total / total) * 100 : 0;
            return (
              <li key={categoria.id}>
                <div className="barra-legenda">
                  <span>{categoria.nome}</span>
                  <span>
                    {formatarMoeda(categoria.total)} · {porcentagem.toFixed(0)}%
                  </span>
                </div>
                <div className="barra-fundo">
                  <div
                    className="barra"
                    style={{ width: `${porcentagem}%`, background: categoria.cor }}
                  />
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

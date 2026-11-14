import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatarMoeda, formatarMoedaCurta, nomeCurtoDoMes, nomeDoMes } from "../utils.js";

// Cores fixas que funcionam tanto no tema claro quanto no escuro
const COR_NORMAL = "#5b6cf0";
const COR_ESTOUROU = "#d9534f";
const COR_TEXTO = "#8a91a3";

// Caixinha que aparece ao passar o mouse (ou tocar) numa barra
function DicaDoMes({ active, payload }) {
  if (!active || !payload?.length) return null;
  const mes = payload[0].payload; // o objeto do mês que veio da API

  return (
    <div className="dica-grafico">
      <strong>{nomeDoMes(mes.mes)}</strong>
      <span className="dica-total">{formatarMoeda(mes.total)}</span>
      {mes.categorias.length === 0 ? (
        <small>Nenhum gasto</small>
      ) : (
        <ul>
          {mes.categorias.map((item) => (
            <li key={item.categoria.id}>
              <span className="marcador" style={{ background: item.categoria.cor }} />
              {item.categoria.nome}: {formatarMoeda(item.total)}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function GraficoMensal({ resumo, mesSelecionado, limiteTotal, onSelecionarMes }) {
  return (
    <section className="cartao">
      <div className="cartao-cabecalho">
        <h2>Últimos 6 meses</h2>
        {limiteTotal != null && (
          <span className="legenda-limite">- - - Limite: {formatarMoeda(limiteTotal)}</span>
        )}
      </div>

      {!resumo ? (
        <p className="vazio">Carregando gráfico...</p>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart
              data={resumo.meses}
              margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
              // Clicar numa coluna troca o mês da página
              onClick={(estado) => estado?.activeLabel && onSelecionarMes(estado.activeLabel)}
            >
              <CartesianGrid vertical={false} stroke={COR_TEXTO} strokeOpacity={0.2} />
              <XAxis
                dataKey="mes"
                tickFormatter={nomeCurtoDoMes}
                tick={{ fill: COR_TEXTO, fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tickFormatter={formatarMoedaCurta}
                tick={{ fill: COR_TEXTO, fontSize: 12 }}
                axisLine={false}
                tickLine={false}
                width={72}
              />
              <Tooltip
                content={<DicaDoMes />}
                cursor={{ fill: COR_TEXTO, fillOpacity: 0.1 }}
              />
              {limiteTotal != null && (
                <ReferenceLine
                  y={limiteTotal}
                  stroke={COR_ESTOUROU}
                  strokeDasharray="6 4"
                  ifOverflow="extendDomain"
                />
              )}
              <Bar dataKey="total" radius={[6, 6, 0, 0]} cursor="pointer">
                {resumo.meses.map((item) => {
                  const estourou = limiteTotal != null && item.total > limiteTotal;
                  const selecionado = item.mes === mesSelecionado;
                  return (
                    <Cell
                      key={item.mes}
                      fill={estourou ? COR_ESTOUROU : COR_NORMAL}
                      fillOpacity={selecionado ? 1 : 0.45}
                    />
                  );
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <p className="dica-rodape">Clique numa barra para ver os gastos daquele mês.</p>
        </>
      )}
    </section>
  );
}
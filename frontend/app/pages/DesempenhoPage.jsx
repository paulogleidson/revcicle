import { useEffect, useState } from 'react'
import Card from '../components/Card'
import CalendarioRevisoes from '../components/charts/CalendarioRevisoes'
import GraficoEvolucao from '../components/charts/GraficoEvolucao'
import GraficoMaterias from '../components/charts/GraficoMaterias'
import { apiGet } from '../lib/api'
import { formatarData } from '../lib/dates'
import { formatarPct } from '../lib/formatos'

function Secao({ titulo, subtitulo, acao, children }) {
  return (
    <Card className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-lg font-medium text-app-fg">{titulo}</h2>
          {subtitulo && <p className="text-sm text-app-muted mt-0.5">{subtitulo}</p>}
        </div>
        {acao}
      </div>
      {children}
    </Card>
  )
}

// Abre no conteúdo revisado mais recentemente — o que o usuário provavelmente quer ver.
function conteudoMaisRecente(evolucao) {
  let melhor = evolucao[0]
  for (const e of evolucao) {
    const ultimaData = e.pontos[e.pontos.length - 1].data
    if (ultimaData > melhor.pontos[melhor.pontos.length - 1].data) melhor = e
  }
  return melhor.conteudo_id
}

function Evolucao({ evolucao }) {
  const [conteudoId, setConteudoId] = useState(() => conteudoMaisRecente(evolucao))
  const [verTabela, setVerTabela] = useState(false)
  const serie = evolucao.find((e) => e.conteudo_id === conteudoId) ?? evolucao[0]

  return (
    <Secao
      titulo="Evolução por conteúdo"
      subtitulo={`Percentual de acerto em cada revisão — ${serie.materia}`}
      acao={
        <select
          value={serie.conteudo_id}
          onChange={(e) => setConteudoId(Number(e.target.value))}
          aria-label="Conteúdo"
          className="h-10 w-full sm:w-56 rounded-lg bg-app-raised border border-app-line text-app-fg px-3 text-sm focus:outline-none focus:border-app-muted"
        >
          {evolucao.map((e) => (
            <option key={e.conteudo_id} value={e.conteudo_id}>
              {e.titulo}
            </option>
          ))}
        </select>
      }
    >
      <GraficoEvolucao key={serie.conteudo_id} pontos={serie.pontos} />
      {serie.pontos.length === 1 && (
        <p className="text-sm text-app-muted">
          Só uma revisão até agora — a linha aparece a partir da segunda.
        </p>
      )}
      <button
        type="button"
        onClick={() => setVerTabela((v) => !v)}
        className="text-sm text-app-muted underline hover:text-app-fg"
      >
        {verTabela ? 'Ocultar tabela' : 'Ver como tabela'}
      </button>
      {verTabela && (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-app-muted border-b border-app-line">
              <th className="py-2 font-normal">Data</th>
              <th className="py-2 font-normal text-right">Acerto</th>
            </tr>
          </thead>
          <tbody>
            {serie.pontos.map((p, i) => (
              <tr key={i} className="border-b border-app-line last:border-0 text-app-fg">
                <td className="py-2 tabular-nums">{formatarData(p.data)}</td>
                <td className="py-2 text-right tabular-nums">{formatarPct(p.percentual)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Secao>
  )
}

export default function DesempenhoPage() {
  const [metricas, setMetricas] = useState(null)
  const [erro, setErro] = useState(null)

  useEffect(() => {
    let cancelado = false
    apiGet('/metricas')
      .then((dados) => {
        if (!cancelado) setMetricas(dados)
      })
      .catch((e) => {
        if (!cancelado) setErro(e.message)
      })
    return () => {
      cancelado = true
    }
  }, [])

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold text-app-fg">Desempenho</h1>
        <p className="text-sm text-app-muted mt-1">
          Como você está indo em cada conteúdo e matéria.
        </p>
      </div>

      {erro && (
        <p className="text-sm text-status-atrasado-fg">Erro ao carregar: {erro}</p>
      )}

      {!erro && metricas === null && <p className="text-app-muted">Carregando…</p>}

      {metricas !== null && metricas.evolucao.length === 0 && (
        <Card className="p-6 sm:p-8 text-center">
          <p className="text-app-fg font-medium">Ainda não há revisões registradas</p>
          <p className="text-sm text-app-muted mt-1">
            Registre a primeira revisão de um conteúdo para ver seus gráficos aqui.
          </p>
        </Card>
      )}

      {metricas !== null && metricas.evolucao.length > 0 && (
        <>
          <Evolucao evolucao={metricas.evolucao} />
          <Secao
            titulo="Média por matéria"
            subtitulo="Média do percentual de acerto de todas as revisões da matéria."
          >
            <GraficoMaterias materias={metricas.por_materia} />
          </Secao>
          <Secao
            titulo="Calendário de revisões"
            subtitulo="Revisões feitas e a próxima agendada de cada conteúdo."
          >
            <CalendarioRevisoes calendario={metricas.calendario} />
          </Secao>
        </>
      )}
    </div>
  )
}

import { useState } from 'react'
import { formatarData, hojeIsoLocal, isoParaDias } from '../../lib/dates'

const MESES = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
]
const DIAS_SEMANA = ['D', 'S', 'T', 'Q', 'Q', 'S', 'S']

function iso(ano, mes, dia) {
  return `${ano}-${String(mes + 1).padStart(2, '0')}-${String(dia).padStart(2, '0')}`
}

function plural(n, um, varios) {
  return `${n} ${n === 1 ? um : varios}`
}

function Marcas({ info }) {
  if (!info) return <span className="h-2" />
  return (
    <span className="flex items-center justify-center gap-1 h-2">
      {info.realizadas.length > 0 && (
        <span className="w-2 h-2 rounded-full bg-chart-1" />
      )}
      {info.agendadas.length > 0 && (
        <span className="w-2 h-2 rounded-full border-2 border-chart-2" />
      )}
    </span>
  )
}

function DetalheDia({ data, info, hoje }) {
  if (!info) {
    return (
      <p className="text-sm text-app-muted">
        {formatarData(data)}: nenhuma revisão neste dia.
      </p>
    )
  }
  return (
    <div className="space-y-2 text-sm">
      <p className="font-medium text-app-fg">{formatarData(data)}</p>
      {info.realizadas.length > 0 && (
        <ul className="space-y-1">
          {info.realizadas.map((r, i) => (
            <li key={`r${i}`} className="flex items-center gap-2 text-app-fg">
              <span className="w-2 h-2 rounded-full bg-chart-1 shrink-0" />
              <span className="truncate">{r.titulo}</span>
              <span className="ml-auto font-medium tabular-nums">{r.percentual}%</span>
            </li>
          ))}
        </ul>
      )}
      {info.agendadas.length > 0 && (
        <ul className="space-y-1">
          {info.agendadas.map((a, i) => (
            <li key={`a${i}`} className="flex items-center gap-2 text-app-fg">
              <span className="w-2 h-2 rounded-full border-2 border-chart-2 shrink-0" />
              <span className="truncate">{a.titulo}</span>
              <span className="ml-auto text-app-muted">
                {data < hoje ? 'agendada (atrasada)' : 'agendada'}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

// Abre no mês atual se ele tiver revisões; senão, no mês do evento mais próximo
// de hoje — quem parou de estudar há semanas veria um calendário vazio.
function mesInicial(calendario, hoje) {
  const mesAtual = hoje.slice(0, 7)
  if (calendario.length === 0 || calendario.some((d) => d.data.startsWith(mesAtual))) {
    return mesAtual
  }
  const alvo = isoParaDias(hoje)
  const maisProximo = calendario.reduce((melhor, d) =>
    Math.abs(isoParaDias(d.data) - alvo) < Math.abs(isoParaDias(melhor.data) - alvo) ? d : melhor
  )
  return maisProximo.data.slice(0, 7)
}

export default function CalendarioRevisoes({ calendario }) {
  const hoje = hojeIsoLocal()
  const [anoInicial, mesInicialNum] = mesInicial(calendario, hoje).split('-').map(Number)
  const [ano, setAno] = useState(anoInicial)
  const [mes, setMes] = useState(mesInicialNum - 1)
  const [selecionado, setSelecionado] = useState(null)
  const [verLista, setVerLista] = useState(false)

  const porData = new Map(calendario.map((d) => [d.data, d]))

  const primeiroDiaSemana = new Date(ano, mes, 1).getDay()
  const diasNoMes = new Date(ano, mes + 1, 0).getDate()
  const celulas = [
    ...Array(primeiroDiaSemana).fill(null),
    ...Array.from({ length: diasNoMes }, (_, i) => i + 1),
  ]
  const prefixoMes = iso(ano, mes, 1).slice(0, 7)
  const doMes = calendario.filter((d) => d.data.startsWith(prefixoMes))

  function mudarMes(delta) {
    const d = new Date(ano, mes + delta, 1)
    setAno(d.getFullYear())
    setMes(d.getMonth())
    setSelecionado(null)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2">
        <button
          type="button"
          onClick={() => mudarMes(-1)}
          aria-label="Mês anterior"
          className="h-9 w-9 rounded-lg text-app-muted hover:bg-app-raised hover:text-app-fg transition"
        >
          ‹
        </button>
        <span className="text-sm font-medium text-app-fg" aria-live="polite">
          {MESES[mes]} de {ano}
        </span>
        <button
          type="button"
          onClick={() => mudarMes(1)}
          aria-label="Próximo mês"
          className="h-9 w-9 rounded-lg text-app-muted hover:bg-app-raised hover:text-app-fg transition"
        >
          ›
        </button>
      </div>

      <div className="grid grid-cols-7 gap-1 text-center">
        {DIAS_SEMANA.map((d, i) => (
          <span key={i} className="text-xs text-app-muted py-1">
            {d}
          </span>
        ))}
        {celulas.map((dia, i) => {
          if (dia === null) return <span key={`v${i}`} />
          const data = iso(ano, mes, dia)
          const info = porData.get(data)
          const ehHoje = data === hoje
          const ativo = data === selecionado
          const resumo = info
            ? `, ${plural(info.realizadas.length, 'revisão realizada', 'revisões realizadas')}, ${plural(info.agendadas.length, 'agendada', 'agendadas')}`
            : ''
          return (
            <button
              key={data}
              type="button"
              onClick={() => setSelecionado(data)}
              onPointerEnter={() => setSelecionado(data)}
              onFocus={() => setSelecionado(data)}
              aria-label={`${formatarData(data)}${resumo}`}
              aria-pressed={ativo}
              className={`flex flex-col items-center gap-1 rounded-lg py-1.5 transition hover:bg-app-raised focus:outline-none focus-visible:ring-1 focus-visible:ring-app-muted ${
                ativo ? 'bg-app-raised' : ''
              } ${ehHoje ? 'ring-1 ring-app-muted' : ''}`}
            >
              <span
                className={`text-sm tabular-nums ${
                  ehHoje ? 'font-semibold text-app-fg' : info ? 'text-app-fg' : 'text-app-muted'
                }`}
              >
                {dia}
              </span>
              <Marcas info={info} />
            </button>
          )
        })}
      </div>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-app-muted">
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-chart-1" /> Revisão realizada
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full border-2 border-chart-2" /> Revisão agendada
        </span>
      </div>

      <div className="min-h-12 border-t border-app-line pt-3">
        {selecionado ? (
          <DetalheDia data={selecionado} info={porData.get(selecionado)} hoje={hoje} />
        ) : (
          <p className="text-sm text-app-muted">Toque em um dia para ver as revisões.</p>
        )}
      </div>

      <div>
        <button
          type="button"
          onClick={() => setVerLista((v) => !v)}
          className="text-sm text-app-muted underline hover:text-app-fg"
        >
          {verLista ? 'Ocultar lista do mês' : 'Ver lista do mês'}
        </button>
        {verLista && (
          <div className="mt-3 space-y-4">
            {doMes.length === 0 ? (
              <p className="text-sm text-app-muted">Nenhuma revisão neste mês.</p>
            ) : (
              doMes.map((d) => (
                <DetalheDia key={d.data} data={d.data} info={d} hoje={hoje} />
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}

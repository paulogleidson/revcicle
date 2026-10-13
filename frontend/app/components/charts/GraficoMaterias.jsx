function formatarPct(v) {
  return `${Number.isInteger(v) ? v : v.toFixed(1)}%`
}

// Barras horizontais de 0 a 100%: cada matéria tem o valor escrito na ponta,
// então nenhum número depende de hover para ser lido.
export default function GraficoMaterias({ materias }) {
  return (
    <ul className="space-y-4">
      {materias.map((m) => (
        <li key={m.materia} className="group">
          <div className="flex items-baseline justify-between gap-3 mb-1.5">
            <span className="text-sm text-app-fg truncate">{m.materia}</span>
            <span className="text-xs text-app-muted shrink-0 tabular-nums">
              {m.total_revisoes} {m.total_revisoes === 1 ? 'revisão' : 'revisões'}
            </span>
          </div>
          <div
            className="flex items-center gap-2"
            role="img"
            aria-label={`${m.materia}: média de ${formatarPct(m.media_percentual)} em ${m.total_revisoes} revisões`}
          >
            {/* 3.5rem reservados para o rótulo, que fica sempre na ponta da barra. */}
            <div
              className="h-4 rounded-r bg-chart-1 transition group-hover:brightness-125"
              style={{ width: `calc((100% - 3.5rem) * ${Math.max(m.media_percentual, 1) / 100})` }}
            />
            <span className="text-sm font-medium text-app-fg tabular-nums">
              {formatarPct(m.media_percentual)}
            </span>
          </div>
        </li>
      ))}
    </ul>
  )
}

import { useState } from 'react'
import { formatarData, formatarDiaMes, isoParaDias } from '../../lib/dates'
import { useLargura } from '../../lib/useLargura'

const ALTURA = 220
const MARGEM = { topo: 14, direita: 48, base: 28, esquerda: 44 }
// 70% e 100% são os limites da regra de intervalo (+1 / +7 / +30 dias).
const TICKS_Y = [0, 70, 100]

function formatarPct(v) {
  return `${Number.isInteger(v) ? v : v.toFixed(1)}%`
}

export default function GraficoEvolucao({ pontos }) {
  const [ref, largura] = useLargura()
  const [ativo, setAtivo] = useState(null)

  const plotL = Math.max(largura - MARGEM.esquerda - MARGEM.direita, 0)
  const plotA = ALTURA - MARGEM.topo - MARGEM.base

  const dias = pontos.map((p) => isoParaDias(p.data))
  const min = Math.min(...dias)
  const max = Math.max(...dias)
  const x = (d) =>
    MARGEM.esquerda + (max === min ? plotL / 2 : ((d - min) / (max - min)) * plotL)
  const y = (v) => MARGEM.topo + plotA - (v / 100) * plotA

  const coords = pontos.map((p, i) => ({ ...p, cx: x(dias[i]), cy: y(p.percentual) }))
  const caminho = coords.map((c, i) => `${i ? 'L' : 'M'}${c.cx},${c.cy}`).join(' ')
  const ultimo = coords[coords.length - 1]

  function maisProximo(px) {
    let melhor = 0
    coords.forEach((c, i) => {
      if (Math.abs(c.cx - px) < Math.abs(coords[melhor].cx - px)) melhor = i
    })
    return melhor
  }

  function aoMover(e) {
    const rect = e.currentTarget.getBoundingClientRect()
    setAtivo(maisProximo(e.clientX - rect.left + MARGEM.esquerda))
  }

  function aoTeclar(e) {
    if (e.key === 'ArrowLeft') {
      e.preventDefault()
      setAtivo((i) => Math.max((i ?? coords.length - 1) - 1, 0))
    } else if (e.key === 'ArrowRight') {
      e.preventDefault()
      setAtivo((i) => Math.min((i ?? coords.length - 2) + 1, coords.length - 1))
    }
  }

  const pontoAtivo = ativo !== null ? coords[ativo] : null

  return (
    <div ref={ref} className="relative w-full" style={{ height: ALTURA }}>
      {largura > 0 && (
        <svg width={largura} height={ALTURA} className="block" aria-hidden="true">
          {TICKS_Y.map((t) => (
            <g key={t}>
              <line
                x1={MARGEM.esquerda}
                x2={MARGEM.esquerda + plotL}
                y1={y(t)}
                y2={y(t)}
                className="stroke-app-line"
                strokeWidth="1"
              />
              <text
                x={MARGEM.esquerda - 8}
                y={y(t)}
                dy="0.32em"
                textAnchor="end"
                className="fill-app-muted text-xs tabular-nums"
              >
                {t}%
              </text>
            </g>
          ))}

          <text
            x={coords[0].cx}
            y={ALTURA - 8}
            textAnchor={coords.length > 1 ? 'start' : 'middle'}
            className="fill-app-muted text-xs tabular-nums"
          >
            {formatarDiaMes(coords[0].data)}
          </text>
          {coords.length > 1 && max !== min && (
            <text
              x={ultimo.cx}
              y={ALTURA - 8}
              textAnchor="end"
              className="fill-app-muted text-xs tabular-nums"
            >
              {formatarDiaMes(ultimo.data)}
            </text>
          )}

          {pontoAtivo && (
            <line
              x1={pontoAtivo.cx}
              x2={pontoAtivo.cx}
              y1={MARGEM.topo}
              y2={MARGEM.topo + plotA}
              className="stroke-app-muted"
              strokeWidth="1"
            />
          )}

          {coords.length > 1 && (
            <path
              d={caminho}
              fill="none"
              className="stroke-chart-1"
              strokeWidth="2"
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          )}

          {coords.map((c, i) => (
            <circle
              key={i}
              cx={c.cx}
              cy={c.cy}
              r={ativo === i ? 6 : 4}
              className="fill-chart-1 stroke-app-surface"
              strokeWidth="2"
            />
          ))}

          <text
            x={ultimo.cx + 10}
            y={ultimo.cy}
            dy="0.32em"
            className="fill-app-fg text-xs font-medium tabular-nums"
          >
            {formatarPct(ultimo.percentual)}
          </text>
        </svg>
      )}

      {/* Camada de hover/teclado: o crosshair encontra a data mais próxima. */}
      <div
        tabIndex={0}
        role="img"
        aria-label={`Evolução do percentual de acerto em ${pontos.length} revisões. Use as setas para navegar.`}
        className="absolute rounded-md focus:outline-none focus-visible:ring-1 focus-visible:ring-app-muted"
        style={{ left: MARGEM.esquerda, top: MARGEM.topo, width: plotL, height: plotA }}
        onPointerMove={aoMover}
        onPointerLeave={() => setAtivo(null)}
        onFocus={() => setAtivo(coords.length - 1)}
        onBlur={() => setAtivo(null)}
        onKeyDown={aoTeclar}
      />

      {pontoAtivo && (
        <div
          role="status"
          className="pointer-events-none absolute z-10 rounded-lg border border-app-line bg-app-raised px-3 py-2 shadow-lg whitespace-nowrap"
          style={{
            left: Math.min(Math.max(pontoAtivo.cx, 70), Math.max(largura - 70, 70)),
            top: pontoAtivo.cy >= 64 ? pontoAtivo.cy - 64 : pontoAtivo.cy + 14,
            transform: 'translateX(-50%)',
          }}
        >
          <div className="text-sm font-semibold text-app-fg tabular-nums">
            {formatarPct(pontoAtivo.percentual)}
          </div>
          <div className="text-xs text-app-muted">{formatarData(pontoAtivo.data)}</div>
        </div>
      )}
    </div>
  )
}

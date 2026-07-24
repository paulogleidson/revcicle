import { useEffect, useState } from 'react'
import Badge from '../components/Badge'
import Button from '../components/Button'
import Card from '../components/Card'
import { apiGet } from '../lib/api'
import { formatarData, hojeIsoLocal } from '../lib/dates'

function StatusBadge({ conteudo }) {
  if (conteudo.proxima_revisao === null) {
    return <Badge variante="novo">Nunca revisado</Badge>
  }
  const hoje = hojeIsoLocal()
  if (conteudo.proxima_revisao < hoje) {
    return (
      <Badge variante="atrasado">
        Atrasado desde {formatarData(conteudo.proxima_revisao)}
      </Badge>
    )
  }
  return <Badge variante="hoje">Revisar hoje</Badge>
}

export default function DashboardPage({ onRegistrar, reloadKey }) {
  const [pendentes, setPendentes] = useState(null)
  const [erro, setErro] = useState(null)

  useEffect(() => {
    let cancelado = false
    setErro(null)
    apiGet('/revisoes/hoje')
      .then((dados) => {
        if (!cancelado) setPendentes(dados)
      })
      .catch((e) => {
        if (!cancelado) {
          setErro(e.message)
          setPendentes([])
        }
      })
    return () => {
      cancelado = true
    }
  }, [reloadKey])

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold text-app-fg">Visão geral</h1>
        <p className="text-sm text-app-muted mt-1">
          Conteúdos que você precisa revisar hoje.
        </p>
      </div>

      {erro && (
        <p className="text-sm text-status-atrasado-fg">
          Erro ao carregar: {erro}
        </p>
      )}

      {pendentes === null && <p className="text-app-muted">Carregando…</p>}

      {pendentes !== null && pendentes.length === 0 && !erro && (
        <Card className="p-6 sm:p-8 text-center">
          {/* Tabler: calendar-check (inline pra não puxar dep) */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            className="w-10 h-10 mx-auto text-app-muted mb-3"
          >
            <path d="M11.5 21h-5.5a2 2 0 0 1 -2 -2v-12a2 2 0 0 1 2 -2h12a2 2 0 0 1 2 2v4" />
            <path d="M16 3v4" />
            <path d="M8 3v4" />
            <path d="M4 11h16" />
            <path d="M15 19l2 2l4 -4" />
          </svg>
          <p className="text-app-fg font-medium">Nada pendente por hoje</p>
          <p className="text-sm text-app-muted mt-1">
            Cadastre conteúdos em "Meus Conteúdos" ou volte amanhã.
          </p>
        </Card>
      )}

      {pendentes !== null && pendentes.length > 0 && (
        <ul className="space-y-2 sm:space-y-3">
          {pendentes.map((c) => (
            <li key={c.id}>
              <Card className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
                <div className="min-w-0 space-y-1">
                  <div className="font-medium text-app-fg">{c.titulo}</div>
                  <div className="text-sm text-app-muted">{c.materia}</div>
                  <div className="pt-1">
                    <StatusBadge conteudo={c} />
                  </div>
                </div>
                <Button
                  variante="primario"
                  onClick={() => onRegistrar(c)}
                  className="shrink-0 self-start"
                >
                  Registrar revisão
                </Button>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

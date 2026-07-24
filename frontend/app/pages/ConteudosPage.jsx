import { useEffect, useState } from 'react'
import Button from '../components/Button'
import Card from '../components/Card'
import ConfirmModal from '../components/ConfirmModal'
import Input from '../components/Input'
import { apiDelete, apiGet, apiPost } from '../lib/api'
import { formatarData } from '../lib/dates'

export default function ConteudosPage({ onRegistrar, reloadKey }) {
  const [conteudos, setConteudos] = useState(null)
  const [erroLista, setErroLista] = useState(null)

  const [titulo, setTitulo] = useState('')
  const [materia, setMateria] = useState('')
  const [salvando, setSalvando] = useState(false)
  const [erroForm, setErroForm] = useState(null)

  const [apagandoId, setApagandoId] = useState(null)
  const [alvoParaApagar, setAlvoParaApagar] = useState(null)

  async function carregar() {
    setErroLista(null)
    try {
      const dados = await apiGet('/conteudos')
      setConteudos(dados)
    } catch (e) {
      setErroLista(e.message)
      setConteudos([])
    }
  }

  useEffect(() => {
    carregar()
  }, [reloadKey])

  async function criar(e) {
    e.preventDefault()
    setSalvando(true)
    setErroForm(null)
    try {
      await apiPost('/conteudos', { titulo, materia })
      setTitulo('')
      setMateria('')
      await carregar()
    } catch (e) {
      setErroForm(e.message)
    } finally {
      setSalvando(false)
    }
  }

  function pedirParaApagar(conteudo) {
    setAlvoParaApagar(conteudo)
  }

  async function confirmarApagar() {
    const c = alvoParaApagar
    if (!c) return
    setApagandoId(c.id)
    setErroLista(null)
    try {
      await apiDelete(`/conteudos/${c.id}`)
      setAlvoParaApagar(null)
      await carregar()
    } catch (e) {
      setErroLista(`Falha ao apagar: ${e.message}`)
    } finally {
      setApagandoId(null)
    }
  }

  function cancelarApagar() {
    setAlvoParaApagar(null)
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      <h1 className="text-2xl font-semibold text-app-fg">Meus Conteúdos</h1>

      <Card>
        <form onSubmit={criar} className="space-y-3">
          <h2 className="text-base font-medium text-app-fg">Novo conteúdo</h2>
          <Input
            type="text"
            placeholder="Nome do conteúdo"
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            required
          />
          <Input
            type="text"
            placeholder="Matéria"
            value={materia}
            onChange={(e) => setMateria(e.target.value)}
            required
          />
          {erroForm && (
            <p className="text-sm text-status-atrasado-fg">{erroForm}</p>
          )}
          <Button type="submit" variante="primario" disabled={salvando}>
            {salvando ? 'Salvando…' : 'Adicionar'}
          </Button>
        </form>
      </Card>

      <section>
        <div className="flex items-baseline justify-between mb-2">
          <h2 className="text-base font-medium text-app-fg">Conteúdos</h2>
          {conteudos !== null && (
            <span className="text-xs text-app-muted">
              {conteudos.length}
            </span>
          )}
        </div>

        {erroLista && (
          <p className="text-sm text-status-atrasado-fg mb-2">{erroLista}</p>
        )}

        {conteudos === null && <p className="text-app-muted">Carregando…</p>}

        {conteudos !== null && conteudos.length === 0 && !erroLista && (
          <Card>
            <p className="text-app-muted">
              Nenhum conteúdo cadastrado ainda. Use o formulário acima.
            </p>
          </Card>
        )}

        {conteudos !== null && conteudos.length > 0 && (
          <ul className="space-y-2 sm:space-y-3">
            {conteudos.map((c) => (
              <li key={c.id}>
                <Card
                  padding={false}
                  className="flex items-stretch overflow-hidden"
                >
                  <button
                    type="button"
                    onClick={() => onRegistrar(c)}
                    className="flex-1 text-left px-4 py-3 sm:px-5 sm:py-4 hover:bg-app-raised transition"
                  >
                    <div className="font-medium text-app-fg">{c.titulo}</div>
                    <div className="text-sm text-app-muted">{c.materia}</div>
                    <div className="text-xs text-app-muted mt-1">
                      {c.proxima_revisao
                        ? `Próxima revisão: ${formatarData(c.proxima_revisao)}`
                        : 'Nunca revisado'}
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={() => pedirParaApagar(c)}
                    disabled={apagandoId === c.id}
                    aria-label={`Apagar ${c.titulo}`}
                    className="inline-flex items-center justify-center gap-1.5 px-2.5 py-1.5 border-l border-app-line text-sm text-status-atrasado-fg hover:bg-status-atrasado-bg disabled:opacity-50 transition-colors duration-150"
                  >
                    {apagandoId === c.id ? (
                      <span>…</span>
                    ) : (
                      <>
                        {/* Tabler: trash (inline pra não puxar dep) */}
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.75"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          aria-hidden="true"
                          className="w-4 h-4"
                        >
                          <path d="M4 7l16 0" />
                          <path d="M10 11l0 6" />
                          <path d="M14 11l0 6" />
                          <path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12" />
                          <path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3" />
                        </svg>
                        <span>Apagar</span>
                      </>
                    )}
                  </button>
                </Card>
              </li>
            ))}
          </ul>
        )}
      </section>

      <ConfirmModal
        aberto={alvoParaApagar !== null}
        titulo="Apagar conteúdo?"
        mensagem={
          alvoParaApagar
            ? `"${alvoParaApagar.titulo}" e todas as revisões desse conteúdo vão ser removidas. Essa ação não tem volta.`
            : null
        }
        textoConfirmar="Apagar"
        destrutivo
        confirmando={apagandoId !== null}
        onConfirmar={confirmarApagar}
        onCancelar={cancelarApagar}
      />
    </div>
  )
}

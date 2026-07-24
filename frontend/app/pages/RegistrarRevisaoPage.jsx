import { useState } from 'react'
import Button from '../components/Button'
import Card from '../components/Card'
import Input from '../components/Input'
import { apiPost } from '../lib/api'
import { hojeIsoLocal } from '../lib/dates'

function formatarPercentual(p) {
  return p % 1 === 0 ? String(p) : p.toFixed(1)
}

export default function RegistrarRevisaoPage({ conteudo, onCancelar, onSucesso }) {
  const [feitas, setFeitas] = useState('')
  const [acertadas, setAcertadas] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState(null)

  const feitasN = Number.parseInt(feitas, 10)
  const acertadasN = Number.parseInt(acertadas, 10)

  const camposPreenchidos = feitas !== '' && acertadas !== ''
  const inteirosValidos =
    Number.isInteger(feitasN) && Number.isInteger(acertadasN)
  const dentroDosLimites =
    inteirosValidos &&
    feitasN >= 1 &&
    acertadasN >= 0 &&
    acertadasN <= feitasN

  const percentual = dentroDosLimites ? (acertadasN / feitasN) * 100 : null
  const percentualParaEnviar =
    percentual === null ? null : Math.round(percentual * 100) / 100

  async function submeter(e) {
    e.preventDefault()
    setErro(null)
    if (!dentroDosLimites) {
      setErro(
        'Preencha "Questões feitas" (≥ 1) e "Questões acertadas" (≥ 0, no máximo igual a feitas).'
      )
      return
    }
    setEnviando(true)
    try {
      await apiPost('/sessoes', {
        conteudo_id: conteudo.id,
        percentual: percentualParaEnviar,
        data: hojeIsoLocal(),
      })
      onSucesso()
    } catch (e) {
      setErro(e.message)
      setEnviando(false)
    }
  }

  return (
    <div className="max-w-[480px] mx-auto space-y-4">
      <div>
        <h1 className="text-2xl font-semibold text-app-fg">
          Registrar revisão
        </h1>
        <p className="text-sm text-app-muted mt-1">
          {conteudo.titulo}
          <span className="text-app-muted/70"> · {conteudo.materia}</span>
        </p>
      </div>

      <Card>
        <form onSubmit={submeter} className="space-y-3">
          {/* type="text" + inputMode="numeric" + regex → aceita SÓ dígitos,
              nada de "e", "+", "-", "." ou letras que type="number" ainda
              deixa passar em alguns browsers. */}
          <Input
            label="Questões feitas"
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            required
            value={feitas}
            onChange={(e) => setFeitas(e.target.value.replace(/\D/g, ''))}
            autoFocus
          />

          <Input
            label="Questões acertadas"
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            required
            value={acertadas}
            onChange={(e) => setAcertadas(e.target.value.replace(/\D/g, ''))}
          />

          {camposPreenchidos && (
            <p
              className={
                'text-sm ' +
                (dentroDosLimites
                  ? 'text-app-muted'
                  : 'text-status-atrasado-fg')
              }
            >
              {dentroDosLimites
                ? `${acertadasN}/${feitasN} = ${formatarPercentual(percentual)}%`
                : 'Acertadas não pode ser maior que feitas, e feitas precisa ser ≥ 1.'}
            </p>
          )}

          {erro && (
            <p className="text-sm text-status-atrasado-fg">{erro}</p>
          )}

          <div className="flex gap-2 pt-1">
            <Button
              type="submit"
              variante="primario"
              disabled={enviando || !dentroDosLimites}
            >
              {enviando ? 'Enviando…' : 'Registrar'}
            </Button>
            <Button
              type="button"
              variante="secundario"
              onClick={onCancelar}
              disabled={enviando}
            >
              Cancelar
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}

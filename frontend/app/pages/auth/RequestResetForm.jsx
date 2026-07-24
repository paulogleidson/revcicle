import { useState } from 'react'
import Button from '../../components/Button'
import Input from '../../components/Input'
import { traduzirErroAuth } from '../../lib/authErrors'
import { supabase } from '../../lib/supabaseClient'
import AuthHero from './AuthHero'

export default function RequestResetForm({ onVoltar }) {
  const [email, setEmail] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState(null)
  const [enviado, setEnviado] = useState(false)

  async function submeter(e) {
    e.preventDefault()
    setErro(null)
    setEnviando(true)
    // O Supabase manda um link pro email; quando o usuário clicar, ele volta
    // pro app com um hash de recovery. O event PASSWORD_RECOVERY dispara e
    // aí a gente mostra o form de nova senha.
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: window.location.origin,
    })
    if (error) {
      setErro(traduzirErroAuth(error.message))
    } else {
      setEnviado(true)
    }
    setEnviando(false)
  }

  if (enviado) {
    return (
      <AuthHero>
        <div className="space-y-4">
          <h1 className="text-2xl font-semibold text-app-fg">
            Verifique seu email
          </h1>
          <p className="text-sm text-app-muted">
            Se existir uma conta com{' '}
            <span className="text-app-fg">{email}</span>, você vai receber um
            link pra definir uma nova senha. Confira a caixa de entrada (e o
            spam).
          </p>
          <Button type="button" variante="secundario" onClick={onVoltar}>
            Voltar pro login
          </Button>
        </div>
      </AuthHero>
    )
  }

  return (
    <AuthHero>
      <form onSubmit={submeter} className="space-y-4">
        <div>
          <h1 className="text-2xl font-semibold text-app-fg">
            Esqueceu sua senha?
          </h1>
          <p className="text-sm text-app-muted mt-1">
            Digite seu email que a gente manda um link pra você redefinir.
          </p>
        </div>

        <Input
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoFocus
        />

        {erro && <p className="text-sm text-status-atrasado-fg">{erro}</p>}

        <div className="flex gap-2">
          <Button
            type="submit"
            variante="primario"
            disabled={enviando}
            className="flex-1"
          >
            {enviando ? 'Enviando…' : 'Enviar link'}
          </Button>
          <Button
            type="button"
            variante="secundario"
            onClick={onVoltar}
            disabled={enviando}
            className="flex-1"
          >
            Cancelar
          </Button>
        </div>
      </form>
    </AuthHero>
  )
}

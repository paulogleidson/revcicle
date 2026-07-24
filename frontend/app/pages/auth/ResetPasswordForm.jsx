import { useState } from 'react'
import Button from '../../components/Button'
import Input from '../../components/Input'
import { traduzirErroAuth } from '../../lib/authErrors'
import { supabase } from '../../lib/supabaseClient'
import AuthHero from './AuthHero'

// Renderizado quando o Supabase dispara `PASSWORD_RECOVERY` (usuário voltou
// pelo link do email). Nesse momento existe uma sessão temporária, então
// `updateUser({password})` funciona.
export default function ResetPasswordForm({ onConcluido }) {
  const [senha, setSenha] = useState('')
  const [confirmacao, setConfirmacao] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState(null)

  const senhaValida = senha.length >= 6
  const igual = senha === confirmacao
  const podeSubmeter = senhaValida && igual

  async function submeter(e) {
    e.preventDefault()
    setErro(null)
    if (!podeSubmeter) {
      setErro(
        !senhaValida
          ? 'A senha precisa ter pelo menos 6 caracteres.'
          : 'As duas senhas não são iguais.'
      )
      return
    }
    setEnviando(true)
    const { error } = await supabase.auth.updateUser({ password: senha })
    if (error) {
      setErro(traduzirErroAuth(error.message))
      setEnviando(false)
      return
    }
    onConcluido()
  }

  return (
    <AuthHero>
      <form onSubmit={submeter} className="space-y-4">
        <div>
          <h1 className="text-2xl font-semibold text-app-fg">Nova senha</h1>
          <p className="text-sm text-app-muted mt-1">
            Escolha uma senha nova pra sua conta. Mínimo 6 caracteres.
          </p>
        </div>

        <Input
          label="Nova senha"
          type="password"
          autoComplete="new-password"
          required
          minLength={6}
          value={senha}
          onChange={(e) => setSenha(e.target.value)}
          autoFocus
        />

        <Input
          label="Confirmar senha"
          type="password"
          autoComplete="new-password"
          required
          minLength={6}
          value={confirmacao}
          onChange={(e) => setConfirmacao(e.target.value)}
        />

        {confirmacao !== '' && !igual && (
          <p className="text-sm text-status-atrasado-fg">
            As duas senhas não são iguais.
          </p>
        )}
        {erro && <p className="text-sm text-status-atrasado-fg">{erro}</p>}

        <Button
          type="submit"
          variante="primario"
          disabled={enviando || !podeSubmeter}
          className="w-full"
        >
          {enviando ? 'Salvando…' : 'Salvar nova senha'}
        </Button>
      </form>
    </AuthHero>
  )
}

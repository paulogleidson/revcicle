import { useState } from 'react'
import Button from '../../components/Button'
import Input from '../../components/Input'
import { traduzirErroAuth } from '../../lib/authErrors'
import { supabase } from '../../lib/supabaseClient'
import AuthHero from './AuthHero'

export default function LoginForm({ onEsqueciSenha }) {
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState(null)
  const [aviso, setAviso] = useState(null)
  const [enviando, setEnviando] = useState(false)

  async function entrar(e) {
    e.preventDefault()
    setErro(null)
    setAviso(null)
    setEnviando(true)
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password: senha,
    })
    if (error) setErro(traduzirErroAuth(error.message))
    setEnviando(false)
  }

  async function cadastrar() {
    setErro(null)
    setAviso(null)
    setEnviando(true)
    const { data, error } = await supabase.auth.signUp({
      email,
      password: senha,
    })
    if (error) {
      setErro(traduzirErroAuth(error.message))
    } else if (!data.session) {
      setAviso(
        'Cadastro criado. Confira seu email pra confirmar antes de entrar.'
      )
    }
    setEnviando(false)
  }

  return (
    <AuthHero>
      <form onSubmit={entrar} className="space-y-4">
        <h1 className="text-2xl font-semibold text-app-fg">Entrar</h1>

        <Input
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <Input
          label="Senha"
          type="password"
          autoComplete="current-password"
          required
          minLength={6}
          value={senha}
          onChange={(e) => setSenha(e.target.value)}
        />

        {erro && <p className="text-sm text-status-atrasado-fg">{erro}</p>}
        {aviso && <p className="text-sm text-app-fg">{aviso}</p>}

        <div className="flex gap-2">
          <Button
            type="submit"
            variante="primario"
            disabled={enviando}
            className="flex-1"
          >
            Entrar
          </Button>
          <Button
            type="button"
            variante="secundario"
            onClick={cadastrar}
            disabled={enviando}
            className="flex-1"
          >
            Cadastrar
          </Button>
        </div>

        <div className="text-center pt-1">
          <button
            type="button"
            onClick={onEsqueciSenha}
            className="text-sm text-app-muted hover:text-app-fg underline transition-colors"
          >
            Esqueci minha senha
          </button>
        </div>
      </form>
    </AuthHero>
  )
}

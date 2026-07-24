import { useEffect, useState } from 'react'
import Footer from './components/Footer'
import Logo from './components/Logo'
import AjudaPage from './pages/AjudaPage'
import ConteudosPage from './pages/ConteudosPage'
import DashboardPage from './pages/DashboardPage'
import RegistrarRevisaoPage from './pages/RegistrarRevisaoPage'
import LoginForm from './pages/auth/LoginForm'
import RequestResetForm from './pages/auth/RequestResetForm'
import ResetPasswordForm from './pages/auth/ResetPasswordForm'
import { supabase } from './lib/supabaseClient'

function BrandRow({ className = '' }) {
  return (
    <div className={`flex items-center gap-2 text-app-fg ${className}`}>
      <Logo className="w-7 h-7" />
      <span className="text-lg font-semibold tracking-tight">RevCicle</span>
    </div>
  )
}

// Wrapper de layout das telas autenticadas — centraliza no 720 col.
// Footer no fim, sempre visível.
function Layout({ children }) {
  return (
    <div className="min-h-screen bg-app-bg flex flex-col">
      <div className="mx-auto max-w-[720px] w-full px-4 sm:px-6 lg:px-8 pt-8 sm:pt-10 pb-8 flex-1">
        {children}
      </div>
      <Footer />
    </div>
  )
}

function TabButton({ ativo, children, onClick }) {
  const base =
    'h-10 px-4 rounded-lg text-sm font-medium transition text-center'
  const estilo = ativo
    ? 'bg-app-fg text-app-bg'
    : 'bg-app-surface text-app-fg border border-app-line hover:bg-app-raised'
  return (
    <button type="button" onClick={onClick} className={`${base} ${estilo}`}>
      {children}
    </button>
  )
}

function ShellHeader({ email, onSair, tela, setTela }) {
  return (
    <header className="flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4 mb-6 sm:mb-8">
      <nav className="grid grid-cols-3 gap-2 sm:flex sm:gap-2">
        <TabButton
          ativo={tela === 'dashboard'}
          onClick={() => setTela('dashboard')}
        >
          Visão geral
        </TabButton>
        <TabButton
          ativo={tela === 'conteudos'}
          onClick={() => setTela('conteudos')}
        >
          Meus Conteúdos
        </TabButton>
        <TabButton
          ativo={tela === 'ajuda'}
          onClick={() => setTela('ajuda')}
        >
          Ajuda
        </TabButton>
      </nav>
      <div className="flex items-center justify-end gap-3 text-sm text-app-muted">
        <span className="truncate max-w-[200px]">{email}</span>
        <button
          type="button"
          onClick={onSair}
          className="underline hover:text-app-fg"
        >
          Sair
        </button>
      </div>
    </header>
  )
}

export default function App() {
  const [session, setSession] = useState(null)
  const [carregandoSessao, setCarregandoSessao] = useState(true)

  // Modo do fluxo de auth. 'password-reset' tem precedência sobre `session`
  // porque o Supabase cria uma sessão temporária durante o recovery e a
  // gente NÃO quer mostrar o Dashboard nesse meio-tempo.
  const [modoAuth, setModoAuth] = useState('login') // 'login' | 'recover-request' | 'password-reset'

  const [tela, setTela] = useState('dashboard')
  const [conteudoAlvo, setConteudoAlvo] = useState(null)
  const [origemRegistrar, setOrigemRegistrar] = useState('dashboard')
  const [reloadDashboard, setReloadDashboard] = useState(0)
  const [reloadConteudos, setReloadConteudos] = useState(0)

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session)
      setCarregandoSessao(false)
    })

    const { data: sub } = supabase.auth.onAuthStateChange((evento, s) => {
      setSession(s)
      if (evento === 'PASSWORD_RECOVERY') {
        // Usuário chegou pelo link do email de reset — mostra form de nova senha.
        setModoAuth('password-reset')
      }
    })
    return () => sub.subscription.unsubscribe()
  }, [])

  async function sair() {
    await supabase.auth.signOut()
    setTela('dashboard')
    setConteudoAlvo(null)
    setModoAuth('login')
  }

  function irRegistrar(conteudo) {
    setOrigemRegistrar(tela === 'conteudos' ? 'conteudos' : 'dashboard')
    setConteudoAlvo(conteudo)
    setTela('registrar')
  }

  function cancelarRegistrar() {
    setConteudoAlvo(null)
    setTela(origemRegistrar)
  }

  function apósRegistrar() {
    setConteudoAlvo(null)
    setTela(origemRegistrar)
    if (origemRegistrar === 'conteudos') {
      setReloadConteudos((k) => k + 1)
    } else {
      setReloadDashboard((k) => k + 1)
    }
  }

  if (carregandoSessao) {
    return (
      <Layout>
        <BrandRow className="mb-6 sm:mb-8" />
        <p className="text-app-muted">Carregando…</p>
      </Layout>
    )
  }

  // Reset de senha tem precedência: o usuário chegou pelo link do email e a
  // sessão temporária existe; só saímos desse modo quando ele salva.
  if (modoAuth === 'password-reset') {
    return (
      <ResetPasswordForm
        onConcluido={() => setModoAuth('login')}
      />
    )
  }

  if (session) {
    return (
      <Layout>
        <BrandRow className="mb-4 sm:mb-6" />
        <ShellHeader
          email={session.user.email}
          onSair={sair}
          tela={tela}
          setTela={(nova) => {
            setTela(nova)
            setConteudoAlvo(null)
          }}
        />
        <main>
          {tela === 'dashboard' && (
            <DashboardPage
              onRegistrar={irRegistrar}
              reloadKey={reloadDashboard}
            />
          )}
          {tela === 'conteudos' && (
            <ConteudosPage
              onRegistrar={irRegistrar}
              reloadKey={reloadConteudos}
            />
          )}
          {tela === 'ajuda' && <AjudaPage />}
          {tela === 'registrar' && conteudoAlvo && (
            <RegistrarRevisaoPage
              conteudo={conteudoAlvo}
              onCancelar={cancelarRegistrar}
              onSucesso={apósRegistrar}
            />
          )}
        </main>
      </Layout>
    )
  }

  if (modoAuth === 'recover-request') {
    return <RequestResetForm onVoltar={() => setModoAuth('login')} />
  }

  return <LoginForm onEsqueciSenha={() => setModoAuth('recover-request')} />
}

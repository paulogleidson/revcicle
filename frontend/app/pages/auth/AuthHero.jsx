import Card from '../../components/Card'
import Footer from '../../components/Footer'
import Logo from '../../components/Logo'

// Layout comum das telas de auth (login, esqueci senha, nova senha).
// Brand grande e centralizada, card centralizado no viewport, footer no fim.
export default function AuthHero({ children }) {
  return (
    <div className="min-h-screen bg-app-bg flex flex-col">
      <div className="flex-1 flex items-center justify-center px-4 py-10">
        <div className="w-full max-w-[480px]">
          <div className="flex items-center justify-center gap-3 text-app-fg mb-8 sm:mb-10">
            <Logo className="w-12 h-12" />
            <span className="text-3xl font-semibold tracking-tight">
              RevCicle
            </span>
          </div>
          <Card>{children}</Card>
        </div>
      </div>
      <Footer />
    </div>
  )
}

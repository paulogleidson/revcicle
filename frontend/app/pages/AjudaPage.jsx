import Card from '../components/Card'

function Pergunta({ children, resposta }) {
  return (
    <div className="space-y-1">
      <p className="text-sm font-medium text-app-fg">{children}</p>
      <p className="text-sm text-app-muted leading-relaxed">{resposta}</p>
    </div>
  )
}

export default function AjudaPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-app-fg">Ajuda</h1>

      <Card>
        <section className="space-y-3">
          <h2 className="text-lg font-medium text-app-fg">O que é este app</h2>
          <p className="text-sm text-app-muted leading-relaxed">
            Um sistema de revisão espaçada: você cadastra o que está estudando,
            e o app calcula sozinho quando você precisa revisar de novo —
            baseado no seu desempenho, não em um calendário fixo.
          </p>
        </section>
      </Card>

      <Card>
        <section className="space-y-3">
          <h2 className="text-lg font-medium text-app-fg">Como funciona</h2>
          <ol className="list-decimal list-outside pl-5 space-y-2 text-sm text-app-muted leading-relaxed marker:text-app-muted">
            <li>
              Cadastre um conteúdo em "Meus Conteúdos" (ex: "Direito
              Constitucional")
            </li>
            <li>
              Quando for revisar, informe quantas questões fez e quantas
              acertou
            </li>
            <li>
              O app calcula a próxima data automaticamente:
              <ul className="list-disc list-outside pl-5 mt-1 space-y-1 marker:text-app-muted">
                <li>100% de acerto → revisa de novo em 30 dias</li>
                <li>70% a 99% → revisa em 7 dias</li>
                <li>Abaixo de 70% → revisa amanhã</li>
              </ul>
            </li>
            <li>O Dashboard sempre mostra o que está pendente hoje</li>
          </ol>
        </section>
      </Card>

      <Card>
        <section className="space-y-4">
          <h2 className="text-lg font-medium text-app-fg">
            Perguntas frequentes
          </h2>
          <div className="space-y-4">
            <Pergunta resposta="É um conteúdo que você cadastrou mas ainda não fez a primeira revisão.">
              O que significa "nunca revisado"?
            </Pergunta>
            <Pergunta resposta='Sim, em "Meus Conteúdos", clicando no botão de apagar.'>
              Posso apagar um conteúdo?
            </Pergunta>
            <Pergunta resposta="Sim — só você tem acesso ao que cadastra.">
              Meus dados são privados?
            </Pergunta>
          </div>
        </section>
      </Card>
    </div>
  )
}

# Projeto: App de Revisão Espaçada (Spaced Repetition)

## Contexto e origem do projeto
Ideia nasceu de um problema real: minha irmã usava uma planilha paga (R$300)
para controlar revisão de conteúdo de estudos, mas era difícil de usar e ela
desistiu. Este projeto recria essa lógica com uma interface amigável.

Está sendo construído como projeto de portfólio, mas desenhado desde o início
como SaaS multi-tenant (múltiplos usuários, não só uso pessoal).

## O que o sistema faz
O usuário registra o quanto acertou ao revisar um conteúdo (%). O sistema
calcula automaticamente quando ele deve revisar aquele conteúdo de novo,
baseado no desempenho — quanto melhor o resultado, mais tempo até a próxima
revisão (repetição espaçada adaptativa, similar à lógica do Anki/SM-2).

## Stack
- Backend: FastAPI + PostgreSQL
- Banco: hospedado no Supabase (ou Neon), não é local/SQLite
- Frontend: React + Vite + Tailwind CSS (responsivo — precisa funcionar bem
  em tablet também, não só desktop/mobile)
- Deploy:
  - Frontend → Vercel
  - Backend → Railway (ou Render)
  - Banco → Supabase/Neon
- Auth: Supabase Auth (não reinventar JWT do zero, ir mais rápido)
- CORS precisa estar configurado no FastAPI, já que frontend e backend
  ficam em domínios diferentes

## Escopo do MVP — NÃO EXPANDIR SEM AVISAR
3 tabelas:
- usuarios (id, email, senha_hash)
- conteudos (id, usuario_id, titulo, materia)
- sessoes_revisao (id, conteudo_id, data, percentual, proxima_revisao)

4 telas:
- Login / Cadastro
- Dashboard (lista o que precisa revisar hoje)
- Meus Conteúdos (criar/listar conteúdos)
- Registrar Revisão (input de %, sistema recalcula automaticamente)

No MVP, a "notificação" é a própria tela do Dashboard — o usuário abre o
app e vê o que precisa revisar. Não precisa de canal externo ainda.

## Fora do escopo do MVP (backlog V2 — não implementar agora)
- Grade semanal (usuário associa matéria a dia da semana, ex: segunda →
  matemática, terça → português). Tabela sugerida para o futuro:
  grade_semanal (id, usuario_id, dia_semana, materia, ordem)
- Notificação via WhatsApp (não Telegram) quando houver revisão pendente.
  Avaliar futuramente: WhatsApp Business API (Meta Cloud API) ou Twilio
  como provedor.
- Gráficos de histórico/evolução de desempenho por conteúdo
- Planos pagos (Stripe)
- App mobile nativo

## Regra de negócio (core do produto)
Ao registrar uma sessão de revisão, calcular a próxima data assim:
- 100% de acerto → próxima revisão em +30 dias
- 70% a 99% de acerto → próxima revisão em +7 dias
- Menos de 70% → próxima revisão em +1 dia

Implementar como função pura e testável, ex:
def calcular_proxima_revisao(percentual: float, data_atual: date) -> date

## Convenções de código
- Nomes de tabelas e campos em português, snake_case
- Commits pequenos e frequentes, um por funcionalidade
- Não criar funcionalidades fora do escopo do MVP sem perguntar antes
- Trabalhar em etapas pequenas: uma tarefa por vez, aguardando revisão
  antes de avançar para a próxima
# RevCicle

Sistema de revisão espaçada adaptativa: você cadastra o que está estudando e o app calcula sozinho quando revisar de novo, com base no seu desempenho — não em um calendário fixo.

## Motivação

Nasceu de um problema real. Minha irmã pagou R$300 numa planilha de controle de revisões para concurso. Usou por algumas semanas e desistiu — a planilha era difícil de operar, precisava editar fórmulas manualmente, arrastar linhas, nada era intuitivo.

O RevCicle recria a lógica dela (repetição espaçada adaptativa) numa interface que não exige planilha nem manual: cadastra o conteúdo, registra o resultado da revisão, e o app decide quando chamar de volta.

## Como funciona

Ao registrar uma revisão, o usuário informa quantas questões fez e quantas acertou. O sistema calcula automaticamente a próxima data com base no percentual:

- **100%** de acerto → próxima revisão em **30 dias**
- **70% a 99%** → próxima revisão em **7 dias**
- **abaixo de 70%** → próxima revisão em **1 dia**

Quanto melhor o desempenho, maior o intervalo. É similar à lógica do Anki/SM-2, simplificada para o caso de estudo por questões.

O Dashboard sempre mostra o que está pendente hoje (atrasados, do dia, e conteúdos ainda nunca revisados). O usuário só precisa abrir o app quando aparecer algo na lista.

## Stack

- **Backend:** FastAPI + SQLAlchemy 2.0
- **Banco:** PostgreSQL (hospedado no Supabase)
- **Frontend:** React + Vite + Tailwind CSS v4
- **Auth:** Supabase Auth com validação de JWT **ES256 via JWKS** (chaves assimétricas)
- **Deploy:** Vercel (frontend) + Render (backend) + Supabase (banco + auth)

## Destaques técnicos

- **Validação de JWT assimétrica.** O Supabase migrou de HS256 (shared secret) para JWT signing keys ES256; o backend usa `PyJWKClient` (do PyJWT) pra baixar/cachear a chave pública do endpoint JWKS do projeto e validar assinatura elíptica localmente. Nenhum secret compartilhado entre frontend e backend.
- **44 testes automatizados no backend** (`pytest`), cobrindo: isolamento por usuário nas rotas (ninguém apaga/lê conteúdo alheio), cascade de sessões ao deletar conteúdo, os limites exatos da regra de negócio (0%, 69.99%, 70%, 99%, 99.9%, 100%), e o fluxo completo de auth Supabase (assinatura inválida, `aud` errada, expirado, get-or-create de usuário novo, JWKS não encontrando kid).
- **Regra de negócio isolada como função pura.** `calcular_proxima_revisao(percentual, data_atual) -> date` fica em `app/services/revisao.py` sem depender de FastAPI, SQLAlchemy ou request — trivialmente testável e portável se um dia virar CLI, worker ou cálculo do lado do frontend.
- **Design system consistente sem CSS-in-JS.** Tokens de cor/tipografia declarados em `@theme` do Tailwind v4 (uma fonte de verdade); componentes reutilizáveis (`Button`, `Input`, `Card`, `Badge`, `ConfirmModal`, `Logo`, `Footer`) compartilhados entre as 5 telas — nada de estilo repetido ou valor mágico espalhado.

## Como rodar localmente

Requer Python 3.11+, Node 22+ e uma conta gratuita no [Supabase](https://supabase.com).

### 1. Banco + Auth

Crie um projeto novo no Supabase. Copie o conteúdo de `backend/schema.sql` no **SQL Editor** e execute — isso cria as três tabelas (`usuarios`, `conteudos`, `sessoes_revisao`). Anote a `DATABASE_URL`, a URL do projeto, a `anon key` e a `JWKS URL` (`https://<PROJECT_REF>.supabase.co/auth/v1/.well-known/jwks.json`).

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate            # Windows (PowerShell/Git Bash)
# source venv/bin/activate       # Linux/Mac
pip install -r requirements-dev.txt
cp .env.example .env             # preenche DATABASE_URL e SUPABASE_JWKS_URL
uvicorn app.main:app --reload    # sobe em http://127.0.0.1:8000
```

Testes:

```bash
pytest
```

### 3. Frontend

Em outro terminal:

```bash
cd frontend
npm install
cp .env.example .env             # preenche VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL
npm run dev                      # sobe em http://localhost:5173
```

Também é preciso liberar `http://localhost:5173/**` em **Authentication → URL Configuration → Redirect URLs** no dashboard do Supabase pro fluxo de reset de senha funcionar.

## Deploy

App no ar em **[revcicle.vercel.app](https://revcicle.vercel.app)**.

Arquitetura em produção:

- **Frontend** — Vercel, deploy automático do `main` (Vite + assets estáticos servidos pela CDN da Vercel).
- **Backend** — Render Free tier em `revcicle.onrender.com`, deploy automático do `main`. Como o Free hiberna com 15min sem tráfego, um monitor externo (UptimeRobot) pinga `/health` a cada 5min pra manter o container quente.
- **Banco + Auth** — Supabase. Conexão via **Transaction Pooler** (porta 6543, IPv4) porque o Render Free só sai por IPv4 e a direct connection do Supabase é IPv6-only nos planos gratuitos.
- **CORS** restringido no backend ao domínio da Vercel + `localhost:5173`; nada de `allow_origins=["*"]` em produção.

---

Desenvolvido por [Paulo Gleidson](https://www.paulogleidsondev.com.br).

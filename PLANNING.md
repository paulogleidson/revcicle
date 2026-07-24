# Checklist do Projeto

## Setup
- [x] Estrutura de pastas do backend (FastAPI)
- [x] Conexão com banco (Supabase/Postgres) — SQLAlchemy engine em
      `backend/app/database.py`, lê `DATABASE_URL` do `.env`
- [x] Schema SQL das 3 tabelas — `backend/schema.sql` (aplicar
      manualmente no Supabase/Neon SQL editor); models equivalentes
      em `backend/app/models.py`
- [x] Configurar Supabase Auth — `get_current_user_id()` valida JWT
      **ES256** (JWT signing keys assimétricas) usando o endpoint JWKS
      público (`SUPABASE_JWKS_URL`), extrai o `sub`, faz get-or-create
      em `usuarios` (via `supabase_uid`) e devolve o `int` local.
      Assinatura da dependency preservada — routers intactos.

## Backend
- [x] Regra de negócio: `calcular_proxima_revisao(percentual, data_atual)`
      em `backend/app/services/revisao.py` + testes em
      `backend/tests/test_revisao.py` (9 casos, todos passam)
- [x] Endpoint: criar conteúdo — `POST /conteudos`
- [x] Endpoint: listar conteúdos — `GET /conteudos`
      (agora inclui `proxima_revisao` via LEFT JOIN com a última sessão)
- [x] Endpoint: apagar conteúdo — `DELETE /conteudos/{id}`
      (cascata ORM apaga sessoes_revisao vinculadas; 404 se não pertencer
      ao usuário; ambos em `backend/app/routers/conteudos.py`; usuario_id
      ainda vem do mock — ver seção Setup)
- [x] Endpoint: registrar sessão de revisão — `POST /sessoes`
      (chama `calcular_proxima_revisao` e grava `proxima_revisao`;
      valida que `conteudo_id` pertence ao usuário)
- [x] Endpoint: listar revisões pendentes de hoje — `GET /revisoes/hoje`
      (retorna `ConteudoRevisaoOut`s: conteúdos SEM sessão OU cuja última
      sessão tem `proxima_revisao <= hoje`; ambos em
      `backend/app/routers/sessoes.py`)
- [ ] CORS configurado para aceitar domínio da Vercel

## Frontend
- [x] Tela de Login/Cadastro — `frontend/app/App.jsx`
      (email + senha usando `supabase.auth.signInWithPassword` /
      `supabase.auth.signUp`; após login exibe "Login OK" temporário
      até haver rotas)
- [x] Tela de Ajuda — `frontend/app/pages/AjudaPage.jsx` (nova aba no
      shell com FAQ estático) + rodapé com crédito ao autor
      (`components/Footer.jsx`) em todas as telas.
- [x] Tela de Dashboard — `frontend/app/pages/DashboardPage.jsx`
      (`GET /revisoes/hoje`, badges "Novo"/"Atrasado desde …"/"Hoje";
      cada item tem botão "Registrar revisão" que abre a tela
      correspondente)
- [x] Tela de Meus Conteúdos — `frontend/app/pages/ConteudosPage.jsx`
      (lista `GET /conteudos` + formulário `POST /conteudos`; JWT do
      Supabase enviado no `Authorization: Bearer` via helper
      `app/lib/api.js`; renderizada depois do login por troca de
      estado no `App.jsx`, sem router ainda)
- [x] Tela de Registrar Revisão — `frontend/app/pages/RegistrarRevisaoPage.jsx`
      (input de percentual 0-100; `POST /sessoes` com data de hoje;
      após sucesso volta pro Dashboard e força reload da lista)
- [x] Identidade visual escura consistente nas 4 telas — tokens CSS
      globais em `frontend/app/index.css`, componentes reutilizáveis
      em `frontend/app/components/` (Button, Input, Card, Badge,
      ConfirmModal), responsivo mobile / tablet / desktop
- [ ] Layout responsivo testado em tablet — desktop e mobile já
      validados; tablet (~768px) fica na estrutura do CSS mas ainda
      não abri o navegador nessa largura pra conferir visualmente

## Escopo do MVP — o que NÃO existe (decisão intencional)

- **Sem notificação ativa.** O MVP não tem WhatsApp, e-mail, push,
  Telegram nem qualquer canal externo que avise o usuário. A
  "notificação" é o próprio usuário abrir o Dashboard e ver os
  conteúdos que precisam ser revisados hoje (badges "Nunca revisado",
  "Revisar hoje", "Atrasado desde …"). Isso está alinhado com o
  CLAUDE.md ("No MVP, a 'notificação' é a própria tela do Dashboard").
- Isso NÃO é pendência esquecida — é decisão de escopo pra manter o
  MVP viável. Notificação via WhatsApp já está registrada como item
  do Backlog V2 abaixo; quando for feita, será via WhatsApp Business
  API (Meta Cloud) ou Twilio, não Telegram.

## Deploy
- [ ] Backend no Railway
- [ ] Frontend na Vercel
- [ ] Banco no Supabase/Neon
- [ ] Variáveis de ambiente configuradas em todos os serviços

## Backlog V2 (não fazer agora, só registrar)
- [ ] Grade semanal (dia da semana → matéria)
- [ ] Notificação via WhatsApp
- [ ] Gráficos de histórico por conteúdo
- [ ] Planos pagos (Stripe)

## Notas / decisões tomadas
(Claude Code: registre aqui decisões importantes tomadas durante o
desenvolvimento)

- 2026-07-23 — Estrutura inicial do backend criada em `/backend`:
  - venv em `backend/venv/`, deps em `backend/requirements.txt`
    (fastapi, uvicorn[standard], sqlalchemy, psycopg2-binary,
    python-dotenv)
  - `backend/app/`: `database.py` (engine + SessionLocal + Base +
    `get_db`), `models.py` (Usuario, Conteudo, SessaoRevisao — nomes
    em pt-br snake_case), `schemas.py` (Pydantic v2, `from_attributes`),
    `main.py` (FastAPI + CORS liberado + `GET /health` que testa o
    banco). Nenhuma rota de negócio ainda, conforme pedido.
  - `.env.example` com `DATABASE_URL` de exemplo (Supabase/Neon).
  - Decisão: `email` como `str` em vez de `EmailStr` pra não puxar
    `email-validator` fora dos requirements combinados. Trocar depois
    se quiser validação forte.
  - Como rodar: `cd backend; venv\Scripts\activate; uvicorn app.main:app --reload`

- 2026-07-23 — Schema SQL em `backend/schema.sql` + `models.py`
  atualizado pra ficar equivalente:
  - Campos base do CLAUDE.md: `usuarios(id, email, senha_hash)`,
    `conteudos(id, usuario_id, titulo, materia)`,
    `sessoes_revisao(id, conteudo_id, data, percentual, proxima_revisao)`.
  - Extras que adicionei (avisando): coluna `criado_em TIMESTAMP DEFAULT now()`
    em `usuarios` e `conteudos` (auditoria básica, útil pra debug e
    ordenação; se preferir remover, é 1 linha em cada arquivo).
  - Constraints: `email UNIQUE`, FK `conteudos.usuario_id → usuarios.id`
    e FK `sessoes_revisao.conteudo_id → conteudos.id`, ambas com
    `ON DELETE CASCADE`. `CHECK (percentual BETWEEN 0 AND 100)`
    replicado no DB (antes só existia no Pydantic).
  - Índices: FKs (`usuario_id`, `conteudo_id`), `email` (unique) e
    `proxima_revisao` (a query "o que revisar hoje" filtra por essa
    coluna).
  - Como aplicar: colar o conteúdo de `backend/schema.sql` no SQL
    editor do Supabase/Neon. Ainda não temos Alembic — se quiser
    migrations versionadas em algum momento, é um add-on separado.

- 2026-07-23 — Regra de negócio da repetição espaçada isolada em
  `backend/app/services/revisao.py` como função pura
  `calcular_proxima_revisao(percentual, data_atual) -> date`:
  - 100% → +30 dias; 70–99% → +7 dias; <70% → +1 dia.
  - `percentual` fora de [0, 100] levanta `ValueError` (proteção
    defensiva; o DB e o Pydantic já barram, mas a função é chamada
    isoladamente e vale falhar cedo).
  - Decisão de borda: `99.9%` cai em +7 dias (só `== 100` vai pra
    +30). Se quiser tratar ">=99.5" como 100%, é 1 linha.
  - Testes em `backend/tests/test_revisao.py` (pytest, 9 casos):
    100, 99, 85, 70, 69.99, 0, 99.9, negativo, >100.
  - Nova dep de dev: `pytest` em `backend/requirements-dev.txt`
    (não entra no runtime do backend). Config em `backend/pytest.ini`.
  - Como rodar: `cd backend; venv\Scripts\activate; pytest`

- 2026-07-23 — Rotas de conteúdo:
  - `POST /conteudos` (201) — body `ConteudoCreate {titulo, materia}`,
    resposta `ConteudoOut`.
  - `GET /conteudos` — lista os do usuário autenticado, ordenados por
    `criado_em desc`.
  - Router em `backend/app/routers/conteudos.py`, plugado no
    `main.py` via `include_router`.
  - **Auth mockada**: `backend/app/auth.py` expõe
    `get_current_user_id()` que devolve `1`. Assinatura já pronta pro
    swap com JWT do Supabase — routers não precisam mudar. Requer
    que exista `usuarios(id=1, ...)` no banco (INSERT de exemplo no
    docstring do módulo).
  - Testes de rota formalizados em `backend/tests/test_conteudos.py`
    (7 casos: GET vazio, POST 201, POST aparece no GET, ordenação,
    422 sem `titulo`, 422 sem `materia`, `usuario_id` do body é ignorado).
  - Fixtures em `backend/tests/conftest.py`: `db_session` (SQLite
    in-memory + `StaticPool`, cria tabelas + semeia o usuário mock,
    dropa no teardown) e `client` (TestClient contra a app real).
    Monkeypatch em `app.database` acontece antes de `app.main` ser
    importado pra que o `get_db` use o engine de teste.
  - Ajuste no router: `.order_by(criado_em desc, id desc)` — o
    `criado_em` do SQLite tem granularidade de segundo, então o
    desempate por `id desc` deixa a ordenação determinística nos
    testes (e é uma escolha razoável em produção também).
  - Nova dep de dev: `httpx` (exigido pelo `TestClient`).

- 2026-07-23 — Rotas de sessão / dashboard em
  `backend/app/routers/sessoes.py`:
  - `POST /sessoes` (201) — body `SessaoRevisaoCreate {conteudo_id,
    data, percentual}`. Verifica que o `conteudo_id` pertence ao
    `usuario_id` autenticado (senão 404, não 403 — evita vazar
    existência de conteudos alheios). Chama
    `calcular_proxima_revisao(percentual, data)` e persiste
    `proxima_revisao`. Retorna `SessaoRevisaoOut`.
  - `GET /revisoes/hoje` — retorna `list[ConteudoOut]` dos conteudos
    do usuário cuja **última** sessão (`max(id)` por `conteudo_id`,
    já que id é monotônico) tem `proxima_revisao <= hoje`. Ordenado
    por `proxima_revisao asc` (mais atrasado primeiro). Conteúdos sem
    nenhuma sessão registrada NÃO entram — só entram no ciclo depois
    da 1ª revisão. Se você quiser incluir "nunca revisados" no
    Dashboard, é uma decisão de produto separada.
  - Retorno do `/revisoes/hoje` é `ConteudoOut` puro; **não** inclui
    a `proxima_revisao` no payload. Pra o Dashboard mostrar
    "atrasado há N dias" seria natural expor essa data — 3 linhas de
    schema. Deixei pra confirmar com você antes.
    **[atualizado 2026-07-23]** — confirmado, ajustado abaixo.
  - Testes em `backend/tests/test_sessoes.py` (11 casos): +30/+7/+1
    dias, conteudo inexistente/alheio → 404, percentual >100 → 422,
    filtro considera só a última sessão, isolamento por usuário, e
    um end-to-end (POST /sessoes com 100% e GET /revisoes/hoje volta
    vazio).

- 2026-07-23 — Ajuste no `/revisoes/hoje` a pedido do usuário:
  - Agora também inclui conteúdos SEM nenhuma sessão registrada
    (pendentes por padrão, "nunca revisados"). Query virou LEFT JOIN
    contra a última sessão por conteudo, com filtro
    `sessao_id IS NULL OR proxima_revisao <= hoje`.
  - Novo schema `ConteudoRevisaoOut` em `backend/app/schemas.py`
    estende `ConteudoOut` com `proxima_revisao: date | None` (null
    quando nunca revisado). É o tipo de retorno do endpoint.
  - Ordenação: atrasados primeiro (`proxima_revisao asc`), nunca
    revisados por último. Implementado com
    `order_by(proxima_revisao.is_(None), proxima_revisao.asc())` pra
    portabilidade SQLite/Postgres (evita `NULLS LAST`).
  - Testes atualizados: removi `test_lista_vazia_quando_usuario_nao_tem_sessoes`
    (comportamento invertido), adicionei
    `test_lista_vazia_quando_usuario_nao_tem_conteudos`,
    `test_conteudo_sem_sessao_aparece_como_pendente_com_proxima_revisao_null`
    e `test_ordena_atrasados_primeiro_e_novos_por_ultimo`. Suite
    completa: 29 casos verdes.

- 2026-07-23 — Auth-mock trocado por Supabase Auth real:
  - `backend/app/auth.py` reescrito: extrai `Authorization: Bearer <jwt>`,
    valida HS256 com `SUPABASE_JWT_SECRET`, checa `aud=authenticated`,
    lê `sub` (UUID do usuário no Supabase) e faz **get-or-create** em
    `usuarios` via `supabase_uid`. Devolve o `int` local — assinatura
    externa da dependency preservada, routers 100% intactos.
  - Sem token → 401; scheme != Bearer → 401; assinatura errada / `aud`
    errada / expirado → 401; sem `sub` → 401; sem `SUPABASE_JWT_SECRET`
    → 500 (má config do servidor).
  - Nova dep runtime: `pyjwt` em `backend/requirements.txt`.
  - `.env.example` atualizado com `SUPABASE_URL`, `SUPABASE_ANON_KEY`
    (documentada como frontend-only) e `SUPABASE_JWT_SECRET`
    (usada de fato pelo backend, NUNCA expor no frontend).
  - Schema mudou (**precisa migração no banco**):
    - `usuarios.supabase_uid TEXT UNIQUE` (nullable) — mapeia JWT `sub`
      → linha local.
    - `usuarios.senha_hash` virou nullable (Supabase gerencia senhas).
    - Instruções `ALTER TABLE` no comentário de `backend/schema.sql`
      pra quem já rodou o schema antigo.
  - Decisões que valem revisar:
    - **Mapeamento por `int` local em vez de UUID no schema todo.**
      Fiz assim pra não tocar em `conteudos.usuario_id`, `sessoes_revisao`,
      routers e schemas Pydantic. Alternativa "correta" long-term é
      migrar tudo pra UUID — mudança grande.
    - **Get-or-create automático na 1ª request autenticada** provisiona
      a linha local. Cai bem pra MVP; se você quiser um passo explícito
      de cadastro, dá pra virar 401 com "usuário não provisionado".
    - **`senha_hash` mantido como coluna vestigial (nullable)** em vez
      de dropado, pra não quebrar rows antigas nem exigir migração
      destrutiva.
  - Testes:
    - `tests/conftest.py` agora usa `app.dependency_overrides` pra
      substituir `get_current_user_id` por uma função que devolve
      `TEST_USER_ID = 1`. Nova fixture `mock_user_id` expõe o valor;
      os testes que usavam `MOCK_USER_ID` importado agora recebem a
      fixture.
    - Novo `tests/test_auth.py` (8 casos) exercita a auth de verdade
      removendo o override e emitindo JWTs válidos/inválidos com
      `pyjwt`: sem header, scheme errado, assinatura errada, expirado,
      `aud` errada, get-or-create de UID novo, reuso de UID existente,
      e ausência de `SUPABASE_JWT_SECRET`.
    - Suite completa: **37 casos verdes**.

- 2026-07-23 — Migração HS256 → ES256 (JWKS):
  - O projeto Supabase migrou pra JWT signing keys assimétricas
    (ECC P-256). O `SUPABASE_JWT_SECRET` (HS256) virou "Previous Key" e
    vai ser descontinuado.
  - `backend/app/auth.py` reescrito pra usar `PyJWKClient` (do pyjwt):
    baixa o JWKS de `SUPABASE_JWKS_URL`, resolve a chave pública pelo
    `kid` do header do token, valida assinatura ES256 + `aud` + `exp`.
    Cache das chaves em memória (`cache_jwk_set=True, lifespan=3600`).
    A resolução da chave está isolada em `_get_signing_key(token)` pra
    facilitar monkeypatch em testes.
  - `backend/requirements.txt`: `pyjwt` → `pyjwt[crypto]` (puxa
    `cryptography`, necessário pra ES256).
  - `backend/.env.example`:
    - Adicionado `SUPABASE_JWKS_URL` como var primária de validação.
    - `SUPABASE_JWT_SECRET` comentado como legado — deixado só como
      referência caso alguém rode contra um projeto ainda em HS256.
    - **Não** mexi na linha `SUPABASE_URL=sb_publishable_...` — o
      linter/user alterou intencionalmente.
  - `backend/tests/test_auth.py` reescrito pra ES256:
    - Gera um par ECC P-256 no import do módulo, assina JWTs de teste
      com a privada e monkeypatcha `auth._get_signing_key` pra devolver
      a pública correspondente — evita HTTP contra o JWKS real.
    - Fixtures separadas: `sem_override` (só desliga o override do
      conftest) e `real_auth_client` (adiciona o mock de chave). Isso
      permite reusar `sem_override` pra testar o caminho de erro do
      JWKS (`PyJWKClientError` → 401).
    - 8 casos mantidos, cobrindo: sem header, scheme errado, assinatura
      inválida (assinado com outra chave privada), expirado, aud errada,
      JWKS não encontra a chave, get-or-create de UID novo, reuso de
      UID existente. Suite completa: **37 casos verdes**.
  - Ficou de fora dos testes: cenário "SUPABASE_JWKS_URL não configurado
    → 500". O código trata (RuntimeError → 500), mas testar exigiria
    desligar o monkeypatch de `_get_signing_key` E limpar o env — dá,
    mas não trouxe. Se quiser, adiciono.

- 2026-07-23 — Estrutura inicial do frontend em `/frontend`:
  - Scaffold via `npx create-vite@latest frontend --template react`
    (Vite 8 + React JS, não TS). Node 22 + npm 10.
  - Estilo: **Tailwind CSS v4** via `@tailwindcss/vite` (mais simples que
    v3 — sem `tailwind.config.js`, sem `postcss.config.js`; só
    `@import "tailwindcss";` em `app/index.css` e o plugin no
    `vite.config.js`).
  - Deps: `@supabase/supabase-js`, `tailwindcss`, `@tailwindcss/vite`.
  - Renomeei `src/` → `app/` pra bater com o pedido do usuário
    (`app/lib/supabaseClient.js`) e ficar consistente com o backend
    (`backend/app/`). Ajustei `index.html` pra apontar `/app/main.jsx`.
    Removi boilerplate (`App.css`, `assets/`, `hero.png`, ícones do
    Vite) — página começa limpa.
  - `app/lib/supabaseClient.js`: lê `VITE_SUPABASE_URL` +
    `VITE_SUPABASE_ANON_KEY` do `import.meta.env`; **throw explícito**
    se estiverem faltando (evita "Invalid URL" críptico do supabase-js).
  - `app/App.jsx`: form email+senha com `signInWithPassword` /
    `signUp`, escuta `onAuthStateChange`. Após login mostra "Login OK"
    + email + botão "Sair" — sem rotas ainda (próximo passo).
    Cobertura de casos: sessão carregando, erro de auth, cadastro que
    exige confirmação de email (`data.session` é `null` nesse caso).
    Estilo só o mínimo do Tailwind, sem tema custom.
  - `frontend/.env.example` documenta as duas vars com aviso:
    tudo com prefixo `VITE_` vai pro bundle público — **nunca** colocar
    o JWT secret aqui.
  - Validado com `npm run build` (60 módulos, CSS 8.4kB, bundle 292kB).
    Não rodei o dev server porque exige `.env` real com credenciais do
    Supabase — deixei o launch pra você fazer com as chaves na mão.
  - Como rodar:
    ```
    cd frontend
    cp .env.example .env    # e preenche as duas vars
    npm run dev
    ```

- 2026-07-23 — Tela "Meus Conteúdos":
  - `frontend/app/lib/api.js`: helper minúsculo (`apiGet`/`apiPost`)
    que lê `VITE_API_URL`, puxa `access_token` da sessão Supabase e
    manda `Authorization: Bearer <jwt>` em cada request. Erro do
    FastAPI (`{detail: "..."}`) é desempacotado numa `Error` legível.
  - `frontend/app/pages/ConteudosPage.jsx`: renderiza lista de
    conteúdos + formulário de criação (título + matéria). Estados
    separados de loading/erro pra lista e pro form. Recarrega a lista
    depois de criar (sem otimistic UI, simples).
  - `App.jsx` agora troca "Login OK" por `<ConteudosPage email={...}
    onSair={...} />` quando há sessão. **Ainda sem router de verdade**
    — só troca de estado, como pedido. Isso vai ficar chato quando
    entrar Dashboard + "registrar revisão", aí adiciono React Router.
  - Nova var: `VITE_API_URL=http://127.0.0.1:8000` documentada em
    `.env.example` e adicionada ao `.env` (o usuário já tinha criado
    o `.env` com credenciais reais do Supabase; só concatenei a linha
    nova).
  - Build validado (`npm run build`, 62 módulos). Dev server não subiu
    aqui — depende do backend rodando pra ter o que listar.
  - Depende do CORS já configurado no backend (`allow_origins=["*"]`
    em `main.py`) — se você trocar `["*"]` por lista específica no
    futuro, inclua `http://localhost:5173` e o domínio da Vercel.

- 2026-07-23 — Dashboard + Registrar Revisão + navegação:
  - `frontend/app/pages/DashboardPage.jsx`: consome `GET /revisoes/hoje`
    e renderiza cada conteúdo com uma badge de status:
      - `proxima_revisao == null` → "Novo" (azul);
      - `proxima_revisao < hoje` → "Atrasado desde DD/MM/AAAA" (vermelho);
      - `proxima_revisao == hoje` → "Hoje" (âmbar).
    Cada item tem botão "Registrar revisão" que abre a tela via
    callback (sem Router). Recebe `reloadKey` — quando muda, refetcha.
    Datas parseadas manualmente (`split('-')`) pra evitar drift de
    timezone que `new Date('2026-07-20')` causa.
  - `frontend/app/pages/RegistrarRevisaoPage.jsx`: form com input
    `type="number" min=0 max=100 step=0.1`, chama `POST /sessoes` com
    `data` = hoje local (sem UTC). Valida faixa no cliente antes de
    enviar. `onCancelar` volta pro Dashboard, `onSucesso` volta E
    incrementa `reloadDashboard` no `App.jsx` pra forçar refetch.
  - `App.jsx` refatorado: introduzi um `<Shell>` com header (email +
    Sair) e nav de duas abas (Dashboard | Meus Conteúdos).
    `ConteudosPage.jsx` perdeu o header próprio — agora o shell
    centraliza.
  - **Nav só tem 2 abas visíveis**. "Registrar Revisão" é contextual:
    reachable via clique no Dashboard, e tem "Cancelar" pra voltar.
    Isso porque expor "Registrar Revisão" como aba sem conteúdo
    selecionado dava tela vazia sem sentido. Se você quiser as 3
    como abas iguais (com um seletor de conteúdo dentro da tela),
    dá pra ajustar.
  - Padrão de state routing: `tela ∈ {'dashboard','conteudos','registrar'}`
    + `conteudoAlvo` (o item clicado no Dashboard) + `reloadDashboard`
    (contador que dispara refetch). Vai virar chatinho de manter com
    mais 1-2 telas; aí puxo `react-router-dom`.
  - Build validado (`npm run build`, 64 módulos, CSS 10.8kB, JS 407kB).

- 2026-07-23 — "Meus Conteúdos" ganhou proxima_revisao, click →
  registrar e delete:
  - **Backend**:
    - `GET /conteudos` agora retorna `list[ConteudoRevisaoOut]`
      (mesmo schema de `/revisoes/hoje`). Query virou LEFT JOIN com
      a última sessão por conteudo (mesma lógica do `sessoes.py`, só
      sem o filtro por data). Ordenação mantida: `criado_em desc, id desc`.
      `POST /conteudos` segue devolvendo `ConteudoOut` puro (a resposta
      é o objeto recém-criado, ainda sem sessão).
    - `DELETE /conteudos/{id}` → 204. Filtro por `usuario_id`; 404 se
      não existir ou não pertencer (não vazar existência). Cascade das
      sessoes_revisao acontece via ORM (`cascade="all, delete-orphan"`
      no relationship de `Conteudo.sessoes`), não depende de PRAGMA
      no SQLite dos testes.
    - Testes: 7 novos em `test_conteudos.py` (3 de proxima_revisao na
      listagem + 4 de DELETE incluindo cascade e cross-user). Suite
      completa: **44 verdes**.
  - **Frontend**:
    - `app/lib/api.js`: novo helper `apiDelete(path)`.
    - `app/lib/dates.js`: extraí `formatarData` e `hojeIsoLocal` num
      módulo comum (estavam duplicados em `DashboardPage` e
      `RegistrarRevisaoPage`). As duas telas passaram a importar de lá.
    - `ConteudosPage`:
      - mostra `Próxima revisão: DD/MM/AAAA` ou "Nunca revisado" em cada item;
      - o corpo do item virou um `<button>` full-width que chama
        `onRegistrar(c)` (item clicável → tela de registrar com o
        `conteudo_id` pré-selecionado);
      - botão "Apagar" separado no fim de cada item (dois `<button>`
        irmãos dentro do `<li>` — HTML válido, sem `stopPropagation`
        gambiarra). Confirma com `window.confirm` antes de disparar
        o DELETE. Estado `apagandoId` desabilita o botão enquanto roda.
    - `App.jsx`: agora rastreia `origemRegistrar` (dashboard vs
      conteudos) — a tela de registrar volta pra origem correta ao
      cancelar/salvar. Dois reload keys (`reloadDashboard`,
      `reloadConteudos`) — o `apósRegistrar` incrementa o da origem
      pra forçar refetch daquela página.
    - Build validado (`npm run build`, 65 módulos).

- 2026-07-23 — Ajustes de UI:
  - Substituí `window.confirm` no fluxo de apagar conteúdo por um
    modal simples do próprio site — novo componente reutilizável em
    `frontend/app/components/ConfirmModal.jsx`. Overlay clicável pra
    cancelar, botão destrutivo em vermelho (`destrutivo=true`), suporta
    estado `confirmando` pra travar interação enquanto o DELETE roda.
    O `ConteudosPage` passou a controlar via state (`alvoParaApagar`)
    em vez de bloquear a thread com prompt nativo. Sem `Esc` nem focus
    trap por enquanto — se quiser a11y mais robusto, é um add-on.
  - `RegistrarRevisaoPage`: input único de percentual virou dois campos
    de inteiro (`Questões feitas` ≥ 1, `Questões acertadas` ≥ 0 e ≤
    feitas). Backend NÃO mudou: o frontend calcula
    `(acertadas / feitas) * 100`, arredonda a 2 casas, e envia como
    `percentual` no `POST /sessoes`. Preview em tempo real "3/10 = 30%"
    (ou mensagem de erro em vermelho quando os valores não fecham).
    Botão "Registrar" fica disabled até o par ser válido.
  - Adicionei uma seção **"Escopo do MVP — o que NÃO existe"** no topo
    (antes de Deploy) deixando explícito que a ausência de notificação
    ativa (WhatsApp/email/push) é intencional, não bug de escopo.
    WhatsApp segue no Backlog V2.
  - Build validado (`npm run build`, 66 módulos, CSS 13.7kB, JS 410kB).

- 2026-07-23 — Identidade visual completa (tema escuro consistente):
  - **Tokens em `frontend/app/index.css`** via `@theme` do Tailwind
    v4 (gera utilitários automaticamente):
    - Paleta: `--color-app-{bg,surface,raised,fg,muted,line}` e
      `--color-status-{atrasado,hoje,novo}-{bg,fg}`.
    - Font: `--font-sans` sistema (fallbacks Segoe UI, Roboto).
    - `html { background: var(--color-app-bg); color: var(--color-app-fg); }`
      pra herdar em toda a árvore.
    - Reset de spinners em `input[type="number"]` (combinam mal com
      o tema).
  - **Componentes reutilizáveis em `frontend/app/components/`**:
    - `Button.jsx` — variantes `primario` (inverso: bg fg, text bg),
      `secundario` (raised), `perigo` (paleta atrasado). Altura 40px,
      radius 8px, `disabled:opacity-50`.
    - `Input.jsx` — label opcional em cima, hint/error embaixo.
      Altura 40px, radius 8px, bg raised.
    - `Card.jsx` — bg surface, border line, radius 12px. Prop
      `padding={false}` pra list items que gerenciam padding interno.
    - `Badge.jsx` — variantes `novo`/`hoje`/`atrasado` mapeadas nas
      cores de status.
    - `ConfirmModal.jsx` — refeito em cima do Button + tokens.
  - **Aplicação nas 4 telas** (`App.jsx`, `DashboardPage`,
    `ConteudosPage`, `RegistrarRevisaoPage`): todo botão/input/card
    do app vem dos componentes acima — nada mais estilizado com
    classes soltas por tela. TabButton do shell inlined em `App.jsx`
    (não usa `Button` porque precisa do estado ativo/inativo distinto
    das variantes existentes; poderia virar 4ª variante no `Button`
    depois se aparecer mais uso).
  - **Responsivo**:
    - Mobile (<640px): shell com `px-4`, tabs em `grid grid-cols-2`
      (full-width), user info em cima em fonte pequena.
    - sm+ (≥640px): `px-6`, nav e user info na mesma linha (nav
      esquerda, user direita).
    - lg+ (≥1024px): `px-8`. Shell max-width `720px` centralizado.
    - Formulários (Login, Registrar Revisão) com wrapper interno
      `max-w-[480px] mx-auto`.
    - Cards das listas empilham verticalmente no mobile (info +
      botão em coluna), viram flex row no sm+.
  - **Verificação visual**:
    - Build: `npm run build` limpo, 70 módulos, CSS 16.1kB, JS 411kB.
    - Login inspecionada via dev server anexado (attach ao
      `http://localhost:5173` já rodando; `.claude/launch.json`
      adicionado). Confirmei via `getComputedStyle`:
      body text=#ececea, card bg=#1e1e1e, border=#2a2a2a,
      input bg=#262626, botão primário bg=#ececea/text=#141414
      (inverso), altura 40px, radius 8px, font system-ui. Em
      desktop (1280px), card centralizado com max 480px.
    - **Não testei visualmente as 3 telas autenticadas** — exigem
      login real no Supabase + backend rodando, e o navegador do
      preview não estava exposto pra screenshot. As telas usam
      exatamente os mesmos tokens/componentes da Login (Card,
      Button, Input, Badge), então herdam o mesmo visual. Tablet
      (~768px) também ficou sem inspeção visual — só o CSS responsivo.
      Vale abrir no seu navegador e revisar.

- 2026-07-23 — Correções de UI que o usuário pediu:
  - **Fix de vazamento de cor de acento**:
    - Grep completo em `frontend/app/**`: só uma ocorrência real de
      cor de status em texto fora do Badge — o aviso "Cadastro criado,
      confira email" no Login usava `text-status-hoje-fg` (âmbar).
      Trocado por `text-app-fg` (informacional é texto padrão).
    - Reafirmo que `text-status-hoje-fg` (âmbar #e0b96a) fica EXCLUSIVO
      do `Badge variante="hoje"`. `text-status-atrasado-fg` (vermelho
      #e08a8a) segue em uso pra badge "atrasado" **e** pra mensagens
      de erro — o vermelho de erro é convenção universal e o usuário
      não pediu pra remover.
  - **Layout wrapper unificado**: `Layout` em `App.jsx` — `min-h-screen
    bg-app-bg` + `mx-auto max-w-[720px] px-4 sm:px-6 lg:px-8 pt-8
    sm:pt-10 pb-10`. As 4 telas (Login, Dashboard, Conteúdos, Registrar)
    renderizam dentro dele. Login perdeu o center vertical (antes era
    `flex items-center justify-center`) — agora fica top-aligned com
    `pt-8`, consistente com as demais.
  - **Empty state do Dashboard**: Card com `p-6 sm:p-8`, texto
    centralizado, ícone Tabler `calendar-check` inline (24×24 SVG,
    `w-10 h-10 text-app-muted mb-3`). Título "Nada pendente por hoje"
    em `text-app-fg font-medium`, descrição em `text-app-muted`. Zero
    dep nova (SVG inline).
  - **Verificação visual em ambos os breakpoints (via `getComputedStyle`
    e `getBoundingClientRect`)** — bypass temporário `?dev=<tela>` foi
    adicionado, usado pra inspecionar, e removido antes de fechar:
    - Desktop 1280: wrapper 720px, margens 280+280 (`centralizado: true`),
      padding `40px 32px`. Form card 480 dentro do wrapper (400+400
      do viewport).
    - Mobile 375: wrapper full-width, padding `32px 16px 40px`. Nav em
      `grid-cols-2` (167.6px cada). User info acima do nav (col-reverse).
    - Auditoria de cores em Dashboard/Conteúdos/Registrar retornou só:
      `rgb(236,236,234)`=#ececea (textos principais/labels/botões
      inativos), `rgb(154,154,150)`=#9a9a96 (subtitles/muted),
      `rgb(20,20,20)`=#141414 (texto de botão primário inverso),
      `rgb(224,138,138)`=#e08a8a (msg de erro do backend down).
      **Zero âmbar. Zero cor fora do sistema.**
  - Build final `npm run build`: 70 módulos, CSS 16.5kB, JS 411kB.

- 2026-07-23 — Refino do botão "Apagar" em `ConteudosPage`:
  - Ícone Tabler `trash` inline (SVG, sem dep nova) ao lado do texto,
    dentro de um `inline-flex items-center gap-1.5`.
  - Hover: `bg-status-atrasado-bg` (#4a1e1e) — antes era um cinza
    (`bg-app-raised`). Texto continua em `text-status-atrasado-fg`
    (#e08a8a) no default e no hover; a mudança de affordance vem do
    fundo. Reaproveita as MESMAS variáveis já usadas no badge "atrasado",
    zero cor nova.
  - Padding `px-2.5 py-1.5` (10px 6px) — o botão continua ocupando a
    altura total da row via `items-stretch` do `<Card>` pai, então o
    click target vertical não encolhe; o padding controla o miolo do
    ícone+texto.
  - Transição explícita: `transition-colors duration-150`.
  - Build final: 70 módulos, CSS 17.2kB.
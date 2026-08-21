-- Schema do MVP — revisão espaçada
-- Alvo: PostgreSQL (Supabase / Neon)
-- Espelho do que está em app/models.py.

CREATE TABLE IF NOT EXISTS usuarios (
    id            SERIAL PRIMARY KEY,
    -- UUID que o Supabase Auth emite no claim `sub` do JWT. Nullable
    -- porque pode existir linha semeada antes da 1ª autenticação.
    supabase_uid  TEXT   UNIQUE,
    email         TEXT   NOT NULL UNIQUE,
    -- Nullable: Supabase Auth gerencia senha; coluna fica só como vestígio.
    senha_hash    TEXT,
    criado_em     TIMESTAMP NOT NULL DEFAULT now()
);

-- Se você já rodou o schema antes desse ajuste, aplique também:
--   ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS supabase_uid TEXT UNIQUE;
--   ALTER TABLE usuarios ALTER COLUMN senha_hash DROP NOT NULL;

CREATE TABLE IF NOT EXISTS conteudos (
    id          SERIAL PRIMARY KEY,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    titulo      TEXT    NOT NULL,
    materia     TEXT    NOT NULL,
    criado_em   TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_conteudos_usuario_id
    ON conteudos (usuario_id);

CREATE TABLE IF NOT EXISTS sessoes_revisao (
    id               SERIAL PRIMARY KEY,
    conteudo_id      INTEGER NOT NULL REFERENCES conteudos(id) ON DELETE CASCADE,
    data             DATE    NOT NULL,
    percentual       DOUBLE PRECISION NOT NULL
        CHECK (percentual >= 0 AND percentual <= 100),
    proxima_revisao  DATE    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessoes_conteudo_id
    ON sessoes_revisao (conteudo_id);

-- Para a query do Dashboard ("o que revisar hoje"): filtra por proxima_revisao <= hoje.
CREATE INDEX IF NOT EXISTS idx_sessoes_proxima_revisao
    ON sessoes_revisao (proxima_revisao);

-- Row Level Security — fecha o acesso via PostgREST/anon key.
-- Todo o CRUD passa pelo FastAPI, que conecta via role postgres (BYPASSRLS),
-- entao RLS ligada sem policies = frontend nao consegue bater direto no
-- REST do Supabase e ler/escrever linhas de outros usuarios usando so a
-- VITE_SUPABASE_ANON_KEY (que e publica, vai no bundle). Backend segue igual.
ALTER TABLE usuarios         ENABLE ROW LEVEL SECURITY;
ALTER TABLE conteudos        ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessoes_revisao  ENABLE ROW LEVEL SECURITY;

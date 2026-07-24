import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  // Falha cedo com uma mensagem clara em dev — evita ficar caçando
  // um "Invalid URL" críptico do supabase-js.
  throw new Error(
    'VITE_SUPABASE_URL e VITE_SUPABASE_ANON_KEY precisam estar definidas em frontend/.env'
  )
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

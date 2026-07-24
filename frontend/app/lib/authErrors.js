// Mapeia mensagens de erro do Supabase Auth (que vêm em inglês) pro pt-BR.
// O Supabase não tem i18n pra auth ainda, então a gente traduz aqui.
// Match é por trecho da mensagem original — se não bater com nenhum, devolve
// a original pra não engolir erros novos silenciosamente.

const TRADUCOES = [
  // Login
  { match: /invalid login credentials/i, pt: 'Email ou senha incorretos.' },
  { match: /email not confirmed/i, pt: 'Você precisa confirmar seu email antes de entrar. Confira sua caixa de entrada.' },
  { match: /invalid email or password/i, pt: 'Email ou senha incorretos.' },

  // Cadastro
  { match: /user already registered/i, pt: 'Já existe uma conta com esse email.' },
  { match: /email address .* is invalid/i, pt: 'Email inválido.' },
  { match: /unable to validate email address/i, pt: 'Email inválido.' },
  { match: /signup( is)? (disabled|not allowed)/i, pt: 'Cadastros novos estão desativados no momento.' },

  // Senha
  { match: /password should be at least (\d+) characters?/i, pt: (m) => `A senha precisa ter pelo menos ${m[1]} caracteres.` },
  { match: /password is too weak/i, pt: 'Senha muito fraca. Tente uma mais longa ou com letras, números e símbolos.' },
  { match: /new password should be different from the old password/i, pt: 'A senha nova precisa ser diferente da atual.' },
  { match: /same( as the)? old password/i, pt: 'A senha nova precisa ser diferente da atual.' },

  // Rate limit / segurança
  { match: /for security purposes, you can only request this after (\d+) seconds?/i, pt: (m) => `Aguarde ${m[1]} segundos antes de tentar de novo.` },
  { match: /email rate limit exceeded/i, pt: 'Muitos emails enviados. Aguarde alguns minutos e tente de novo.' },
  { match: /too many requests/i, pt: 'Muitas tentativas. Aguarde alguns minutos e tente de novo.' },

  // Sessão / token
  { match: /invalid refresh token/i, pt: 'Sua sessão expirou. Entre de novo.' },
  { match: /jwt expired/i, pt: 'Sua sessão expirou. Entre de novo.' },
  { match: /session (from session_id claim in jwt does not exist|not found)/i, pt: 'Sua sessão expirou. Entre de novo.' },

  // Recovery
  { match: /token has expired or is invalid/i, pt: 'Link de recuperação expirado ou inválido. Peça um novo.' },
  { match: /otp( is)? expired/i, pt: 'Link expirado. Peça um novo.' },
]

export function traduzirErroAuth(mensagemOriginal) {
  if (!mensagemOriginal) return 'Erro desconhecido.'
  for (const { match, pt } of TRADUCOES) {
    const m = mensagemOriginal.match(match)
    if (m) return typeof pt === 'function' ? pt(m) : pt
  }
  return mensagemOriginal
}

import { supabase } from './supabaseClient'

const API_URL = import.meta.env.VITE_API_URL
if (!API_URL) {
  throw new Error('VITE_API_URL precisa estar definida em frontend/.env')
}

async function authHeaders() {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function unwrap(response) {
  if (!response.ok) {
    // Tenta extrair `detail` do FastAPI; senão joga o texto cru.
    let detalhe = ''
    try {
      const j = await response.json()
      detalhe = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail ?? j)
    } catch {
      detalhe = await response.text()
    }
    throw new Error(`${response.status}: ${detalhe || response.statusText}`)
  }
  return response.status === 204 ? null : response.json()
}

export async function apiGet(path) {
  const r = await fetch(`${API_URL}${path}`, {
    headers: { ...(await authHeaders()) },
  })
  return unwrap(r)
}

export async function apiPost(path, body) {
  const r = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(await authHeaders()),
    },
    body: JSON.stringify(body),
  })
  return unwrap(r)
}

export async function apiDelete(path) {
  const r = await fetch(`${API_URL}${path}`, {
    method: 'DELETE',
    headers: { ...(await authHeaders()) },
  })
  return unwrap(r)
}

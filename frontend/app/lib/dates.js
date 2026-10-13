// Formata "2026-07-20" → "20/07/2026" sem passar por Date (evita drift
// de timezone que `new Date('2026-07-20')` causa).
export function formatarData(iso) {
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

// "2026-07-20" → "20/07"
export function formatarDiaMes(iso) {
  const [, m, d] = iso.split('-')
  return `${d}/${m}`
}

// "2026-07-20" → número de dias desde a época, para posicionar em escala de tempo.
export function isoParaDias(iso) {
  const [y, m, d] = iso.split('-').map(Number)
  return Date.UTC(y, m - 1, d) / 86400000
}

// Data local de hoje em ISO "YYYY-MM-DD" (sem UTC).
export function hojeIsoLocal() {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

// 96.6667 → "96,7%"; 70 → "70%"
export function formatarPct(valor) {
  return `${valor.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`
}

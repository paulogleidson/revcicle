const VARIANTES = {
  novo: 'bg-status-novo-bg text-status-novo-fg',
  hoje: 'bg-status-hoje-bg text-status-hoje-fg',
  atrasado: 'bg-status-atrasado-bg text-status-atrasado-fg',
}

export default function Badge({ variante, children }) {
  const estilo = VARIANTES[variante] ?? VARIANTES.novo
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${estilo}`}
    >
      {children}
    </span>
  )
}

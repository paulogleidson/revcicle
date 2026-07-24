const VARIANTES = {
  primario:
    'bg-app-fg text-app-bg hover:bg-app-muted disabled:hover:bg-app-fg',
  secundario:
    'bg-app-raised text-app-fg border border-app-line hover:bg-app-surface',
  perigo:
    'bg-status-atrasado-bg text-status-atrasado-fg border border-status-atrasado-bg hover:brightness-110',
}

export default function Button({
  variante = 'primario',
  className = '',
  children,
  ...rest
}) {
  const estilo = VARIANTES[variante] ?? VARIANTES.primario
  return (
    <button
      {...rest}
      className={`inline-flex items-center justify-center h-10 px-4 rounded-lg text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed ${estilo} ${className}`}
    >
      {children}
    </button>
  )
}

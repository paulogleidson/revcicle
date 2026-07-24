export default function Input({
  label,
  hint,
  error,
  className = '',
  ...rest
}) {
  return (
    <label className="block">
      {label && (
        <span className="block text-sm text-app-muted mb-1">{label}</span>
      )}
      <input
        {...rest}
        className={`block w-full h-10 rounded-lg bg-app-raised border border-app-line text-app-fg placeholder:text-app-muted px-3 focus:outline-none focus:border-app-muted transition ${className}`}
      />
      {hint && !error && (
        <span className="block text-xs text-app-muted mt-1">{hint}</span>
      )}
      {error && (
        <span className="block text-xs text-status-atrasado-fg mt-1">
          {error}
        </span>
      )}
    </label>
  )
}

export default function Card({ padding = true, className = '', children }) {
  const paddingClass = padding ? 'p-4 sm:p-5' : ''
  return (
    <div
      className={`bg-app-surface border border-app-line rounded-xl ${paddingClass} ${className}`}
    >
      {children}
    </div>
  )
}

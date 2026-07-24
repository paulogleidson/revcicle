export default function Logo({ className = '' }) {
  return (
    <img
      src="/logo.png"
      alt="RevCicle"
      className={className}
      draggable={false}
    />
  )
}

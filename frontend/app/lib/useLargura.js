import { useEffect, useRef, useState } from 'react'

// Largura atual de um elemento, atualizada no resize — gráficos SVG desenham
// em pixels reais em vez de escalar o viewBox (que distorceria o texto).
export function useLargura() {
  const ref = useRef(null)
  const [largura, setLargura] = useState(0)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new ResizeObserver(([entry]) => {
      setLargura(Math.floor(entry.contentRect.width))
    })
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  return [ref, largura]
}

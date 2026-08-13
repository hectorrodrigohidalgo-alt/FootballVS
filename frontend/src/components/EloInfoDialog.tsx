import { useEffect, useRef } from 'react'

type EloInfoDialogProps = {
  isOpen: boolean
  onClose: () => void
}

export function EloInfoDialog({ isOpen, onClose }: EloInfoDialogProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null)
  const panelRef = useRef<HTMLElement>(null)

  useEffect(() => {
    if (!isOpen) return
    const previouslyFocused = document.activeElement as HTMLElement | null
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    closeButtonRef.current?.focus()
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
      if (event.key !== 'Tab') return
      const focusable = panelRef.current?.querySelectorAll<HTMLElement>(
        'button, [href], [tabindex]:not([tabindex="-1"])',
      )
      if (!focusable?.length) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }
    document.addEventListener('keydown', handleEscape)
    return () => {
      document.body.style.overflow = previousOverflow
      document.removeEventListener('keydown', handleEscape)
      previouslyFocused?.focus()
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div
      aria-labelledby="elo-dialog-title"
      aria-modal="true"
      className="fixed inset-0 z-50 grid place-items-center bg-ink-950/80 p-4"
      onMouseDown={(event) => {
        if (event.currentTarget === event.target) onClose()
      }}
      role="dialog"
    >
      <section
        className="flex max-h-[85vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl"
        ref={panelRef}
      >
        <header className="flex items-start justify-between gap-4 border-b border-slate-200 p-5 sm:p-6">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-pitch-700">
              Modelo estadístico
            </p>
            <h2 className="mt-1 text-2xl font-black text-ink-950" id="elo-dialog-title">
              ¿Cómo funciona el rating Elo?
            </h2>
          </div>
          <button
            aria-label="Cerrar información de Elo"
            className="rounded-lg border border-slate-300 px-3 py-2 font-bold text-slate-700 hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pitch-700"
            onClick={onClose}
            ref={closeButtonRef}
            type="button"
          >
            Cerrar
          </button>
        </header>

        <div className="overflow-y-auto p-5 text-sm leading-7 text-slate-700 sm:p-6" tabIndex={0}>
          <p>
            Elo representa la fuerza relativa de cada equipo con un número. Un rating mayor
            indica que, según los resultados anteriores, el equipo ha demostrado más fuerza.
            No es una garantía del resultado del próximo partido.
          </p>

          <h3 className="mt-5 text-lg font-black text-ink-950">Cómo cambia después de un partido</h3>
          <p className="mt-2">
            Antes del encuentro se calcula un resultado esperado a partir de la diferencia
            entre ambos ratings. Después se compara esa expectativa con el resultado real. Si
            un equipo supera lo esperado gana puntos; si rinde por debajo, los pierde. Los
            puntos que gana uno son los que pierde el otro.
          </p>
          <pre className="mt-3 overflow-x-auto rounded-xl bg-slate-950 p-4 text-xs text-pitch-100">
            rating nuevo = rating anterior + K × (resultado real − esperado)
          </pre>

          <h3 className="mt-5 text-lg font-black text-ink-950">Configuración de FootballVS</h3>
          <ul className="mt-2 list-disc space-y-2 pl-5">
            <li>Rating inicial general: 1500 puntos.</li>
            <li>Equipos ascendidos: 1400 puntos.</li>
            <li>Factor K: 20, que controla cuánto cambia el rating por partido.</li>
            <li>Ventaja local temporal: 65 puntos al calcular la expectativa.</li>
            <li>Entre temporadas se conserva el 75% de la diferencia respecto de 1500.</li>
            <li>No se añaden puntos por diferencia de goles.</li>
          </ul>

          <h3 className="mt-5 text-lg font-black text-ink-950">Ventaja local y rachas</h3>
          <p className="mt-2">
            Los 65 puntos de localía no se acumulan en el rating. Sólo se usan durante la
            predicción del encuentro. Una racha de derrotas como local reduce el Elo real del
            equipo; por eso la ventaja fija puede quedar compensada o superada por su pérdida
            de fuerza reciente.
          </p>

          <h3 className="mt-5 text-lg font-black text-ink-950">Cambio de temporada</h3>
          <p className="mt-2">
            El Elo no se borra completamente. FootballVS acerca cada rating un 25% hacia 1500
            y conserva el 75% restante. Esto mantiene memoria del rendimiento anterior sin
            asumir que los equipos comienzan exactamente con la misma fuerza.
          </p>

          <h3 className="mt-5 text-lg font-black text-ink-950">Cómo fue validado</h3>
          <p className="mt-2">
            Se probaron 180 configuraciones sobre las temporadas 2024/25 y 2025/26 sin usar
            resultados futuros. Una alternativa sólo podía reemplazar la configuración base
            si mejoraba al menos un 1% y lo hacía en ambas temporadas. La mejor alternativa
            alcanzó 0,93%, por lo que se conservó la configuración más estable.
          </p>

          <p className="mt-5 rounded-xl bg-amber-50 p-4 text-amber-950">
            Elo resume resultados históricos. No conoce lesiones, alineaciones, clima,
            decisiones arbitrales ni cambios tácticos de última hora.
          </p>
        </div>
      </section>
    </div>
  )
}

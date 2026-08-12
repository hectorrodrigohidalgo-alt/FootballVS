type ApiErrorPanelProps = {
  message: string
  onRetry: () => void
  compact?: boolean
}

export function ApiErrorPanel({
  message,
  onRetry,
  compact = false,
}: ApiErrorPanelProps) {
  return (
    <div
      className={`rounded-2xl border border-red-200 bg-red-50 ${compact ? 'p-4' : 'mx-auto max-w-2xl p-6 text-center'}`}
      role="alert"
    >
      <p className="font-bold text-red-900">No pudimos cargar los datos</p>
      <p className="mt-1 text-sm leading-6 text-red-700">{message}</p>
      <button
        className="mt-4 rounded-lg border border-red-300 bg-white px-4 py-2 text-sm font-bold text-red-800 transition hover:bg-red-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-600"
        onClick={onRetry}
        type="button"
      >
        Reintentar
      </button>
    </div>
  )
}

export function DashboardSkeleton() {
  return (
    <div aria-label="Cargando comparación" role="status">
      <div className="h-4 w-28 animate-pulse rounded-full bg-white/15" />
      <div className="mt-3 h-8 w-72 max-w-full animate-pulse rounded-lg bg-white/15" />
      <div className="mt-7 grid gap-4 sm:grid-cols-3">
        {[0, 1, 2].map((item) => (
          <div className="h-32 animate-pulse rounded-2xl bg-white/10" key={item} />
        ))}
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        {[0, 1].map((item) => (
          <div className="h-64 animate-pulse rounded-2xl bg-white/10" key={item} />
        ))}
      </div>
      <span className="sr-only">Cargando resultados de la comparación.</span>
    </div>
  )
}

type CatalogEmptyStateProps = {
  title: string
  message: string
}

export function CatalogEmptyState({ title, message }: CatalogEmptyStateProps) {
  return (
    <div
      className="mb-6 rounded-2xl border border-amber-200 bg-amber-50 p-4"
      role="status"
    >
      <p className="font-bold text-amber-950">{title}</p>
      <p className="mt-1 text-sm leading-6 text-amber-800">{message}</p>
    </div>
  )
}

export function RefreshStatus() {
  return (
    <div
      className="mb-4 rounded-xl border border-white/10 bg-white/10 px-4 py-3 text-sm text-pitch-100"
      role="status"
    >
      Actualizando la comparación con los datos más recientes…
    </div>
  )
}

export function EmptyDashboard() {
  return (
    <div className="mx-auto max-w-xl text-center">
      <span className="mx-auto grid size-14 place-items-center rounded-2xl border border-white/10 bg-white/10 text-2xl text-pitch-400">
        ⚽
      </span>
      <h2 className="mt-5 text-xl font-bold text-white">Tu dashboard aparecerá aquí</h2>
      <p className="mt-2 text-sm leading-6 text-slate-400">
        Completa la selección para consultar las métricas disponibles de ambos equipos.
      </p>
    </div>
  )
}

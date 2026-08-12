export const DATA_STALE_AFTER_HOURS = 48

const HOUR_IN_MILLISECONDS = 60 * 60 * 1000

export type DataFreshness = {
  status: 'fresh' | 'stale' | 'unknown'
  updatedAt: Date | null
  ageInHours: number | null
}

export function getDataFreshness(
  dataUpdatedAt: string,
  nowInMilliseconds = Date.now(),
): DataFreshness {
  const updatedAt = new Date(dataUpdatedAt)
  const updatedAtMilliseconds = updatedAt.getTime()

  // Una fecha inválida se informa como desconocida en vez de provocar que el
  // dashboard falle mientras intenta formatearla.
  if (!Number.isFinite(updatedAtMilliseconds) || !Number.isFinite(nowInMilliseconds)) {
    return { status: 'unknown', updatedAt: null, ageInHours: null }
  }

  // Si el reloj del servidor está unos minutos adelantado, la edad mínima es 0.
  const ageInHours = Math.max(
    0,
    Math.floor((nowInMilliseconds - updatedAtMilliseconds) / HOUR_IN_MILLISECONDS),
  )

  return {
    status: ageInHours > DATA_STALE_AFTER_HOURS ? 'stale' : 'fresh',
    updatedAt,
    ageInHours,
  }
}

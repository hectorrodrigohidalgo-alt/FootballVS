import { describe, expect, it } from 'vitest'

import { getDataFreshness } from './dataFreshness'

const NOW = Date.parse('2026-08-12T12:00:00Z')

describe('antigüedad de datos', () => {
  it('considera recientes los datos de hasta 48 horas', () => {
    expect(getDataFreshness('2026-08-10T12:00:00Z', NOW).status).toBe('fresh')
  })

  it('advierte cuando han pasado más de 48 horas', () => {
    const freshness = getDataFreshness('2026-08-10T11:00:00Z', NOW)

    expect(freshness.status).toBe('stale')
    expect(freshness.ageInHours).toBe(49)
  })

  it('tolera una fecha inválida sin romper la interfaz', () => {
    expect(getDataFreshness('fecha-desconocida', NOW)).toEqual({
      status: 'unknown',
      updatedAt: null,
      ageInHours: null,
    })
  })
})

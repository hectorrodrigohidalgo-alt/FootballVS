import { describe, expect, it } from 'vitest'

import type { Comparison, TeamStatistics } from '../api/types'
import {
  buildHeadToHeadOption,
  formToPoints,
  hasRadarData,
  radarValues,
} from './comparisonOptions'

const statistics: TeamStatistics = {
  matches_played: 10,
  wins: 5,
  draws: 3,
  losses: 2,
  win_percentage: 50,
  points_per_game: 1.8,
  goals_for_per_match: 1.5,
  goals_against_per_match: 0.75,
  clean_sheets: 4,
  both_teams_scored: 5,
  recent_form: ['W', 'D', 'L', 'W', 'W'],
  elo_rating: null,
}

const comparison: Comparison = {
  competition: { id: 'PL', name: 'Premier League', country: 'England', season: '2026/27' },
  team_1: { id: 'team-1', name: 'Arsenal FC', short_name: 'Arsenal', tla: 'ARS', statistics },
  team_2: { id: 'team-2', name: 'Liverpool FC', short_name: 'Liverpool', tla: 'LIV', statistics },
  venue: 'neutral',
  head_to_head: {
    matches_played: 4,
    team_1_wins: 2,
    draws: 1,
    team_2_wins: 1,
    recent_matches: [],
  },
  prediction: null,
  model: { version: null, is_available: false, data_updated_at: '2026-08-12T00:00:00Z' },
}

describe('opciones de gráficos comparativos', () => {
  it('convierte la forma reciente a puntos', () => {
    expect(formToPoints(['W', 'D', 'L'])).toEqual([3, 1, 0])
  })

  it('normaliza todas las dimensiones del radar entre cero y cien', () => {
    const values = radarValues(statistics)

    expect(values).toHaveLength(6)
    expect(values.every((value) => value >= 0 && value <= 100)).toBe(true)
    expect(values[0]).toBe(50)
    expect(values[4]).toBe(40)
  })

  it('evita el radar cuando un equipo no tiene partidos', () => {
    const emptyComparison = {
      ...comparison,
      team_1: {
        ...comparison.team_1,
        statistics: { ...statistics, matches_played: 0 },
      },
    }

    expect(hasRadarData(emptyComparison)).toBe(false)
  })

  it('construye las tres barras del historial directo', () => {
    const option = buildHeadToHeadOption(comparison) as {
      series: Array<{ data: Array<{ value: number }> }>
    }

    expect(option.series[0].data.map((item) => item.value)).toEqual([2, 1, 1])
  })
})

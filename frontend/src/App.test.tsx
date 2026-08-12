import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import App from './App'
import {
  ApiClientError,
  fetchComparison,
  fetchCompetitions,
  fetchTeams,
} from './api/client'
import type { Comparison } from './api/types'
import { renderWithQueryClient } from './test/render'

// Las pruebas del flujo principal no necesitan dibujar SVG reales. El wrapper
// de ECharts se valida por separado en EChart.test.tsx.
vi.mock('./components/EChart', () => ({
  EChart: ({ ariaLabel }: { ariaLabel: string }) => (
    <div aria-label={ariaLabel} role="img" />
  ),
}))

vi.mock('./api/client', async () => {
  const actual = await vi.importActual<typeof import('./api/client')>('./api/client')
  return {
    ...actual,
    fetchComparison: vi.fn(),
    fetchCompetitions: vi.fn(),
    fetchTeams: vi.fn(),
  }
})

const mockedFetchCompetitions = vi.mocked(fetchCompetitions)
const mockedFetchTeams = vi.mocked(fetchTeams)
const mockedFetchComparison = vi.mocked(fetchComparison)

const teams = [
  { id: 'arsenal', name: 'Arsenal', short_name: 'Arsenal', tla: 'ARS' },
  { id: 'liverpool', name: 'Liverpool', short_name: 'Liverpool', tla: 'LIV' },
]

const comparison: Comparison = {
  competition: {
    id: 'PL',
    name: 'Premier League',
    country: 'England',
    season: '2026/27',
  },
  team_1: {
    ...teams[0],
    statistics: {
      matches_played: 10,
      wins: 7,
      draws: 2,
      losses: 1,
      goals_for_per_match: 2.1,
      goals_against_per_match: 0.8,
      recent_form: ['W', 'W', 'D', 'W', 'W'],
      elo_rating: 1852,
    },
  },
  team_2: {
    ...teams[1],
    statistics: {
      matches_played: 10,
      wins: 6,
      draws: 2,
      losses: 2,
      goals_for_per_match: 2,
      goals_against_per_match: 1,
      recent_form: ['W', 'L', 'W', 'W', 'D'],
      elo_rating: 1831,
    },
  },
  venue: 'team1',
  prediction: {
    team_1_win_probability: 0.45,
    draw_probability: 0.25,
    team_2_win_probability: 0.3,
    estimated_team_1_goals: 1.65,
    estimated_team_2_goals: 1.4,
  },
  model: {
    version: 'mock-contract-v1',
    is_mock: true,
    data_updated_at: '2026-08-07T00:00:00+00:00',
  },
}

beforeEach(() => {
  mockedFetchCompetitions.mockResolvedValue([comparison.competition])
  mockedFetchTeams.mockResolvedValue(teams)
  mockedFetchComparison.mockResolvedValue(comparison)
})

async function selectTeams() {
  const user = userEvent.setup()
  const team1Selector = screen.getByLabelText('Equipo 1')
  const team2Selector = screen.getByLabelText('Equipo 2')

  await waitFor(() => expect(team1Selector).toBeEnabled())
  await user.selectOptions(team1Selector, 'arsenal')
  await user.selectOptions(team2Selector, 'liverpool')

  return user
}

describe('comparador principal', () => {
  it('habilita el botón sólo con dos equipos y muestra el dashboard', async () => {
    renderWithQueryClient(<App />)
    const compareButton = screen.getByRole('button', { name: /comparar equipos/i })

    expect(compareButton).toBeDisabled()
    const user = await selectTeams()
    expect(compareButton).toBeEnabled()

    await user.click(compareButton)

    expect(
      await screen.findByRole('heading', { name: 'Arsenal vs Liverpool' }),
    ).toBeInTheDocument()
    expect(mockedFetchComparison).toHaveBeenCalledWith({
      competition: 'PL',
      team1: 'arsenal',
      team2: 'liverpool',
      venue: 'team1',
    })
    expect(screen.getByText('Datos simulados')).toBeInTheDocument()
  })

  it('muestra un error comprensible cuando falla la comparación', async () => {
    mockedFetchComparison.mockRejectedValueOnce(
      new ApiClientError(
        'One or more selected teams do not exist.',
        'team_not_found',
        404,
      ),
    )
    renderWithQueryClient(<App />)
    const user = await selectTeams()

    await user.click(screen.getByRole('button', { name: /comparar equipos/i }))

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Uno de los equipos seleccionados no está disponible.')
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeEnabled()
  })

  it('representa datos reales sin inventar predicción ni Elo', async () => {
    mockedFetchComparison.mockResolvedValueOnce({
      ...comparison,
      team_1: {
        ...comparison.team_1,
        statistics: { ...comparison.team_1.statistics, elo_rating: null },
      },
      team_2: {
        ...comparison.team_2,
        statistics: { ...comparison.team_2.statistics, elo_rating: null },
      },
      head_to_head: {
        matches_played: 0,
        team_1_wins: 0,
        draws: 0,
        team_2_wins: 0,
        recent_matches: [],
      },
      prediction: null,
      model: {
        version: null,
        is_available: false,
        message: 'Predictions and Elo will be available in Phase 4.',
        data_updated_at: '2026-08-12T00:00:00Z',
      },
    })
    renderWithQueryClient(<App />)
    const user = await selectTeams()

    await user.click(screen.getByRole('button', { name: /comparar equipos/i }))

    expect(await screen.findByText('Predicción aún no disponible')).toBeInTheDocument()
    expect(screen.getAllByText('Elo pendiente')).toHaveLength(2)
    expect(screen.getByText('Datos reales · modelo pendiente')).toBeInTheDocument()
  })
})

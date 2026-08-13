import { afterEach, describe, expect, it, vi } from 'vitest'

import { fetchComparison } from './client'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('cliente HTTP', () => {
  it('construye la consulta de comparación y entrega los datos', async () => {
    const comparison = {
      competition: {
        id: 'PL',
        name: 'Premier League',
        country: 'England',
        season: '2026/27',
      },
      team_1: {
        id: 'arsenal',
        name: 'Arsenal',
        short_name: 'Arsenal',
        tla: 'ARS',
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
        id: 'liverpool',
        name: 'Liverpool',
        short_name: 'Liverpool',
        tla: 'LIV',
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
        over_2_5_probability: 0.58,
        under_2_5_probability: 0.42,
        both_teams_score_probability: 0.55,
        top_scorelines: [
          { team_1_goals: 1, team_2_goals: 1, probability: 0.12 },
          { team_1_goals: 2, team_2_goals: 1, probability: 0.11 },
          { team_1_goals: 1, team_2_goals: 0, probability: 0.1 },
        ],
      },
      model: {
        version: 'mock-contract-v1',
        is_mock: true,
        data_updated_at: '2026-08-07T00:00:00+00:00',
      },
    }
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ data: comparison, meta: { source: 'mock' } }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchComparison({
      competition: 'PL',
      team1: 'arsenal',
      team2: 'liverpool',
      venue: 'team1',
    })

    expect(result).toEqual(comparison)
    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:7071/api/v1/comparisons?competition=PL&team1=arsenal&team2=liverpool&venue=team1',
      { headers: { Accept: 'application/json' } },
    )
  })

  it('convierte el contrato de error de la API en ApiClientError', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: {
              code: 'team_not_found',
              message: 'One or more selected teams do not exist.',
            },
          }),
          { status: 404, headers: { 'Content-Type': 'application/json' } },
        ),
      ),
    )

    await expect(
      fetchComparison({
        competition: 'PL',
        team1: 'unknown',
        team2: 'liverpool',
        venue: 'neutral',
      }),
    ).rejects.toEqual(
      expect.objectContaining({
        code: 'team_not_found',
        status: 404,
      }),
    )
  })
})

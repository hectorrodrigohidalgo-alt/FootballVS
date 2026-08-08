export type Venue = 'team1' | 'neutral' | 'team2'

export type Competition = {
  id: string
  name: string
  country: string
  season: string
}

export type TeamSummary = {
  id: string
  name: string
  short_name: string
  tla: string
}

export type TeamStatistics = {
  matches_played: number
  wins: number
  draws: number
  losses: number
  goals_for_per_match: number
  goals_against_per_match: number
  recent_form: Array<'W' | 'D' | 'L'>
  elo_rating: number
}

export type ComparedTeam = TeamSummary & {
  statistics: TeamStatistics
}

export type Prediction = {
  team_1_win_probability: number
  draw_probability: number
  team_2_win_probability: number
  estimated_team_1_goals: number
  estimated_team_2_goals: number
}

export type ModelMetadata = {
  version: string
  is_mock: boolean
  data_updated_at: string
}

export type Comparison = {
  competition: Competition
  team_1: ComparedTeam
  team_2: ComparedTeam
  venue: Venue
  prediction: Prediction
  model: ModelMetadata
}

export type ComparisonRequest = {
  team1: string
  team2: string
  venue: Venue
}

export type ApiEnvelope<T> = {
  data: T
  meta: {
    source: string
    [key: string]: unknown
  }
}

export type ApiErrorBody = {
  error: {
    code: string
    message: string
  }
}

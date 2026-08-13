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
  scope?: 'overall' | 'home' | 'away'
  matches_played: number
  wins: number
  draws: number
  losses: number
  win_percentage?: number
  points_per_game?: number
  goals_for_per_match: number
  goals_against_per_match: number
  clean_sheets?: number
  both_teams_scored?: number
  recent_form: Array<'W' | 'D' | 'L'>
  elo_rating: number | null
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
  over_2_5_probability: number
  under_2_5_probability: number
  both_teams_score_probability: number
  top_scorelines: Array<{
    team_1_goals: number
    team_2_goals: number
    probability: number
  }>
}

export type ModelMetadata = {
  version: string | null
  elo_version?: string
  status?: 'validated' | 'experimental'
  is_mock?: boolean
  is_available?: boolean
  message?: string | null
  input_data_cutoff?: string
  matches_used?: number
  data_updated_at: string
}

export type HeadToHeadMatch = {
  id: string
  utc_date: string
  home_team_id: string
  away_team_id: string
  home_score: number
  away_score: number
}

export type HeadToHead = {
  matches_played: number
  team_1_wins: number
  draws: number
  team_2_wins: number
  recent_matches: HeadToHeadMatch[]
}

export type Comparison = {
  competition: Competition
  team_1: ComparedTeam
  team_2: ComparedTeam
  venue: Venue
  head_to_head?: HeadToHead
  prediction: Prediction | null
  model: ModelMetadata
}

export type ComparisonRequest = {
  competition: string
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

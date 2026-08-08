import type {
  ApiEnvelope,
  ApiErrorBody,
  Comparison,
  ComparisonRequest,
  Competition,
  TeamSummary,
} from './types'

// Vite sólo expone al navegador variables con el prefijo VITE_. Esta URL es
// pública; la clave de football-data.org permanece en Azure Functions.
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:7071/api/v1'
).replace(/\/$/, '')

export class ApiClientError extends Error {
  readonly code: string
  readonly status: number

  constructor(message: string, code: string, status: number) {
    super(message)
    this.name = 'ApiClientError'
    this.code = code
    this.status = status
  }
}

async function request<T>(path: string): Promise<ApiEnvelope<T>> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Accept: 'application/json' },
  })

  // Leemos JSON incluso en errores para conservar el código y el mensaje
  // uniformes enviados por Azure Functions.
  const body = (await response.json()) as ApiEnvelope<T> | ApiErrorBody

  if (!response.ok) {
    const apiError = 'error' in body ? body.error : undefined
    throw new ApiClientError(
      apiError?.message ?? 'The API request failed.',
      apiError?.code ?? 'request_failed',
      response.status,
    )
  }

  return body as ApiEnvelope<T>
}

export async function fetchCompetitions(): Promise<Competition[]> {
  return (await request<Competition[]>('/competitions')).data
}

export async function fetchTeams(competitionId: string): Promise<TeamSummary[]> {
  const encodedCompetition = encodeURIComponent(competitionId)
  return (await request<TeamSummary[]>(`/competitions/${encodedCompetition}/teams`)).data
}

export async function fetchComparison(
  comparison: ComparisonRequest,
): Promise<Comparison> {
  const parameters = new URLSearchParams(comparison)
  return (await request<Comparison>(`/comparisons?${parameters.toString()}`)).data
}

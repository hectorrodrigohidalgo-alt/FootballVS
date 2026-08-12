import { useEffect, useState, type FormEvent } from 'react'
import { useQuery } from '@tanstack/react-query'

import {
  ApiClientError,
  fetchComparison,
  fetchCompetitions,
  fetchTeams,
} from './api/client'
import type { ComparisonRequest, TeamSummary, Venue } from './api/types'
import { ComparisonDashboard } from './components/ComparisonDashboard'
import {
  ApiErrorPanel,
  DashboardSkeleton,
  EmptyDashboard,
} from './components/DashboardStates'

type TeamSelectorProps = {
  id: string
  label: string
  value: string
  excludedTeam: string
  teams: TeamSummary[]
  isLoading: boolean
  isDisabled: boolean
  onChange: (value: string) => void
}

// Icono local en SVG: no requiere descargar imágenes ni cargar una librería.
function FootballIcon({ className = 'size-6' }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      className={className}
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.7" />
      <path
        d="m9.4 8.5 2.6-1.9 2.6 1.9-1 3h-3.2l-1-3Zm1 3-3 2.2m6.2-2.2 3 2.2M12 6.6V3m-4.6 10.7.9 3.4m8.3-3.4-.9 3.4M8.3 17.1l3.7 1.7 3.7-1.7"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.7"
      />
    </svg>
  )
}

function TeamSelector({
  id,
  label,
  value,
  excludedTeam,
  teams,
  isLoading,
  isDisabled,
  onChange,
}: TeamSelectorProps) {
  return (
    <div>
      <label className="mb-2 block text-sm font-semibold text-slate-700" htmlFor={id}>
        {label}
      </label>
      <select
        className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3.5 text-base text-slate-900 shadow-sm outline-none transition focus:border-pitch-500 focus:ring-4 focus:ring-pitch-100 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400"
        disabled={isDisabled}
        id={id}
        onChange={(event) => onChange(event.target.value)}
        value={value}
      >
        <option value="">{isLoading ? 'Cargando equipos…' : 'Selecciona un equipo'}</option>
        {teams.map((team) => (
          // Excluir el otro equipo impide comparar un club consigo mismo.
          <option disabled={team.id === excludedTeam} key={team.id} value={team.id}>
            {team.name}
          </option>
        ))}
      </select>
    </div>
  )
}

function friendlyErrorMessage(error: Error | null): string {
  if (error instanceof ApiClientError) {
    const messages: Record<string, string> = {
      competition_not_found: 'La competición solicitada no está disponible.',
      invalid_team_selection: 'Debes seleccionar dos equipos diferentes.',
      invalid_venue: 'La condición del encuentro no es válida.',
      missing_parameters: 'Faltan datos para realizar la comparación.',
      team_not_found: 'Uno de los equipos seleccionados no está disponible.',
      comparison_data_not_found:
        'Todavía no hay estadísticas sincronizadas para esta comparación.',
    }
    return messages[error.code] ?? 'La API no pudo completar la solicitud.'
  }

  return 'No pudimos conectar con la API local. Comprueba que Azure Functions esté ejecutándose.'
}

function App() {
  const [competitionId, setCompetitionId] = useState('')
  const [team1, setTeam1] = useState('')
  const [team2, setTeam2] = useState('')
  const [venue, setVenue] = useState<Venue>('team1')
  const [submittedComparison, setSubmittedComparison] =
    useState<ComparisonRequest | null>(null)

  // Competiciones y equipos se consultan al cargar. TanStack Query conserva
  // ambos resultados durante cinco minutos según la configuración global.
  const competitionsQuery = useQuery({
    queryKey: ['competitions'],
    queryFn: fetchCompetitions,
  })

  const teamsQuery = useQuery({
    queryKey: ['teams', competitionId],
    queryFn: () => fetchTeams(competitionId),
    enabled: Boolean(competitionId),
  })

  // La comparación es una consulta declarativa diferida: sólo se habilita
  // después de que el usuario envía una selección válida.
  const comparisonQuery = useQuery({
    queryKey: ['comparison', submittedComparison],
    queryFn: () => fetchComparison(submittedComparison!),
    enabled: submittedComparison !== null,
  })

  const teams = teamsQuery.data ?? []
  const selectedCompetition = competitionsQuery.data?.find(
    (competition) => competition.id === competitionId,
  )
  const canCompare = Boolean(
    competitionId && teamsQuery.isSuccess && team1 && team2 && team1 !== team2,
  )

  useEffect(() => {
    const firstCompetition = competitionsQuery.data?.[0]
    if (!competitionId && firstCompetition) {
      setCompetitionId(firstCompetition.id)
    }
  }, [competitionId, competitionsQuery.data])

  function clearPreviousComparison() {
    // Oculta resultados antiguos cuando cambia cualquier entrada del formulario.
    setSubmittedComparison(null)
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!canCompare) return
    setSubmittedComparison({ competition: competitionId, team1, team2, venue })
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,#536449_0%,#2d3b29_42%,#172117_100%)]">
      {/* Cabecera global con identidad del producto y estado del MVP. */}
      <header className="border-b border-white/10 bg-moss-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <a className="flex items-center gap-2 text-white" href="#top" aria-label="FootballVS, inicio">
            <span className="grid size-10 place-items-center rounded-xl bg-pitch-500 text-white shadow-sm">
              <FootballIcon />
            </span>
            <span className="text-lg font-black tracking-tight">
              Football<span className="text-pitch-400">VS</span>
            </span>
          </a>
          <span className="rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-bold uppercase tracking-[0.16em] text-pitch-100">
            MVP en desarrollo
          </span>
        </div>
      </header>

      <main id="top">
        {/* Presentación del producto y formulario principal de comparación. */}
        <section className="mx-auto max-w-7xl px-4 pb-12 pt-12 sm:px-6 sm:pt-16 lg:px-8 lg:pb-20 lg:pt-24">
          <div className="mx-auto max-w-3xl text-center">
            <p className="mb-4 text-sm font-bold uppercase tracking-[0.2em] text-pitch-400">
              {selectedCompetition
                ? `${selectedCompetition.name} · Temporada ${selectedCompetition.season}`
                : 'Datos reales de fútbol'}
            </p>
            <h1 className="text-balance text-4xl font-black tracking-[-0.04em] text-white sm:text-5xl lg:text-6xl">
              Compara equipos. Entiende el partido.
            </h1>
            <p className="mx-auto mt-5 max-w-2xl text-pretty text-base leading-7 text-slate-300 sm:text-lg">
              Explora forma reciente, rendimiento histórico y probabilidades estimadas en un dashboard claro e interactivo.
            </p>
          </div>

          <form
            className="mx-auto mt-10 max-w-5xl rounded-3xl border border-white bg-white/95 p-5 shadow-[0_24px_70px_-30px_rgba(16,60,43,0.35)] sm:p-8"
            onSubmit={handleSubmit}
          >
            <div className="mb-7 flex flex-col gap-4 border-b border-slate-100 pb-6 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-pitch-600">Nueva comparación</p>
                <h2 className="mt-1 text-2xl font-bold tracking-tight text-ink-950">Elige los protagonistas</h2>
              </div>
              <div className="w-full sm:w-64">
                <label className="mb-2 block text-sm font-semibold text-slate-700" htmlFor="competition">
                  Competición
                </label>
                <select
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700"
                  id="competition"
                  onChange={(event) => {
                    setCompetitionId(event.target.value)
                    setTeam1('')
                    setTeam2('')
                    clearPreviousComparison()
                  }}
                  value={competitionId}
                  disabled={competitionsQuery.isPending || competitionsQuery.isError}
                >
                  <option value="">
                    {competitionsQuery.isPending
                      ? 'Cargando competición…'
                      : 'Selecciona una competición'}
                  </option>
                  {(competitionsQuery.data ?? []).map((competition) => (
                    <option key={competition.id} value={competition.id}>
                      {competition.name} · {competition.season}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {competitionsQuery.isError || teamsQuery.isError ? (
              <div className="mb-6">
                <ApiErrorPanel
                  compact
                  message={friendlyErrorMessage(
                    competitionsQuery.error ?? teamsQuery.error,
                  )}
                  onRetry={() => {
                    void competitionsQuery.refetch()
                    void teamsQuery.refetch()
                  }}
                />
              </div>
            ) : null}

            <div className="grid items-end gap-4 lg:grid-cols-[1fr_auto_1fr] lg:gap-6">
              <TeamSelector
                excludedTeam={team2}
                id="team-1"
                isDisabled={!teamsQuery.isSuccess}
                isLoading={teamsQuery.isPending}
                label="Equipo 1"
                onChange={(value) => {
                  setTeam1(value)
                  clearPreviousComparison()
                }}
                teams={teams}
                value={team1}
              />

              <div className="mx-auto grid size-12 place-items-center rounded-full border-4 border-white bg-ink-950 text-sm font-black text-white shadow-md lg:mb-1">
                VS
              </div>

              <TeamSelector
                excludedTeam={team1}
                id="team-2"
                isDisabled={!teamsQuery.isSuccess}
                isLoading={teamsQuery.isPending}
                label="Equipo 2"
                onChange={(value) => {
                  setTeam2(value)
                  clearPreviousComparison()
                }}
                teams={teams}
                value={team2}
              />
            </div>

            {/* La localía es obligatoria porque modifica las probabilidades. */}
            <fieldset className="mt-7">
              <legend className="text-sm font-semibold text-slate-700">Condición del encuentro</legend>
              <div className="mt-3 grid gap-3 sm:grid-cols-3">
                {[
                  ['team1', 'Equipo 1 local'],
                  ['neutral', 'Campo neutral'],
                  ['team2', 'Equipo 2 local'],
                ].map(([value, label]) => (
                  <label
                    className={`flex cursor-pointer items-center gap-3 rounded-xl border px-4 py-3 text-sm font-semibold transition ${
                      venue === value
                        ? 'border-pitch-500 bg-pitch-50 text-pitch-900 ring-2 ring-pitch-100'
                        : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
                    }`}
                    key={value}
                  >
                    <input
                      checked={venue === value}
                      className="size-4 accent-pitch-600"
                      name="venue"
                      onChange={() => {
                        setVenue(value as Venue)
                        clearPreviousComparison()
                      }}
                      type="radio"
                      value={value}
                    />
                    {label}
                  </label>
                ))}
              </div>
            </fieldset>

            <div className="mt-8 flex flex-col items-center justify-between gap-4 border-t border-slate-100 pt-6 sm:flex-row">
              <p className="text-center text-sm text-slate-500 sm:text-left">
                {!canCompare ? 'Selecciona dos equipos distintos para continuar.' : 'La comparación está lista.'}
              </p>
              <button
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-pitch-600 px-6 py-3.5 text-sm font-bold text-white shadow-lg shadow-pitch-600/20 transition enabled:hover:-translate-y-0.5 enabled:hover:bg-pitch-500 enabled:focus-visible:outline-2 enabled:focus-visible:outline-offset-2 enabled:focus-visible:outline-pitch-600 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400 disabled:shadow-none sm:w-auto"
                disabled={!canCompare || comparisonQuery.isFetching}
                type="submit"
              >
                {comparisonQuery.isFetching ? 'Comparando…' : 'Comparar equipos'}
                <span aria-hidden="true">→</span>
              </button>
            </div>
          </form>
        </section>

        {/* aria-live comunica cambios del dashboard a tecnologías de asistencia. */}
        <section aria-live="polite" className="border-t border-white/10 bg-moss-950/70">
          <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
            {comparisonQuery.isLoading ? <DashboardSkeleton /> : null}
            {comparisonQuery.isError ? (
              <ApiErrorPanel
                message={friendlyErrorMessage(comparisonQuery.error)}
                onRetry={() => void comparisonQuery.refetch()}
              />
            ) : null}
            {comparisonQuery.isSuccess ? (
              <ComparisonDashboard comparison={comparisonQuery.data} />
            ) : null}
            {!submittedComparison ? <EmptyDashboard /> : null}
          </div>
        </section>
      </main>

      <footer className="border-t border-white/10 bg-[#0d140f] px-4 py-6 text-center text-xs text-slate-400">
        FootballVS · Datos estadísticos informativos; el modelo predictivo se incorporará en la Fase 4.
      </footer>
    </div>
  )
}

export default App

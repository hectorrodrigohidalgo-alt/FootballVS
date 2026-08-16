import { useState } from 'react'
import type { Comparison, TeamStatistics } from '../api/types'
import { DATA_STALE_AFTER_HOURS, getDataFreshness } from '../utils/dataFreshness'
import { ComparisonCharts } from './ComparisonCharts'
import { EloInfoDialog } from './EloInfoDialog'

type ComparisonDashboardProps = {
  comparison: Comparison
}

const percentFormatter = new Intl.NumberFormat('es-CL', {
  style: 'percent',
  maximumFractionDigits: 1,
})

const formLabels = {
  W: { label: 'V', description: 'Victoria', className: 'bg-pitch-100 text-pitch-900' },
  D: { label: 'E', description: 'Empate', className: 'bg-amber-100 text-amber-900' },
  L: { label: 'D', description: 'Derrota', className: 'bg-red-100 text-red-900' },
} as const

function RecentForm({ form }: { form: TeamStatistics['recent_form'] }) {
  if (form.length === 0) {
    return <span className="text-sm text-slate-600">Sin datos</span>
  }

  return (
    <div
      aria-label={`Forma reciente: ${form.map((result) => formLabels[result].description).join(', ')}`}
      className="flex flex-wrap justify-end gap-1.5"
      role="img"
    >
      {form.map((result, index) => (
        <span
          aria-hidden="true"
          className={`grid size-7 place-items-center rounded-md text-xs font-black ${formLabels[result].className}`}
          key={`${result}-${index}`}
          title={formLabels[result].description}
        >
          {formLabels[result].label}
        </span>
      ))}
    </div>
  )
}

function TeamStatisticsCard({
  name,
  statistics,
  onOpenEloInfo,
}: {
  name: string
  statistics: TeamStatistics
  onOpenEloInfo: () => void
}) {
  return (
    <article className="min-w-0 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <div className="flex flex-col items-start justify-between gap-3 min-[420px]:flex-row">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-600">Rendimiento</p>
          <h3 className="mt-1 break-words text-xl font-black text-ink-950">{name}</h3>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className="rounded-lg bg-slate-100 px-3 py-1 text-sm font-bold text-slate-700">
            {statistics.elo_rating === null
              ? 'Elo no disponible'
              : `Elo ${Math.round(statistics.elo_rating)}`}
          </span>
          <button
            className="text-xs font-bold text-pitch-800 underline decoration-pitch-300 underline-offset-2"
            onClick={onOpenEloInfo}
            type="button"
          >
            ¿Cómo funciona?
          </button>
        </div>
      </div>
      <div className="mt-6 grid grid-cols-2 gap-2 text-center min-[420px]:grid-cols-4">
        {[
          ['PJ', statistics.matches_played],
          ['V', statistics.wins],
          ['E', statistics.draws],
          ['D', statistics.losses],
        ].map(([label, value]) => (
          <div className="rounded-xl bg-slate-50 px-2 py-3" key={label}>
            <p className="text-lg font-black text-ink-950">{value}</p>
            <p className="mt-1 text-xs font-bold text-slate-600">{label}</p>
          </div>
        ))}
      </div>
      <dl className="mt-5 space-y-3 text-sm">
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">Puntos por partido</dt>
          <dd className="font-bold text-slate-800">{statistics.points_per_game ?? '—'}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">Porcentaje de victorias</dt>
          <dd className="font-bold text-slate-800">
            {statistics.win_percentage === undefined
              ? '—'
              : `${statistics.win_percentage}%`}
          </dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">Goles a favor por partido</dt>
          <dd className="font-bold text-slate-800">{statistics.goals_for_per_match}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">Goles en contra por partido</dt>
          <dd className="font-bold text-slate-800">{statistics.goals_against_per_match}</dd>
        </div>
        <div className="flex items-center justify-between gap-4">
          <dt className="text-slate-500">Últimos cinco</dt>
          <dd><RecentForm form={statistics.recent_form} /></dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">Porterías a cero</dt>
          <dd className="font-bold text-slate-800">{statistics.clean_sheets ?? '—'}</dd>
        </div>
      </dl>
    </article>
  )
}

export function ComparisonDashboard({ comparison }: ComparisonDashboardProps) {
  const [isEloInfoOpen, setIsEloInfoOpen] = useState(false)
  const { prediction, team_1: team1, team_2: team2, model } = comparison
  const freshness = getDataFreshness(model.data_updated_at)
  const updatedAt = freshness.updatedAt
    ? new Intl.DateTimeFormat('es-CL', {
        dateStyle: 'medium',
        timeStyle: 'short',
        timeZone: 'UTC',
      }).format(freshness.updatedAt)
    : 'fecha desconocida'

  return (
    <div className="min-w-0">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-pitch-400">Dashboard</p>
          <h2 className="mt-1 break-words text-2xl font-black tracking-tight text-white sm:text-3xl">
            {team1.name} <span className="text-slate-500">vs</span> {team2.name}
          </h2>
        </div>
        <div className="text-left sm:text-right">
          <span className="inline-flex rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-900">
            {model.status === 'validated'
              ? 'Datos reales · modelo validado'
              : model.is_mock
                ? 'Datos simulados'
                : 'Modelo no disponible'}
          </span>
          <p className="mt-2 text-xs text-slate-400">Actualizado: {updatedAt}</p>
        </div>
      </div>

      {prediction ? (
        <div className="mt-7">
          <div className="grid gap-4 sm:grid-cols-3">
          {[
            [team1.name, prediction.team_1_win_probability],
            ['Empate', prediction.draw_probability],
            [team2.name, prediction.team_2_win_probability],
          ].map(([label, probability], index) => (
            <article
              className={`rounded-2xl border p-5 ${index === 1 ? 'border-slate-200 bg-white' : 'border-pitch-100 bg-pitch-50'}`}
              key={String(label)}
            >
              <p className="text-sm font-semibold text-slate-600">{label}</p>
              <p className="mt-2 text-3xl font-black text-ink-950">
                {percentFormatter.format(Number(probability))}
              </p>
            </article>
          ))}
          </div>
          <div className="mt-4 grid gap-4 sm:grid-cols-3">
            <article className="rounded-2xl border border-slate-200 bg-white p-5">
              <p className="text-sm text-slate-500">Goles esperados</p>
              <p className="mt-2 text-xl font-black text-ink-950">
                {prediction.estimated_team_1_goals.toFixed(2)} –{' '}
                {prediction.estimated_team_2_goals.toFixed(2)}
              </p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-5">
              <p className="text-sm text-slate-500">Más de 2,5 goles</p>
              <p className="mt-2 text-xl font-black text-ink-950">
                {percentFormatter.format(prediction.over_2_5_probability)}
              </p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-5">
              <p className="text-sm text-slate-500">Ambos equipos marcan</p>
              <p className="mt-2 text-xl font-black text-ink-950">
                {percentFormatter.format(prediction.both_teams_score_probability)}
              </p>
            </article>
          </div>
          <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-5">
            <p className="text-sm font-bold text-slate-700">Marcadores más probables</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {prediction.top_scorelines.map((scoreline) => (
                <span
                  className="rounded-full bg-pitch-50 px-3 py-2 text-sm font-bold text-pitch-900"
                  key={`${scoreline.team_1_goals}-${scoreline.team_2_goals}`}
                >
                  {scoreline.team_1_goals}–{scoreline.team_2_goals}{' '}
                  {percentFormatter.format(scoreline.probability)}
                </span>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="mt-7 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-amber-950">
          <p className="font-bold">Predicción aún no disponible</p>
          <p className="mt-1 text-sm">{model.message ?? 'El modelo se incorporará en la Fase 4.'}</p>
        </div>
      )}

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <div className="rounded-2xl bg-ink-950 p-5 text-white">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-pitch-400">Historial directo</p>
          <p className="mt-3 text-3xl font-black">{comparison.head_to_head?.matches_played ?? 0}</p>
          <p className="mt-1 text-sm text-slate-400">partidos finalizados disponibles</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-600">Modelo</p>
          <p className="mt-3 font-bold text-ink-950">{model.version ?? 'No disponible'}</p>
          <p className="mt-1 text-sm leading-6 text-slate-500">
            {model.matches_used ?? 0} partidos utilizados · Elo {model.elo_version ?? 'no disponible'}
          </p>
        </div>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <TeamStatisticsCard
          name={team1.name}
          onOpenEloInfo={() => setIsEloInfoOpen(true)}
          statistics={team1.statistics}
        />
        <TeamStatisticsCard
          name={team2.name}
          onOpenEloInfo={() => setIsEloInfoOpen(true)}
          statistics={team2.statistics}
        />
      </div>

      {freshness.status !== 'fresh' ? (
        <div
          className="mt-5 rounded-2xl border border-amber-300/40 bg-amber-100 p-4 text-amber-950"
          role="status"
        >
          <p className="font-bold">
            {freshness.status === 'stale'
              ? `Datos con más de ${DATA_STALE_AFTER_HOURS} horas`
              : 'Fecha de actualización no disponible'}
          </p>
          <p className="mt-1 text-sm leading-6">
            {freshness.status === 'stale'
              ? `La última sincronización fue hace aproximadamente ${freshness.ageInHours} horas. Las cifras pueden no incluir los partidos más recientes.`
              : 'No pudimos comprobar cuándo se sincronizaron estas cifras.'}
          </p>
        </div>
      ) : null}

      <ComparisonCharts comparison={comparison} />
      <EloInfoDialog isOpen={isEloInfoOpen} onClose={() => setIsEloInfoOpen(false)} />
    </div>
  )
}

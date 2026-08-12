import type { Comparison, TeamStatistics } from '../api/types'

type ComparisonDashboardProps = {
  comparison: Comparison
}

const percentFormatter = new Intl.NumberFormat('es-CL', {
  style: 'percent',
  maximumFractionDigits: 1,
})

const formLabels = {
  W: { label: 'V', className: 'bg-pitch-100 text-pitch-900' },
  D: { label: 'E', className: 'bg-amber-100 text-amber-900' },
  L: { label: 'D', className: 'bg-red-100 text-red-900' },
} as const

function RecentForm({ form }: { form: TeamStatistics['recent_form'] }) {
  return (
    <div className="flex gap-1.5" aria-label="Forma reciente">
      {form.map((result, index) => (
        <span
          className={`grid size-7 place-items-center rounded-md text-xs font-black ${formLabels[result].className}`}
          key={`${result}-${index}`}
          title={result === 'W' ? 'Victoria' : result === 'D' ? 'Empate' : 'Derrota'}
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
}: {
  name: string
  statistics: TeamStatistics
}) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">Rendimiento</p>
          <h3 className="mt-1 text-xl font-black text-ink-950">{name}</h3>
        </div>
        <span className="rounded-lg bg-slate-100 px-3 py-1 text-sm font-bold text-slate-700">
          {statistics.elo_rating === null ? 'Elo pendiente' : `Elo ${statistics.elo_rating}`}
        </span>
      </div>
      <div className="mt-6 grid grid-cols-4 gap-2 text-center">
        {[
          ['PJ', statistics.matches_played],
          ['V', statistics.wins],
          ['E', statistics.draws],
          ['D', statistics.losses],
        ].map(([label, value]) => (
          <div className="rounded-xl bg-slate-50 px-2 py-3" key={label}>
            <p className="text-lg font-black text-ink-950">{value}</p>
            <p className="mt-1 text-xs font-bold text-slate-400">{label}</p>
          </div>
        ))}
      </div>
      <dl className="mt-5 space-y-3 text-sm">
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
      </dl>
    </article>
  )
}

export function ComparisonDashboard({ comparison }: ComparisonDashboardProps) {
  const { prediction, team_1: team1, team_2: team2, model } = comparison
  const updatedAt = new Intl.DateTimeFormat('es-CL', {
    dateStyle: 'medium',
    timeZone: 'UTC',
  }).format(new Date(model.data_updated_at))

  return (
    <div>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-pitch-400">Dashboard</p>
          <h2 className="mt-1 text-2xl font-black tracking-tight text-white sm:text-3xl">
            {team1.name} <span className="text-slate-500">vs</span> {team2.name}
          </h2>
        </div>
        <div className="text-left sm:text-right">
          <span className="inline-flex rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-900">
            {model.is_available === false ? 'Datos reales · modelo pendiente' : 'Datos simulados'}
          </span>
          <p className="mt-2 text-xs text-slate-400">Actualizado: {updatedAt}</p>
        </div>
      </div>

      {prediction ? (
        <div className="mt-7 grid gap-4 sm:grid-cols-3">
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
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">Modelo</p>
          <p className="mt-3 font-bold text-ink-950">{model.version ?? 'Pendiente de implementación'}</p>
          <p className="mt-1 text-sm leading-6 text-slate-500">
            Contrato provisional para validar la interfaz. No representa el modelo final.
          </p>
        </div>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <TeamStatisticsCard name={team1.name} statistics={team1.statistics} />
        <TeamStatisticsCard name={team2.name} statistics={team2.statistics} />
      </div>
    </div>
  )
}

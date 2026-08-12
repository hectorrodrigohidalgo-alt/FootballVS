import { useMemo } from 'react'

import type { Comparison, HeadToHeadMatch } from '../api/types'
import {
  buildFormOption,
  buildHeadToHeadOption,
  buildRadarOption,
  hasRadarData,
} from '../charts/comparisonOptions'
import { EChart } from './EChart'

type ComparisonChartsProps = {
  comparison: Comparison
}

function EmptyChart({ message }: { message: string }) {
  return (
    <div className="grid h-72 place-items-center rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm leading-6 text-slate-500">
      {message}
    </div>
  )
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <article className="min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <h3 className="text-lg font-black text-ink-950">{title}</h3>
      <div className="mt-4 min-w-0">{children}</div>
    </article>
  )
}

function matchLabel(match: HeadToHeadMatch, comparison: Comparison): string {
  const teamNames = new Map([
    [comparison.team_1.id, comparison.team_1.short_name],
    [comparison.team_2.id, comparison.team_2.short_name],
  ])
  const date = new Intl.DateTimeFormat('es-CL', {
    dateStyle: 'medium',
    timeZone: 'UTC',
  }).format(new Date(match.utc_date))
  return `${date} · ${teamNames.get(match.home_team_id) ?? 'Local'} ${match.home_score}–${match.away_score} ${teamNames.get(match.away_team_id) ?? 'Visita'}`
}

export function ComparisonCharts({ comparison }: ComparisonChartsProps) {
  // Evita reconstruir objetos grandes de configuración durante renders que no
  // cambian la comparación seleccionada.
  const radarOption = useMemo(() => buildRadarOption(comparison), [comparison])
  const formOption = useMemo(() => buildFormOption(comparison), [comparison])
  const historyOption = useMemo(() => buildHeadToHeadOption(comparison), [comparison])
  const hasForm =
    comparison.team_1.statistics.recent_form.length > 0 ||
    comparison.team_2.statistics.recent_form.length > 0
  const history = comparison.head_to_head

  return (
    <section
      aria-label="Gráficos de comparación"
      className="mt-4 grid min-w-0 gap-4 lg:grid-cols-2"
    >
      <ChartCard title="Perfil comparativo">
        {hasRadarData(comparison) ? (
          <EChart
            ariaLabel={`Radar estadístico de ${comparison.team_1.name} y ${comparison.team_2.name}`}
            className="h-80 sm:h-96"
            option={radarOption}
          />
        ) : (
          <EmptyChart message="Aún no hay partidos finalizados suficientes para construir el radar." />
        )}
      </ChartCard>

      <ChartCard title="Forma reciente">
        {hasForm ? (
          <EChart
            ariaLabel={`Forma reciente de ${comparison.team_1.name} y ${comparison.team_2.name}`}
            className="h-80 sm:h-96"
            option={formOption}
          />
        ) : (
          <EmptyChart message="La temporada todavía no tiene resultados para mostrar la forma reciente." />
        )}
      </ChartCard>

      <div className="lg:col-span-2">
        <ChartCard title="Historial directo">
          {history && history.matches_played > 0 ? (
            <div className="grid min-w-0 gap-6 lg:grid-cols-2">
              <EChart
                ariaLabel={`Resultados históricos entre ${comparison.team_1.name} y ${comparison.team_2.name}`}
                className="h-72"
                option={historyOption}
              />
              <ol className="space-y-2" aria-label="Últimos enfrentamientos">
                {history.recent_matches.map((match) => (
                  <li
                    className="break-words rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-700"
                    key={match.id}
                  >
                    {matchLabel(match, comparison)}
                  </li>
                ))}
              </ol>
            </div>
          ) : (
            <EmptyChart message="No hay enfrentamientos directos disponibles en las temporadas sincronizadas." />
          )}
        </ChartCard>
      </div>
    </section>
  )
}

import type { Comparison, TeamStatistics } from '../api/types'
import type { EChartsCoreOption } from './echarts'

const TEAM_COLORS = ['#16a34a', '#2563eb']

function clamp(value: number, minimum = 0, maximum = 100): number {
  return Math.min(Math.max(value, minimum), maximum)
}

function ratio(numerator: number, denominator: number): number {
  return denominator > 0 ? numerator / denominator : 0
}

export function formToPoints(form: TeamStatistics['recent_form']): number[] {
  // Usamos la puntuación tradicional del fútbol para dibujar la evolución:
  // victoria = 3, empate = 1 y derrota = 0.
  return form.map((result) => (result === 'W' ? 3 : result === 'D' ? 1 : 0))
}

export function radarValues(statistics: TeamStatistics): number[] {
  // Un radar necesita que todos sus ejes compartan la misma escala. Convertimos
  // cada métrica a 0–100 y limitamos valores extremos para poder compararlas.
  const formPoints = formToPoints(statistics.recent_form)
  const possibleFormPoints = formPoints.length * 3
  return [
    clamp(statistics.win_percentage ?? ratio(statistics.wins, statistics.matches_played) * 100),
    clamp(ratio(statistics.points_per_game ?? 0, 3) * 100),
    clamp(ratio(statistics.goals_for_per_match, 3) * 100),
    clamp(100 - ratio(statistics.goals_against_per_match, 3) * 100),
    clamp(ratio(statistics.clean_sheets ?? 0, statistics.matches_played) * 100),
    clamp(ratio(formPoints.reduce((total, value) => total + value, 0), possibleFormPoints) * 100),
  ].map((value) => Math.round(value * 10) / 10)
}

export function hasRadarData(comparison: Comparison): boolean {
  return (
    comparison.team_1.statistics.matches_played > 0 &&
    comparison.team_2.statistics.matches_played > 0
  )
}

export function buildRadarOption(comparison: Comparison): EChartsCoreOption {
  // Las funciones build* sólo convierten el contrato de la API al objeto de
  // configuración de ECharts; no consultan datos ni modifican el estado React.
  return {
    aria: { enabled: true, decal: { show: true } },
    color: TEAM_COLORS,
    tooltip: { trigger: 'item' },
    legend: {
      bottom: 0,
      data: [comparison.team_1.name, comparison.team_2.name],
      textStyle: { color: '#475569' },
    },
    radar: {
      center: ['50%', '45%'],
      radius: '62%',
      indicator: [
        { name: 'Victorias', max: 100 },
        { name: 'Puntos', max: 100 },
        { name: 'Ataque', max: 100 },
        { name: 'Defensa', max: 100 },
        { name: 'Vallas invictas', max: 100 },
        { name: 'Forma', max: 100 },
      ],
      axisName: { color: '#475569', fontSize: 11 },
      splitArea: { areaStyle: { color: ['#f8fafc', '#f1f5f9'] } },
      splitLine: { lineStyle: { color: '#cbd5e1' } },
    },
    series: [
      {
        type: 'radar',
        symbolSize: 6,
        data: [
          { name: comparison.team_1.name, value: radarValues(comparison.team_1.statistics) },
          { name: comparison.team_2.name, value: radarValues(comparison.team_2.statistics) },
        ],
      },
    ],
  }
}

export function buildFormOption(comparison: Comparison): EChartsCoreOption {
  const team1Form = formToPoints(comparison.team_1.statistics.recent_form)
  const team2Form = formToPoints(comparison.team_2.statistics.recent_form)
  const maximumLength = Math.max(team1Form.length, team2Form.length)
  return {
    aria: { enabled: true, decal: { show: true } },
    color: TEAM_COLORS,
    tooltip: { trigger: 'axis' },
    legend: {
      bottom: 0,
      data: [comparison.team_1.name, comparison.team_2.name],
      textStyle: { color: '#475569' },
    },
    grid: { left: 40, right: 20, top: 25, bottom: 55 },
    xAxis: {
      type: 'category',
      data: Array.from({ length: maximumLength }, (_, index) => `Partido ${index + 1}`),
      axisLabel: { color: '#64748b' },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 3,
      interval: 1,
      axisLabel: {
        color: '#64748b',
        formatter: (value: number) => ({ 0: 'D', 1: 'E', 3: 'V' })[value] ?? '',
      },
    },
    series: [
      { name: comparison.team_1.name, type: 'line', data: team1Form, smooth: true },
      { name: comparison.team_2.name, type: 'line', data: team2Form, smooth: true },
    ],
  }
}

export function buildHeadToHeadOption(comparison: Comparison): EChartsCoreOption {
  const history = comparison.head_to_head
  return {
    aria: { enabled: true, decal: { show: true } },
    color: [TEAM_COLORS[0], '#d97706', TEAM_COLORS[1]],
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 110, right: 25, top: 15, bottom: 25 },
    xAxis: { type: 'value', minInterval: 1, axisLabel: { color: '#64748b' } },
    yAxis: {
      type: 'category',
      data: [comparison.team_1.short_name, 'Empates', comparison.team_2.short_name],
      axisLabel: { color: '#475569' },
    },
    series: [
      {
        type: 'bar',
        barMaxWidth: 30,
        data: [
          history?.team_1_wins ?? 0,
          history?.draws ?? 0,
          history?.team_2_wins ?? 0,
        ].map((value, index) => ({ value, itemStyle: { color: [TEAM_COLORS[0], '#d97706', TEAM_COLORS[1]][index] } })),
      },
    ],
  }
}

import { useEffect, useRef } from 'react'
import type { ECharts } from 'echarts/core'

import { init, type EChartsCoreOption } from '../charts/echarts'

type EChartProps = {
  option: EChartsCoreOption
  ariaLabel: string
  className?: string
}

export function EChart({ option, ariaLabel, className = 'h-80' }: EChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<ECharts | null>(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    // SVG conserva texto nítido en pantallas de distinta densidad y funciona
    // bien para la cantidad pequeña de datos del comparador.
    const chart = init(container, undefined, { renderer: 'svg' })
    chartRef.current = chart
    const observer = new ResizeObserver(() => chart.resize())
    observer.observe(container)

    return () => {
      observer.disconnect()
      chart.dispose()
      chartRef.current = null
    }
  }, [])

  useEffect(() => {
    // notMerge reemplaza la comparación anterior para no conservar series de
    // equipos que ya no están seleccionados.
    const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    const accessibleOption = reduceMotion ? { ...option, animation: false } : option
    chartRef.current?.setOption(accessibleOption, { notMerge: true })
  }, [option])

  return (
    <div
      aria-label={ariaLabel}
      className={`w-full ${className}`}
      ref={containerRef}
      role="img"
    />
  )
}

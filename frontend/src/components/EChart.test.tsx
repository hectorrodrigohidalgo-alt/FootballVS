import { render } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { EChart } from './EChart'

const chartMocks = vi.hoisted(() => ({
  dispose: vi.fn(),
  resize: vi.fn(),
  setOption: vi.fn(),
  init: vi.fn(),
}))

vi.mock('../charts/echarts', () => ({
  init: chartMocks.init,
}))

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('puente React para ECharts', () => {
  it('inicializa, actualiza y libera la instancia', () => {
    chartMocks.init.mockReturnValue({
      dispose: chartMocks.dispose,
      resize: chartMocks.resize,
      setOption: chartMocks.setOption,
    })
    const firstOption = { series: [] }
    const secondOption = { series: [{ type: 'bar', data: [1] }] }
    const view = render(<EChart ariaLabel="Gráfico de prueba" option={firstOption} />)

    expect(chartMocks.init).toHaveBeenCalledOnce()
    expect(chartMocks.setOption).toHaveBeenCalledWith(firstOption, { notMerge: true })
    expect(view.getByRole('img', { name: 'Gráfico de prueba' })).toBeInTheDocument()

    view.rerender(<EChart ariaLabel="Gráfico de prueba" option={secondOption} />)
    expect(chartMocks.setOption).toHaveBeenLastCalledWith(secondOption, { notMerge: true })

    view.unmount()
    expect(chartMocks.dispose).toHaveBeenCalledOnce()
  })

  it('desactiva la animación cuando el sistema solicita movimiento reducido', () => {
    vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: true })))
    chartMocks.init.mockReturnValue({
      dispose: chartMocks.dispose,
      resize: chartMocks.resize,
      setOption: chartMocks.setOption,
    })
    const option = { series: [{ type: 'line', data: [1, 3, 0] }] }

    render(<EChart ariaLabel="Forma reciente" option={option} />)

    expect(chartMocks.setOption).toHaveBeenCalledWith(
      { ...option, animation: false },
      { notMerge: true },
    )
  })
})

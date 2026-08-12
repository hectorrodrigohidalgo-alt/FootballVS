import { render } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

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
})

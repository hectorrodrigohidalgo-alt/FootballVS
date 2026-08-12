import { BarChart, LineChart, RadarChart } from 'echarts/charts'
import {
  AriaComponent,
  GridComponent,
  LegendComponent,
  RadarComponent,
  TooltipComponent,
} from 'echarts/components'
import { use as registerEChartsModules } from 'echarts/core'
import { SVGRenderer } from 'echarts/renderers'

// Registrar sólo los gráficos, componentes y renderer utilizados permite que
// Vite excluya del bundle el resto de la biblioteca Apache ECharts.
registerEChartsModules([
  BarChart,
  LineChart,
  RadarChart,
  AriaComponent,
  GridComponent,
  LegendComponent,
  RadarComponent,
  TooltipComponent,
  SVGRenderer,
])

export { init } from 'echarts/core'
export type { EChartsCoreOption } from 'echarts/core'

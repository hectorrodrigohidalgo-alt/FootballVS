import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

class ResizeObserverMock implements ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// jsdom no calcula cambios de layout; este sustituto conserva el mismo
// contrato que usa EChart sin simular medidas inexistentes.
globalThis.ResizeObserver = ResizeObserverMock

// Cada prueba comienza con un DOM vacío para evitar resultados dependientes
// del orden de ejecución.
afterEach(() => {
  cleanup()
})

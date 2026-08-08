import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Cada prueba comienza con un DOM vacío para evitar resultados dependientes
// del orden de ejecución.
afterEach(() => {
  cleanup()
})

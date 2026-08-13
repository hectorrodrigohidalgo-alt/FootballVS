import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it } from 'vitest'
import { renderWithQueryClient } from '../test/render'
import { EloInfoDialog } from './EloInfoDialog'

function Harness() {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button onClick={() => setOpen(true)} type="button">Información Elo</button>
      <EloInfoDialog isOpen={open} onClose={() => setOpen(false)} />
    </>
  )
}

describe('EloInfoDialog', () => {
  it('se abre a petición, explica el modelo y vuelve al disparador al cerrar', async () => {
    const user = userEvent.setup()
    renderWithQueryClient(<Harness />)
    const opener = screen.getByRole('button', { name: 'Información Elo' })

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    await user.click(opener)

    expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true')
    expect(screen.getByRole('heading', { name: '¿Cómo funciona el rating Elo?' })).toBeVisible()
    expect(screen.getByText(/Se probaron 180 configuraciones/)).toBeVisible()
    expect(screen.getByRole('button', { name: 'Cerrar información de Elo' })).toHaveFocus()

    await user.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(opener).toHaveFocus()
  })
})

import { expect, test } from '@playwright/test'

test('compara dos equipos y explica el rating Elo', async ({ page }) => {
  await page.goto('/')

  await expect(
    page.getByRole('heading', { name: 'Compara equipos. Entiende el partido.' }),
  ).toBeVisible()

  const competition = page.getByLabel('Competición')
  await competition.selectOption({ index: 1 })

  const team1 = page.getByLabel('Equipo 1', { exact: true })
  const team2 = page.getByLabel('Equipo 2', { exact: true })
  await expect(team1.locator('option')).toHaveCount(5)
  await team1.selectOption({ index: 1 })
  await team2.selectOption({ index: 2 })
  await page.getByRole('radio', { name: 'Equipo 1 local' }).check()

  const compareButton = page.getByRole('button', { name: 'Comparar equipos' })
  await expect(compareButton).toBeEnabled()
  await compareButton.click()

  await expect(page.getByText(/Comparación lista:/)).toBeVisible()
  await expect(page.getByText('Dashboard', { exact: true })).toBeVisible()
  await expect(page.getByText('Goles esperados')).toBeVisible()
  await expect(page.getByText('Marcadores más probables')).toBeVisible()
  await expect(page.getByText(/^Elo \d+$/).first()).toBeVisible()

  await page.getByRole('button', { name: '¿Cómo funciona?' }).first().click()
  const dialog = page.getByRole('dialog', { name: '¿Cómo funciona el rating Elo?' })
  await expect(dialog).toBeVisible()
  await expect(dialog.getByText(/Se probaron 180 configuraciones/)).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(dialog).toBeHidden()
})

test('impide seleccionar el mismo equipo', async ({ page }) => {
  await page.goto('/')
  await page.getByLabel('Competición').selectOption({ index: 1 })

  const team1 = page.getByLabel('Equipo 1', { exact: true })
  const team2 = page.getByLabel('Equipo 2', { exact: true })
  await expect(team1.locator('option')).toHaveCount(5)
  await team1.selectOption({ index: 1 })
  const selectedTeam = await team1.inputValue()

  await expect(team2.locator(`option[value="${selectedTeam}"]`)).toBeDisabled()
  await expect(page.getByRole('button', { name: 'Comparar equipos' })).toBeDisabled()
})

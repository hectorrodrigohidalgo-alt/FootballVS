import { expect, type Page } from '@playwright/test'

export async function createComparison(page: Page) {
  await page.goto('/')
  await page.getByLabel('Competición').selectOption({ index: 1 })
  const team1 = page.getByLabel('Equipo 1', { exact: true })
  const team2 = page.getByLabel('Equipo 2', { exact: true })
  await expect(team1.locator('option')).toHaveCount(5)
  await team1.selectOption({ index: 1 })
  await team2.selectOption({ index: 2 })
  await page.getByRole('radio', { name: 'Equipo 1 local' }).check()
  await page.getByRole('button', { name: 'Comparar equipos' }).click()
  await expect(page.getByText(/Comparación lista:/)).toBeVisible()
}


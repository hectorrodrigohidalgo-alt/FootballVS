import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page, type TestInfo } from '@playwright/test'
import { createComparison } from './helpers'

const wcagTags = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']

async function expectNoSeriousViolations(page: Page, testInfo: TestInfo) {
  const results = await new AxeBuilder({ page }).withTags(wcagTags).analyze()
  await testInfo.attach('axe-results', {
    body: JSON.stringify(results.violations, null, 2),
    contentType: 'application/json',
  })
  const blocking = results.violations.filter(
    (violation) => violation.impact === 'serious' || violation.impact === 'critical',
  )
  expect(blocking, JSON.stringify(blocking, null, 2)).toEqual([])
}

test('no presenta infracciones graves en inicio, dashboard y diálogo', async ({ page }, testInfo) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Compara equipos. Entiende el partido.' })).toBeVisible()
  await expectNoSeriousViolations(page, testInfo)

  await createComparison(page)
  await expectNoSeriousViolations(page, testInfo)

  await page.getByRole('button', { name: '¿Cómo funciona?' }).first().click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await expectNoSeriousViolations(page, testInfo)
})

test('mantiene navegación y foco mediante teclado', async ({ page }) => {
  await page.goto('/')
  await page.keyboard.press('Tab')
  const skipLink = page.getByRole('link', { name: 'Saltar al contenido principal' })
  await expect(skipLink).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(page.locator('#main-content')).toBeFocused()

  await createComparison(page)
  const opener = page.getByRole('button', { name: '¿Cómo funciona?' }).first()
  await opener.focus()
  await page.keyboard.press('Enter')
  const closeButton = page.getByRole('button', { name: 'Cerrar información de Elo' })
  await expect(closeButton).toBeFocused()
  await page.keyboard.press('Shift+Tab')
  await expect(page.getByLabel('Fórmula para actualizar el rating Elo')).toBeFocused()
  await page.keyboard.press('Tab')
  await expect(closeButton).toBeFocused()
  await page.keyboard.press('Escape')
  await expect(opener).toBeFocused()
})

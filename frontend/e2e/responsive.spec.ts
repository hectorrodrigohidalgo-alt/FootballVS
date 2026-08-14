import { expect, test } from '@playwright/test'
import { createComparison } from './helpers'

for (const viewport of [
  { name: '320px', width: 320, height: 720 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1280, height: 900 },
]) {
  test(`evita desbordamiento horizontal en ${viewport.name}`, async ({ page }) => {
    await page.setViewportSize(viewport)
    await createComparison(page)
    const dimensions = await page.evaluate(() => ({
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
    }))
    expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth)
    await expect(page.getByText('Marcadores más probables')).toBeVisible()
  })
}

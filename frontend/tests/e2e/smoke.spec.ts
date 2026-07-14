import { expect, test } from '@playwright/test'

test('two-pane layout shell loads', async ({ page }) => {
  await page.goto('/')

  await expect(page).toHaveTitle('PDF Eater')
  await expect(page.getByRole('complementary', { name: 'Uploaded documents' })).toBeVisible()
  await expect(page.getByRole('region', { name: 'Chat' })).toBeVisible()
})

import { defineConfig, devices } from '@playwright/test'

const DEV_SERVER_URL = 'http://localhost:5173'

export default defineConfig({
  testDir: './tests/e2e',
  use: {
    baseURL: DEV_SERVER_URL,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: DEV_SERVER_URL,
    reuseExistingServer: true,
  },
})

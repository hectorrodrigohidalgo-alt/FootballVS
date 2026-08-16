import { defineConfig, devices } from '@playwright/test'

const apiCommand =
  process.platform === 'win32'
    ? '.venv\\Scripts\\activate.bat && func start --port 7171 --cors http://localhost:5273'
    : '. .venv/bin/activate && func start --port 7171 --cors http://localhost:5273'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI
    ? [['github'], ['html', { open: 'never' }]]
    : [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: 'http://localhost:5273',
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium-desktop',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'chromium-mobile',
      use: { ...devices['Pixel 5'] },
    },
  ],
  webServer: [
    {
      command: apiCommand,
      cwd: '../api',
      env: {
        APP_DATA_SOURCE: 'mock',
        FUNCTIONS_WORKER_RUNTIME: 'python',
      },
      reuseExistingServer: false,
      stderr: 'pipe',
      stdout: 'pipe',
      timeout: 120_000,
      url: 'http://localhost:7171/api/v1/health',
    },
    {
      command: 'npm run dev -- --host localhost --port 5273',
      cwd: '.',
      env: {
        VITE_API_BASE_URL: 'http://localhost:7171/api/v1',
      },
      reuseExistingServer: false,
      stderr: 'pipe',
      stdout: 'pipe',
      timeout: 120_000,
      url: 'http://localhost:5273',
    },
  ],
})

import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests/dashboard',
  use: {
    baseURL: 'http://localhost:5173',
    screenshot: 'on',
    video: 'retain-on-failure',
  },
});

import { test, expect } from '@playwright/test';

test('dashboard loads, no console errors', async ({ page }) => {
  const errs: string[] = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto('/');
  await page.waitForSelector('[data-testid="transaction-feed"]', { timeout: 5000 });
  expect(errs).toHaveLength(0);
  await page.screenshot({ path: 'screenshots/01-loaded.png' });
});

test('suspicious transaction → red fraud row', async ({ page }) => {
  await page.goto('/');
  await page.fill('[data-testid="amount-input"]', '1200');
  await page.fill('[data-testid="v1-input"]', '-4.5');
  await page.fill('[data-testid="v2-input"]', '-3.0');
  await page.click('[data-testid="submit-btn"]');
  await expect(page.locator('[data-testid="fraud-row"]').first()).toBeVisible({ timeout: 3000 });
  await page.screenshot({ path: 'screenshots/02-fraud.png' });
});

test('normal transaction → green row', async ({ page }) => {
  await page.goto('/');
  await page.fill('[data-testid="amount-input"]', '42');
  await page.click('[data-testid="submit-btn"]');
  await expect(page.locator('[data-testid="legit-row"]').first()).toBeVisible({ timeout: 3000 });
  await page.screenshot({ path: 'screenshots/03-legit.png' });
});

test('fraud row click → SHAP drawer with 5 bars', async ({ page }) => {
  await page.goto('/');
  await page.fill('[data-testid="amount-input"]', '1200');
  await page.fill('[data-testid="v1-input"]', '-4.5');
  await page.click('[data-testid="submit-btn"]');
  await page.locator('[data-testid="fraud-row"]').first().click();
  await expect(page.locator('[data-testid="shap-drawer"]')).toBeVisible({ timeout: 2000 });
  await expect(page.locator('[data-testid="shap-bar"]')).toHaveCount(5);
  await page.screenshot({ path: 'screenshots/04-shap.png' });
});

test('stats bar visible', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('[data-testid="stats-bar"]')).toBeVisible();
});

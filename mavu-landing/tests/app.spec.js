import { test, expect } from '@playwright/test';

test.describe('MAVU Landing Page', () => {

  test.describe('Home Page', () => {
    test('should load home page correctly', async ({ page }) => {
      await page.goto('/');

      // Check page title exists
      await expect(page).toHaveTitle(/MAVU/i);

      // Check header is visible
      await expect(page.locator('header')).toBeVisible();

      // Check logo is present
      await expect(page.locator('header a[href="/"]')).toBeVisible();

      // Check hero section content
      await expect(page.locator('section').first()).toBeVisible();
    });

    test('should have working navigation links', async ({ page }) => {
      await page.goto('/');

      // Check navigation links exist
      const nav = page.locator('nav');
      await expect(nav.first()).toBeVisible();
    });

    test('should scroll to sections on anchor click', async ({ page }) => {
      await page.goto('/');

      // Click on features link (desktop)
      const featuresLink = page.locator('a[href="/#features"]').first();
      if (await featuresLink.isVisible()) {
        await featuresLink.click();

        // Wait for scroll
        await page.waitForTimeout(500);

        // Check features section is in view
        const featuresSection = page.locator('#features');
        await expect(featuresSection).toBeVisible();
      }
    });

    test('should display all main sections', async ({ page }) => {
      await page.goto('/');

      // Check all sections exist
      await expect(page.locator('#features')).toBeVisible();
      await expect(page.locator('#screenshots')).toBeVisible();
      await expect(page.locator('#safety')).toBeVisible();
      await expect(page.locator('#pricing')).toBeVisible();
    });

    test('should have working CTA buttons', async ({ page }) => {
      await page.goto('/');

      // Check buy promo button exists and links to purchase
      const buyButton = page.locator('a[href="/purchase"]').first();
      await expect(buyButton).toBeVisible();
    });
  });

  test.describe('Language Switcher', () => {
    test('should switch language', async ({ page }) => {
      await page.goto('/');

      // Find language switcher
      const langSwitcher = page.locator('button').filter({ hasText: /Русский|English|O'zbek/i }).first();

      if (await langSwitcher.isVisible()) {
        await langSwitcher.click();

        // Check dropdown appears
        const dropdown = page.locator('[class*="absolute"]').filter({ hasText: /English/i });
        await expect(dropdown.first()).toBeVisible();
      }
    });
  });

  test.describe('Purchase Page', () => {
    test('should load purchase page', async ({ page }) => {
      await page.goto('/purchase');

      // Check page loads
      await expect(page.locator('h1')).toBeVisible();

      // Check Payme payment method is shown (use first match)
      await expect(page.getByText('Payme').first()).toBeVisible();

      // Check pay button exists
      const payButton = page.locator('button').filter({ hasText: /Оплатить|Pay|To'lash/i });
      await expect(payButton).toBeVisible();
    });

    test('should show order summary', async ({ page }) => {
      await page.goto('/purchase');

      // Check price is displayed
      await expect(page.getByText('$11')).toBeVisible();
    });
  });

  test.describe('Contacts Page', () => {
    test('should load contacts page', async ({ page }) => {
      await page.goto('/contacts');

      // Check page loads with title
      await expect(page.locator('h1')).toBeVisible();

      // Check email is displayed
      await expect(page.getByText('support@mavu.app')).toBeVisible();

      // Check telegram support section exists
      await expect(page.locator('a[href*="t.me"]').first()).toBeVisible();
    });
  });

  test.describe('Privacy Page', () => {
    test('should load privacy page', async ({ page }) => {
      await page.goto('/privacy');

      // Check page loads
      await expect(page.locator('h1')).toBeVisible();

      // Check content sections exist
      await expect(page.locator('section')).toBeVisible();
    });
  });

  test.describe('Offer Page', () => {
    test('should load offer page', async ({ page }) => {
      await page.goto('/offer');

      // Check page loads
      await expect(page.locator('h1')).toBeVisible();
    });
  });

  test.describe('404 Page', () => {
    test('should show 404 for unknown routes', async ({ page }) => {
      await page.goto('/unknown-page-xyz');

      // Check 404 content
      await expect(page.getByText('404')).toBeVisible();

      // Check back home link exists (use first match)
      await expect(page.locator('a[href="/"]').first()).toBeVisible();
    });
  });

  test.describe('Footer', () => {
    test('should display footer with links', async ({ page }) => {
      await page.goto('/');

      // Scroll to footer
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await page.waitForTimeout(500);

      // Check footer exists
      await expect(page.locator('footer')).toBeVisible();

      // Check footer links
      await expect(page.locator('footer a[href="/privacy"]')).toBeVisible();
      await expect(page.locator('footer a[href="/offer"]')).toBeVisible();
    });
  });

  test.describe('Responsive Design', () => {
    test('should work on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/');

      // Check page loads
      await expect(page.locator('header')).toBeVisible();

      // Check mobile menu button exists
      const menuButton = page.locator('button[aria-label="Toggle menu"]');
      await expect(menuButton).toBeVisible();

      // Click mobile menu
      await menuButton.click();
      await page.waitForTimeout(300);

      // Check mobile nav items are visible
      const mobileNavLinks = page.locator('a[href="/#features"]');
      await expect(mobileNavLinks.last()).toBeVisible();
    });

    test('should work on tablet viewport', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.goto('/');

      await expect(page.locator('header')).toBeVisible();
      await expect(page.locator('section').first()).toBeVisible();
    });
  });

  test.describe('Performance', () => {
    test('should load page within acceptable time', async ({ page }) => {
      const startTime = Date.now();
      await page.goto('/');
      const loadTime = Date.now() - startTime;

      // Page should load within 5 seconds
      expect(loadTime).toBeLessThan(5000);
    });
  });

  test.describe('SEO', () => {
    test('should have proper meta tags', async ({ page }) => {
      await page.goto('/');

      // Check meta description
      const metaDescription = page.locator('meta[name="description"]');
      await expect(metaDescription).toHaveAttribute('content', /MAVU/);

      // Check Open Graph tags
      const ogTitle = page.locator('meta[property="og:title"]');
      await expect(ogTitle).toHaveAttribute('content', /MAVU/);

      // Check Twitter card
      const twitterCard = page.locator('meta[name="twitter:card"]');
      await expect(twitterCard).toHaveAttribute('content', 'summary_large_image');
    });

    test('should have favicon', async ({ page }) => {
      await page.goto('/');

      const favicon = page.locator('link[rel="icon"]').first();
      await expect(favicon).toHaveAttribute('href', /favicon/);
    });
  });

});

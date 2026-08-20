import { expect, test, type Page } from "@playwright/test";

interface CaptchaCredential {
  id: string;
  answer: string;
}

const captchaImage =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=";

async function installCaptchaPool(page: Page): Promise<() => CaptchaCredential> {
  const credentials = JSON.parse(process.env.E2E_CAPTCHAS || "[]") as CaptchaCredential[];
  if (credentials.length < 6) {
    throw new Error("E2E_CAPTCHAS must contain at least six prepared credentials");
  }
  let current = credentials[0];
  await page.route("**/api/captcha", async (route) => {
    const credential = credentials.shift();
    if (!credential) throw new Error("The E2E CAPTCHA pool is exhausted");
    current = credential;
    await route.fulfill({
      contentType: "application/json",
      json: { id: credential.id, image_data: captchaImage, expires_in: 300 },
    });
  });
  return () => current;
}

test("registration, authentication, comments, reply, image and search", async ({ page }) => {
  const captcha = await installCaptchaPool(page);
  const suffix = Date.now();
  const username = `E2EUser${suffix}`;
  const email = `e2e-${suffix}@example.test`;
  const password = "G7!vQ2#nL9@r";
  const rootText = `E2E searchable root ${suffix}`;
  const replyText = `E2E reply ${suffix}`;

  await page.goto("/");
  await page.getByRole("button", { name: "Register" }).click();
  const authDialog = page.getByRole("dialog");
  await authDialog.getByLabel("Username", { exact: true }).fill(username);
  await authDialog.getByLabel("Email", { exact: true }).fill(email);
  await authDialog.getByLabel("Password", { exact: true }).fill(password);
  await authDialog.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByText(username, { exact: true }).first()).toBeVisible();

  await page.getByRole("button", { name: "Sign out" }).click();
  await page.getByRole("button", { name: "Sign in", exact: true }).first().click();
  await authDialog.getByLabel("Username or email").fill(email);
  await authDialog.getByLabel("Password", { exact: true }).fill(password);
  await authDialog.locator("form").getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByText(username, { exact: true }).first()).toBeVisible();

  await page.locator("textarea").fill(rootText);
  await page.getByLabel("CAPTCHA", { exact: true }).fill(captcha().answer);
  await page.locator('input[type="file"]').last().setInputFiles({
    name: "pixel.png",
    mimeType: "image/png",
    buffer: Buffer.from(
      "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
      "base64",
    ),
  });
  await page.getByRole("button", { name: "Send comment" }).click();
  const root = page.locator("article.comment").filter({ hasText: rootText });
  await expect(root).toBeVisible();
  await expect(root.getByRole("img", { name: "pixel.png" })).toBeVisible();

  await root.getByRole("button", { name: "Reply" }).click();
  const replyForm = root.locator("form.inline-reply-form");
  await expect(replyForm.getByRole("heading", { name: `Reply to ${username}` })).toBeVisible();
  await expect(replyForm.locator("textarea")).toBeFocused();
  await replyForm.locator("textarea").fill(replyText);
  await replyForm.getByLabel("CAPTCHA", { exact: true }).fill(captcha().answer);
  await replyForm.getByRole("button", { name: "Send comment" }).click();
  await expect(root.getByText(replyText, { exact: true })).toBeVisible();

  await page.getByPlaceholder("Search comments and authors…").fill(username);
  await page.getByText("Filters", { exact: true }).click();
  await page.getByLabel("Author", { exact: true }).fill(username);
  await page.locator(".search-filters select").first().selectOption("date");
  const searchResult = page.locator(".search-hit").filter({ hasText: username });
  await expect
    .poll(
      async () => {
        await page.getByRole("button", { name: "Search" }).click();
        await page.waitForTimeout(500);
        return searchResult.count();
      },
      { timeout: 15_000 },
    )
    .toBeGreaterThan(0);
});

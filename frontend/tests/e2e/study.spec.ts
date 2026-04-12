import { expect, test } from "@playwright/test";

const MOCK_BACKEND_URL = "http://127.0.0.1:8000";

test.beforeEach(async () => {
  await fetch(`${MOCK_BACKEND_URL}/__reset`, { method: "POST" });
});

async function signIn(page) {
  await page.goto("/study");
  await expect(page).toHaveURL(/\/login$/);

  await page.getByLabel("Логин").fill("shamil.isaev");
  await page.getByLabel("Пароль").fill("12345678");
  await page.getByRole("button", { name: "Войти" }).click();

  await expect(page).toHaveURL(/\/today$/);
}

async function openStudy(page) {
  await page.goto("/study");
  await expect(page.getByRole("button", { name: "Python" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Network" })).toBeVisible();
}

test("auth flow and track tabs keep Python and Network plans separate", async ({ page }) => {
  await signIn(page);
  await openStudy(page);

  await page.getByRole("button", { name: "+ Новый план" }).click();
  await page.getByLabel("Название плана · Python").fill("Python sprint");
  await page.getByLabel("Описание", { exact: true }).fill("Алгоритмы и синтаксис");
  await page.getByRole("button", { name: "Создать" }).click();
  await expect(page.getByRole("button", { name: "Python sprint", exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Network" }).click();
  await page.getByRole("button", { name: "+ Новый план" }).click();
  await page.getByLabel("Название плана · Network").fill("Network sprint");
  await page.getByLabel("Описание", { exact: true }).fill("Протоколы и конфиги");
  await page.getByRole("button", { name: "Создать" }).click();
  await expect(page.getByRole("button", { name: "Network sprint", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Python sprint", exact: true })).toHaveCount(0);

  await page.getByRole("button", { name: "Python" }).click();
  await expect(page.getByRole("button", { name: "Python sprint", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Network sprint", exact: true })).toHaveCount(0);
});

test("study timer records progress, restarts, and closes a topic", async ({ page }) => {
  await signIn(page);
  await openStudy(page);

  await page.getByRole("button", { name: "+ Новый план" }).click();
  await page.getByLabel("Название плана · Python").fill("Timer plan");
  await page.getByLabel("Описание", { exact: true }).fill("Таймер и прогресс");
  await page.getByRole("button", { name: "Создать" }).click();

  await page.getByRole("button", { name: "+ Тема" }).click();
  await page.getByLabel("Название темы").fill("BGP basics");
  await page.getByLabel("Описание", { exact: true }).fill("Маршрутизация и соседства");
  await page.getByRole("button", { name: "Добавить" }).click();
  await expect(page.getByRole("button", { name: "Старт" })).toBeVisible();
  await page.getByRole("button", { name: "Старт", exact: true }).click();
  await expect(page.getByRole("button", { name: "Стоп" })).toBeVisible();

  await expect(page.getByRole("spinbutton")).toBeVisible();
  await page.getByRole("spinbutton").fill("50");
  await page.getByRole("button", { name: "Остановить" }).click();

  await expect(page.getByText("История сессий · 1 записей")).toBeVisible();
  await expect(page.locator("span.page-sub").filter({ hasText: "50%" }).first()).toBeVisible();
  await expect(page.getByRole("checkbox", { name: "Тема BGP basics завершена" })).not.toBeChecked();

  await page.getByRole("button", { name: "Старт", exact: true }).click();
  await expect(page.getByRole("button", { name: "Стоп" })).toBeVisible();
  await expect(page.getByRole("spinbutton")).toBeVisible();
  await page.getByRole("spinbutton").fill("100");
  await page.getByRole("button", { name: "Остановить" }).click();

  await expect(page.getByText("История сессий · 2 записей")).toBeVisible();
  await expect(page.getByRole("checkbox", { name: "Тема BGP basics завершена" })).toBeChecked();
  await expect(page.locator("span.page-sub").filter({ hasText: "100%" }).first()).toBeVisible();
});

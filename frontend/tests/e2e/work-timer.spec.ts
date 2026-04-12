import { expect, test } from "@playwright/test";

const MOCK_BACKEND_URL = "http://127.0.0.1:8000";

test.beforeEach(async () => {
  await fetch(`${MOCK_BACKEND_URL}/__reset`, { method: "POST" });
});

async function signIn(page) {
  await page.goto("/work-timer");
  await expect(page).toHaveURL(/\/login$/);

  await page.getByLabel("Логин").fill("shamil.isaev");
  await page.getByLabel("Пароль").fill("12345678");
  await page.getByRole("button", { name: "Войти" }).click();

  await expect(page).toHaveURL(/\/today$/);
}

test("work timer tracks start pause resume and stop", async ({ page }) => {
  await signIn(page);
  await page.goto("/work-timer");

  await page.getByLabel("Название").fill("Network incident");
  await page.getByLabel("Описание").fill("Разобрать проблему с доступностью");
  await page.getByLabel("Номер задачи").fill("INC-42");
  await page.getByLabel("Ссылка").fill("https://example.com/tickets/INC-42");
  await page.getByLabel("Теги").fill("network, ops");
  await page.getByRole("button", { name: "Создать задачу" }).click();

  await expect(page.getByText("Network incident")).toBeVisible();
  await page.getByRole("button", { name: "Старт" }).first().click();
  await expect(page.getByRole("button", { name: "Пауза" })).toBeVisible();
  await expect(page.getByText("Таймер активен")).toBeVisible();

  await page.getByRole("button", { name: "Пауза" }).click();
  await expect(page.getByRole("button", { name: "Продолжить" })).toBeVisible();

  await page.getByRole("button", { name: "Продолжить" }).click();
  await expect(page.getByRole("button", { name: "Пауза" })).toBeVisible();

  await page.getByRole("button", { name: "Стоп" }).click();
  await expect(page.getByRole("button", { name: "Старт" })).toBeVisible();
  await expect(page.getByText("Таймер активен")).toHaveCount(0);
});

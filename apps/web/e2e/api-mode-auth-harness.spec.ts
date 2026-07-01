import { expect, test } from "@playwright/test";
import {
  API_MODE_PROJECTS,
  API_MODE_USERS,
  apiModeSession,
  expectNoPersistentApiAuth,
  installApiModeHarness,
  loginViaApiMode,
} from "./api-mode-auth-harness";

test("API-mode harness restores a real session without persistent auth storage", async ({ page }) => {
  const harness = await installApiModeHarness(page, apiModeSession(API_MODE_USERS.teacherA));

  await page.goto("/");

  await expect(page.getByText("项目概览")).toBeVisible();
  await expect(page.getByRole("heading", { name: API_MODE_PROJECTS[0].name }).first()).toBeVisible();
  await expect(page.getByText(API_MODE_PROJECTS[1].name)).toHaveCount(0);
  await expectNoPersistentApiAuth(page);

  expect(harness.requests.some((request) => request.pathname === "/auth/me")).toBe(true);
  expect(harness.requests.every((request) => request.authorization === null)).toBe(true);
});

test("API-mode harness supports login and logout through backend auth endpoints", async ({ page }) => {
  const harness = await installApiModeHarness(page, null);

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "登录工作台" })).toBeVisible();

  await loginViaApiMode(page, API_MODE_USERS.teacherA);
  await expect(page.getByText("项目概览")).toBeVisible();
  await expect(page.getByRole("heading", { name: API_MODE_PROJECTS[0].name }).first()).toBeVisible();

  await page.getByRole("button", { name: /教师 A/ }).click();
  await page.getByRole("menuitem", { name: "退出登录" }).click();
  await expect(page.getByRole("heading", { name: "登录工作台" })).toBeVisible();
  await expectNoPersistentApiAuth(page);

  expect(harness.requests.some((request) => request.pathname === "/auth/login")).toBe(true);
  expect(harness.requests.some((request) => request.pathname === "/auth/logout")).toBe(true);
  const logout = harness.requests.find((request) => request.pathname === "/auth/logout");
  expect(logout?.csrfToken).toBeTruthy();
});

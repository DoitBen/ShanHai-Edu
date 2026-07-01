import { expect, test } from "@playwright/test";
import {
  API_MODE_PROJECTS,
  API_MODE_USERS,
  apiModeSession,
  installApiModeHarness,
} from "./api-mode-auth-harness";

test("unauthenticated API-mode users stay on the real login screen", async ({ page }) => {
  await installApiModeHarness(page, null);

  await page.goto("/");

  await expect(page.getByRole("heading", { name: "登录工作台" })).toBeVisible();
  await expect(page.getByLabel("邮箱")).toBeVisible();
  await expect(page.getByLabel("用户名")).toHaveCount(0);
});

test("teacher sessions only list owned projects and hide admin entry points", async ({ page }) => {
  await installApiModeHarness(page, apiModeSession(API_MODE_USERS.teacherA));

  await page.goto("/");

  await expect(page.getByText("项目概览")).toBeVisible();
  await expect(page.getByRole("heading", { name: API_MODE_PROJECTS[0].name }).first()).toBeVisible();
  await expect(page.getByText(API_MODE_PROJECTS[1].name)).toHaveCount(0);
  await expect(page.getByRole("button", { name: "配置中心" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "规则控制面" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "媒体生成工作台" })).toHaveCount(0);
});

test("teacher project-id guessing returns 404 and client Authorization cannot bypass the session", async ({ page }) => {
  await installApiModeHarness(page, apiModeSession(API_MODE_USERS.teacherA));
  await page.goto("/");
  await expect(page.getByText("项目概览")).toBeVisible();

  const response = await page.evaluate(async (projectId) => {
    const res = await fetch(`/api/backend/projects/${encodeURIComponent(projectId)}/manifest`, {
      headers: {
        Authorization: "Bearer attacker-controlled-token",
      },
    });
    return {
      status: res.status,
      body: await res.json(),
    };
  }, API_MODE_PROJECTS[1].project_id);

  expect(response.status).toBe(404);
  expect(response.body).toMatchObject({
    ok: false,
    error: {
      code: "PROJECT_NOT_FOUND",
    },
  });
});

test("admin sessions can see all projects and admin entry points", async ({ page }) => {
  await installApiModeHarness(page, apiModeSession(API_MODE_USERS.admin));

  await page.goto("/");

  await expect(page.getByText("项目概览")).toBeVisible();
  await expect(page.getByRole("heading", { name: API_MODE_PROJECTS[0].name }).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: API_MODE_PROJECTS[1].name }).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "配置中心" })).toBeVisible();
  await expect(page.getByRole("button", { name: "规则控制面" })).toBeVisible();
  await expect(page.getByRole("button", { name: "媒体生成工作台" })).toBeVisible();
});

import { expect, test, type Page } from "@playwright/test";
import {
  API_MODE_CSRF,
  API_MODE_PROJECTS,
  API_MODE_USERS,
  apiModeSession,
  installApiModeHarness,
} from "./api-mode-auth-harness";

async function openTeacherVideoWorkbench(page: Page) {
  await page.goto("/");
  await expect(page.getByText("项目概览")).toBeVisible();
  await page.getByRole("button", { name: /进入工作区/ }).first().click();
  await page.getByRole("button", { name: "视频生成" }).click();
  await expect(page.getByText("项目素材")).toBeVisible();
}

test("video workbench loads through API-mode real session and sends CSRF on unsafe requests", async ({ page }) => {
  const harness = await installApiModeHarness(page, apiModeSession(API_MODE_USERS.teacherA));

  await openTeacherVideoWorkbench(page);
  await expect(page.getByText("Phase E 安全验收视频")).toBeVisible();

  const missingCsrf = await page.evaluate(async (projectId) => {
    const res = await fetch(`/api/backend/projects/${encodeURIComponent(projectId)}/video-workflow/storage/cleanup`, {
      method: "POST",
    });
    return { status: res.status, body: await res.json() };
  }, API_MODE_PROJECTS[0].project_id);
  expect(missingCsrf).toMatchObject({
    status: 403,
    body: {
      ok: false,
      error: { code: "CSRF_INVALID" },
    },
  });

  const withCsrf = await page.evaluate(async ({ projectId, csrfToken }) => {
    const res = await fetch(`/api/backend/projects/${encodeURIComponent(projectId)}/video-workflow/storage/cleanup`, {
      method: "POST",
      headers: { "X-CSRF-Token": csrfToken },
    });
    return { status: res.status, body: await res.json() };
  }, { projectId: API_MODE_PROJECTS[0].project_id, csrfToken: API_MODE_CSRF.teacherA });
  expect(withCsrf.status).toBe(200);
  expect(withCsrf.body.ok).toBe(true);

  const cleanupRequests = harness.requests.filter((request) =>
    request.pathname.endsWith("/video-workflow/storage/cleanup")
  );
  expect(cleanupRequests.map((request) => request.csrfToken)).toContain(API_MODE_CSRF.teacherA);
});

test("teacher cannot access another project video-workflow resources, previews, downloads, or cleanup", async ({ page }) => {
  await installApiModeHarness(page, apiModeSession(API_MODE_USERS.teacherA));

  await page.goto("/");
  await expect(page.getByText("项目概览")).toBeVisible();

  const denied = await page.evaluate(async ({ projectId, csrfToken }) => {
    const paths = [
      `/api/backend/projects/${projectId}/video-workflow`,
      `/api/backend/projects/${projectId}/video-workflow/assets/asset_${projectId}/content`,
      `/api/backend/projects/${projectId}/video-workflow/runs/run_${projectId}/content`,
      `/api/backend/projects/${projectId}/video-workflow/runs/run_${projectId}/download`,
      `/api/backend/projects/${projectId}/video-workflow/storage/cleanup`,
    ];
    const results: Array<{
      path: string;
      status: number;
      body: unknown;
    }> = [];
    for (const path of paths) {
      const isCleanup = path.endsWith("/cleanup");
      const res = await fetch(path, {
        method: isCleanup ? "POST" : "GET",
        headers: isCleanup ? { "X-CSRF-Token": csrfToken } : undefined,
      });
      const contentType = res.headers.get("content-type") || "";
      results.push({
        path,
        status: res.status,
        body: contentType.includes("application/json") ? await res.json() : null,
      });
    }
    return results;
  }, { projectId: API_MODE_PROJECTS[1].project_id, csrfToken: API_MODE_CSRF.teacherA });

  for (const result of denied) {
    expect(result.status, result.path).toBe(404);
    expect(result.body).toMatchObject({
      ok: false,
      error: { code: "PROJECT_NOT_FOUND" },
    });
  }
});

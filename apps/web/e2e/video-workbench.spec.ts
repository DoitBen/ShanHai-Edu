import { expect, type Page, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M/wHwAF/gL+XcIYAAAAAElFTkSuQmCC",
  "base64",
);
const MP4 = readFileSync(join(__dirname, "fixtures/video-workbench-valid.mp4"));

function createMockVideoWorkflowState() {
  return {
    assets: [] as Array<Record<string, unknown>>,
    runs: [] as Array<Record<string, unknown>>,
    syncCount: 0,
  };
}

async function mockVideoWorkflowApi(page: Page, state = createMockVideoWorkflowState()) {
  const stats = {
    createRunCount: 0,
    lastReferenceAssetIds: [] as string[],
  };
  await page.route("**/api/backend/video/capabilities", async (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        data: {
          models: [
            {
              model: "omni_flash-10s",
              display_name: "Omni Flash 10s",
              reference_image_support: true,
              first_last_frame: false,
              video_edit: false,
              extend: false,
              max_reference_images: 7,
              duration: { default: 10, supported: [10] },
              resolution: { default: "1280x720", supported: ["1280x720"] },
              recommended_use: "项目视频工作台默认模型",
            },
          ],
        },
      }),
    }),
  );
  await page.route("**/api/backend/projects/**/video-workflow**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const ok = (data: unknown) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ok: true, data }),
      });

    if (path.endsWith("/content") && path.includes("/assets/")) {
      return route.fulfill({ status: 200, contentType: "image/png", body: PNG });
    }
    if (path.endsWith("/content") && path.includes("/runs/")) {
      return route.fulfill({ status: 200, contentType: "video/mp4", body: MP4 });
    }
    if (path.endsWith("/download")) {
      return route.fulfill({
        status: 200,
        contentType: "video/mp4",
        headers: { "Content-Disposition": 'attachment; filename="test.mp4"' },
        body: MP4,
      });
    }
    if (request.method() === "POST" && path.endsWith("/assets")) {
      state.assets = ["a", "b", "c", "d", "e", "f", "g", "h"].map((suffix, index) => ({
        asset_id: `vref_${suffix}`,
        filename: `reference-${suffix}.png`,
        path: `video_workflow/references/reference-${suffix}.png`,
        mime_type: "image/png",
        byte_size: PNG.length,
        width: 1,
        height: 1,
        created_at: new Date(Date.now() + index).toISOString(),
        deleted_at: null,
      }));
      return ok({ assets: state.assets, uploaded: state.assets, errors: [], max_reference_images: 7 });
    }
    if (request.method() === "POST" && path.endsWith("/runs")) {
      const payload = request.postDataJSON();
      stats.createRunCount += 1;
      stats.lastReferenceAssetIds = payload.reference_asset_ids as string[];
      const run = {
        run_id: "task_e2e",
        client_request_id: payload.client_request_id,
        retry_of_run_id: null,
        project_id: "demo",
        status: "queued",
        download_status: "not_started",
        progress: 0,
        prompt: payload.prompt,
        model: "omni_flash-10s",
        size: "1280x720",
        duration_sec: 10,
        reference_asset_ids: payload.reference_asset_ids,
        reference_assets: state.assets
          .filter((asset) => (payload.reference_asset_ids as string[]).includes(asset.asset_id as string))
          .map((asset) => ({
            asset_id: asset.asset_id,
            filename: asset.filename,
            mime_type: asset.mime_type,
            width: asset.width,
            height: asset.height,
          })),
        provider_task_id: "remote_e2e",
        error_code: null,
        error_message: null,
        retryable: false,
        video_ready: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      state.runs = [run];
      return ok(run);
    }
    if (request.method() === "POST" && path.endsWith("/sync")) {
      if (state.runs.some((run) => run.status === "completed_pending_download")) {
        return ok(state.runs[0]);
      }
      state.syncCount += 1;
      state.runs = state.runs.map((run) => ({
        ...run,
        status: state.syncCount >= 2 ? "completed" : "processing",
        progress: state.syncCount >= 2 ? 100 : 50,
        download_status: state.syncCount >= 2 ? "downloaded" : "not_started",
        video_ready: state.syncCount >= 2,
      }));
      return ok(state.runs[0]);
    }
    if (request.method() === "GET" && path.endsWith("/runs")) return ok(state.runs);
    if (request.method() === "GET" && path.endsWith("/video-workflow")) {
      return ok({
        project_id: "demo",
        config: {
          model: "omni_flash-10s",
          size: "1280x720",
          duration_sec: 10,
          max_reference_images: 7,
          max_project_assets: 50,
          max_asset_bytes: 10485760,
          poll_interval_ms: 50,
          provider_ready: true,
          provider_reason_code: "VIDEO_PROVIDER_READY",
          provider_user_message: "视频生成服务已就绪",
        },
        assets: state.assets,
        runs: state.runs,
      });
    }
    return route.fallback();
  });
  return stats;
}

async function openAuthenticatedProject(page: Page) {
  await page.addInitScript(() => {
    window.localStorage.setItem(
      "shanhai_auth",
      JSON.stringify({
        username: "admin",
        role: "admin",
        displayName: "管理员",
        loginAt: new Date().toISOString(),
      }),
    );
  });
  await page.goto("/");
  await expect(page.getByText("项目概览")).toBeVisible();
  await expect(page.getByRole("heading", { name: "古诗文诵读——静夜思" })).toBeVisible();
  await page.getByRole("button", { name: /^进入$/ }).nth(2).click();
}

async function openVideoWorkbench(page: Page) {
  await page.getByRole("button", { name: "视频生成" }).click();
  await expect(page.getByText("项目素材")).toBeVisible();
}

test("project video workbench completes the core flow", async ({ page }) => {
  const apiStats = await mockVideoWorkflowApi(page);
  await openAuthenticatedProject(page);
  await openVideoWorkbench(page);

  await page.getByLabel("上传参考图").setInputFiles(
    ["a", "b", "c", "d", "e", "f", "g", "h"].map((name) => ({
      name: `reference-${name}.png`,
      mimeType: "image/png",
      buffer: PNG,
    })),
  );
  for (const name of ["a", "b", "c", "d", "e", "f", "g"]) {
    await page.getByRole("button", { name: new RegExp(`reference-${name}\\.png`) }).click();
  }
  await expect(page.getByText("已选 7 / 7")).toBeVisible();
  await page.getByRole("button", { name: /reference-h\.png/ }).click();
  await expect(page.getByText("已选 7 / 7")).toBeVisible();

  await page.getByRole("textbox", { name: "视频提示词" }).first().fill(
    "卡通三角形积木逐渐组合成一座桥，固定镜头，温暖课堂插画风格。",
  );
  const generateButton = page.getByRole("button", { name: "生成 10 秒视频" });
  let confirmMessage = "";
  page.once("dialog", async (dialog) => {
    confirmMessage = dialog.message();
    expect(confirmMessage).toContain("确认生成 10 秒视频");
    expect(confirmMessage).toContain("参考图数量：7");
    await dialog.accept();
  });
  await Promise.all([generateButton.click(), generateButton.click()]);
  expect(confirmMessage).toContain("omni_flash-10s");
  await expect.poll(() => apiStats.createRunCount).toBe(1);
  expect(apiStats.lastReferenceAssetIds).toEqual([
    "vref_a",
    "vref_b",
    "vref_c",
    "vref_d",
    "vref_e",
    "vref_f",
    "vref_g",
  ]);
  const video = page.locator("video:visible").first();
  await expect(video).toBeVisible({ timeout: 30_000 });
  await video.evaluate((node: HTMLVideoElement) => {
    if (node.readyState >= HTMLMediaElement.HAVE_METADATA && node.duration > 0) return;
    return new Promise<void>((resolve, reject) => {
      const timer = window.setTimeout(() => reject(new Error("video metadata did not load")), 10_000);
      node.addEventListener(
        "loadedmetadata",
        () => {
          window.clearTimeout(timer);
          if (node.duration > 0) resolve();
          else reject(new Error(`invalid video duration: ${node.duration}`));
        },
        { once: true },
      );
      node.load();
    });
  });

  await page.reload();
  await expect(page.getByText("项目概览")).toBeVisible();
  await page.getByRole("button", { name: /^进入$/ }).nth(2).click();
  await openVideoWorkbench(page);
  await expect(page.locator("video:visible").first()).toBeVisible();
  await page.getByRole("button", { name: "复用参数" }).first().click();
  await expect(page.getByRole("textbox", { name: "视频提示词" }).first()).toHaveValue(/三角形积木/);
});

test("project video workbench disables keyboard submit while a run is active", async ({ page }) => {
  const state = createMockVideoWorkflowState();
  state.runs = [
    {
      run_id: "task_active",
      client_request_id: "req_active",
      retry_of_run_id: null,
      project_id: "demo",
      status: "completed_pending_download",
      download_status: "pending_url",
      progress: 100,
      prompt: "等待上游返回视频下载地址",
      model: "omni_flash-10s",
      size: "1280x720",
      duration_sec: 10,
      reference_asset_ids: [],
      reference_assets: [],
      provider_task_id: "remote_active",
      error_code: null,
      error_message: null,
      retryable: false,
      video_ready: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];
  const apiStats = await mockVideoWorkflowApi(page, state);
  await openAuthenticatedProject(page);
  await openVideoWorkbench(page);

  await page.getByRole("textbox", { name: "视频提示词" }).first().fill(
    "已有任务时键盘不能绕过生成按钮禁用状态。",
  );
  const generateButton = page.getByRole("button", { name: "生成 10 秒视频" });
  await expect(generateButton).toBeDisabled();
  await expect(page.getByText("已有视频任务正在生成，请等待完成后再创建新任务。").first()).toBeVisible();

  await generateButton.focus();
  await page.keyboard.press("Enter");
  await page.keyboard.press("Space");
  await page.waitForTimeout(100);

  expect(apiStats.createRunCount).toBe(0);
});

test("project video workbench refreshes another open tab after a run is created", async ({ context }) => {
  const first = await context.newPage();
  const second = await context.newPage();
  const sharedState = createMockVideoWorkflowState();
  await mockVideoWorkflowApi(first, sharedState);
  await mockVideoWorkflowApi(second, sharedState);

  await openAuthenticatedProject(first);
  await openVideoWorkbench(first);
  await openAuthenticatedProject(second);
  await openVideoWorkbench(second);

  await expect(second.getByText("暂无任务")).toBeVisible();

  await first.getByRole("textbox", { name: "视频提示词" }).first().fill(
    "卡通数学尺子在黑板前缓慢旋转，暖色课堂插画风格。",
  );
  first.once("dialog", async (dialog) => {
    expect(dialog.message()).toContain("确认生成 10 秒视频");
    await dialog.accept();
  });
  await first.getByRole("button", { name: "生成 10 秒视频" }).click();

  await expect(second.getByText("卡通数学尺子在黑板前缓慢旋转")).toBeVisible({ timeout: 10_000 });
});

test("project video workbench pauses offline polling and resumes automatically", async ({ page }) => {
  await mockVideoWorkflowApi(page);
  await openAuthenticatedProject(page);
  await openVideoWorkbench(page);

  await page.context().setOffline(true);
  await page.getByRole("textbox", { name: "视频提示词" }).first().fill(
    "卡通几何图形在课桌上排队前进，固定镜头，明亮课堂插画风格。",
  );
  await page.context().setOffline(false);
  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toContain("确认生成 10 秒视频");
    await dialog.accept();
  });
  await page.getByRole("button", { name: "生成 10 秒视频" }).click();

  await page.context().setOffline(true);
  await expect(page.getByText("视频任务轮询已暂停")).toBeVisible({ timeout: 10_000 });
  await page.context().setOffline(false);

  await expect(page.locator("video:visible").first()).toBeVisible({ timeout: 30_000 });
});

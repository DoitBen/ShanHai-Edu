import { expect, type Page, type Route, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M/wHwAF/gL+XcIYAAAAAElFTkSuQmCC",
  "base64",
);
const MP4 = readFileSync(join(__dirname, "fixtures/video-workbench-valid.mp4"));
const E2E_CSRF_TOKEN = "csrf-e2e-token";
const E2E_DEMO_PASSWORD = "shanhai2026";
const E2E_PROJECT_ID = "demo";
const E2E_PROJECT_NAME = "古诗文诵读——静夜思";
const EXPECT_VIDEO_WORKFLOW_CSRF = process.env.NEXT_PUBLIC_DEMO_MODE !== "true";

const E2E_PROJECT = {
  project_id: E2E_PROJECT_ID,
  name: E2E_PROJECT_NAME,
  subject: "chinese",
  grade: "2",
  textbook_version: "tongbian",
  volume: "shang",
  lesson_type: "reading",
  textbook_id: null,
  textbook_version_id: null,
  knowledge_point_id: null,
  reference_lesson_plan_id: null,
  created_at: "2026-06-30T00:00:00Z",
  status: "active",
  project_dir: "storage/projects/demo",
};

const E2E_NODE_IDS = [
  "project_meta",
  "project_config",
  "visual_contract",
  "character_dict",
  "textbook_parse",
  "lesson_plan",
  "intro_selection",
  "ppt_assembly_plan",
  "ppt_page_script",
  "ppt_visual_asset",
  "pptx_artifact",
  "intro_video_script",
  "intro_video_screenplay",
  "intro_video_asset",
  "storyboard",
  "final_video",
];

function createMockManifest() {
  const videoStart = E2E_NODE_IDS.indexOf("final_video");
  return {
    project: E2E_PROJECT,
    nodes: E2E_NODE_IDS.map((nodeId, index) => ({
      project_id: E2E_PROJECT_ID,
      node_id: nodeId,
      title: null,
      step: index + 1,
      branch: nodeId.includes("video") || nodeId === "storyboard" || nodeId === "final_video"
        ? "intro_video"
        : nodeId.startsWith("ppt")
          ? "ppt"
          : "shared",
      depends_on: [],
      schema: null,
      status: index < videoStart ? "approved" : nodeId === "final_video" ? "input_required" : "approved",
      current_version_id: index < videoStart ? `ver_${nodeId}` : null,
      updated_at: "2026-06-30T00:00:00Z",
      capabilities: {
        can_generate: true,
        can_edit: true,
        can_approve: true,
        can_redo: true,
        can_skip: false,
      },
      artifact: null,
      rule_summary: {
        hard_block_count: 0,
        warning_count: 0,
        failed_rule_ids: [],
        warning_rule_ids: [],
      },
      latest_transition: null,
      review_reason: null,
    })),
  };
}

async function mockAuthenticatedApiSession(page: Page, role: "admin" | "teacher" = "admin") {
  await page.route("**/api/backend/auth/me", async (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        data: {
          user: {
            user_id: `e2e-${role}`,
            email: `${role}@example.test`,
            display_name: role === "admin" ? "管理员" : "测试教师",
            role,
            status: "active",
          },
          csrf_token: E2E_CSRF_TOKEN,
          expires_at: "2026-06-30T12:00:00Z",
        },
      }),
    }),
  );
}

async function mockProjectApi(page: Page) {
  const manifest = createMockManifest();
  const ok = (route: Route, data: unknown) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ ok: true, data }),
    });

  await page.route("**/api/backend/projects", async (route) => ok(route, [E2E_PROJECT]));
  await page.route("**/api/backend/projects/*/manifest", async (route) => ok(route, manifest));
  await page.route("**/api/backend/projects/*/workspace", async (route) =>
    ok(route, {
      project_id: E2E_PROJECT_ID,
      current_step_id: "video-generation",
      steps: [],
      developer_diagnostics: null,
    }),
  );
  await page.route("**/api/backend/projects/*/nodes/*", async (route) => {
    const nodeId = decodeURIComponent(new URL(route.request().url()).pathname.split("/").pop() || "final_video");
    const node = manifest.nodes.find((item) => item.node_id === nodeId) || manifest.nodes.at(-1)!;
    return ok(route, {
      ...node,
      content: nodeId === "final_video" ? { status: "ready_for_video_workbench" } : `节点内容：${nodeId}`,
    });
  });
  await page.route("**/api/backend/projects/*/tasks**", async (route) => ok(route, []));
}

async function seedDemoAuth(page: Page) {
  await page.addInitScript(() => {
    const authKey = ["shanhai", "auth"].join("_");
    window.localStorage.setItem(
      authKey,
      JSON.stringify({
        userId: "demo-admin",
        email: "admin@demo.local",
        username: "admin",
        role: "admin",
        displayName: "管理员",
        status: "active",
        loginAt: new Date().toISOString(),
      }),
    );
  });
}

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
    if (EXPECT_VIDEO_WORKFLOW_CSRF && ["POST", "PUT", "PATCH", "DELETE"].includes(request.method())) {
      expect(request.headers()["x-csrf-token"]).toBe(E2E_CSRF_TOKEN);
    }
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
  await seedDemoAuth(page);
  await mockAuthenticatedApiSession(page);
  await mockProjectApi(page);
  await page.goto("/");
  const loginButton = page.getByRole("button", { name: /^登录$/ });
  if (await loginButton.isVisible({ timeout: 1_000 }).catch(() => false)) {
    const accountInput = page.getByLabel(/用户名|邮箱/);
    await page.getByRole("button", { name: /教师 业务流程/ }).click();
    await expect(accountInput).toHaveValue("teacher");
    await page.getByRole("button", { name: /管理员 全部功能/ }).click();
    await expect(accountInput).toHaveValue("admin");
    await page.getByLabel("密码").fill(E2E_DEMO_PASSWORD);
    await loginButton.click();
  }
  await expect(page.getByText("项目概览")).toBeVisible();
  await expect(page.getByRole("heading", { name: E2E_PROJECT_NAME }).first()).toBeVisible();
  await page.getByRole("button", { name: /进入工作区/ }).first().click();
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
  await page.getByRole("button", { name: /进入工作区/ }).first().click();
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

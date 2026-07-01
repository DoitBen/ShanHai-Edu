import { expect, type Page, type Route } from "@playwright/test";
import { readFileSync } from "node:fs";
import { join } from "node:path";

export type ApiModeRole = "admin" | "teacher";

export type ApiModeUser = {
  user_id: string;
  email: string;
  display_name: string;
  role: ApiModeRole;
  status: "active";
  password: string;
};

export type ApiModeProject = {
  project_id: string;
  owner_user_id: string;
  name: string;
  subject: string;
  grade: string;
  textbook_version: string;
  volume: string;
  lesson_type: string;
  created_at: string;
  status: string;
  project_dir: string;
};

export type ApiModeSession = {
  user: ApiModeUser;
  csrfToken: string;
};

export type ApiModeRequestRecord = {
  method: string;
  pathname: string;
  csrfToken: string | null;
  authorization: string | null;
};

export type ApiModeHarness = {
  requests: ApiModeRequestRecord[];
  setSession: (session: ApiModeSession | null) => void;
  getSession: () => ApiModeSession | null;
};

export const API_MODE_PASSWORD = "phase-e-password";
export const API_MODE_CSRF = {
  teacherA: "csrf-teacher-a",
  teacherB: "csrf-teacher-b",
  admin: "csrf-admin",
} as const;

export const API_MODE_USERS = {
  teacherA: {
    user_id: "user_teacher_a",
    email: "teacher.a@example.test",
    display_name: "教师 A",
    role: "teacher",
    status: "active",
    password: API_MODE_PASSWORD,
  },
  teacherB: {
    user_id: "user_teacher_b",
    email: "teacher.b@example.test",
    display_name: "教师 B",
    role: "teacher",
    status: "active",
    password: API_MODE_PASSWORD,
  },
  admin: {
    user_id: "user_admin",
    email: "admin@example.test",
    display_name: "管理员",
    role: "admin",
    status: "active",
    password: API_MODE_PASSWORD,
  },
} satisfies Record<string, ApiModeUser>;

export const API_MODE_PROJECTS: ApiModeProject[] = [
  {
    project_id: "project_teacher_a",
    owner_user_id: API_MODE_USERS.teacherA.user_id,
    name: "教师 A 的视频项目",
    subject: "math",
    grade: "3",
    textbook_version: "renjiao",
    volume: "shang",
    lesson_type: "new",
    created_at: "2026-07-01T00:00:00Z",
    status: "active",
    project_dir: "storage/projects/project_teacher_a",
  },
  {
    project_id: "project_teacher_b",
    owner_user_id: API_MODE_USERS.teacherB.user_id,
    name: "教师 B 的视频项目",
    subject: "chinese",
    grade: "2",
    textbook_version: "tongbian",
    volume: "shang",
    lesson_type: "reading",
    created_at: "2026-07-01T00:10:00Z",
    status: "active",
    project_dir: "storage/projects/project_teacher_b",
  },
];

export const API_MODE_MP4 = readFileSync(join(__dirname, "fixtures/video-workbench-valid.mp4"));
export const API_MODE_PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M/wHwAF/gL+XcIYAAAAAElFTkSuQmCC",
  "base64",
);

export function apiModeSession(user: ApiModeUser): ApiModeSession {
  const csrfToken =
    user.user_id === API_MODE_USERS.admin.user_id
      ? API_MODE_CSRF.admin
      : user.user_id === API_MODE_USERS.teacherB.user_id
        ? API_MODE_CSRF.teacherB
        : API_MODE_CSRF.teacherA;
  return { user, csrfToken };
}

export async function installApiModeHarness(
  page: Page,
  initialSession: ApiModeSession | null = null,
): Promise<ApiModeHarness> {
  let session = initialSession;
  const requests: ApiModeRequestRecord[] = [];

  const harness: ApiModeHarness = {
    requests,
    setSession: (next) => {
      session = next;
    },
    getSession: () => session,
  };

  await page.route("**/api/backend/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const pathname = url.pathname.replace(/^\/api\/backend/, "") || "/";
    requests.push({
      method: request.method(),
      pathname,
      csrfToken: request.headers()["x-csrf-token"] ?? null,
      authorization: request.headers().authorization ?? null,
    });

    if (pathname === "/auth/me" && request.method() === "GET") {
      if (!session) return authRequired(route);
      return ok(route, authSessionPayload(session));
    }

    if (pathname === "/auth/login" && request.method() === "POST") {
      const payload = request.postDataJSON() as { email?: string; password?: string };
      const user = Object.values(API_MODE_USERS).find(
        (candidate) => candidate.email === payload.email && candidate.password === payload.password,
      );
      if (!user) {
        return fail(route, 401, "AUTH_INVALID_CREDENTIALS", "邮箱或密码不正确");
      }
      session = apiModeSession(user);
      return ok(route, authSessionPayload(session), {
        "Set-Cookie": "shanhai_session=e2e-session; Path=/; HttpOnly; SameSite=Lax",
      });
    }

    if (pathname === "/auth/logout" && request.method() === "POST") {
      if (session && request.headers()["x-csrf-token"] !== session.csrfToken) {
        return fail(route, 403, "CSRF_INVALID", "CSRF 校验失败");
      }
      session = null;
      return ok(route, { logged_out: true }, {
        "Set-Cookie": "shanhai_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax",
      });
    }

    if (!session) return authRequired(route);

    if (pathname === "/projects" && request.method() === "GET") {
      const allowed = API_MODE_PROJECTS.filter((project) => canAccessProject(session!, project));
      return ok(route, allowed.map(stripProjectOwner));
    }

    if (pathname === "/video/capabilities" && request.method() === "GET") {
      return ok(route, videoCapabilities());
    }

    const projectMatch = pathname.match(/^\/projects\/([^/]+)(?:\/(.*))?$/);
    if (projectMatch) {
      const projectId = decodeURIComponent(projectMatch[1]);
      const suffix = projectMatch[2] || "";
      const project = API_MODE_PROJECTS.find((candidate) => candidate.project_id === projectId);
      if (!project || !canAccessProject(session, project)) return projectNotFound(route);
      if (["POST", "PUT", "PATCH", "DELETE"].includes(request.method())) {
        if (request.headers()["x-csrf-token"] !== session.csrfToken) {
          return fail(route, 403, "CSRF_INVALID", "CSRF 校验失败");
        }
      }
      return handleProjectRoute(route, project, suffix);
    }

    return fail(route, 404, "NOT_FOUND", "未找到接口");
  });

  return harness;
}

export async function loginViaApiMode(page: Page, user: ApiModeUser = API_MODE_USERS.teacherA) {
  await page.getByLabel("邮箱").fill(user.email);
  await page.getByRole("textbox", { name: "密码" }).fill(user.password);
  await page.getByRole("button", { name: /^登录$/ }).click();
}

export async function expectNoPersistentApiAuth(page: Page) {
  const storage = await page.evaluate(() => ({
    auth: window.localStorage.getItem("shanhai_auth"),
    localKeys: Object.keys(window.localStorage),
    sessionKeys: Object.keys(window.sessionStorage),
  }));
  expect(storage.auth).toBeNull();
  expect(storage.localKeys.some((key) => /csrf|session|token/i.test(key))).toBe(false);
  expect(storage.sessionKeys.some((key) => /csrf|session|token/i.test(key))).toBe(false);
}

function authSessionPayload(session: ApiModeSession) {
  return {
    user: {
      user_id: session.user.user_id,
      email: session.user.email,
      display_name: session.user.display_name,
      role: session.user.role,
      status: session.user.status,
    },
    csrf_token: session.csrfToken,
    expires_at: "2026-07-01T12:00:00Z",
  };
}

function canAccessProject(session: ApiModeSession, project: ApiModeProject) {
  return session.user.role === "admin" || project.owner_user_id === session.user.user_id;
}

function stripProjectOwner(project: ApiModeProject) {
  const { owner_user_id: _ownerUserId, ...apiProject } = project;
  return apiProject;
}

function handleProjectRoute(route: Route, project: ApiModeProject, suffix: string) {
  const request = route.request();
  if (suffix === "manifest" && request.method() === "GET") {
    return ok(route, { project: stripProjectOwner(project), nodes: manifestNodes(project.project_id) });
  }
  if (suffix === "workspace" && request.method() === "GET") {
    return ok(route, {
      project_id: project.project_id,
      current_step_id: "video-generation",
      steps: [],
      developer_diagnostics: null,
    });
  }
  if (/^nodes\/[^/]+$/.test(suffix) && request.method() === "GET") {
    const nodeId = decodeURIComponent(suffix.split("/").at(-1) || "final_video");
    const node = manifestNodes(project.project_id).find((item) => item.node_id === nodeId) || manifestNodes(project.project_id).at(-1)!;
    return ok(route, { ...node, content: nodeId === "final_video" ? { status: "ready" } : `节点内容：${nodeId}` });
  }
  if (suffix.startsWith("tasks") && request.method() === "GET") return ok(route, []);
  if (suffix === "video-workflow" && request.method() === "GET") return ok(route, videoWorkflow(project.project_id));
  if (suffix === "video-workflow/storage/cleanup" && request.method() === "POST") {
    return ok(route, {
      policy: { max_project_assets: 50, max_run_retention: 50 },
      before: { total_bytes: 1024, asset_count: 1, run_count: 1 },
      after: { total_bytes: 1024, asset_count: 1, run_count: 1 },
      deleted: [],
    });
  }
  if (/^video-workflow\/assets\/[^/]+\/content$/.test(suffix) && request.method() === "GET") {
    return route.fulfill({ status: 200, contentType: "image/png", body: API_MODE_PNG });
  }
  if (/^video-workflow\/assets\/[^/]+$/.test(suffix) && request.method() === "DELETE") {
    return ok(route, { asset_id: suffix.split("/")[2], deleted: true });
  }
  if (suffix === "video-workflow/assets" && request.method() === "POST") {
    return ok(route, { assets: videoWorkflow(project.project_id).assets, uploaded: videoWorkflow(project.project_id).assets, errors: [] });
  }
  if (suffix === "video-workflow/runs" && request.method() === "POST") {
    const run = videoWorkflow(project.project_id).runs[0];
    return ok(route, run);
  }
  if (/^video-workflow\/runs\/[^/]+\/(sync|retry)$/.test(suffix) && request.method() === "POST") {
    return ok(route, videoWorkflow(project.project_id).runs[0]);
  }
  if (/^video-workflow\/runs\/[^/]+\/content$/.test(suffix) && request.method() === "GET") {
    return route.fulfill({ status: 200, contentType: "video/mp4", body: API_MODE_MP4 });
  }
  if (/^video-workflow\/runs\/[^/]+\/download$/.test(suffix) && request.method() === "GET") {
    return route.fulfill({
      status: 200,
      contentType: "video/mp4",
      headers: { "Content-Disposition": 'attachment; filename="phase-e.mp4"' },
      body: API_MODE_MP4,
    });
  }
  if (/^video-workflow\/runs(?:\/[^/]+)?$/.test(suffix) && request.method() === "GET") {
    return ok(route, suffix === "video-workflow/runs" ? videoWorkflow(project.project_id).runs : videoWorkflow(project.project_id).runs[0]);
  }
  return ok(route, {});
}

function manifestNodes(projectId: string) {
  const nodeIds = [
    "project_meta",
    "project_config",
    "textbook_parse",
    "lesson_plan",
    "intro_selection",
    "intro_video_script",
    "intro_video_screenplay",
    "intro_video_asset",
    "storyboard",
    "final_video",
  ];
  return nodeIds.map((nodeId, index) => ({
    project_id: projectId,
    node_id: nodeId,
    title: null,
    step: index + 1,
    branch: nodeId.includes("video") || nodeId === "storyboard" || nodeId === "final_video" ? "intro_video" : "shared",
    depends_on: [],
    schema: null,
    status: index < nodeIds.length - 1 ? "approved" : "input_required",
    current_version_id: index < nodeIds.length - 1 ? `ver_${nodeId}` : null,
    updated_at: "2026-07-01T00:00:00Z",
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
  }));
}

function videoCapabilities() {
  return {
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
  };
}

function videoWorkflow(projectId: string) {
  return {
    project_id: projectId,
    config: {
      model: "omni_flash-10s",
      size: "1280x720",
      duration_sec: 10,
      max_reference_images: 7,
      max_project_assets: 50,
      max_asset_bytes: 10 * 1024 * 1024,
      poll_interval_ms: 50,
      run_create_window_seconds: 600,
      run_create_project_window_limit: 1,
      provider_ready: true,
      provider_reason_code: "VIDEO_PROVIDER_READY",
      provider_user_message: "视频生成服务已就绪",
    },
    storage_usage: {
      total_bytes: 1024,
      asset_count: 1,
      run_count: 1,
    },
    assets: [
      {
        asset_id: `asset_${projectId}`,
        filename: "reference.png",
        path: "video_workflow/references/reference.png",
        mime_type: "image/png",
        byte_size: API_MODE_PNG.length,
        width: 1,
        height: 1,
        created_at: "2026-07-01T00:00:00Z",
        deleted_at: null,
      },
    ],
    runs: [
      {
        run_id: `run_${projectId}`,
        client_request_id: `request_${projectId}`,
        retry_of_run_id: null,
        project_id: projectId,
        status: "completed",
        download_status: "downloaded",
        progress: 100,
        prompt: "Phase E 安全验收视频",
        model: "omni_flash-10s",
        size: "1280x720",
        duration_sec: 10,
        reference_asset_ids: [`asset_${projectId}`],
        reference_assets: [],
        provider_task_id: null,
        error_code: null,
        error_message: null,
        retryable: false,
        video_ready: true,
        created_at: "2026-07-01T00:00:00Z",
        updated_at: "2026-07-01T00:01:00Z",
      },
    ],
    latest_run: null,
  };
}

function ok(route: Route, data: unknown, headers?: Record<string, string>) {
  return route.fulfill({
    status: 200,
    contentType: "application/json",
    headers,
    body: JSON.stringify({ ok: true, data }),
  });
}

function authRequired(route: Route) {
  return fail(route, 401, "AUTH_REQUIRED", "请先登录");
}

function projectNotFound(route: Route) {
  return fail(route, 404, "PROJECT_NOT_FOUND", "项目不存在或无权访问");
}

function fail(route: Route, status: number, code: string, message: string) {
  return route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify({
      ok: false,
      error: {
        code,
        message,
        retryable: false,
        details: null,
        action: null,
        trace_id: "trace_e2e",
      },
    }),
  });
}

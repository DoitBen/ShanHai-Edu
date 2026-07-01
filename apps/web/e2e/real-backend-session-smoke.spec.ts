import { expect, test, type Page } from "@playwright/test";

const PASSWORD = "CorrectHorse123!";

const USERS = {
  teacherA: {
    email: "phase-e-teacher-a@example.test",
    password: PASSWORD,
  },
  teacherB: {
    email: "phase-e-teacher-b@example.test",
    password: PASSWORD,
  },
  admin: {
    email: "phase-e-admin@example.test",
    password: PASSWORD,
  },
} as const;

type ApiResult = {
  status: number;
  body: {
    ok?: boolean;
    data?: unknown;
    error?: {
      code?: string;
      message?: string;
    };
  };
};

type AuthPayload = {
  user: {
    email: string;
    role: "admin" | "teacher";
    status: "active" | "disabled";
  };
  csrf_token: string;
};

type ProjectPayload = {
  project_id: string;
  name: string;
};

async function apiFetch(
  page: Page,
  path: string,
  options: { method?: string; csrfToken?: string; body?: unknown } = {},
): Promise<ApiResult> {
  return page.evaluate(
    async ({ path, method, csrfToken, body }) => {
      const headers: Record<string, string> = {};
      if (body !== undefined) headers["Content-Type"] = "application/json";
      if (csrfToken) headers["X-CSRF-Token"] = csrfToken;
      const response = await fetch(`/api/backend${path}`, {
        method,
        headers,
        credentials: "same-origin",
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      const contentType = response.headers.get("content-type") || "";
      return {
        status: response.status,
        body: contentType.includes("application/json") ? await response.json() : {},
      };
    },
    { path, method: options.method || "GET", csrfToken: options.csrfToken, body: options.body },
  );
}

async function login(page: Page, email: string, password = PASSWORD): Promise<AuthPayload> {
  const response = await apiFetch(page, "/auth/login", {
    method: "POST",
    body: { email, password },
  });
  expect(response.status).toBe(200);
  expect(response.body.ok).toBe(true);
  return response.body.data as AuthPayload;
}

async function me(page: Page): Promise<AuthPayload> {
  const response = await apiFetch(page, "/auth/me");
  expect(response.status).toBe(200);
  expect(response.body.ok).toBe(true);
  return response.body.data as AuthPayload;
}

async function logout(page: Page, csrfToken: string) {
  const response = await apiFetch(page, "/auth/logout", {
    method: "POST",
    csrfToken,
  });
  expect(response.status).toBe(200);
  expect(response.body.ok).toBe(true);
}

async function createProject(page: Page, name: string, csrfToken?: string): Promise<ApiResult> {
  return apiFetch(page, "/projects", {
    method: "POST",
    csrfToken,
    body: {
      name,
      subject: "math",
      grade: "3",
      textbook_version: "renjiao",
      volume: "xia",
      lesson_type: "public",
    },
  });
}

function projectIds(response: ApiResult): string[] {
  expect(response.status).toBe(200);
  expect(response.body.ok).toBe(true);
  return (response.body.data as ProjectPayload[]).map((project) => project.project_id);
}

test("real Next proxy and FastAPI session smoke enforces project RBAC and CSRF", async ({ page }) => {
  await page.goto("/");

  await login(page, USERS.teacherA.email);
  const teacherA = await me(page);
  expect(teacherA.user).toMatchObject({
    email: USERS.teacherA.email,
    role: "teacher",
    status: "active",
  });

  const missingCsrfCreate = await createProject(page, "Phase E missing csrf");
  expect(missingCsrfCreate.status).toBe(403);
  expect(missingCsrfCreate.body.error?.code).toBe("CSRF_TOKEN_REQUIRED");

  const wrongCsrfCreate = await createProject(page, "Phase E wrong csrf", "wrong-csrf-token");
  expect(wrongCsrfCreate.status).toBe(403);
  expect(wrongCsrfCreate.body.error?.code).toBe("CSRF_TOKEN_INVALID");

  const projectAResponse = await createProject(page, "Phase E Teacher A Project", teacherA.csrf_token);
  expect(projectAResponse.status).toBe(200);
  const projectA = projectAResponse.body.data as ProjectPayload;
  await logout(page, teacherA.csrf_token);

  await login(page, USERS.teacherB.email);
  const teacherB = await me(page);
  const projectBResponse = await createProject(page, "Phase E Teacher B Project", teacherB.csrf_token);
  expect(projectBResponse.status).toBe(200);
  const projectB = projectBResponse.body.data as ProjectPayload;
  await logout(page, teacherB.csrf_token);

  await login(page, USERS.teacherA.email);
  const teacherAAgain = await me(page);
  const teacherAProjects = projectIds(await apiFetch(page, "/projects"));
  expect(teacherAProjects).toContain(projectA.project_id);
  expect(teacherAProjects).not.toContain(projectB.project_id);

  for (const suffix of ["manifest", "video-workflow"]) {
    const denied = await apiFetch(page, `/projects/${projectB.project_id}/${suffix}`);
    expect(denied.status).toBe(404);
    expect(denied.body.error?.code).toBe("PROJECT_NOT_FOUND");
  }

  const cleanup = await apiFetch(page, `/projects/${projectA.project_id}/video-workflow/storage/cleanup`, {
    method: "POST",
    csrfToken: teacherAAgain.csrf_token,
  });
  expect(cleanup.status).toBe(200);
  expect(cleanup.body.ok).toBe(true);
  await logout(page, teacherAAgain.csrf_token);

  await login(page, USERS.admin.email);
  const admin = await me(page);
  expect(admin.user.role).toBe("admin");
  const adminProjects = projectIds(await apiFetch(page, "/projects"));
  expect(adminProjects).toEqual(expect.arrayContaining([projectA.project_id, projectB.project_id]));
});

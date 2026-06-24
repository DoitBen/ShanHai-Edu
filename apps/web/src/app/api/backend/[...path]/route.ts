import { NextRequest, NextResponse } from "next/server";

const BACKEND_BASE_URL = process.env.BACKEND_API_BASE_URL || "http://localhost:8000";
const BACKEND_API_TOKEN = process.env.BACKEND_API_TOKEN;
const AUTH_COOKIE_NAME = "shanhai_auth";

type RouteContext = {
  params: Promise<{ path?: string[] }> | { path?: string[] };
};

async function proxyBackend(request: NextRequest, context: RouteContext) {
  const params = await context.params;
  const pathParts = params.path || [];
  const path = pathParts.map(encodeURIComponent).join("/");
  if (isAdminBackendPath(pathParts) && !isLocalAdminRequest(request)) {
    return NextResponse.json(
      {
        ok: false,
        error: {
          code: "NOT_FOUND",
          message: "资源不存在",
          retryable: false,
        },
      },
      { status: 404 },
    );
  }
  const search = request.nextUrl.search || "";
  const backendUrl = `${BACKEND_BASE_URL.replace(/\/+$/, "")}/${path}${search}`;
  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("expect");
  if (BACKEND_API_TOKEN) {
    headers.set("Authorization", `Bearer ${BACKEND_API_TOKEN}`);
  } else {
    headers.delete("Authorization");
  }

  const response = await fetch(backendUrl, {
    method: request.method,
    headers,
    body: ["GET", "HEAD"].includes(request.method) ? undefined : request.body,
    cache: "no-store",
    duplex: "half",
  } as RequestInit & { duplex: "half" });

  return new NextResponse(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
}

function isAdminBackendPath(path: string[]) {
  return path[0] === "admin";
}

function isLocalAdminRequest(request: NextRequest) {
  const raw = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (!raw) return false;
  try {
    const parsed = JSON.parse(decodeURIComponent(raw)) as { role?: unknown };
    return parsed.role === "admin";
  } catch {
    return false;
  }
}

export async function GET(request: NextRequest, context: RouteContext) {
  return proxyBackend(request, context);
}

export async function POST(request: NextRequest, context: RouteContext) {
  return proxyBackend(request, context);
}

export async function PUT(request: NextRequest, context: RouteContext) {
  return proxyBackend(request, context);
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  return proxyBackend(request, context);
}

export async function DELETE(request: NextRequest, context: RouteContext) {
  return proxyBackend(request, context);
}

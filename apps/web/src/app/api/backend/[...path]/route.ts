import { NextRequest, NextResponse } from "next/server";

const BACKEND_BASE_URL = process.env.BACKEND_API_BASE_URL || "http://localhost:8000";

type RouteContext = {
  params: Promise<{ path?: string[] }> | { path?: string[] };
};

async function proxyBackend(request: NextRequest, context: RouteContext) {
  const params = await context.params;
  const pathParts = params.path || [];
  const path = pathParts.map(encodeURIComponent).join("/");
  const search = request.nextUrl.search || "";
  const backendUrl = `${BACKEND_BASE_URL.replace(/\/+$/, "")}/${path}${search}`;
  const headers = new Headers();
  copyHeader(request.headers, headers, "accept");
  copyHeader(request.headers, headers, "accept-language");
  copyHeader(request.headers, headers, "content-type");
  copyHeader(request.headers, headers, "cookie");
  copyHeader(request.headers, headers, "origin");
  copyHeader(request.headers, headers, "user-agent");
  copyHeader(request.headers, headers, "x-csrf-token");
  headers.delete("host");
  headers.delete("expect");
  headers.delete("authorization");

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

function copyHeader(source: Headers, target: Headers, name: string) {
  const value = source.get(name);
  if (value) target.set(name, value);
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

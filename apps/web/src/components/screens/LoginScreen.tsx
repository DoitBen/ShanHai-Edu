"use client";

import { useState } from "react";
import { useAppStore } from "@/lib/store";
import { DEMO_PASSWORD, isDemoMode } from "@/lib/demo-mode";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import {
  ArrowRight,
  Eye,
  EyeOff,
  Loader2,
  Mountain,
  ShieldCheck,
  UserRound,
  Waves,
} from "lucide-react";
import { cn } from "@/lib/utils";

export function LoginScreen() {
  const login = useAppStore((s) => s.login);
  const go = useAppStore((s) => s.go);
  const demoMode = isDemoMode();
  const [username, setUsername] = useState(demoMode ? "admin" : "");
  const [password, setPassword] = useState(demoMode ? DEMO_PASSWORD : "");
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = () => setError(null);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!demoMode && !username.trim()) {
      setError("请输入用户名");
      return;
    }
    setLoading(true);
    setError(null);
    setTimeout(() => {
      const res = login(username.trim(), password);
      setLoading(false);
      if (!res.ok) {
        setError(res.msg || "登录失败");
        return;
      }
      toast.success("欢迎回到山海教育工作台");
      go("dashboard");
    }, 600);
  };

  const fillDemo = (role: "admin" | "teacher") => {
    setUsername(role);
    setPassword(DEMO_PASSWORD);
    setError(null);
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#0b1d32] text-white">
      <BrandBackground />

      <div className="relative z-10 flex min-h-screen">
        <section className="relative hidden w-[58%] items-center justify-center overflow-hidden border-r border-white/[0.10] px-12 lg:flex">
          <div
            className="absolute inset-0"
            style={{
              background:
                "linear-gradient(135deg, rgba(8,19,35,.92), rgba(13,48,80,.78) 48%, rgba(14,83,76,.72))",
            }}
          />
          <BrandLineScene />

          <div className="relative z-10 flex max-w-2xl flex-col items-center text-center">
            <div
              className="flex h-28 w-28 items-center justify-center overflow-hidden rounded-2xl border border-white/[0.20] bg-white/[0.10] shadow-lift backdrop-blur-md"
              style={{ boxShadow: "0 24px 55px -24px rgba(245,158,11,.55)" }}
            >
              <img
                src="/logo.png"
                alt="山海教育"
                className="h-full w-full object-cover"
              />
            </div>

            <h1
              className="mt-8 text-5xl font-black leading-tight text-white xl:text-6xl"
              style={{
                textShadow:
                  "0 4px 34px rgba(212,175,55,.26), 0 0 72px rgba(20,184,166,.12)",
              }}
            >
              山海教育
            </h1>

            <BrandDivider />

            <p className="mt-5 text-2xl font-light text-amber-100/85">
              AI 教学资源可视化工作台
            </p>
            <p className="mt-3 max-w-xl t-body text-white/[0.62]">
              把教材解析、公开课教案、导入视频、PPT 与最终交付收束到同一条可确认、可追溯、可推进的生产链路。
            </p>

            <div className="mt-10 grid w-full max-w-lg grid-cols-3 gap-3">
              <BrandStat label="真实接口" value="API" />
              <BrandStat label="项目数据" value="实时" />
              <BrandStat label="教材库" value="已接入" />
            </div>
          </div>
        </section>

        <section className="relative flex w-full items-center justify-center px-5 py-10 sm:px-8 lg:w-[42%]">
          <div className="w-full max-w-md">
            <div className="mb-9 text-center lg:hidden">
              <div className="mx-auto flex h-24 w-24 items-center justify-center overflow-hidden rounded-2xl border border-white/[0.18] bg-white/[0.10] shadow-lift backdrop-blur-md">
                <img
                  src="/logo.png"
                  alt="山海教育"
                  className="h-full w-full object-cover"
                />
              </div>
              <h1 className="mt-5 text-4xl font-black leading-tight text-white">
                山海教育
              </h1>
              <p className="mt-2 t-body text-amber-100/75">可视化工作台</p>
            </div>

            <div className="mb-8">
              <div className="t-overline text-amber-300/80">欢迎回来</div>
              <h2 className="mt-2 text-3xl font-bold leading-tight text-white">
                登录工作台
              </h2>
              <p className="mt-2 t-body text-slate-400">
                {demoMode
                  ? "登录以访问山海教育生产指挥台。"
                  : "当前为真实 API 模式，登录后将读取后端项目数据。"}
              </p>
            </div>

            <form onSubmit={submit} className="space-y-5" noValidate>
              <div className="space-y-2">
                <Label htmlFor="username" className="t-body font-medium text-slate-300">
                  用户名
                </Label>
                <Input
                  id="username"
                  value={username}
                  onChange={(e) => {
                    setUsername(e.target.value);
                    clearError();
                  }}
                  placeholder="请输入用户名"
                  autoComplete="username"
                  autoFocus
                  className="h-12 rounded-lg border-white/[0.12] bg-white/[0.06] text-base text-white placeholder:text-slate-500 focus-visible:ring-amber-500/[0.30]"
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password" className="t-body font-medium text-slate-300">
                    密码
                  </Label>
                  {demoMode && (
                    <button
                      type="button"
                      className="rounded t-caption text-slate-400 transition-colors hover:text-amber-300 focus-ring"
                      onClick={() => toast.info("演示环境暂不支持找回密码")}
                    >
                      忘记密码？
                    </button>
                  )}
                </div>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPwd ? "text" : "password"}
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      clearError();
                    }}
                    placeholder={demoMode ? "请输入密码" : "真实 API 模式可留空"}
                    autoComplete="current-password"
                    className="h-12 rounded-lg border-white/[0.12] bg-white/[0.06] pr-12 text-base text-white placeholder:text-slate-500 focus-visible:ring-amber-500/[0.30]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPwd((v) => !v)}
                    className="absolute right-2 top-1/2 inline-flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-md text-slate-400 transition-colors hover:bg-white/[0.08] hover:text-amber-300 focus-ring"
                    aria-label={showPwd ? "隐藏密码" : "显示密码"}
                  >
                    {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {error && (
                <div className="rounded-lg border border-red-300/20 bg-red-500/10 px-3 py-2.5 t-body text-red-100">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                size="lg"
                disabled={loading}
                className="h-12 w-full gap-2 rounded-lg border-0 bg-[linear-gradient(90deg,#d97706,#f59e0b_52%,#eab308)] text-base font-semibold text-white shadow-[0_14px_32px_-18px_rgba(245,158,11,.75)] transition-transform hover:scale-[1.01] hover:bg-[linear-gradient(90deg,#d97706,#f59e0b_52%,#eab308)] active:scale-[0.99]"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    登录中...
                  </>
                ) : (
                  <>
                    登录
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </Button>
            </form>

            {demoMode && (
              <div className="mt-8 rounded-lg border border-white/[0.10] bg-white/[0.045] p-4 backdrop-blur-sm">
                <div className="mb-3 t-caption font-medium text-slate-400">
                  演示账号
                </div>
                <div className="grid gap-3">
                  <DemoAccountButton
                    label="管理员"
                    desc="全部功能"
                    credential={`admin / ${DEMO_PASSWORD}`}
                    icon={<ShieldCheck className="h-4 w-4" />}
                    active={username === "admin"}
                    onClick={() => fillDemo("admin")}
                  />
                  <DemoAccountButton
                    label="教师"
                    desc="业务流程"
                    credential={`teacher / ${DEMO_PASSWORD}`}
                    icon={<UserRound className="h-4 w-4" />}
                    active={username === "teacher"}
                    onClick={() => fillDemo("teacher")}
                  />
                </div>
              </div>
            )}

            <p className="mt-10 text-center t-caption text-slate-500">
              山海教育工作台 v1.0 · 2026
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}

function DemoAccountButton({
  label,
  desc,
  credential,
  icon,
  active,
  onClick,
}: {
  label: string;
  desc: string;
  credential: string;
  icon: React.ReactNode;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex min-h-12 w-full items-center justify-between gap-3 rounded-lg border px-3 py-2 text-left transition-colors focus-ring",
        active
          ? "border-amber-400/45 bg-amber-400/10"
          : "border-white/[0.08] bg-white/[0.035] hover:bg-white/[0.06]"
      )}
    >
      <span className="flex min-w-0 items-center gap-2.5">
        <span
          className={cn(
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-md",
            active ? "bg-amber-400/[0.16] text-amber-300" : "bg-white/[0.06] text-slate-400"
          )}
        >
          {icon}
        </span>
        <span className="min-w-0">
          <span className="block t-body font-medium text-slate-100">{label}</span>
          <span className="block t-caption text-slate-500">{desc}</span>
        </span>
      </span>
      <code className="shrink-0 rounded-md bg-white/[0.06] px-2 py-1 font-mono text-[0.7rem] text-amber-300/90">
        {credential}
      </code>
    </button>
  );
}

function BrandStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-white/[0.12] bg-white/[0.055] px-4 py-3 backdrop-blur-sm">
      <div className="text-2xl font-semibold leading-none text-white">{value}</div>
      <div className="mt-1.5 t-caption text-white/[0.56]">{label}</div>
    </div>
  );
}

function BrandDivider() {
  return (
    <div className="mt-6 flex items-center justify-center gap-4">
      <span
        className="h-px w-16"
        style={{
          background:
            "linear-gradient(90deg, transparent, rgba(251,191,36,.64))",
        }}
      />
      <Mountain className="h-5 w-5 text-amber-300/80" />
      <span className="h-px w-8 bg-amber-300/40" />
      <Waves className="h-5 w-5 text-teal-300/80" />
      <span
        className="h-px w-16"
        style={{
          background:
            "linear-gradient(270deg, transparent, rgba(45,212,191,.64))",
        }}
      />
    </div>
  );
}

function BrandBackground() {
  return (
    <div className="pointer-events-none absolute inset-0" aria-hidden>
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: "url('/login-bg.png')",
          backgroundPosition: "center",
          backgroundSize: "cover",
        }}
      />
      <div
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(90deg, rgba(5,14,28,.22) 0%, rgba(5,14,28,.38) 48%, rgba(5,14,28,.78) 100%)",
        }}
      />
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse at 18% 24%, rgba(217,119,6,.16), transparent 36%), radial-gradient(ellipse at 82% 88%, rgba(20,184,166,.12), transparent 38%)",
        }}
      />
    </div>
  );
}

function BrandLineScene() {
  return (
    <svg
      className="pointer-events-none absolute inset-0 h-full w-full opacity-[0.14]"
      viewBox="0 0 900 700"
      preserveAspectRatio="xMidYMid slice"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <path
        d="M90 438 L210 308 L276 340 L394 210 L480 320 L586 244 L804 452"
        stroke="rgba(255,255,255,.72)"
        strokeWidth="2"
      />
      <path
        d="M84 498 Q238 438 396 494 Q554 552 816 486"
        stroke="rgba(45,212,191,.72)"
        strokeWidth="2"
      />
      <path
        d="M126 542 Q276 484 430 538 Q586 592 790 530"
        stroke="rgba(251,191,36,.52)"
        strokeWidth="2"
      />
      <path
        d="M330 170 Q486 72 652 156 Q742 202 806 314"
        stroke="rgba(251,191,36,.78)"
        strokeWidth="3"
      />
      <path
        d="M708 154 L722 190 L760 204 L722 218 L708 254 L694 218 L656 204 L694 190 Z"
        fill="rgba(251,191,36,.72)"
      />
    </svg>
  );
}

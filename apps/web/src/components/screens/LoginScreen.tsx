"use client";

import { useState } from "react";
import { useAppStore } from "@/lib/store";
import { Logo, LogoMark } from "@/components/brand/Logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { Eye, EyeOff, ArrowRight, ShieldCheck, UserRound } from "lucide-react";
import { cn } from "@/lib/utils";

export function LoginScreen() {
  const login = useAppStore((s) => s.login);
  const go = useAppStore((s) => s.go);
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("shanhai2026");
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = () => setError(null);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
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
    setPassword("shanhai2026");
    setError(null);
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      {/* 背景层：极淡山海纹 + 左侧深青灰品牌区 */}
      <div className="pointer-events-none absolute inset-0 bg-topo" />
      <div className="pointer-events-none absolute inset-0 bg-grid opacity-40" />

      <div className="relative grid min-h-screen lg:grid-cols-[1.05fr_1fr]">
        {/* 左：品牌叙事 */}
        <section
          className="relative hidden flex-col justify-between overflow-hidden p-12 lg:flex"
          style={{ backgroundColor: "#2d4356", color: "#f7f6f1" }}
        >
          <div className="pointer-events-none absolute inset-0 opacity-[0.07]">
            <BrandScene />
          </div>
          <div className="relative">
            <Logo size={44} subline="AI 幼教 ProMax" wordmarkClassName="text-[#f7f6f1]" />
          </div>

          <div className="relative max-w-md">
            <div className="t-overline" style={{ color: "rgba(247,246,241,0.6)" }}>
              AI 教学资源生产指挥台
            </div>
            <h1 className="mt-4 text-[2.25rem] font-semibold leading-[1.2] tracking-[-0.01em]">
              从教材到课堂
              <br />
              一站式可视化生产
            </h1>
            <p className="mt-5 t-body" style={{ color: "rgba(247,246,241,0.75)" }}>
              统一管理教材解析、公开课教案、导入视频、PPT 与最终交付的全流程。
              克制、专业、可控——让每一份教学资源都可被查看、修改、确认与推进。
            </p>
            <div className="mt-8 flex items-center gap-6" style={{ color: "rgba(247,246,241,0.7)" }}>
              <Stat label="工作流节点" value="14" />
              <span className="h-8 w-px" style={{ backgroundColor: "rgba(247,246,241,0.15)" }} />
              <Stat label="演示项目" value="3" />
              <span className="h-8 w-px" style={{ backgroundColor: "rgba(247,246,241,0.15)" }} />
              <Stat label="视频方案" value="9" />
            </div>
          </div>

          <div className="relative t-caption" style={{ color: "rgba(247,246,241,0.5)" }}>
            山海教育 · 2026 · 第一阶段演示版
          </div>
        </section>

        {/* 右：登录表单 */}
        <section className="flex items-center justify-center px-6 py-12 sm:px-12">
          <div className="w-full max-w-sm">
            {/* 移动端品牌头 */}
            <div className="mb-10 flex items-center justify-center lg:hidden">
              <div className="flex flex-col items-center gap-3 text-center">
                <LogoMark size={56} />
                <div>
                  <div className="t-module">山海教育</div>
                  <div className="t-caption mt-1 text-muted-foreground">
                    AI 幼教 ProMax 可视化工作台
                  </div>
                </div>
              </div>
            </div>

            <div className="mb-8">
              <h2 className="t-title">登录工作台</h2>
              <p className="mt-2 t-body text-muted-foreground">
                请输入账号密码进入生产指挥台。
              </p>
            </div>

            <form onSubmit={submit} className="space-y-5" noValidate>
              <div className="space-y-2">
                <Label htmlFor="username" className="t-body font-medium">
                  账号
                </Label>
                <Input
                  id="username"
                  value={username}
                  onChange={(e) => {
                    setUsername(e.target.value);
                    clearError();
                  }}
                  placeholder="请输入账号"
                  autoComplete="username"
                  className="h-11 bg-card"
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password" className="t-body font-medium">
                    密码
                  </Label>
                  <button
                    type="button"
                    className="t-caption text-muted-foreground transition-colors hover:text-foreground focus-ring"
                    onClick={() => toast.info("演示环境暂不支持找回密码")}
                  >
                    忘记密码？
                  </button>
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
                    placeholder="请输入密码"
                    autoComplete="current-password"
                    className="h-11 bg-card pr-11"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPwd((v) => !v)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 inline-flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:bg-muted focus-ring"
                    aria-label={showPwd ? "隐藏密码" : "显示密码"}
                  >
                    {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {error && (
                <div className="rounded-lg border border-destructive/25 bg-destructive/5 px-3 py-2.5 t-body text-destructive">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                size="lg"
                disabled={loading}
                className="h-11 w-full gap-2 text-[0.95rem]"
              >
                {loading ? "登录中…" : "进入工作台"}
                {!loading && <ArrowRight className="h-4 w-4" />}
              </Button>
            </form>

            <div className="my-7 flex items-center gap-4">
              <Separator className="flex-1" />
              <span className="t-caption text-muted-foreground">演示账号</span>
              <Separator className="flex-1" />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <DemoAccountButton
                role="admin"
                label="管理员"
                desc="全部功能"
                icon={<ShieldCheck className="h-4 w-4" />}
                active={username === "admin"}
                onClick={() => fillDemo("admin")}
              />
              <DemoAccountButton
                role="teacher"
                label="教师"
                desc="业务流程"
                icon={<UserRound className="h-4 w-4" />}
                active={username === "teacher"}
                onClick={() => fillDemo("teacher")}
              />
            </div>

            <p className="mt-8 t-caption text-center text-muted-foreground">
              演示账号：admin / shanhai2026
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-2xl font-semibold leading-none">{value}</div>
      <div className="mt-1.5 t-caption" style={{ color: "rgba(247,246,241,0.6)" }}>{label}</div>
    </div>
  );
}

function DemoAccountButton({
  label,
  desc,
  icon,
  active,
  onClick,
}: {
  role: string;
  label: string;
  desc: string;
  icon: React.ReactNode;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex flex-col items-start gap-1 rounded-lg border bg-card p-3 text-left transition-all hover:shadow-soft focus-ring",
        active ? "border-primary/40 ring-1 ring-primary/20" : "border-border"
      )}
    >
      <span className="flex items-center gap-1.5 text-muted-foreground">
        {icon}
        <span className="t-caption">{desc}</span>
      </span>
      <span className="t-body font-medium">{label}</span>
    </button>
  );
}

/** 品牌场景：极简山海线条装饰，纯 SVG 本地 */
function BrandScene() {
  return (
    <svg
      width="100%"
      height="100%"
      viewBox="0 0 600 600"
      preserveAspectRatio="xMidYMid slice"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      {/* 远山 */}
      <path
        d="M0 420 L80 340 L160 390 L240 300 L320 360 L400 280 L480 350 L600 300 L600 600 L0 600 Z"
        stroke="currentColor"
        strokeWidth="1"
        fill="none"
        style={{ color: "#f7f6f1" }}
      />
      {/* 近山 */}
      <path
        d="M0 480 L120 400 L220 450 L340 380 L460 440 L600 400 L600 600 L0 600 Z"
        stroke="currentColor"
        strokeWidth="1.2"
        fill="none"
        style={{ color: "#f7f6f1" }}
      />
      {/* 海浪 */}
      <path
        d="M0 520 Q150 500 300 520 Q450 540 600 520"
        stroke="currentColor"
        strokeWidth="1"
        fill="none"
        style={{ color: "#f7f6f1" }}
      />
      <path
        d="M0 545 Q150 525 300 545 Q450 565 600 545"
        stroke="currentColor"
        strokeWidth="1"
        fill="none"
        style={{ color: "#f7f6f1" }}
      />
      {/* 星 */}
      <circle cx="470" cy="160" r="2" fill="#c9a36a" />
      <circle cx="510" cy="120" r="1.4" fill="#c9a36a" />
      <circle cx="430" cy="110" r="1" fill="#c9a36a" />
    </svg>
  );
}

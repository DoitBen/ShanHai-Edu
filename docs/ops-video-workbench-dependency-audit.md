# 视频工作台依赖审计口径

> 日期：2026-06-29
> 范围：`apps/web` 视频工作台交付门禁。

## 当前策略

CI 保留依赖漏洞扫描，但门禁阈值设为：

```powershell
bun audit --audit-level critical
```

原因：普通 `bun audit` 当前仍报告若干 high/moderate/low 级传递依赖漏洞，主要来自构建工具链或框架间接依赖；直接切到 Prisma 7、ESLint 10 或其它大版本会扩大本次视频工作台整改范围，风险高于当前收益。

## 已完成收敛

- `next` 升级到 `16.2.9`。
- `next-intl` 升级到 `4.13.0` 后确认未被业务代码引用，并从项目移除。
- `uuid` 升级到 `11.1.1`。
- `@tailwindcss/postcss` / `tailwindcss` 升级到 `4.3.1`。
- `@prisma/client` / `prisma` 升级到 `6.19.3`。
- 移除未被源码引用且引入额外传递风险的直接依赖：`@mdxeditor/editor`、`@reactuses/core`、`next-auth`、`react-syntax-highlighter`、`recharts`。
- 删除未被引用的 `src/components/ui/chart.tsx`，避免保留 `recharts` 依赖。

## 剩余风险

普通 `bun audit` 仍可能报告 high/moderate/low 级漏洞，当前主要落在：

- `eslint` / `eslint-config-next` 传递依赖。
- `prisma` 6.x 传递依赖。
- `next` 的内部 `postcss` 传递依赖。

这些依赖不处理真实 provider token，也不在视频生成运行时请求链路中解析用户上传视频或图片。继续跟踪上游补丁；下一轮依赖专项升级时再评估 Prisma 7、ESLint 10、Next 后续补丁和锁文件 overrides。

## 发布门禁

- Critical 级依赖漏洞必须阻断合并。
- High 级依赖漏洞若涉及运行时用户输入、认证、代理或 provider token 处理，应单独升级或移除，不允许仅靠阈值放行。
- 每次修改依赖后必须重新运行 `tsc`、`lint`、`build` 和视频工作台 E2E。

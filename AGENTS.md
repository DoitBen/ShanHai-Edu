# 项目级 Codex 工作规则

> 本文件约束当前项目 `ShanHaiEdu`。若与用户当前明确指令冲突，以用户当前指令为准；若与平台、安全或工具权限限制冲突，以平台和工具限制为准。

## 项目概况

- 项目名称：ShanHaiEdu
- 项目类型：Next.js Web 应用
- 技术栈：Next.js 16、React 19、TypeScript、Tailwind CSS 4、shadcn/Radix UI、Prisma、Bun
- 主要入口：`apps\web\src\app\page.tsx`
- 主要输出物：本地 Web 站点与 Next.js 构建产物

## 运行与验证

- 开发目录：`apps\web`
- 开发启动：`bun run dev`
- 构建验证：`bun run build`
- 代码检查：`bun run lint`
- 数据库相关命令：`bun run db:generate`、`bun run db:push`、`bun run db:migrate`、`bun run db:reset`

## 工作规则

- 默认轻量模式，优先做只读分析和小范围外科式改动。
- 修改前先确认目标、关键假设和可验证成功标准；多种合理解释并存时先说明取舍。
- 不顺手重构、不批量格式化、不改名无关文件。
- 涉及数据库、环境变量、外部写入、部署、批量删除或生产数据时，先给计划并等待确认。
- 读取 `.env`、数据库配置或账号密钥时仅限任务确实需要，回复和提交信息中不得明文展示敏感值。
- 前端 UI 分析必须结合实际浏览器渲染证据，不能只从源码判断视觉质量。
- 验证命令按风险最小化执行；不要一上来跑全量重型测试。

## 关键风险

- `apps\web\.env` 存在本地环境配置，处理时注意脱敏。
- `apps\web\prisma` 与数据库命令可能产生外部状态变化，默认只读分析不执行迁移或重置。
- `apps\web\.next`、`node_modules`、日志文件属于生成物，除非用户明确要求，不纳入代码结论或提交范围。

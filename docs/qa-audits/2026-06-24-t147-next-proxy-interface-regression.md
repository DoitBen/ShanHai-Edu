# T147 Next.js API 代理与前端接口适配回归

日期：2026-06-24
角色：测试工程师子智能体 B
范围：Next.js API 代理、前端 mapper/client/workspace/admin 契约、client-visible secret 扫描
证据目录：`docs\qa-audits\t147-next-proxy-evidence\20260624-153142`

## 结论

【通过，但 live proxy 未完成】。

T147 指定的 5 个前端契约测试、TypeScript 类型检查和 client-visible secret 扫描均退出 0。静态契约确认：

- `api-client` 默认走 `/api/backend` Next 代理，不暴露公开后端 origin 环境变量。
- `/api/backend/[...path]` 代理在服务端读取 `BACKEND_API_TOKEN` 并以 Bearer 形式转发给 FastAPI。
- 代理会删除 multipart 相关的 `Expect` header。
- admin 后端路径存在本地 admin cookie 门禁，非 admin 本地态隐藏为 404。
- workspace、new project、admin rules 和 API mapper 契约均满足当前前端接口适配要求。

本轮没有读取真实密钥，没有跑真实 provider，没有修改业务代码，也没有替代 T148 浏览器验收。

## 命令与退出码

工作目录：`apps\web`
环境：`VITEST_MAX_WORKERS=2`

| 命令 | 退出码 | 证据 |
|---|---:|---|
| `bun src\lib\api-proxy-contract.test.ts` | 0 | `api-proxy-contract.out.txt` / `api-proxy-contract.err.txt` |
| `bun src\lib\api-mappers-contract.test.ts` | 0 | `api-mappers-contract.out.txt` / `api-mappers-contract.err.txt` |
| `bun src\lib\admin-rules-contract.test.ts` | 0 | `admin-rules-contract.out.txt` / `admin-rules-contract.err.txt` |
| `bun src\lib\workspace-user-flow-contract.test.ts` | 0 | `workspace-user-flow-contract.out.txt` / `workspace-user-flow-contract.err.txt` |
| `bun src\lib\new-project-user-flow-contract.test.ts` | 0 | `new-project-user-flow-contract.out.txt` / `new-project-user-flow-contract.err.txt` |
| `bunx tsc --noEmit --pretty false` | 0 | `tsc-noemit.out.txt` / `tsc-noemit.err.txt` |
| `bun run scan:client-secrets` | 0 | `scan-client-secrets.out.txt` / `scan-client-secrets.err.txt` |

汇总文件：`command-results.json`。

## 覆盖矩阵

| 验收点 | 结果 | 证据说明 |
|---|---|---|
| `/api/backend/[...path]` 代理存在并作为前端默认 API 入口 | 通过 | `api-proxy-contract` 检查 `api-client.ts` 默认 `API_BASE="/api/backend"` |
| 服务端 token 注入 | 通过 | `api-proxy-contract` 检查代理服务端读取 `BACKEND_API_TOKEN` 并设置 Bearer header |
| 浏览器不可见 `BACKEND_API_TOKEN` | 通过 | `scan:client-secrets` 退出 0，输出 `Client-visible secret scan passed.`；未发现 client-visible bundle/public 资源包含当前环境哨兵或公开密钥变量名 |
| admin cookie 门禁 | 通过 | `admin-rules-contract` 检查 admin path 判定、`shanhai_auth` 角色 cookie 和非 admin 404 隐藏逻辑 |
| multipart `Expect` header | 通过 | `api-proxy-contract` 检查代理删除 `expect` header |
| 文件流下载代理 | 部分通过 | 源码确认代理直接透传 `response.body/status/statusText/headers`；live proxy 未完成，未采集实际二进制响应 |
| mapper 适配 | 通过 | `api-mappers-contract` 覆盖 manifest、final delivery artifact、skipped 状态、项目创建 payload、教材解析结果和知识点资产映射 |
| workspace 用户态契约 | 通过 | `workspace-user-flow-contract` 覆盖 `/workspace` client、store 缓存、7 步用户态、PPT/视频子门禁、普通区红线文本静态扫描 |
| new project 用户流契约 | 通过 | `new-project-user-flow-contract` 覆盖教材库下拉、导入/切分/解析三段式、知识点选择、PPT 模板和普通 UI 隐藏输出路径/安全模式 |
| admin rules client 契约 | 通过 | `admin-rules-contract` 覆盖规则列表、版本创建、启用、回滚和 workflow graph client |
| TypeScript 类型检查 | 通过 | `tsc-noemit` 退出 0 |

## live proxy 说明

本轮尝试启动隔离 mock 后端 `8147` 和 Web `3147` 做 live proxy 实证，但 Next dev 未能取得 `apps\web\.next\dev\lock`，日志显示已有其他 Next dev 实例占用开发锁：

- `live-proxy-web.err.log`
- `live-proxy-web.log`
- `live-proxy-processes.json`
- `live-proxy-cleanup.json`

因此本轮没有完成真实 HTTP 层的 GET/POST/PATCH/DELETE 转发、admin 404、文件流 `content-type` 和 multipart header 实测。已清理本轮启动尝试，没有留下 T147 mock/Next 进程。

## 失败清单与缺陷分级

| 级别 | 问题 | 影响 | 建议 |
|---|---|---|---|
| P2 一般 | live proxy 未完成，缺少 HTTP 运行态证据 | 静态契约已覆盖核心源码约束，但文件流和方法转发未被真实请求验证 | 等当前 Next dev 锁释放后，用独立端口 `8147/3147` 补跑 live proxy smoke；不阻塞 T147 静态契约通过，但应作为 T148 前的剩余风险 |

本轮未发现 P0/P1。

## 剩余风险

- 本报告不能替代 T148 浏览器真实 API 串联验收。
- 未实测真实 provider、生产 RBAC/JWT/session、多浏览器或容器冷启动。
- `scan:client-secrets` 只扫描当前已存在的 client-visible 静态产物目录和 `public`，不是生产构建后完整审计；如后续重新构建，应重新运行扫描。
- live proxy 未完成，因此代理二进制流、header 透传和 HTTP 方法转发仍建议补一次运行态 smoke。

## 后续建议

T148 可继续执行，但报告回收时应保留一个低风险补测项：在没有 Next dev 锁冲突时补跑 T147 live proxy smoke，专门验证代理转发、admin 404、服务端 token 注入、Expect 删除和文件流下载。

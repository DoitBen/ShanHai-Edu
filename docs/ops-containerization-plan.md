# ShanHaiEdu 本地/内网最小容器化部署草案

> 任务 ID：T008
> 角色席位：运维/部署专题子智能体
> 日期：2026-06-24
> 范围：在 T006 后端运行契约基础上，补 Web/API 本地与内网最小容器化部署草案。本文只给方案和配置草案，不读取、不记录、不打印真实密钥，不执行 `docker build` 或 `docker compose up`。

## 1. 结论

当前推荐路线是 `docker-compose` / 内网最小部署优先，Cloud Run 后置。最小拓扑为单台主机上的 `web`、`api` 两个容器，共享一个 Docker network，API 挂载持久 `storage` volume，Web 通过服务端代理访问 API。

本轮只输出文档草案，不创建实际 Dockerfile、compose 或 `.dockerignore` 文件。原因是当前仓库未发现正式容器化约定，且 T009 还未做新人冷启动验收；直接提交未经验证的配置文件容易被误认为可发布资产。T009 可按本文复制草案到临时分支或专门部署目录验证，通过后再沉淀为正式配置。

## 2. 最小部署拓扑

### 服务与端口

| 服务 | 容器职责 | 容器端口 | 主机暴露建议 | 健康检查 |
|---|---|---:|---:|---|
| `web` | Next.js standalone Web 服务，同源代理 `/api/backend/*` 到 API | `3000` | `3000` 或经 Caddy/Nginx 暴露 `80/443` | `GET /` 或专门 Web smoke |
| `api` | FastAPI 后端、workflow、provider 服务端调用、storage 写入 | `8000` | 内网可暴露 `8000`；公网不建议直接暴露 | `GET /health` 仅做 liveness |
| `storage` | Docker named volume 或主机 bind mount | 不适用 | 不直接暴露 | readiness smoke 检查可写 |

### 网络

- 使用单个 bridge network，例如 `shanhaiedu_internal`。
- `web` 通过 `http://api:8000` 访问 API，不把后端 token 放入浏览器环境。
- 外部用户只访问 `web` 或反代入口；API 端口仅限内网调试或由防火墙限制来源。

### Storage volume

推荐挂载：

```text
api:/app/storage
```

并设置：

```text
STORAGE_ROOT=/app/storage
WORKFLOW_ROOT=workflow
CAPABILITIES_PATH=docs/api-research/octo-video/capabilities.json
```

storage 内包含项目 SQLite、上传文件、生成资产、任务产物和项目级日志。备份恢复必须整体覆盖 `project.db`、WAL/SHM、uploads、assets、clips、audio、outputs、exports、logs、`control_plane.db`、`prompt_registry.db`。

## 3. Web Dockerfile 草案

> 草案路径建议：`apps\web\Dockerfile`。本轮不创建实际文件。

```dockerfile
# syntax=docker/dockerfile:1

FROM oven/bun:1 AS deps
WORKDIR /app/apps/web
COPY apps/web/package.json apps/web/bun.lock* ./
RUN bun install --frozen-lockfile

FROM deps AS builder
WORKDIR /app
COPY apps/web ./apps/web
WORKDIR /app/apps/web
ENV NEXT_TELEMETRY_DISABLED=1
RUN bun run build

FROM oven/bun:1 AS runner
WORKDIR /app/apps/web
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./.next/static
COPY --from=builder /app/apps/web/public ./public
EXPOSE 3000
CMD ["bun", "server.js"]
```

注意：

- `NEXT_PUBLIC_DEMO_MODE=false` 属于前端公开配置，可以通过运行环境注入。
- `BACKEND_API_BASE_URL=http://api:8000` 和 `BACKEND_API_TOKEN` 必须只存在于 Next 服务端运行环境，不得使用 `NEXT_PUBLIC_*`。
- Next `next.config.ts` 已启用 `output: "standalone"`；当前 `typescript.ignoreBuildErrors=true` 是前端质量风险，容器化不改变该事实。

## 4. API Dockerfile 草案

> 草案路径建议：`apps\api\Dockerfile` 或根目录 `Dockerfile.api`。本轮不创建实际文件。

```dockerfile
# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt ./apps/api/requirements.txt
RUN python -m pip install --no-cache-dir --upgrade pip \
  && python -m pip install --no-cache-dir -r apps/api/requirements.txt

COPY apps/api ./apps/api
COPY workflow ./workflow
COPY docs/api-research ./docs/api-research

ENV STORAGE_ROOT=/app/storage
ENV WORKFLOW_ROOT=workflow
ENV CAPABILITIES_PATH=docs/api-research/octo-video/capabilities.json
ENV PROVIDER_MODE=fake
ENV VIDEO_PROVIDER_MODE=placeholder
ENV IMAGE_PROVIDER_MODE=placeholder
ENV TTS_PROVIDER_MODE=placeholder

RUN mkdir -p /app/storage
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()" || exit 1

CMD ["python", "-m", "uvicorn", "apps.api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### ffmpeg 建议

默认草案不把 `ffmpeg` 放进 API 镜像，只保证 fake/placeholder 链路和文本链路最小运行。

如果 T009 或后续真实视频验收要求容器内完成多 clip 合成，应改为安装 `ffmpeg`：

```dockerfile
RUN apt-get update \
  && apt-get install -y --no-install-recommends curl ca-certificates ffmpeg \
  && rm -rf /var/lib/apt/lists/*
```

风险与取舍：

- 安装 `ffmpeg` 会增大镜像体积和 CVE 扫描面。
- 不安装 `ffmpeg` 时，真实 `final_video` 多 clip 合成不可用；后端应写入 `FINAL_VIDEO_COMPOSE_FAILED`，不得伪造成片成功。
- 当前后端从 `PATH` 查找 `ffmpeg`，`FFMPEG_PATH` 仍只是运维预留变量，不能假设该变量已经被代码消费。

## 5. compose 草案

> 草案路径建议：`docker-compose.yml`。本轮不创建实际文件。

```yaml
services:
  api:
    build:
      context: .
      dockerfile: apps/api/Dockerfile
    image: shanhaiedu-api:local
    restart: unless-stopped
    environment:
      STORAGE_ROOT: /app/storage
      WORKFLOW_ROOT: workflow
      CAPABILITIES_PATH: docs/api-research/octo-video/capabilities.json
      CORS_ORIGINS: http://localhost:3000,http://127.0.0.1:3000
      PROVIDER_MODE: fake
      VIDEO_PROVIDER_MODE: placeholder
      IMAGE_PROVIDER_MODE: placeholder
      TTS_PROVIDER_MODE: placeholder
      BACKEND_API_TOKEN_FILE: /run/secrets/backend_api_token
    secrets:
      - backend_api_token
    volumes:
      - shanhaiedu_storage:/app/storage
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 20s

  web:
    build:
      context: .
      dockerfile: apps/web/Dockerfile
    image: shanhaiedu-web:local
    restart: unless-stopped
    depends_on:
      api:
        condition: service_healthy
    environment:
      NODE_ENV: production
      NEXT_PUBLIC_DEMO_MODE: "false"
      BACKEND_API_BASE_URL: http://api:8000
      BACKEND_API_TOKEN_FILE: /run/secrets/backend_api_token
    secrets:
      - backend_api_token
    ports:
      - "3000:3000"

volumes:
  shanhaiedu_storage:

secrets:
  backend_api_token:
    file: ./secrets/backend_api_token.txt
```

### 当前 compose 草案的重要风险

- 当前代码是否支持 `*_FILE` 读取需要 T009 验证；如果暂不支持，应改为由部署入口脚本读取 secret 文件并导出 `BACKEND_API_TOKEN`，或使用 compose 环境变量注入。
- 不应把 `secrets\backend_api_token.txt` 提交到 git；该文件只在部署主机本地存在。
- `depends_on.condition=service_healthy` 只说明 API liveness 可达，不代表 provider/storage readiness。

## 6. `.dockerignore` 草案

> 草案路径建议：仓库根 `.dockerignore`。本轮不创建实际文件。

```gitignore
.git
.gitignore
.dockerignore

# env and secrets
.env
.env.*
apps/api/.env
apps/api/.env.*
apps/web/.env
apps/web/.env.*
skills/imagegen-myself/.env.local
secrets/

# dependencies and build outputs
node_modules/
apps/web/node_modules/
apps/web/.next/
apps/web/dist/
dist/
build/
.venv/
venv/
env/
__pycache__/
*.py[cod]
.pytest_cache/

# runtime data and logs
storage/
storage-*/
projects/
logs/
*.log
*.db
*.db-journal
*.db-wal
*.db-shm

# provider outputs and QA generated media
output/imagegen/
docs/qa-audits/imagegen-real-smoke/
docs/qa-audits/octo-real-video-smoke/
docs/qa-audits/fullchain-smoke-evidence/
docs/qa-audits/**/*real*.png
docs/qa-audits/**/*real*.jpg
docs/qa-audits/**/*real*.jpeg
docs/qa-audits/**/*real*.webp
docs/qa-audits/**/*.mp4
docs/qa-audits/**/*.pptx

# local artifacts
graphify-out/
apps/web/graphify-out/
apps/web/upload/
apps/web/download/
tmp/
.tmp/
```

关键点：

- `.dockerignore` 必须比 `.gitignore` 更严格，避免把本地真实 `.env`、storage、logs、SQLite、真实 provider 产物、技能私有 env 打进镜像上下文。
- `docs` 下允许提交的 PDF/PPTX 白名单不应自动进入 Docker build context，除非某个镜像运行时确实需要。

## 7. 密钥注入策略

只列变量名和策略，不列真实值。

### 必须后端服务端注入

- `BACKEND_API_TOKEN`
- `DEEPSEEK_API_KEY`
- `MINIMAX_API_KEY` / `MINMAX_API_KEY`
- `IMAGEGEN_MYSELF_API_KEY`
- `IMAGEGEN_MYSELF_PRIMARY_API_KEY`
- `NEWAPI_API_KEY`
- `PINAI_API_KEY`
- `AIRCODE_API_KEY`
- `OCTO_API_KEY`

### 可按环境注入但不得硬编码

- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_MODEL`
- `MINIMAX_BASE_URL` / `MINMAX_BASE_URL`
- `MINMAX_TEXT_MODEL`
- `IMAGEGEN_MYSELF_BASE_URL`
- `IMAGEGEN_MYSELF_PRIMARY_BASE_URL`
- `NEWAPI_BASE_URL`
- `PINAI_BASE_URL`
- `IMAGEGEN_MODEL` / `NEWAPI_IMAGE_MODEL` / `IMAGEGEN_MYSELF_MODEL`
- `OCTO_BASE_URL`
- `OCTO_VIDEO_PROVIDER`
- `VIDEO_MODEL`
- `OMNI_DEFAULT_MODEL` / `NEWAPI_DEFAULT_MODEL`
- `OMNI_DEFAULT_SIZE` / `NEWAPI_DEFAULT_SIZE`
- `MINIMAX_TTS_MODEL` / `MINMAX_TTS_MODEL`
- `MINIMAX_TTS_VOICE_ID`

### 注入方式

- 本地开发：使用 shell 环境变量或未提交的 `apps\api\.env`，不要把真实值写入文档。
- 内网 compose：优先使用 Docker secrets 或部署主机私有 env file。若当前代码不支持 `*_FILE`，使用 entrypoint 转换为进程环境变量，或暂用 `env_file` 但确保文件在 `.gitignore` 与 `.dockerignore` 内。
- Web：`BACKEND_API_TOKEN` 只给 Next 服务端代理使用，不得进入 `NEXT_PUBLIC_*`。
- 镜像：禁止把任何密钥 baked into image；禁止复制 `skills\imagegen-myself\.env.local`。

## 8. 健康检查与 readiness

`GET /health` 只能做 liveness，表示 API 进程可响应且 workflow 配置对象已加载。

它不能证明：

- storage 可写。
- SQLite 可创建或恢复。
- `BACKEND_API_TOKEN` 已配置。
- provider 密钥、额度、模型权限和网络连通性正常。
- `ffmpeg` 可用。
- CORS 与当前 Web 端口匹配。

T009 readiness smoke 建议拆成：

1. `GET /health` 返回 200。
2. 用临时 storage 创建项目，确认项目目录和 `project.db` 可写。
3. `PROVIDER_MODE=fake` + placeholder 模式跑创建项目、上传教材文本、`textbook_parse/generate`、approve 的最小链路。
4. 配置 `BACKEND_API_TOKEN` 后验证无 token 为 401、错误 token 为 403。
5. 按目标环境单独执行 provider smoke：真实文本、真实图片、真实视频、TTS 不混入默认 E2E。
6. 如果启用真实多 clip 合成，检查容器内 `ffmpeg -version` 和失败时 `FINAL_VIDEO_COMPOSE_FAILED` 行为。

## 9. 日志策略

最小内网部署建议：

- 容器进程日志输出到 stdout/stderr，由 Docker logging driver 收集。
- API 项目级事件与错误日志继续写入 `STORAGE_ROOT\projects\...\logs\`，跟随 storage 一起备份。
- Web 当前 `bun run start` 会写 `server.log`，容器内建议直接运行 standalone server，使日志进入 stdout/stderr；如果保留 `server.log`，需挂载或轮转。
- Docker 默认 `json-file` 建议配置 `max-size` 与 `max-file`，例如 `10m` 和 `5`。

compose 可选日志片段：

```yaml
logging:
  driver: json-file
  options:
    max-size: "10m"
    max-file: "5"
```

禁止日志打印完整 `Authorization`、API key、token、secret、provider 原始密钥。Provider 错误只允许脱敏摘要。

## 10. 备份与恢复

### 备份对象

- `STORAGE_ROOT\projects\**\project.db`
- `*.db-wal`、`*.db-shm`、`*.db-journal`
- `uploads`、`assets`、`clips`、`audio`、`outputs`、`exports`
- `logs`
- `control_plane.db`
- `prompt_registry.db`
- 当前部署使用的非密钥配置模板、镜像 tag、compose 文件版本

### 备份方式

- 低风险内网最小部署：每日停写窗口内打包 storage volume 或 bind mount 目录。
- 如无法停写：至少先执行应用停机或未来补 SQLite online backup 脚本，再复制 SQLite 文件和 WAL/SHM。
- 真实 provider 产物体积可能快速增长，需要容量阈值和保留周期。

### 恢复方式

1. 停止 `web` 和 `api`。
2. 备份当前损坏或待替换的 storage 目录到单独路径。
3. 恢复目标 storage 快照到 `STORAGE_ROOT`。
4. 确认目录权限归运行用户可读写。
5. 启动 `api`，执行 `/health` 和 storage 写入 smoke。
6. 启动 `web`，执行真实 API 模式最小浏览器 smoke。

## 11. 回滚方式

### 镜像回滚

- 每次部署使用不可变 tag，例如 `shanhaiedu-api:20260624-t008`、`shanhaiedu-web:20260624-t008`。
- 保留上一版镜像和上一版 compose 文件。
- 回滚时切回上一版 tag，执行 `docker compose up -d`。

### 配置回滚

- 非密钥配置以模板或部署说明记录版本。
- 密钥文件不进 git；如密钥轮换失败，按 secret manager 或部署主机 secret 备份策略恢复。

### 数据回滚

- SQLite/storage 没有正式迁移链路前，不承诺自动降级。
- 若新版本写入不兼容数据，只能从部署前 storage 快照恢复。
- 因此每次涉及 storage schema 或项目数据结构变化前必须先备份。

## 12. 已可做与生产前必须补齐

### 已可做内网最小部署草案

- Web/API 双容器拓扑明确。
- API 单实例和 storage 持久卷边界明确。
- liveness 与 readiness 分层明确。
- 密钥变量名和注入原则明确。
- `.dockerignore` 排除范围明确。
- 日志、备份、恢复、回滚草案明确。
- `ffmpeg` 是否纳入镜像的取舍明确。

### 生产前必须补齐

- 正式 Dockerfile、compose 与 `.dockerignore` 文件落地并通过 T009 冷启动验收。
- `BACKEND_API_TOKEN` 生产非空强制，或升级到正式 JWT/RBAC/session。
- 当前代码对 Docker secrets `*_FILE` 的支持方式确认。
- API readiness 脚本或运维 smoke 脚本。
- SQLite 单实例运行约束写入部署门禁；多实例前迁移外部数据库和对象存储。
- storage 容量、清理、备份和恢复演练。
- provider 超时、重试、并发、成本和失败率监控。
- `ffmpeg` 镜像策略和真实 final video 合成验收。
- TLS、访问控制、防火墙和反代日志策略。
- Cloud Run 另起专题，不在当前内网最小部署草案中承诺。

## 13. 给 T009 的验收输入

T009 测试工程师可基于本文验证：

- 新人能从草案创建临时 Dockerfile/compose，并确认不需要真实密钥跑 fake/placeholder 最小链路。
- Docker build context 不包含 `.env`、storage、logs、SQLite、真实 provider 产物和 `skills\imagegen-myself\.env.local`。
- API `/health` 只作为 liveness；readiness 另测 storage 写入和 fake provider 最小链路。
- `BACKEND_API_TOKEN` 注入后，Web 代理可访问 API，浏览器端不可见 token。
- storage volume 重启后项目数据仍存在。
- 删除容器不删除 named volume；删除 volume 前必须有明确备份和授权。
- 不安装 `ffmpeg` 时真实多 clip 合成不可宣称通过；安装后需单独 smoke。
- 回滚至少覆盖镜像 tag 回退和 storage 快照恢复两条路径。

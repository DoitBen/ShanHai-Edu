# ShanHai-Edu

小学数学公开课 AI 半自动化生产产品。

教研团队内部用 → 打磨成熟后封装外销。

## 这是什么

把"教材内容 → 教案 → PPT → 导入视频"的公开课生产流程做成：

- **半自动化**：AI 出草稿 + 字段化反幻觉 + 教研员审核重做编辑 + approve 进下一步
- **可执行基线**：workflow.yaml + JSON Schema + 规则 YAML + LLM 模板，机器可直接消费
- **飞轮驱动**：用户偏好沉淀，越用越懂用户
- **绝对主导权**：教研员对项目有完全控制权，AI 在合规红线内服务

## 仓库结构

```
ShanHai-Edu/
├── README.md                            项目入口（本文件）
├── docs/
│   ├── PRD.md                           产品决策记录（775 行）
│   └── TECH_ROADMAP.md                  技术路线规划（616 行）
├── workflow/                            可执行基线（75 个文件）
│   ├── README.md
│   ├── schema.md / state_machine.md / rules.md
│   ├── workflow.yaml                    调度总枢纽
│   ├── schemas/   *.json   ×19          节点字段定义
│   ├── rules/     *.yaml   ×37          机器可调度规则
│   └── prompts/   *.md     ×12          LLM 模板（含 supervisor 逐页审查智能体）
└── history/                             决策档案（9 份）
    ├── README.md
    ├── 00_决策时间线.md
    ├── 01_产品定位演进.md
    ├── 02_关键拐点.md
    ├── 03_为什么这样设计.md
    ├── 04_拒绝过的方案.md
    ├── 05_风险与不确定性.md
    ├── 06_团队与角色.md
    └── 07_对话精华.md
```

## 推荐阅读顺序

| 用时 | 读什么 |
|---|---|
| 5 分钟了解 | `history/00_决策时间线.md` |
| 30 分钟全貌 | 加 `docs/PRD.md` 前 4 章 + `history/01_产品定位演进.md` |
| 开发动手前 | `docs/TECH_ROADMAP.md` + `workflow/workflow.yaml` + `workflow/README.md` |
| 加新规则 | `workflow/rules.md` 看分类 → 加 `workflow/rules/R{nnn}.yaml` + 改 `workflow/rules/index.yaml` |
| 加新字段 | 改对应 `workflow/schemas/{node}.schema.json` |
| 改流程 | 改 `workflow/workflow.yaml` |
| 争议时回原点 | `history/02_关键拐点.md` + `07_对话精华.md` |

## 工作流核心：9 步双分支

```
第 0 步  项目配置 + 角色字典 + 视觉契约
   ↓
第 1 步  公开课教案
   ↓
   ├── PPT 分支：第 2 步 总装方案 → 第 3 步 页面脚本（13 字段 + 逐页审查智能体） → 第 5A 步 视觉资产 → 第 7 步 ppt-master PPTX
   └── 导入视频分支：第 1.5 步 选择集 → 第 4B 文稿 → 第 4C 剧本 → 第 5B 资产 → 第 6 步 分镜 → 第 8 步 omni_flash + 中文男声 + 拼接
   ↓
第 9 步  最终交付（PPT + 视频 + 反馈弹窗）
```

## 产品红线（不可被用户编辑）

1. 中文男声 + 禁英文配音
2. 禁真人未成年 / 禁可识别儿童脸 / 禁真实课堂实拍感
3. 完整视频必须多分镜拼接（单段不算终版）
4. 候选不能伪装终版
5. 角色字典中"禁真人 / photorealistic"硬约束
6. 数学事实必须进可编辑文本层

## 开发资源

- **团队**：3 人 × 3 月（全栈主导 + 前端 + 0.5 AI 接入 + 0.2 DevOps + 0.3 教学法负责人）
- **估时**：107 人日
- **技术栈**：Next.js + FastAPI + SQLite + Celery + LiteLLM
- **里程碑**：第 1 月骨架 / 第 2 月 PPT 主链路 / 第 3 月视频分支 + 收尾

详见 `docs/TECH_ROADMAP.md` 第 4-6 章。

## 当前状态

2026-06-19 — 完成 v1 规范层 + 产品决策 + 技术路线 + 历程档案全部交付，进入开发阶段。

## License

私有项目，未公开授权。

# jiaocaiTojiaoan 项目级适配说明

## 定位

`skills/jiaocaiTojiaoan` 是从 AI-youjiao 沉淀过来的 MinerU 图文教材解析经验包，只负责指导“教材页段 PDF -> MinerU Markdown -> 教材内容核验”的产物质量。

它不替代 ShanHaiEdu 现有主链路：

- `TextbookLibraryStore`
- 教材库 DB
- 新建项目教材绑定
- StateEngine
- RuleExecutor
- 现有工作流节点

若经验包与 ShanHaiEdu 当前接口、状态机或工作流契约冲突，以 ShanHaiEdu 当前契约为准。

## 本项目采用方式

- 导入教材：进入全局教材库，建立教材版本和目录索引。
- 切分教材：按知识点生成页段 PDF。
- 解析教材内容：对页段 PDF 运行 MinerU 或 fixture provider，生成教材内容 Markdown。
- 教案生成：只能读取当前知识点的教材内容 Markdown；历史教案只能作为参考。

## Markdown 质量契约

教材内容 Markdown 至少包含：

1. 课节范围判断
2. 核心知识点
3. 图片、物体、道具清单
4. 逐页结构化内容
5. 可转成教案的课堂流程
6. 可直接形成的教学目标
7. 建议板书
8. 输出与核验说明

占位或未人工确认内容不能标记为 `approved`。

## 多教材边界

本轮只保证人教版小学数学一年级上册为已验证模板。其他教材可以入库、建立版本和解析策略字段，但必须处于未验证或待人工确认状态，不能伪装为自动泛化成功。

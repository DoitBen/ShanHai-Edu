import type {
  ProjectMeta,
  WorkflowStage,
  VideoIntroPlan,
  TextbookParseResult,
  PptPlan,
  SystemStatus,
  PendingItem,
  StageLog,
  ActivityItem,
} from "./types";

/**
 * Mock 数据中心 —— 第一阶段所有数据均来自此处，无外部 API。
 */

export const MOCK_PROJECTS: ProjectMeta[] = [
  {
    id: "demo-001",
    name: "认识分数——分一分",
    subject: "数学",
    grade: "三年级",
    textbookVersion: "人教版",
    volume: "下册",
    lessonType: "新授课",
    currentStage: "video-script",
    progress: 42,
    status: "active",
    nextAction: "确认采纳视频剧本方案",
    owner: "林老师",
    createdAt: "2026-05-12 09:20",
    updatedAt: "2026-06-17 14:32",
  },
  {
    id: "demo-002",
    name: "春天的色彩——植物观察",
    subject: "科学",
    grade: "二年级",
    textbookVersion: "教科版",
    volume: "下册",
    lessonType: "探究课",
    currentStage: "ppt-plan",
    progress: 58,
    status: "pending",
    nextAction: "确认 PPT 方案结构",
    owner: "周老师",
    createdAt: "2026-05-08 11:05",
    updatedAt: "2026-06-16 17:48",
  },
  {
    id: "demo-003",
    name: "古诗文诵读——静夜思",
    subject: "语文",
    grade: "一年级",
    textbookVersion: "统编版",
    volume: "上册",
    lessonType: "诵读课",
    currentStage: "video-generation",
    progress: 71,
    status: "blocked",
    nextAction: "处理视频生成失败并重试",
    owner: "陈老师",
    createdAt: "2026-04-22 08:40",
    updatedAt: "2026-06-15 10:11",
  },
];

function log(
  id: string,
  time: string,
  level: StageLog["level"],
  message: string
): StageLog {
  return { id, time, level, message };
}

/**
 * 为 demo-001 构造完整 14 节点工作流
 */
export function buildDemo001Stages(): WorkflowStage[] {
  return [
    {
      key: "project-config",
      title: "项目配置",
      branch: "common",
      order: 1,
      status: "approved",
      summary: "已完成项目基本信息与路径约束配置。",
      input:
        "项目名：认识分数——分一分；学科：数学；年级：三年级；教材版本：人教版 下册；课型：新授课；输出路径：/output/demo-001；安全模式：开启。",
      result:
        "项目已创建，配置项已校验通过，输出目录可写，安全模式生效。",
      evidence: ["config.json", "path-check.log"],
      logs: [
        log("l1", "06-12 09:20", "info", "创建项目 demo-001"),
        log("l2", "06-12 09:21", "success", "配置校验通过"),
      ],
      duration: "0分12秒",
    },
    {
      key: "textbook-parse",
      title: "教材解析与核验",
      branch: "common",
      order: 2,
      status: "approved",
      summary: "教材已解析，知识点与教学目标核验通过。",
      input: "教材文件：人教版数学三年级下册.pdf（第 8 单元）",
      result:
        "课题：认识分数；核心知识点：二分之一、四分之一的含义；教学目标：理解分数表示部分与整体的关系；重点：理解分数意义；难点：用分数描述实际生活量。",
      evidence: ["textbook.pdf", "parse-result.json", "preview.png"],
      logs: [
        log("l3", "06-12 09:24", "info", "开始解析教材"),
        log("l4", "06-12 09:25", "info", "识别 9 页，抽取结构化字段"),
        log("l5", "06-12 09:25", "success", "解析完成，等待确认"),
        log("l6", "06-12 09:30", "success", "教师确认解析结果"),
      ],
      duration: "1分03秒",
    },
    {
      key: "open-lesson-plan",
      title: "公开课教案",
      branch: "common",
      order: 3,
      status: "approved",
      summary: "教案初稿已生成并确认教学目标与重难点。",
      input: "基于教材解析结果生成公开课教案初稿。",
      result:
        "教案包含：教学目标 3 条、教学重点 2 条、教学难点 1 条、教学过程 5 环节、板书设计、作业设计。已与教师确认。",
      evidence: ["lesson-plan-v1.docx", "lesson-plan-v1.pdf"],
      logs: [
        log("l7", "06-13 10:02", "info", "生成教案初稿"),
        log("l8", "06-13 10:15", "success", "教师确认教案"),
      ],
      duration: "2分41秒",
    },
    {
      key: "video-design-import",
      title: "视频设计导入",
      branch: "video",
      order: 4,
      status: "approved",
      summary: "视频用途与类型方向已确认。",
      input:
        "视频用途：课堂导入；类型：科普类、应用类、故事类；每类数量：3；目标受众：三年级学生；预计时长：90 秒；创意要求：贴近生活、悬念引入。",
      result: "已生成 9 套视频导入方案，等待剧本阶段采纳。",
      evidence: ["video-design-spec.json"],
      logs: [
        log("l9", "06-14 14:10", "info", "视频设计导入完成"),
        log("l10", "06-14 14:11", "success", "方案已就绪"),
      ],
      duration: "0分22秒",
    },
    {
      key: "video-script",
      title: "视频剧本",
      branch: "video",
      order: 5,
      status: "pending_confirm",
      summary: "已生成 9 套视频剧本方案，等待教师采纳。",
      input: "依据视频设计导入方向生成多套剧本。",
      result:
        "9 套方案已就绪，推荐方案得分 92，类型：应用类，主题：分披萨里的分数。",
      evidence: ["video-plans.json"],
      logs: [
        log("l11", "06-17 14:20", "info", "生成 9 套视频方案"),
        log("l12", "06-17 14:30", "info", "推荐排序完成"),
        log("l13", "06-17 14:32", "warn", "等待教师采纳"),
      ],
      duration: "3分18秒",
    },
    {
      key: "video-assets",
      title: "视频资产",
      branch: "video",
      order: 6,
      status: "not_started",
      summary: "尚未开始。",
      input: "",
      result: "",
      evidence: [],
      logs: [],
    },
    {
      key: "storyboard",
      title: "分镜脚本",
      branch: "video",
      order: 7,
      status: "not_started",
      summary: "尚未开始。",
      input: "",
      result: "",
      evidence: [],
      logs: [],
    },
    {
      key: "video-generation",
      title: "视频生成",
      branch: "video",
      order: 8,
      status: "not_started",
      summary: "尚未开始。",
      input: "",
      result: "",
      evidence: [],
      logs: [],
    },
    {
      key: "ppt-plan",
      title: "PPT 方案",
      branch: "ppt",
      order: 9,
      status: "not_started",
      summary: "尚未开始。",
      input: "",
      result: "",
      evidence: [],
      logs: [],
    },
    {
      key: "lesson-plan-final",
      title: "教案完善稿",
      branch: "common",
      order: 10,
      status: "not_started",
      summary: "尚未开始。",
      input: "",
      result: "",
      evidence: [],
      logs: [],
    },
    {
      key: "ppt-script",
      title: "PPT 脚本",
      branch: "ppt",
      order: 11,
      status: "not_started",
      summary: "尚未开始。",
      input: "",
      result: "",
      evidence: [],
      logs: [],
    },
    {
      key: "ppt-assets",
      title: "PPT 资产",
      branch: "ppt",
      order: 12,
      status: "not_started",
      summary: "尚未开始。",
      input: "",
      result: "",
      evidence: [],
      logs: [],
    },
    {
      key: "pptx-generation",
      title: "PPTX 生成",
      branch: "ppt",
      order: 13,
      status: "not_started",
      summary: "尚未开始。",
      input: "",
      result: "",
      evidence: [],
      logs: [],
    },
    {
      key: "final-delivery",
      title: "最终交付",
      branch: "common",
      order: 14,
      status: "not_started",
      summary: "尚未开始。",
      input: "",
      result: "",
      evidence: [],
      logs: [],
    },
  ];
}

/** demo-002：进行到 ppt-plan，pending */
export function buildDemo002Stages(): WorkflowStage[] {
  const stages = buildDemo001Stages().map((s) => ({ ...s, logs: [...s.logs] }));
  // 重置为 demo-002 的实际进度
  return stages.map((s) => {
    const base: WorkflowStage = { ...s, evidence: [], logs: [] };
    if (s.order <= 4) {
      base.status = "approved";
      base.summary = "已完成。";
    } else if (s.order === 5) {
      base.status = "approved";
      base.summary = "视频剧本方案已采纳。";
    } else if (s.order === 9) {
      base.status = "pending_confirm";
      base.summary = "PPT 方案结构已生成，等待确认。";
      base.input = "PPT 风格：清新简约；页数：18；结构：导入-探究-小结-练习。";
      base.result =
        "PPT 方案包含 18 页，结构清晰，匹配教案落点，等待教师确认。";
      base.evidence = ["ppt-plan.json"];
      base.logs = [
        log("p1", "06-16 17:40", "info", "生成 PPT 方案"),
        log("p2", "06-16 17:48", "warn", "等待确认 PPT 结构"),
      ];
    } else {
      base.status = "not_started";
      base.summary = "尚未开始。";
      base.input = "";
      base.result = "";
    }
    return base;
  });
}

/** demo-003：阻塞在 video-generation，failed */
export function buildDemo003Stages(): WorkflowStage[] {
  const stages = buildDemo001Stages().map((s) => ({ ...s, logs: [...s.logs] }));
  return stages.map((s) => {
    const base: WorkflowStage = { ...s, evidence: [], logs: [] };
    if (s.order <= 7) {
      base.status = "approved";
      base.summary = "已完成。";
    } else if (s.order === 8) {
      base.status = "failed";
      base.summary = "视频生成失败：分镜资产缺少关键帧，需补充后重试。";
      base.input = "分镜脚本：storyboard.json；资产清单：assets.json";
      base.result = "生成失败，已记录错误日志，等待补充资产后重试。";
      base.evidence = ["error-trace.log", "retry-plan.json"];
      base.logs = [
        log("f1", "06-15 09:50", "info", "开始视频生成"),
        log("f2", "06-15 10:02", "error", "缺少关键帧 frame-07.png"),
        log("f3", "06-15 10:03", "error", "生成中止，已回滚临时文件"),
        log("f4", "06-15 10:11", "warn", "等待补充资产后重试"),
      ];
    } else {
      base.status = "not_started";
      base.summary = "尚未开始。";
      base.input = "";
      base.result = "";
    }
    return base;
  });
}

export function buildStagesForProject(projectId: string): WorkflowStage[] {
  if (projectId === "demo-001") return buildDemo001Stages();
  if (projectId === "demo-002") return buildDemo002Stages();
  if (projectId === "demo-003") return buildDemo003Stages();
  return buildDemo001Stages();
}

export const MOCK_TEXTBOOK_PARSE: TextbookParseResult = {
  subject: "数学",
  grade: "三年级",
  textbookVersion: "人教版",
  volume: "下册",
  lesson: "认识分数——分一分",
  coreKnowledgePoints: [
    "二分之一的含义",
    "四分之一的含义",
    "分数各部分名称",
    "分数表示部分与整体的关系",
  ],
  teachingGoalSummary:
    "通过分一分、折一折、画一画等活动，理解分数表示部分与整体的关系，能正确读写简单分数。",
  keyPoints: [
    "理解分数产生的实际意义",
    "掌握分子、分母、分数线的含义",
  ],
  difficulties: [
    "用分数描述实际生活中的量",
    "理解同一整体不同分法对应不同分数",
  ],
};

export const MOCK_VIDEO_PLANS: VideoIntroPlan[] = [
  {
    id: "vp-1",
    rank: 1,
    score: 92,
    type: "application",
    title: "分披萨里的分数",
    hook: "一家四口分一个披萨，每个人到底能吃到多少？",
    courseAnchor: "从‘平均分’自然过渡到‘二分之一’",
    classroomLandingQuestion: "如果再来一位客人，每个人还能吃到二分之一吗？",
    avoidTeaching: "不提前讲解分子分母的书写规则",
    lessonEntryPoint: "在‘认识二分之一’环节后插入 90 秒",
    reason: "生活场景贴切，悬念自然，落点问题指向分数本质，推荐采纳。",
    accepted: false,
  },
  {
    id: "vp-2",
    rank: 2,
    score: 88,
    type: "story",
    title: "小熊分蛋糕",
    hook: "小熊过生日，要把一块蛋糕分给三位好朋友，怎么分才公平？",
    courseAnchor: "通过故事引出‘平均分’是分数的前提",
    classroomLandingQuestion: "三份中的一份，可以用哪个数表示？",
    avoidTeaching: "不提前出现三分之一之外的其它分数",
    lessonEntryPoint: "在导入环节播放，时长 90 秒",
    reason: "故事性强、情绪温暖，适合低年级，但与‘四分之一’衔接略弱。",
    accepted: false,
  },
  {
    id: "vp-3",
    rank: 3,
    score: 85,
    type: "science",
    title: "分数从哪里来",
    hook: "古人没有分数时，遇到‘分东西’会怎么办？",
    courseAnchor: "从数学史角度建立分数的必要性",
    classroomLandingQuestion: "如果不能用分数，你会怎么记录‘半块’？",
    avoidTeaching: "不展开分数的演变史细节",
    lessonEntryPoint: "可作为导入或拓展环节使用",
    reason: "文化视野开阔，但信息密度偏高，需控制节奏。",
    accepted: false,
  },
  {
    id: "vp-4",
    rank: 4,
    score: 81,
    type: "suspense",
    title: "消失的一半",
    hook: "桌上有半块巧克力，过一会儿却变成了两小块，发生了什么？",
    courseAnchor: "用悬念引出‘半’与‘二分之一’的关系",
    classroomLandingQuestion: "两小块和原来的半块，是一样多吗？",
    avoidTeaching: "不提前讲解等值分数",
    lessonEntryPoint: "导入环节，时长 75 秒",
    reason: "悬念感强，但需注意不要误导‘等值’概念。",
    accepted: false,
  },
  {
    id: "vp-5",
    rank: 5,
    score: 78,
    type: "discovery",
    title: "折纸里的秘密",
    hook: "一张长方形纸，对折一次、再对折一次，会出现几个同样大的部分？",
    courseAnchor: "通过折纸操作发现‘四分之一’",
    classroomLandingQuestion: "对折两次后，每一份是这张纸的几分之几？",
    avoidTeaching: "不提前给出‘四分之一’的写法",
    lessonEntryPoint: "探究环节导入，时长 90 秒",
    reason: "操作性强，与课堂活动衔接紧密，但视觉冲击略弱。",
    accepted: false,
  },
  {
    id: "vp-6",
    rank: 6,
    score: 74,
    type: "application",
    title: "半个苹果的旅行",
    hook: "半个苹果从树上到餐桌，经过了哪些‘一半’？",
    courseAnchor: "从生活链路理解‘一半’的稳定性",
    classroomLandingQuestion: "为什么不管怎么分，‘一半’都一样多？",
    avoidTeaching: "不展开分数加法",
    lessonEntryPoint: "拓展环节，时长 80 秒",
    reason: "生活气息浓，但与教学重难点关联中等。",
    accepted: false,
  },
  {
    id: "vp-7",
    rank: 7,
    score: 71,
    type: "story",
    title: "魔法厨房",
    hook: "魔法厨房里，所有食物都会自己分成同样大的小份。",
    courseAnchor: "用奇幻设定强化‘平均分’",
    classroomLandingQuestion: "魔法分出来的每一份，大小一样吗？",
    avoidTeaching: "不引入非平均分情境",
    lessonEntryPoint: "导入环节，时长 70 秒",
    reason: "趣味性强，但奇幻设定可能分散对数学本身的注意。",
    accepted: false,
  },
  {
    id: "vp-8",
    rank: 8,
    score: 68,
    type: "suspense",
    title: "谁偷走了四分之一",
    hook: "披萨被切了四块，却少了一块，剩下的是整体的几分之几？",
    courseAnchor: "从‘缺少’引出部分与整体的关系",
    classroomLandingQuestion: "三块是四块里的几分之几？",
    avoidTeaching: "不提前讲解四分之三的读法",
    lessonEntryPoint: "拓展环节，时长 85 秒",
    reason: "悬念与数学结合较好，但理解门槛略高。",
    accepted: false,
  },
  {
    id: "vp-9",
    rank: 9,
    score: 64,
    type: "discovery",
    title: "水杯里的分数",
    hook: "把一杯水倒进两个同样大的杯子，每杯是原来的几分之几？",
    courseAnchor: "通过液体测量理解‘二分之一’",
    classroomLandingQuestion: "如果杯子不一样大，还能叫二分之一吗？",
    avoidTeaching: "不展开体积单位的换算",
    lessonEntryPoint: "探究环节，时长 90 秒",
    reason: "实验感强，但课堂可操作性受场地限制。",
    accepted: false,
  },
];

export const MOCK_PPT_PLANS: PptPlan[] = [
  {
    id: "ppt-1",
    slides: 18,
    style: "清新简约",
    structure: ["导入", "探究", "归纳", "练习", "小结"],
    highlight: "以生活情境贯穿，配折纸操作图示。",
    accepted: true,
  },
  {
    id: "ppt-2",
    slides: 22,
    style: "童趣插画风",
    structure: ["情境", "新授", "活动", "巩固", "延伸"],
    highlight: "插画丰富，适合低年级注意力引导。",
    accepted: false,
  },
];

export const MOCK_SYSTEM_STATUS: SystemStatus = {
  scheduler: "running",
  queueTasks: 3,
  storageUsedPct: 38,
  lastHeartbeat: "2026-06-17 14:33:02",
  services: [
    { name: "教材解析服务", status: "ok", note: "正常" },
    { name: "视频生成服务", status: "degraded", note: "demo-003 任务失败重试中" },
    { name: "PPT 生成服务", status: "ok", note: "正常" },
    { name: "存储服务", status: "ok", note: "已用 38%" },
    { name: "安全模式", status: "ok", note: "已开启" },
  ],
};

export const MOCK_PENDING_ITEMS: PendingItem[] = [
  {
    id: "pi-1",
    projectId: "demo-001",
    projectName: "认识分数——分一分",
    stage: "video-script",
    stageTitle: "视频剧本",
    kind: "confirm",
    title: "等待采纳视频剧本方案",
    desc: "已生成 9 套方案，推荐方案得分 92，请确认采纳或编辑。",
    priority: "high",
    createdAt: "2026-06-17 14:32",
  },
  {
    id: "pi-2",
    projectId: "demo-002",
    projectName: "春天的色彩——植物观察",
    stage: "ppt-plan",
    stageTitle: "PPT 方案",
    kind: "confirm",
    title: "等待确认 PPT 方案结构",
    desc: "PPT 方案 18 页，结构：导入-探究-小结-练习，请确认。",
    priority: "high",
    createdAt: "2026-06-16 17:48",
  },
  {
    id: "pi-3",
    projectId: "demo-003",
    projectName: "古诗文诵读——静夜思",
    stage: "video-generation",
    stageTitle: "视频生成",
    kind: "error",
    title: "视频生成失败需处理",
    desc: "缺少关键帧 frame-07.png，补充资产后可重试。",
    priority: "high",
    createdAt: "2026-06-15 10:11",
  },
  {
    id: "pi-4",
    projectId: "demo-001",
    projectName: "认识分数——分一分",
    stage: "video-assets",
    stageTitle: "视频资产",
    kind: "input",
    title: "视频资产清单待补充",
    desc: "采纳剧本后需补充画面与配音资产清单。",
    priority: "medium",
    createdAt: "2026-06-17 14:33",
  },
];

export const MOCK_SCRIPTS = [
  {
    id: "sc-1",
    name: "教材解析脚本",
    type: "解析",
    status: "成功",
    duration: "1分03秒",
    lastRun: "2026-06-12 09:24",
    note: "解析人教版数学三年级下册第 8 单元",
  },
  {
    id: "sc-2",
    name: "视频方案生成脚本",
    type: "生成",
    status: "成功",
    duration: "3分18秒",
    lastRun: "2026-06-17 14:20",
    note: "生成 9 套视频导入方案",
  },
  {
    id: "sc-3",
    name: "PPT 方案生成脚本",
    type: "生成",
    status: "成功",
    duration: "2分05秒",
    lastRun: "2026-06-16 17:40",
    note: "生成 PPT 方案 2 套",
  },
  {
    id: "sc-4",
    name: "视频生成脚本",
    type: "生成",
    status: "失败",
    duration: "12分20秒",
    lastRun: "2026-06-15 09:50",
    note: "缺少关键帧，已回滚",
  },
  {
    id: "sc-5",
    name: "交付归档脚本",
    type: "归档",
    status: "待运行",
    duration: "—",
    lastRun: "—",
    note: "等待最终交付阶段触发",
  },
];

export const MOCK_STAGE_LOGS: StageLog[] = [
  log("g1", "06-17 14:20:01", "info", "启动视频方案生成脚本"),
  log("g2", "06-17 14:20:14", "info", "加载教材解析结果"),
  log("g3", "06-17 14:21:02", "info", "生成候选方案 9 套"),
  log("g4", "06-17 14:22:30", "info", "计算推荐分数"),
  log("g5", "06-17 14:23:11", "success", "方案排序完成"),
  log("g6", "06-17 14:30:00", "warn", "等待教师采纳"),
  log("g7", "06-15 10:02:33", "error", "视频生成失败：缺少关键帧 frame-07.png"),
];

export const MOCK_RECENT_ACTIVITIES: ActivityItem[] = [
  {
    id: "ac-1",
    time: "14:32",
    kind: "generate",
    projectName: "认识分数——分一分",
    projectId: "demo-001",
    stageTitle: "视频剧本",
    title: "生成 9 套视频导入方案",
    desc: "推荐方案得分 92，等待教师采纳",
  },
  {
    id: "ac-2",
    time: "14:20",
    kind: "approve",
    projectName: "认识分数——分一分",
    projectId: "demo-001",
    stageTitle: "视频设计导入",
    title: "确认通过「视频设计导入」",
    desc: "进入视频剧本阶段",
  },
  {
    id: "ac-3",
    time: "10:11",
    kind: "reject",
    projectName: "古诗文诵读——静夜思",
    projectId: "demo-003",
    stageTitle: "视频生成",
    title: "视频生成失败",
    desc: "缺少关键帧 frame-07.png，已回滚",
  },
  {
    id: "ac-4",
    time: "昨日 17:48",
    kind: "generate",
    projectName: "春天的色彩——植物观察",
    projectId: "demo-002",
    stageTitle: "PPT 方案",
    title: "生成 PPT 方案 2 套",
    desc: "18 页结构，等待确认",
  },
  {
    id: "ac-5",
    time: "昨日 10:15",
    kind: "adopt",
    projectName: "认识分数——分一分",
    projectId: "demo-001",
    stageTitle: "公开课教案",
    title: "采纳教案初稿",
    desc: "教学目标 3 条，重难点已确认",
  },
];

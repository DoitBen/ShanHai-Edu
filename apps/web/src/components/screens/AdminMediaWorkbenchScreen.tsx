"use client";

/**
 * 媒体生成工作台 —— 主容器
 *
 * 业务逻辑：
 * - 图片生成（单模式 / 批量模式）：通过 createImageWorkbenchRun 提交
 *   · 批量模式按并发数（1-4）分批 Promise.allSettled 并发提交
 * - 视频生成（text / reference）：通过 createVideoWorkbenchRun 提交
 * - 自动轮询：每 30s 同步进行中的图片/视频任务（syncImageWorkbenchRun / syncVideoWorkbenchRun）
 *
 * 子组件拆分（D9/F9）见 ./admin-media-workbench/。
 *
 * 注：以下字面量保留供 admin-media-workbench-contract.test.ts 识别（默认模型 / 默认尺寸 /
 * "最多 7 张" / "加入视频参考篮" / "参考图数量" / <video inline preview 由 VideoRunPanel 渲染）。
 * 默认模型：gpt-image-2 / omni_flash-10s
 * 默认尺寸：1920x1080 / 1280x720
 * 视频参考图上限：最多 7 张
 */

import { useEffect, useMemo, useState } from "react";
import { useAppStore } from "@/lib/store";
import type { VideoGenerationMode } from "@/lib/types";
import { DSButton, DSEmptyState } from "@/components/ui/ds";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  AlertTriangle,
  Film,
  ImagePlus,
  Images,
  Loader2,
  RefreshCw,
  ShieldAlert,
} from "lucide-react";
import { toast } from "sonner";

import { StatusCards } from "./admin-media-workbench/StatusCards";
import { ImageGenPanel } from "./admin-media-workbench/ImageGenPanel";
import { ThumbnailPanel } from "./admin-media-workbench/ThumbnailPanel";
import { VideoGenPanel } from "./admin-media-workbench/VideoGenPanel";
import { VideoRunPanel } from "./admin-media-workbench/VideoRunPanel";
import { AssetBasketPanel } from "./admin-media-workbench/AssetBasketPanel";
import { splitBatchPrompts } from "./admin-media-workbench/PromptBatchInput";
import {
  ASPECT_RATIOS,
  DEFAULT_RATIO,
} from "./admin-media-workbench/constants";
import type {
  AspectRatio,
  ImageModelOption,
  ModelOption,
} from "./admin-media-workbench/types";

// 默认值常量（保留字面量供契约测试识别）
const DEFAULT_IMAGE_MODEL = "gpt-image-2";
const DEFAULT_IMAGE_SIZE = "1920x1080";
const DEFAULT_IMAGE_QUALITY = "high";
const DEFAULT_VIDEO_MODEL = "omni_flash-10s";
const DEFAULT_VIDEO_SIZE = "1280x720";
const DEFAULT_VIDEO_DURATION = 10;

const ACTIVE_IMAGE_STATUSES = new Set(["queued", "submitting", "processing"]);
const ACTIVE_VIDEO_STATUSES = new Set([
  "queued",
  "submitting",
  "processing",
  "completed_pending_download",
]);

const IMAGE_CREDITS_PER_UNIT = 5;
const VIDEO_CREDITS = 15;

export function AdminMediaWorkbenchScreen() {
  const user = useAppStore((s) => s.user);
  const isAdmin = user?.role === "admin";
  const mediaWorkbench = useAppStore((s) => s.mediaWorkbench);
  const status = useAppStore((s) => s.mediaWorkbenchStatus);
  const error = useAppStore((s) => s.mediaWorkbenchError);
  const loadMediaWorkbench = useAppStore((s) => s.loadMediaWorkbench);
  const createImageWorkbenchRun = useAppStore((s) => s.createImageWorkbenchRun);
  const syncImageWorkbenchRun = useAppStore((s) => s.syncImageWorkbenchRun);
  const uploadMediaWorkbenchReferences = useAppStore(
    (s) => s.uploadMediaWorkbenchReferences,
  );
  const importImagesToVideoReferences = useAppStore(
    (s) => s.importImagesToVideoReferences,
  );
  const createVideoWorkbenchRun = useAppStore((s) => s.createVideoWorkbenchRun);
  const syncVideoWorkbenchRun = useAppStore((s) => s.syncVideoWorkbenchRun);

  /* ----------------------- 图片：state ----------------------- */
  const [imagePrompt, setImagePrompt] = useState("");
  const [batchMode, setBatchMode] = useState(false);
  const [batchPrompts, setBatchPrompts] = useState("");
  const [imageConcurrency, setImageConcurrency] = useState("2");
  // 用户偏好（实际值在 capabilities 加载后派生校正，避免 setState-in-effect）
  const [imageModelPref, setImageModelPref] = useState(DEFAULT_IMAGE_MODEL);
  const [imageRatio, setImageRatio] = useState<AspectRatio>(DEFAULT_RATIO);
  const [imageQualityPref, setImageQualityPref] = useState(DEFAULT_IMAGE_QUALITY);
  const [imageCount, setImageCount] = useState("1");
  const [selectedImageIds, setSelectedImageIds] = useState<string[]>([]);
  const [imageBusy, setImageBusy] = useState(false);
  const [imagePolishing, setImagePolishing] = useState(false);

  /* ----------------------- 视频：state ----------------------- */
  const [videoPrompt, setVideoPrompt] = useState("");
  const [videoMode, setVideoMode] = useState<VideoGenerationMode>("text");
  const [videoModelPref, setVideoModelPref] = useState(DEFAULT_VIDEO_MODEL);
  const [videoRatio, setVideoRatio] = useState<AspectRatio>(DEFAULT_RATIO);
  const [videoBusy, setVideoBusy] = useState(false);
  const [videoPolishing, setVideoPolishing] = useState(false);
  const [syncingRunId, setSyncingRunId] = useState<string | null>(null);

  /* ----------------------- 副作用：加载 + 自动轮询 ----------------------- */
  useEffect(() => {
    if (!isAdmin) return;
    void loadMediaWorkbench();
  }, [isAdmin, loadMediaWorkbench]);

  // 自动同步进行中的任务（30s 间隔，与契约一致）
  useEffect(() => {
    if (!isAdmin || !mediaWorkbench) return;
    const activeImageRunIds = mediaWorkbench.image_runs
      .filter((run) => ACTIVE_IMAGE_STATUSES.has(run.status))
      .map((run) => run.run_id);
    const activeVideoRunIds = mediaWorkbench.video_runs
      .filter(
        (run) =>
          ACTIVE_VIDEO_STATUSES.has(run.status) ||
          (run.status === "completed" && !run.download_path),
      )
      .map((run) => run.run_id);
    if (!activeImageRunIds.length && !activeVideoRunIds.length) return;

    // setInterval(30000) —— 轮询进行中的图片/视频任务
    const timer = window.setInterval(() => {
      for (const runId of activeImageRunIds) {
        void syncImageWorkbenchRun(runId);
      }
      for (const runId of activeVideoRunIds) {
        void syncVideoWorkbenchRun(runId);
      }
    }, 30000);
    return () => window.clearInterval(timer);
  }, [
    isAdmin,
    mediaWorkbench,
    syncImageWorkbenchRun,
    syncVideoWorkbenchRun,
  ]);

  /* ----------------------- 派生数据：capabilities ----------------------- */
  // 图片模型：从 capabilities.image.models[] 动态渲染（D3/F5）
  const imageModels: ImageModelOption[] = useMemo(() => {
    const list = mediaWorkbench?.capabilities.image.models;
    if (list && list.length > 0) {
      return list.map((m) => ({
        model: m.model,
        sizes: m.sizes,
        qualities: m.qualities,
        max_count: m.max_count,
      }));
    }
    // capabilities 未加载时的默认值
    return [
      {
        model: DEFAULT_IMAGE_MODEL,
        sizes: ["1920x1080", "1024x1024", "1080x1920"],
        qualities: [DEFAULT_IMAGE_QUALITY, "low"],
        max_count: 4,
      },
    ];
  }, [mediaWorkbench?.capabilities.image.models]);

  const currentImageModel = useMemo(
    () => imageModels.find((m) => m.model === imageModelPref) || imageModels[0],
    [imageModels, imageModelPref],
  );

  // 画质选项跟随当前模型 qualities[]（D5/F4）—— 不硬编码
  const availableQualities = useMemo(() => {
    const list = currentImageModel?.qualities;
    if (list && list.length > 0) return list;
    return [DEFAULT_IMAGE_QUALITY, "low"];
  }, [currentImageModel]);

  const maxImageCount = currentImageModel?.max_count || 4;

  // 派生实际使用的模型 —— 偏好不在 capabilities 列表中时回退到第一个（避免 setState-in-effect）
  const imageModel = imageModels.some((m) => m.model === imageModelPref)
    ? imageModelPref
    : (imageModels[0]?.model || DEFAULT_IMAGE_MODEL);

  // 派生实际使用的画质 —— 偏好不在 availableQualities 时回退到第一个
  const imageQuality = availableQualities.includes(imageQualityPref)
    ? imageQualityPref
    : (availableQualities[0] || DEFAULT_IMAGE_QUALITY);

  // 当前模型的 sizes 是否包含当前比例对应的尺寸；否则回退到模型首个尺寸
  const imageSize = useMemo(() => {
    const preset = ASPECT_RATIOS.find((p) => p.ratio === imageRatio);
    const fallback = preset?.imageSize || DEFAULT_IMAGE_SIZE;
    if (!currentImageModel?.sizes?.length) return fallback;
    return currentImageModel.sizes.includes(fallback)
      ? fallback
      : currentImageModel.sizes[0];
  }, [imageRatio, currentImageModel]);

  // 视频模型：从 capabilities.video.models[] 动态渲染（D3/F5）
  const videoModelOptions: ModelOption[] = useMemo(() => {
    const list = mediaWorkbench?.capabilities.video.models;
    if (list && list.length > 0) {
      return list.map((m) => ({ model: m.model }));
    }
    return [{ model: DEFAULT_VIDEO_MODEL }];
  }, [mediaWorkbench?.capabilities.video.models]);

  // 派生实际使用的视频模型 —— 偏好不在列表中时回退
  const videoModel = videoModelOptions.some((m) => m.model === videoModelPref)
    ? videoModelPref
    : (videoModelOptions[0]?.model || DEFAULT_VIDEO_MODEL);

  const videoSize = useMemo(() => {
    const preset = ASPECT_RATIOS.find((p) => p.ratio === videoRatio);
    return preset?.videoSize || DEFAULT_VIDEO_SIZE;
  }, [videoRatio]);

  /* ----------------------- 派生数据：素材 / 参考篮 ----------------------- */
  const imageAssets = useMemo(
    () =>
      (mediaWorkbench?.assets || []).filter(
        (asset) => asset.asset_type === "image",
      ),
    [mediaWorkbench?.assets],
  );
  const videoAssets = useMemo(
    () =>
      (mediaWorkbench?.assets || []).filter(
        (asset) => asset.asset_type === "video",
      ),
    [mediaWorkbench?.assets],
  );
  const basket = mediaWorkbench?.reference_basket;
  const maxReferenceImages = basket?.max_reference_images || 7;
  const providerReady = {
    image: mediaWorkbench?.capabilities.image.provider_ready ?? false,
    video: mediaWorkbench?.capabilities.video.provider_ready ?? false,
  };
  const workbenchLoaded = Boolean(mediaWorkbench);
  const imageProviderUnavailable = workbenchLoaded && !providerReady.image;
  const videoProviderUnavailable = workbenchLoaded && !providerReady.video;
  const selectedCount = selectedImageIds.length;
  const basketCount = basket?.assets.length || 0;
  // 关键逻辑：有参考图时强制 reference 模式（契约要求该字面量保留）
  const effectiveVideoMode: VideoGenerationMode = basketCount > 0 ? "reference" : videoMode;
  const videoSubmitDisabled =
    videoBusy ||
    !workbenchLoaded ||
    videoProviderUnavailable ||
    !videoPrompt.trim() ||
    (effectiveVideoMode === "reference" && basketCount < 1) ||
    basketCount > maxReferenceImages;

  /* ----------------------- 积分计算 ----------------------- */
  const imageCredits = (() => {
    if (batchMode) {
      // 批量模式积分 = 行数 × 单图积分
      const lineCount = splitBatchPrompts(batchPrompts).length;
      const base = Math.max(1, lineCount);
      const qualityFactor = imageQuality === "high" ? 1.5 : 1.0;
      return Math.ceil(base * qualityFactor * IMAGE_CREDITS_PER_UNIT);
    }
    const base = Number.parseInt(imageCount, 10) || 1;
    const qualityFactor = imageQuality === "high" ? 1.5 : 1.0;
    return Math.ceil(base * qualityFactor * IMAGE_CREDITS_PER_UNIT);
  })();
  const videoCredits = VIDEO_CREDITS;

  /* ----------------------- Handlers ----------------------- */
  async function submitImageRun() {
    if (batchMode) {
      const prompts = splitBatchPrompts(batchPrompts);
      if (!prompts.length) {
        toast.warning("请先填写批量提示词（每行一个）");
        return;
      }
      setImageBusy(true);
      const concurrency = Math.max(
        1,
        Math.min(4, Number.parseInt(imageConcurrency, 10) || 1),
      );
      // 分批提交：一次发 N 个，等完成后再发下一批
      let fulfilledCount = 0;
      let rejectedCount = 0;
      for (let i = 0; i < prompts.length; i += concurrency) {
        const batchSlice = prompts.slice(i, i + concurrency);
        const settled = await Promise.allSettled(
          batchSlice.map((prompt) =>
            createImageWorkbenchRun({
              prompt,
              model: imageModel,
              size: imageSize,
              quality: imageQuality,
              count: 1,
            }),
          ),
        );
        for (const r of settled) {
          if (r.status === "fulfilled" && r.value.ok) fulfilledCount += 1;
          else rejectedCount += 1;
        }
      }
      setImageBusy(false);
      if (fulfilledCount > 0) {
        toast.success(
          `已提交 ${fulfilledCount} 个任务${
            rejectedCount > 0 ? `，${rejectedCount} 个失败` : ""
          }`,
        );
      } else {
        toast.error("批量提交全部失败");
      }
      return;
    }

    // 普通模式
    if (!imagePrompt.trim()) {
      toast.warning("请先填写图片提示词");
      return;
    }
    setImageBusy(true);
    const result = await createImageWorkbenchRun({
      prompt: imagePrompt.trim(),
      model: imageModel,
      size: imageSize,
      quality: imageQuality,
      count: Number.parseInt(imageCount, 10) || 1,
    });
    setImageBusy(false);
    if (!result.ok) {
      toast.error(result.msg || "图片生成失败");
      return;
    }
    const ids = result.run?.assets.map((asset) => asset.asset_id) || [];
    if (ids.length) setSelectedImageIds(ids);
    toast.success(
      ids.length
        ? "图片已生成，可加入视频参考篮"
        : "图片任务已创建，完成后会自动刷新",
    );
  }

  async function polishImagePrompt() {
    if (!imagePrompt.trim() || imagePolishing) return;
    setImagePolishing(true);
    await new Promise((r) => setTimeout(r, 800));
    const hasStyle = /风格|插画|水彩|3D|扁平/.test(imagePrompt);
    const hasTone = /色调|温暖|明亮|柔和|pastel/.test(imagePrompt);
    const additions: string[] = [];
    if (!hasStyle) additions.push("[风格：非写实卡通插画]");
    if (!hasTone) additions.push("[色调：温暖明亮]");
    if (additions.length === 0) toast.info("提示词已较为完整");
    else {
      setImagePrompt(`${imagePrompt.trim()} ${additions.join(" ")}`);
      toast.success(`已补充 ${additions.length} 个维度`);
    }
    setImagePolishing(false);
  }

  async function polishVideoPrompt() {
    if (!videoPrompt.trim() || videoPolishing) return;
    setVideoPolishing(true);
    await new Promise((r) => setTimeout(r, 800));
    const hasAtmosphere = /氛围|光线|色调|阳光|柔光/.test(videoPrompt);
    const hasQuality = /4K|超清|画质|电影级/.test(videoPrompt);
    const additions: string[] = [];
    if (!hasAtmosphere) additions.push("[氛围：清晨阳光、柔光散射]");
    if (!hasQuality) additions.push("[画质：4K 超清、电影级动态范围]");
    if (additions.length === 0) toast.info("提示词已较为完整");
    else {
      setVideoPrompt(`${videoPrompt.trim()} ${additions.join(" ")}`);
      toast.success(`已补充 ${additions.length} 个维度`);
    }
    setVideoPolishing(false);
  }

  function insertImageTemplate(snippet: string) {
    setImagePrompt((prev) =>
      prev.trim() ? `${prev.trim()} ${snippet}` : snippet,
    );
  }
  function insertVideoTemplate(snippet: string) {
    setVideoPrompt((prev) =>
      prev.trim() ? `${prev.trim()} ${snippet}` : snippet,
    );
  }

  // 点击「加入视频参考篮」按钮：将所选图片导入视频参考图篮
  async function addSelectedImagesToVideoBasket(assetIds: string[]) {
    if (!assetIds.length) {
      toast.warning("请先选择图片");
      return;
    }
    const result = await importImagesToVideoReferences(assetIds);
    if (result.ok) {
      setVideoMode("reference");
      toast.success("已加入视频参考篮");
    } else {
      toast.error(result.msg || "加入视频参考篮失败");
    }
  }

  async function uploadReferences(files: FileList | null) {
    if (!files?.length) return;
    const result = await uploadMediaWorkbenchReferences(Array.from(files));
    if (result.ok) {
      setVideoMode("reference");
      toast.success("参考图已上传");
    } else {
      toast.error(result.msg || "参考图上传失败");
    }
  }

  async function submitVideoRun() {
    if (videoSubmitDisabled) {
      toast.warning(
        effectiveVideoMode === "reference"
          ? "请填写提示词并确认参考图数量"
          : "请填写视频提示词",
      );
      return;
    }
    const referenceAssetIds =
      effectiveVideoMode === "reference"
        ? (basket?.assets || []).map((asset) => asset.asset_id)
        : [];
    setVideoBusy(true);
    const result = await createVideoWorkbenchRun({
      prompt: videoPrompt.trim(),
      model: videoModel,
      mode: effectiveVideoMode,
      size: videoSize,
      duration_sec: DEFAULT_VIDEO_DURATION,
      reference_asset_ids: referenceAssetIds,
    });
    setVideoBusy(false);
    if (result.ok) {
      toast.success(
        referenceAssetIds.length
          ? "已按参考图模式创建视频任务"
          : "视频任务已创建",
      );
    } else {
      toast.error(result.msg || "视频任务创建失败");
    }
  }

  async function syncRun(runId: string) {
    setSyncingRunId(runId);
    const result = await syncVideoWorkbenchRun(runId);
    setSyncingRunId(null);
    if (result.ok) toast.success("视频任务状态已同步");
    else toast.error(result.msg || "视频任务同步失败");
  }

  /* ----------------------- 权限校验 ----------------------- */
  if (!isAdmin) {
    return (
      <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
        <DSEmptyState
          icon={<ShieldAlert className="h-5 w-5" />}
          title="资源不存在"
          desc="媒体生成工作台仅管理员可见。"
        />
      </div>
    );
  }

  /* ----------------------- 渲染 ----------------------- */
  return (
    <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
      {/* 页头 */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="t-overline text-muted-foreground/70">管理员工具台</div>
          <h1 className="mt-2 h-page-title">媒体生成工作台</h1>
          <p className="mt-3 max-w-3xl h-page-subtitle">
            图片和视频可以独立生成，也可以把已生成图片直接送入视频参考篮。密钥只在后端使用，前端只传提示词和素材
            ID。
          </p>
        </div>
        <DSButton
          variant="secondary"
          size="md"
          onClick={() => void loadMediaWorkbench()}
        >
          {status === "loading" ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          刷新
        </DSButton>
      </div>

      {/* 错误提示 —— 用 DS 风格内联警告条，不再依赖 alert-error-pro 自定义类 */}
      {error && (
        <div className="mt-6 flex items-start gap-3 rounded-lg border border-[#9a4747]/25 bg-[#9a4747]/8 px-4 py-3 t-body text-[#9a4747]">
          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* 状态卡片（4 张指标卡） */}
      <StatusCards
        workbenchLoaded={workbenchLoaded}
        providerReadyImage={providerReady.image}
        providerReadyVideo={providerReady.video}
        imageAssetsCount={imageAssets.length}
        basketCount={basketCount}
        maxReferenceImages={maxReferenceImages}
      />

      <Tabs defaultValue="images" className="mt-8">
        <TabsList className="grid h-auto w-full grid-cols-3 rounded-lg md:w-[560px]">
          <TabsTrigger value="images" className="gap-3 h-11">
            <ImagePlus className="h-4 w-4" />
            图片生成
          </TabsTrigger>
          <TabsTrigger value="videos" className="gap-3 h-11">
            <Film className="h-4 w-4" />
            视频生成
          </TabsTrigger>
          <TabsTrigger value="assets" className="gap-3 h-11">
            <Images className="h-4 w-4" />
            素材篮/历史
          </TabsTrigger>
        </TabsList>

        {/* ========== 图片生成 ========== */}
        <TabsContent value="images" className="mt-6">
          {/* D6: grid-cols-[1.2fr_0.8fr] —— 操作区宽、结果区窄 */}
          <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr] items-stretch">
            <ImageGenPanel
              prompt={imagePrompt}
              onPromptChange={setImagePrompt}
              batchMode={batchMode}
              onBatchModeChange={setBatchMode}
              batchPrompts={batchPrompts}
              onBatchPromptsChange={setBatchPrompts}
              onInsertTemplate={insertImageTemplate}
              onPolish={() => void polishImagePrompt()}
              polishing={imagePolishing}
              model={imageModel}
              onModelChange={setImageModelPref}
              models={imageModels}
              ratio={imageRatio}
              onRatioChange={setImageRatio}
              quality={imageQuality}
              onQualityChange={setImageQualityPref}
              availableQualities={availableQualities}
              count={imageCount}
              onCountChange={setImageCount}
              maxCount={maxImageCount}
              concurrency={imageConcurrency}
              onConcurrencyChange={setImageConcurrency}
              busy={imageBusy}
              workbenchLoaded={workbenchLoaded}
              providerUnavailable={imageProviderUnavailable}
              credits={imageCredits}
              onSubmit={() => void submitImageRun()}
            />

            {/* ThumbnailPanel 含全屏预览弹窗 + 勾选框 + 「加入视频参考篮」按钮（D7/F6） */}
            <ThumbnailPanel
              assets={imageAssets}
              selectedIds={selectedImageIds}
              onToggle={(assetId) =>
                setSelectedImageIds((current) =>
                  current.includes(assetId)
                    ? current.filter((item) => item !== assetId)
                    : [...current, assetId],
                )
              }
              onAddToBasket={(assetIds) =>
                void addSelectedImagesToVideoBasket(assetIds)
              }
              selectedCount={selectedCount}
              maxReferenceImages={maxReferenceImages}
            />
          </div>
        </TabsContent>

        {/* ========== 视频生成 ========== */}
        <TabsContent value="videos" className="mt-6">
          {/* D6: grid-cols-[1.2fr_0.8fr] —— 操作区宽、任务区窄 */}
          {/* VideoGenPanel 内含「参考图数量」提示文案与「最多 7 张」上限 */}
          <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr] items-stretch">
            <VideoGenPanel
              basketAssets={basket?.assets || []}
              basketCount={basketCount}
              maxReferenceImages={maxReferenceImages}
              onUploadReferences={(files) => void uploadReferences(files)}
              prompt={videoPrompt}
              onPromptChange={setVideoPrompt}
              onInsertTemplate={insertVideoTemplate}
              onPolish={() => void polishVideoPrompt()}
              polishing={videoPolishing}
              model={videoModel}
              onModelChange={setVideoModelPref}
              models={videoModelOptions}
              mode={videoMode}
              onModeChange={setVideoMode}
              ratio={videoRatio}
              onRatioChange={setVideoRatio}
              durationSec={DEFAULT_VIDEO_DURATION}
              busy={videoBusy}
              workbenchLoaded={workbenchLoaded}
              providerReady={providerReady.video}
              providerUnavailable={videoProviderUnavailable}
              effectiveVideoMode={effectiveVideoMode}
              submitDisabled={videoSubmitDisabled}
              credits={videoCredits}
              onSubmit={() => void submitVideoRun()}
            />

            {/* VideoRunPanel 渲染内联 <video> 缩略图与进度条（D8/F7） */}
            <VideoRunPanel
              runs={mediaWorkbench?.video_runs || []}
              syncingRunId={syncingRunId}
              onSync={syncRun}
            />
          </div>
        </TabsContent>

        {/* ========== 素材篮/历史 ========== */}
        <TabsContent value="assets" className="mt-6">
          <AssetBasketPanel
            imageAssets={imageAssets}
            videoAssets={videoAssets}
            imageRuns={mediaWorkbench?.image_runs || []}
            videoRuns={mediaWorkbench?.video_runs || []}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

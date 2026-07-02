"use client";

import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useAppStore } from "@/lib/store";
import type { MediaAsset, VideoGenerationMode } from "@/lib/types";
import { downloadMediaWorkbenchAsset, downloadVideoWorkbenchRun } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import {
  DSButton,
  DSCard,
  DSSectionTitle,
  DSBadge,
  DSPill,
  DSEmptyState,
  DSProgress,
  DSStatusDot,
} from "@/components/ui/ds";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Download,
  Film,
  ImagePlus,
  Images,
  Layers,
  Loader2,
  Monitor,
  RefreshCw,
  Send,
  ShieldAlert,
  Smartphone,
  Sparkles,
  Upload,
  Wand2,
  Zap,
} from "lucide-react";
import { toast } from "sonner";

const DEFAULT_IMAGE_MODEL = "gpt-image-2";
const DEFAULT_IMAGE_SIZE = "1920x1080";
const DEFAULT_IMAGE_QUALITY = "high";
const DEFAULT_VIDEO_MODEL = "omni_flash-10s";
const DEFAULT_VIDEO_SIZE = "1280x720";
const DEFAULT_VIDEO_DURATION = 10;

const PROMPT_TEMPLATES_IMAGE: { label: string; snippet: string }[] = [
  { label: "主体", snippet: "[主体：明亮的小学数学课堂，桌面上有彩色计数棒和练习卡]" },
  { label: "风格", snippet: "[风格：非写实卡通插画 / 水彩手绘 / 3D 渲染 / 简约扁平]" },
  { label: "色调", snippet: "[色调：温暖明亮 / 柔和 pastel / 高饱和度 / 冷色调]" },
  { label: "构图", snippet: "[构图：俯视桌面 / 侧面视角 / 居中对称 / 三分法]" },
  { label: "细节", snippet: "[细节：无文字水印 / 高清细节 / 景深虚化 / 干净背景]" },
];

const PROMPT_TEMPLATES_VIDEO: { label: string; snippet: string }[] = [
  { label: "主体", snippet: "[主体：温暖明亮的小学数学课堂]" },
  { label: "动作", snippet: "[动作：镜头缓慢推进桌面上的计数棒和卡片]" },
  { label: "运镜", snippet: "[运镜：缓慢推进 / 横向平移 / 环绕拍摄 / 固定机位]" },
  { label: "氛围", snippet: "[氛围：清晨阳光 / 暖色调 / 柔光散射]" },
  { label: "画质", snippet: "[画质：4K 超清 / 电影级动态范围 / 浅景深虚化]" },
];

// DSButton-equivalent anchor styles (for download links that must render as <a>)
const DS_ANCHOR_PRIMARY_SM =
  "inline-flex items-center justify-center gap-3 font-medium rounded-lg transition-all duration-300 ease-apple focus-ring whitespace-nowrap h-9 px-3.5 text-xs bg-[#1a2b3c] text-white shadow-[0_4px_12px_rgba(26,43,60,0.25),0_8px_20px_-4px_rgba(26,43,60,0.20)] hover:bg-[#142233] hover:-translate-y-0.5 hover:shadow-[0_6px_16px_rgba(26,43,60,0.30),0_12px_28px_-6px_rgba(26,43,60,0.25)] active:translate-y-0";

const DS_ANCHOR_SECONDARY_SM =
  "inline-flex items-center justify-center gap-3 font-medium rounded-lg transition-all duration-300 ease-apple focus-ring whitespace-nowrap h-9 px-3.5 text-xs bg-transparent text-foreground border border-border hover:border-bronze/50 hover:text-bronze hover:bg-bronze/5 hover:-translate-y-0.5 active:translate-y-0";

// DSPill-equivalent button styles (for template tag buttons that need onClick)
const DS_PILL_BTN_H8 =
  "inline-flex h-8 items-center gap-3 rounded-full px-4 text-xs font-medium transition-all duration-300 ease-apple bg-muted text-foreground hover:bg-muted/70 hover:border-border border border-transparent cursor-pointer focus-ring";

export function AdminMediaWorkbenchScreen() {
  const user = useAppStore((s) => s.user);
  const isAdmin = user?.role === "admin";
  const mediaWorkbench = useAppStore((s) => s.mediaWorkbench);
  const status = useAppStore((s) => s.mediaWorkbenchStatus);
  const error = useAppStore((s) => s.mediaWorkbenchError);
  const loadMediaWorkbench = useAppStore((s) => s.loadMediaWorkbench);
  const createImageWorkbenchRun = useAppStore((s) => s.createImageWorkbenchRun);
  const uploadMediaWorkbenchReferences = useAppStore((s) => s.uploadMediaWorkbenchReferences);
  const importImagesToVideoReferences = useAppStore((s) => s.importImagesToVideoReferences);
  const createVideoWorkbenchRun = useAppStore((s) => s.createVideoWorkbenchRun);
  const syncVideoWorkbenchRun = useAppStore((s) => s.syncVideoWorkbenchRun);

  const [imagePrompt, setImagePrompt] = useState("");
  const [imageModel, setImageModel] = useState(DEFAULT_IMAGE_MODEL);
  const [imageSize, setImageSize] = useState(DEFAULT_IMAGE_SIZE);
  const [imageQuality, setImageQuality] = useState(DEFAULT_IMAGE_QUALITY);
  const [imageCount, setImageCount] = useState("1");
  const [selectedImageIds, setSelectedImageIds] = useState<string[]>([]);
  const [imageBusy, setImageBusy] = useState(false);
  const [imagePolishing, setImagePolishing] = useState(false);

  const [videoPrompt, setVideoPrompt] = useState("");
  const [videoMode, setVideoMode] = useState<VideoGenerationMode>("text");
  const [videoModel, setVideoModel] = useState(DEFAULT_VIDEO_MODEL);
  const [videoSize, setVideoSize] = useState(DEFAULT_VIDEO_SIZE);
  const [videoBusy, setVideoBusy] = useState(false);
  const [videoPolishing, setVideoPolishing] = useState(false);
  const [syncingRunId, setSyncingRunId] = useState<string | null>(null);

  useEffect(() => {
    if (!isAdmin) return;
    void loadMediaWorkbench();
  }, [isAdmin, loadMediaWorkbench]);

  const imageAssets = useMemo(
    () => (mediaWorkbench?.assets || []).filter((asset) => asset.asset_type === "image"),
    [mediaWorkbench?.assets],
  );
  const videoAssets = useMemo(
    () => (mediaWorkbench?.assets || []).filter((asset) => asset.asset_type === "video"),
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
  const effectiveVideoMode: VideoGenerationMode = basketCount > 0 ? "reference" : videoMode;
  const videoSubmitDisabled =
    videoBusy ||
    !workbenchLoaded ||
    videoProviderUnavailable ||
    !videoPrompt.trim() ||
    (effectiveVideoMode === "reference" && basketCount < 1) ||
    basketCount > maxReferenceImages;

  const imageCredits = (() => {
    const base = Number.parseInt(imageCount, 10) || 1;
    const qualityFactor = imageQuality === "high" ? 1.5 : 1.0;
    return Math.ceil(base * qualityFactor * 5);
  })();
  const videoCredits = 15;

  async function submitImageRun() {
    if (!imagePrompt.trim()) { toast.warning("请先填写图片提示词"); return; }
    setImageBusy(true);
    const result = await createImageWorkbenchRun({
      prompt: imagePrompt.trim(), model: imageModel, size: imageSize,
      quality: imageQuality, count: Number.parseInt(imageCount, 10) || 1,
    });
    setImageBusy(false);
    if (!result.ok) { toast.error(result.msg || "图片生成失败"); return; }
    const ids = result.run?.assets.map((asset) => asset.asset_id) || [];
    setSelectedImageIds(ids);
    toast.success("图片已生成，可加入视频参考篮");
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
    else { setImagePrompt(`${imagePrompt.trim()} ${additions.join(" ")}`); toast.success(`已补充 ${additions.length} 个维度`); }
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
    else { setVideoPrompt(`${videoPrompt.trim()} ${additions.join(" ")}`); toast.success(`已补充 ${additions.length} 个维度`); }
    setVideoPolishing(false);
  }

  function insertImageTemplate(snippet: string) {
    setImagePrompt((prev) => (prev.trim() ? `${prev.trim()} ${snippet}` : snippet));
  }
  function insertVideoTemplate(snippet: string) {
    setVideoPrompt((prev) => (prev.trim() ? `${prev.trim()} ${snippet}` : snippet));
  }

  async function addSelectedImagesToVideoBasket() {
    if (!selectedImageIds.length) { toast.warning("请先选择图片"); return; }
    const result = await importImagesToVideoReferences(selectedImageIds);
    if (result.ok) { setVideoMode("reference"); toast.success("已加入视频参考篮"); }
    else toast.error(result.msg || "加入视频参考篮失败");
  }

  async function uploadReferences(files: FileList | null) {
    if (!files?.length) return;
    const result = await uploadMediaWorkbenchReferences(Array.from(files));
    if (result.ok) { setVideoMode("reference"); toast.success("参考图已上传"); }
    else toast.error(result.msg || "参考图上传失败");
  }

  async function submitVideoRun() {
    if (videoSubmitDisabled) {
      toast.warning(effectiveVideoMode === "reference" ? "请填写提示词并确认参考图数量" : "请填写视频提示词");
      return;
    }
    const referenceAssetIds = effectiveVideoMode === "reference" ? (basket?.assets || []).map((asset) => asset.asset_id) : [];
    setVideoBusy(true);
    const result = await createVideoWorkbenchRun({
      prompt: videoPrompt.trim(), model: videoModel, mode: effectiveVideoMode,
      size: videoSize, duration_sec: DEFAULT_VIDEO_DURATION, reference_asset_ids: referenceAssetIds,
    });
    setVideoBusy(false);
    if (result.ok) toast.success("视频任务已创建");
    else toast.error(result.msg || "视频任务创建失败");
  }

  async function syncRun(runId: string) {
    setSyncingRunId(runId);
    const result = await syncVideoWorkbenchRun(runId);
    setSyncingRunId(null);
    if (result.ok) toast.success("视频任务状态已同步");
    else toast.error(result.msg || "视频任务同步失败");
  }

  if (!isAdmin) {
    return (
      <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
        <DSEmptyState icon={<ShieldAlert className="h-5 w-5" />} title="资源不存在" desc="媒体生成工作台仅管理员可见。" />
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
      {/* 页头 */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="t-overline text-muted-foreground/70">管理员工具台</div>
          <h1 className="mt-2 h-page-title">媒体生成工作台</h1>
          <p className="mt-3 max-w-3xl h-page-subtitle">
            图片和视频可以独立生成，也可以把已生成图片直接送入视频参考篮。密钥只在后端使用，前端只传提示词和素材 ID。
          </p>
        </div>
        <DSButton variant="secondary" size="md" onClick={() => void loadMediaWorkbench()}>
          {status === "loading" ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          刷新
        </DSButton>
      </div>

      {error && (
        <div className="alert-error-pro mt-6">
          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
          <span className="t-body">{error}</span>
        </div>
      )}

      {/* VLM 修复：状态卡片 — 检测中用 loading-dot 轻量动画 */}
      <div className="mt-6 grid gap-4 md:grid-cols-4 items-stretch">
        <StatusTile icon={<ImagePlus className="h-4 w-4" />} label="图片接口"
          value={!workbenchLoaded ? "检测中" : providerReady.image ? "已连接" : "未连接"}
          loading={!workbenchLoaded}
          tone={!workbenchLoaded ? "neutral" : providerReady.image ? "success" : "warning"} />
        <StatusTile icon={<Film className="h-4 w-4" />} label="视频接口"
          value={!workbenchLoaded ? "检测中" : providerReady.video ? "已连接" : "未连接"}
          loading={!workbenchLoaded}
          tone={!workbenchLoaded ? "neutral" : providerReady.video ? "success" : "warning"} />
        <StatusTile icon={<Images className="h-4 w-4" />} label="图片素材"
          value={`${imageAssets.length} 张`} tone="info" />
        <StatusTile icon={<Layers className="h-4 w-4" />} label="视频参考篮"
          value={`${basketCount} / ${maxReferenceImages}`}
          tone={basketCount > maxReferenceImages ? "warning" : basketCount > 0 ? "success" : "neutral"} />
      </div>

      <Tabs defaultValue="images" className="mt-8">
        <TabsList className="grid h-auto w-full grid-cols-3 rounded-lg md:w-[560px]">
          <TabsTrigger value="images" className="gap-3 h-11"><ImagePlus className="h-4 w-4" />图片生成</TabsTrigger>
          <TabsTrigger value="videos" className="gap-3 h-11"><Film className="h-4 w-4" />视频生成</TabsTrigger>
          <TabsTrigger value="assets" className="gap-3 h-11"><Images className="h-4 w-4" />素材篮/历史</TabsTrigger>
        </TabsList>

        {/* ========== 图片生成 ========== */}
        <TabsContent value="images" className="mt-6">
          <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr] items-stretch">
            <DSCard className="h-full">
              <DSSectionTitle icon={<ImagePlus className="h-4 w-4" />} title="图片生成" desc="默认 gpt-image-2 / 1920x1080 / high" />

              {/* 结构化模板 */}
              <div className="mt-4">
                <div className="mb-3 flex items-center gap-3 t-overline text-muted-foreground/70">
                  <Wand2 className="h-3 w-3" />结构化模板
                </div>
                <div className="flex flex-wrap gap-3">
                  {PROMPT_TEMPLATES_IMAGE.map((tpl) => (
                    <button key={tpl.label} type="button" onClick={() => insertImageTemplate(tpl.snippet)}
                      className={DS_PILL_BTN_H8}>
                      {tpl.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* VLM 修复：AI 润色改为链接式（降低视觉权重） */}
              <div className="mt-4 flex flex-col gap-3">
                <div className="flex items-center justify-between gap-3">
                  <Label className="t-caption text-muted-foreground">图片提示词</Label>
                  <div className="flex items-center gap-4">
                    <button type="button" onClick={() => void polishImagePrompt()}
                      disabled={!imagePrompt.trim() || imagePolishing} className="ai-polish-link">
                      {imagePolishing ? <Loader2 className="h-3 w-3 animate-spin" /> : <Wand2 className="h-3 w-3" />}AI 润色
                    </button>
                    <span className="t-caption tabular-nums text-muted-foreground">{imagePrompt.length}/2000</span>
                  </div>
                </div>
                <Textarea value={imagePrompt} onChange={(event) => setImagePrompt(event.target.value)}
                  className="input-pro min-h-[100px] bg-background"
                  placeholder="例如：明亮的小学数学课堂，桌面上有彩色计数棒和练习卡，非写实卡通插画风格，无文字。" />
              </div>

              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <SelectField label="模型" value={imageModel} onValueChange={setImageModel} values={[DEFAULT_IMAGE_MODEL]} />
                <SelectField label="尺寸" value={imageSize} onValueChange={setImageSize} values={["1920x1080", "1024x1024", "1080x1920"]} />
                <SelectField label="质量" value={imageQuality} onValueChange={setImageQuality} values={["high", "low"]} />
                <SelectField label="张数" value={imageCount} onValueChange={setImageCount} values={["1", "2", "3", "4"]} />
              </div>

              {/* VLM 修复：积分提示柔化为灰色小字 */}
              <DSButton variant="primary" size="lg" className="mt-6 w-full font-semibold"
                onClick={() => void submitImageRun()} disabled={imageBusy || !workbenchLoaded || imageProviderUnavailable}>
                {imageBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                <span>生成图片</span>
                <span className="credits-hint">≈{imageCredits} 积分</span>
              </DSButton>
              {imageProviderUnavailable && (
                <div className="alert-warning-pro mt-3 t-caption">
                  <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                  <span>后端没有检测到图片生成接口配置，暂时不能提交真实生图任务。</span>
                </div>
              )}
            </DSCard>

            <DSCard className="h-full">
              <DSSectionTitle icon={<Images className="h-4 w-4" />} title="图片结果" desc="选择后可加入视频参考篮" />
              <AssetGrid assets={imageAssets} selectedIds={selectedImageIds}
                onToggle={(assetId) => setSelectedImageIds((current) =>
                  current.includes(assetId) ? current.filter((item) => item !== assetId) : [...current, assetId])} />
              <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="t-caption text-muted-foreground">
                  已选择 <span className="font-semibold text-foreground">{selectedCount}</span> 张 · 参考篮最多 {maxReferenceImages} 张
                </p>
                <DSButton variant="secondary" size="md"
                  onClick={() => void addSelectedImagesToVideoBasket()} disabled={selectedCount === 0}>
                  <Send className="h-4 w-4" />加入视频参考篮
                </DSButton>
              </div>
            </DSCard>
          </div>
        </TabsContent>

        {/* ========== 视频生成 — 小云雀规范核心 ========== */}
        <TabsContent value="videos" className="mt-6">
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px] items-stretch">
            <DSCard className="h-full">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <DSSectionTitle className="mb-0" icon={<Film className="h-4 w-4" />} title="视频生成" desc="Omni 默认生成 10 秒横版视频" />
                <DSBadge variant={providerReady.video ? "success" : "neutral"}>
                  {providerReady.video ? "真实接口已连接" : "检测中"}
                </DSBadge>
              </div>

              {/* 参考图篮 + 提示词 */}
              <div className="mt-6 rounded-xl border border-border bg-gradient-to-br from-muted/30 to-muted/10 p-4">
                <div className="mb-4 flex items-center justify-between">
                  <div className="t-overline text-muted-foreground/70">参考图篮</div>
                  <span className={cn("t-caption font-semibold", basketCount > 0 ? "text-success" : "text-muted-foreground")}>
                    {basketCount} / {maxReferenceImages}
                  </span>
                </div>
                <div className="grid gap-4 lg:grid-cols-[100px_minmax(0,1fr)]">
                  <label className="group flex h-[100px] cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-border bg-card transition-all duration-300 ease-apple hover:border-bronze/50 hover:bg-bronze/5">
                    <Upload className="h-5 w-5 text-muted-foreground transition-colors group-hover:text-bronze" />
                    <span className="mt-2 text-xs font-medium text-foreground">上传参考图</span>
                    <span className="text-[11px] text-muted-foreground">点击/拖拽</span>
                    <input type="file" accept="image/*" multiple className="sr-only" onChange={(event) => void uploadReferences(event.target.files)} />
                  </label>
                  <div className="flex flex-col gap-3">
                    <div className="flex items-center justify-between gap-3">
                      <Label className="t-caption text-muted-foreground">视频提示词</Label>
                      <div className="flex items-center gap-4">
                        {/* VLM 修复：AI 润色改为链接式 */}
                        <button type="button" onClick={() => void polishVideoPrompt()}
                          disabled={!videoPrompt.trim() || videoPolishing} className="ai-polish-link">
                          {videoPolishing ? <Loader2 className="h-3 w-3 animate-spin" /> : <Wand2 className="h-3 w-3" />}AI 润色
                        </button>
                        <span className="t-caption tabular-nums text-muted-foreground">{videoPrompt.length}/5000</span>
                      </div>
                    </div>
                    <Textarea value={videoPrompt} onChange={(event) => setVideoPrompt(event.target.value)}
                      className="input-pro min-h-[100px] resize-none bg-background"
                      placeholder="描述你想生成的视频内容，例如：温暖明亮的小学数学课堂导入镜头，镜头缓慢推进桌面上的计数棒和卡片。" />
                  </div>
                </div>

                {/* 结构化模板 */}
                <div className="mt-4">
                  <div className="mb-3 flex items-center gap-3 t-overline text-muted-foreground/70">
                    <Wand2 className="h-3 w-3" />结构化模板
                  </div>
                  <div className="flex flex-wrap gap-3">
                    {PROMPT_TEMPLATES_VIDEO.map((tpl) => (
                      <button key={tpl.label} type="button" onClick={() => insertVideoTemplate(tpl.snippet)}
                        className={DS_PILL_BTN_H8}>
                        {tpl.label}
                      </button>
                    ))}
                  </div>
                </div>

                {basketCount > 0 && <MiniAssetList assets={basket?.assets || []} compact />}

                {/* Pill 参数 + CTA */}
                <div className="mt-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div className="flex flex-wrap gap-3">
                    <PillSelect icon={<span className="text-sm font-semibold">O</span>} value={videoModel} onValueChange={setVideoModel} values={[DEFAULT_VIDEO_MODEL]} />
                    <PillSelect icon={<Film className="h-4 w-4" />} value={effectiveVideoMode} onValueChange={(value) => setVideoMode(value as VideoGenerationMode)} values={["text", "reference"]} />
                    <PillSelect icon={<Monitor className="h-4 w-4" />} value={videoSize} onValueChange={setVideoSize} values={["1280x720"]} />
                    <ReadonlyPill icon={<Smartphone className="h-4 w-4" />} value={`${DEFAULT_VIDEO_DURATION} 秒`} />
                  </div>
                  {/* VLM 修复：CTA 深色强化 + 积分柔化 */}
                  <DSButton variant="primary" size="lg" className="shrink-0" disabled={videoSubmitDisabled} onClick={() => void submitVideoRun()}>
                    {videoBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
                    <span>生成 10 秒视频</span>
                    <span className="credits-hint">≈{videoCredits} 积分</span>
                  </DSButton>
                </div>
              </div>

              {videoProviderUnavailable && (
                <div className="alert-warning-pro mt-3 t-caption">
                  <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                  <span>后端没有检测到视频生成接口配置，暂时不能提交真实视频任务。</span>
                </div>
              )}
            </DSCard>

            {/* VLM 修复：任务队列 — 状态视觉区分 + 占位卡片 */}
            <DSCard className="h-full p-4">
              <div className="module-card-header-pro !px-0 !border-0 !pb-3">
                <div className="title-block">
                  <div className="overline">任务队列</div>
                  <h3>视频任务</h3>
                </div>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </div>
              <RunList runs={mediaWorkbench?.video_runs || []} syncingRunId={syncingRunId} onSync={syncRun} />
            </DSCard>
          </div>
        </TabsContent>

        {/* ========== 素材篮/历史 ========== */}
        <TabsContent value="assets" className="mt-6">
          <div className="grid gap-6 xl:grid-cols-[1fr_1fr] items-stretch">
            <DSCard className="h-full">
              <DSSectionTitle icon={<Images className="h-4 w-4" />} title="素材库" desc="图片、上传参考图和视频输出统一保存" />
              <AssetList assets={[...imageAssets, ...videoAssets]} />
            </DSCard>
            <DSCard className="h-full">
              <DSSectionTitle icon={<RefreshCw className="h-4 w-4" />} title="历史任务" desc="图片任务和视频任务" />
              <HistoryList imageRuns={mediaWorkbench?.image_runs || []} videoRuns={mediaWorkbench?.video_runs || []} />
            </DSCard>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

/* ==================== 子组件 ==================== */

// VLM 修复：StatusTile — loading 态用 loading-dot；用 DSCard + DSBadge 重写
function StatusTile({ icon, label, value, tone, loading }: {
  icon: ReactNode; label: string; value: string;
  tone: "success" | "warning" | "info" | "neutral"; loading?: boolean;
}) {
  const toneText =
    tone === "success" ? "stat-value-success"
    : tone === "info" ? "stat-value-info"
    : tone === "warning" ? "stat-value-warning"
    : "text-foreground font-semibold";
  const iconClass =
    tone === "success" ? "text-success"
    : tone === "info" ? "text-info"
    : tone === "warning" ? "text-warning"
    : "text-muted-foreground";
  const badgeVariant =
    tone === "success" ? "success"
    : tone === "info" ? "info"
    : tone === "warning" ? "warning"
    : "neutral";
  return (
    <DSCard hover={false} className="h-full p-4">
      <div className="flex items-center justify-between">
        <span className="t-caption font-medium text-muted-foreground">{label}</span>
        <span className={iconClass}>{icon}</span>
      </div>
      <div className={cn("mt-3 flex items-center gap-3 text-lg", toneText)}>
        {loading && <span className="loading-dot" />}
        {value}
      </div>
      <div className="mt-3">
        <DSBadge variant={badgeVariant}>{value}</DSBadge>
      </div>
    </DSCard>
  );
}

function SelectField({ label, value, values, onValueChange }: { label: string; value: string; values: string[]; onValueChange: (value: string) => void; }) {
  return (
    <div className="form-field-pro">
      <Label>{label}</Label>
      <Select value={value} onValueChange={onValueChange}>
        <SelectTrigger className="input-pro ctrl-md bg-background"><SelectValue /></SelectTrigger>
        <SelectContent>{values.map((item) => (<SelectItem key={item} value={item}>{item}</SelectItem>))}</SelectContent>
      </Select>
    </div>
  );
}

function PillSelect({ icon, value, values, onValueChange }: { icon: ReactNode; value: string; values: string[]; onValueChange: (value: string) => void; }) {
  return (
    <DSPill className="w-auto p-0">
      <span className="text-muted-foreground">{icon}</span>
      <Select value={value} onValueChange={onValueChange}>
        <SelectTrigger className="h-10 w-auto border-0 bg-transparent px-0 shadow-none focus:ring-0 focus-visible:ring-0">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>{values.map((item) => (<SelectItem key={item} value={item}>{item}</SelectItem>))}</SelectContent>
      </Select>
    </DSPill>
  );
}

function ReadonlyPill({ icon, value }: { icon: ReactNode; value: string }) {
  return (
    <DSPill>
      <span className="text-muted-foreground">{icon}</span><span className="font-medium">{value}</span>
    </DSPill>
  );
}

function AssetGrid({ assets, selectedIds, onToggle }: { assets: MediaAsset[]; selectedIds: string[]; onToggle: (assetId: string) => void; }) {
  if (!assets.length) {
    return (
      <DSEmptyState className="mt-6"
        icon={<Images className="h-5 w-5" />}
        title="暂无图片素材"
        desc="先在左侧生成图片，结果会出现在这里。" />
    );
  }
  return (
    <div className="mt-6 grid max-h-[520px] gap-4 overflow-y-auto scroll-fine sm:grid-cols-2">
      {assets.map((asset) => {
        const selected = selectedIds.includes(asset.asset_id);
        return (
          <button key={asset.asset_id} type="button" onClick={() => onToggle(asset.asset_id)}
            className={cn("group overflow-hidden rounded-lg border bg-background text-left focus-ring transition-all duration-300 ease-apple",
              selected ? "border-primary ring-2 ring-primary/25 shadow-apple-sm" : "border-border hover:border-bronze/40 hover:-translate-y-0.5")}>
            <div className="aspect-video overflow-hidden bg-muted">
              <img src={downloadMediaWorkbenchAsset(asset.asset_id)} alt={asset.filename}
                className="h-full w-full object-cover transition-transform duration-500 ease-apple group-hover:scale-[1.04]" />
            </div>
            <div className="flex items-start gap-3 p-3">
              <Checkbox checked={selected} className="mt-0.5" aria-label="选择图片素材" />
              <div className="min-w-0">
                <div className="truncate t-body font-medium text-foreground">{asset.filename}</div>
                <p className="line-clamp-2 t-caption text-muted-foreground">{asset.prompt || asset.source}</p>
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}

function MiniAssetList({ assets, compact = false }: { assets: MediaAsset[]; compact?: boolean }) {
  if (!assets.length) return null;
  return (
    <div className={cn("mt-4 grid gap-3", compact ? "sm:grid-cols-4" : "sm:grid-cols-2")}>
      {assets.map((asset) => (
        <div key={asset.asset_id} className="flex items-center gap-3 rounded-lg border border-border bg-card p-2 transition-all duration-300 ease-apple hover:border-bronze/30 hover:shadow-apple-sm">
          <img src={downloadMediaWorkbenchAsset(asset.asset_id)} alt={asset.filename}
            className={cn("rounded object-cover", compact ? "h-9 w-12" : "h-12 w-16")} />
          {!compact && (
            <div className="min-w-0">
              <div className="truncate t-caption font-medium">{asset.filename}</div>
              <div className="t-caption text-muted-foreground">{asset.source}</div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// VLM 修复：RunList — 用 DSBadge + DSStatusDot + DSProgress 重写状态视觉
function RunList({ runs, syncingRunId, onSync }: {
  runs: Array<{ run_id: string; status: string; prompt?: string; progress?: number; download_path?: string | null; error_message?: string | null }>;
  syncingRunId: string | null; onSync: (runId: string) => Promise<void>;
}) {
  if (!runs.length) {
    // VLM 修复：空状态改为「等待生成」占位卡片
    return (
      <DSEmptyState className="mt-4"
        icon={<Clock className="h-4 w-4" />}
        title="等待生成"
        desc="提交视频生成后，任务状态会出现在这里" />
    );
  }
  return (
    <div className="mt-4 flex-1 space-y-3 overflow-y-auto scroll-fine" style={{ maxHeight: "calc(100vh - 320px)" }}>
      {runs.map((run) => {
        const isActive = run.status === "processing" || run.status === "queued";
        const dotStatus: "active" | "completed" | "failed" | "pending" =
          run.status === "completed" ? "completed"
          : run.status === "failed" ? "failed"
          : isActive ? "active"
          : "pending";
        const badgeVariant: "success" | "warning" | "error" | "info" | "neutral" =
          run.status === "failed" ? "error"
          : run.status === "completed" ? "success"
          : isActive ? "info"
          : "neutral";
        return (
          <div key={run.run_id}
            className={cn("rounded-lg border bg-background p-3 transition-all duration-300 ease-apple",
              isActive ? "border-primary/30 shadow-apple-sm" : "border-border hover:border-bronze/30")}>
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-3">
                <DSStatusDot status={dotStatus} />
                <DSBadge variant={badgeVariant}>{run.status}</DSBadge>
                {isActive && (
                  <span className="flex items-center gap-3 t-caption text-muted-foreground">
                    <Clock className="h-3 w-3" />{run.progress || 0}%
                  </span>
                )}
                {run.status === "completed" && run.download_path && (
                  <span className="flex items-center gap-3 t-caption text-success">
                    <CheckCircle2 className="h-3 w-3" />可下载
                  </span>
                )}
              </div>
              <p className="line-clamp-2 t-caption text-foreground">{run.prompt || run.run_id}</p>
              {isActive && (
                <DSProgress value={run.progress || 0} variant="default" />
              )}
              {run.error_message && (
                <div className="alert-error-pro t-caption !py-2">
                  <AlertTriangle className="h-3 w-3 shrink-0 mt-0.5" /><span>{run.error_message}</span>
                </div>
              )}
              <div className="flex shrink-0 gap-3">
                <DSButton variant="secondary" size="sm" className="t-caption"
                  onClick={() => void onSync(run.run_id)} disabled={syncingRunId === run.run_id}>
                  {syncingRunId === run.run_id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}同步
                </DSButton>
                {run.download_path && (
                  <a href={downloadVideoWorkbenchRun(run.run_id)} className={cn(DS_ANCHOR_PRIMARY_SM, "t-caption")}>
                    <Download className="h-3.5 w-3.5" />下载
                  </a>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function AssetList({ assets }: { assets: MediaAsset[] }) {
  if (!assets.length) {
    return (
      <DSEmptyState className="mt-6"
        icon={<Images className="h-5 w-5" />}
        title="暂无素材"
        desc="生成图片或视频后，素材会在这里归档。" />
    );
  }
  return (
    <div className="mt-6 max-h-[560px] space-y-3 overflow-y-auto scroll-fine">
      {assets.map((asset) => (
        <div key={asset.asset_id} className="flex items-center justify-between gap-4 rounded-lg border border-border bg-background p-3 transition-all duration-300 ease-apple hover:border-bronze/30 hover:-translate-y-0.5">
          <div className="min-w-0">
            <div className="truncate t-body font-medium text-foreground">{asset.filename}</div>
            <div className="t-caption text-muted-foreground">{asset.asset_type} · {asset.source}</div>
          </div>
          <a href={downloadMediaWorkbenchAsset(asset.asset_id)} className={DS_ANCHOR_SECONDARY_SM}>
            <Download className="h-3.5 w-3.5" />下载
          </a>
        </div>
      ))}
    </div>
  );
}

function HistoryList({ imageRuns, videoRuns }: {
  imageRuns: Array<{ run_id: string; status: string; prompt?: string; assets?: MediaAsset[] }>;
  videoRuns: Array<{ run_id: string; status: string; prompt?: string; progress?: number }>;
}) {
  const rows = [
    ...imageRuns.map((run) => ({ id: run.run_id, kind: "图片", status: run.status, prompt: run.prompt, meta: `${run.assets?.length || 0} 张` })),
    ...videoRuns.map((run) => ({ id: run.run_id, kind: "视频", status: run.status, prompt: run.prompt, meta: `${run.progress || 0}%` })),
  ];
  if (!rows.length) {
    return (
      <DSEmptyState className="mt-6"
        icon={<RefreshCw className="h-5 w-5" />}
        title="暂无历史任务"
        desc="真实生成任务会在这里保留最近记录。" />
    );
  }
  return (
    <div className="mt-6 max-h-[560px] space-y-3 overflow-y-auto scroll-fine">
      {rows.map((row) => {
        const badgeVariant: "success" | "warning" | "error" | "info" | "neutral" =
          row.status === "failed" ? "error"
          : row.status === "completed" ? "success"
          : row.status === "processing" || row.status === "queued" ? "info"
          : "neutral";
        return (
          <div key={row.id} className="rounded-lg border border-border bg-background p-3 transition-all duration-300 ease-apple hover:border-bronze/30 hover:-translate-y-0.5">
            <div className="flex items-center justify-between gap-4">
              <div className="t-caption font-medium text-muted-foreground">{row.kind} · {row.meta}</div>
              <DSBadge variant={badgeVariant}>{row.status}</DSBadge>
            </div>
            <p className="mt-2 line-clamp-2 t-caption text-foreground">{row.prompt || row.id}</p>
          </div>
        );
      })}
    </div>
  );
}

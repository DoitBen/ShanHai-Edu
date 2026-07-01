"use client";

import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useAppStore } from "@/lib/store";
import type { MediaAsset, VideoGenerationMode } from "@/lib/types";
import { downloadMediaWorkbenchAsset, downloadVideoWorkbenchRun } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
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
import { EmptyState } from "@/components/common/StateViews";
import { ToneBadge } from "@/components/common/StatusBadge";
import {
  Download,
  Film,
  ImagePlus,
  Images,
  Loader2,
  Monitor,
  Play,
  RefreshCw,
  Send,
  ShieldAlert,
  Smartphone,
  Upload,
} from "lucide-react";
import { toast } from "sonner";

const DEFAULT_IMAGE_MODEL = "gpt-image-2";
const DEFAULT_IMAGE_SIZE = "1920x1080";
const DEFAULT_IMAGE_QUALITY = "high";
const DEFAULT_VIDEO_MODEL = "omni_flash-10s";
const DEFAULT_VIDEO_SIZE = "1280x720";
const DEFAULT_VIDEO_DURATION = 10;

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

  const [videoPrompt, setVideoPrompt] = useState("");
  const [videoMode, setVideoMode] = useState<VideoGenerationMode>("text");
  const [videoModel, setVideoModel] = useState(DEFAULT_VIDEO_MODEL);
  const [videoSize, setVideoSize] = useState(DEFAULT_VIDEO_SIZE);
  const [videoBusy, setVideoBusy] = useState(false);
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

  async function submitImageRun() {
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
    setSelectedImageIds(ids);
    toast.success("图片已生成，可加入视频参考篮");
  }

  async function addSelectedImagesToVideoBasket() {
    if (!selectedImageIds.length) {
      toast.warning("请先选择图片");
      return;
    }
    const result = await importImagesToVideoReferences(selectedImageIds);
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
      toast.warning(effectiveVideoMode === "reference" ? "请填写提示词并确认参考图数量" : "请填写视频提示词");
      return;
    }
    const referenceAssetIds = effectiveVideoMode === "reference" ? (basket?.assets || []).map((asset) => asset.asset_id) : [];
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
        <EmptyState
          icon={<ShieldAlert className="h-5 w-5" />}
          title="资源不存在"
          desc="媒体生成工作台仅管理员可见。"
        />
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="t-overline text-muted-foreground/70">管理员工具台</div>
          <h1 className="mt-2 t-title">媒体生成工作台</h1>
          <p className="mt-2 max-w-3xl t-body text-muted-foreground">
            图片和视频可以独立生成，也可以把已生成图片直接送入视频参考篮。密钥只在后端使用，前端只传提示词和素材 ID。
          </p>
        </div>
        <Button variant="outline" className="gap-2" onClick={() => void loadMediaWorkbench()}>
          {status === "loading" ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          刷新
        </Button>
      </div>

      {error && (
        <Card className="mt-6 border-destructive/40 bg-destructive/5 p-4 text-destructive">
          {error}
        </Card>
      )}

      <div className="mt-6 grid gap-3 md:grid-cols-4">
        <StatusTile
          label="图片接口"
          value={!workbenchLoaded ? "检测中" : providerReady.image ? "已连接" : "未连接"}
          tone={!workbenchLoaded ? "neutral" : providerReady.image ? "success" : "warning"}
        />
        <StatusTile
          label="视频接口"
          value={!workbenchLoaded ? "检测中" : providerReady.video ? "已连接" : "未连接"}
          tone={!workbenchLoaded ? "neutral" : providerReady.video ? "success" : "warning"}
        />
        <StatusTile label="图片素材" value={`${imageAssets.length} 张`} tone="neutral" />
        <StatusTile label="视频参考篮" value={`${basketCount} / 最多 7 张`} tone={basketCount > maxReferenceImages ? "warning" : "neutral"} />
      </div>

      <Tabs defaultValue="images" className="mt-8">
        <TabsList className="grid h-auto w-full grid-cols-3 rounded-md md:w-[560px]">
          <TabsTrigger value="images" className="gap-2">
            <ImagePlus className="h-4 w-4" />
            图片生成
          </TabsTrigger>
          <TabsTrigger value="videos" className="gap-2">
            <Film className="h-4 w-4" />
            视频生成
          </TabsTrigger>
          <TabsTrigger value="assets" className="gap-2">
            <Images className="h-4 w-4" />
            素材篮/历史任务
          </TabsTrigger>
        </TabsList>

        <TabsContent value="images" className="mt-5">
          <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
            <Card className="border-border bg-card p-5 shadow-soft">
              <SectionTitle icon={<ImagePlus className="h-4 w-4" />} title="图片生成" desc="默认 gpt-image-2 / 1920x1080 / high" />
              <div className="mt-5 space-y-4">
                <div className="space-y-2">
                  <Label>图片提示词</Label>
                  <Textarea
                    value={imagePrompt}
                    onChange={(event) => setImagePrompt(event.target.value)}
                    className="min-h-36 bg-background"
                    placeholder="例如：明亮的小学数学课堂，桌面上有彩色计数棒和练习卡，非写实卡通插画风格，无文字。"
                  />
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <SelectField label="模型" value={imageModel} onValueChange={setImageModel} values={[DEFAULT_IMAGE_MODEL]} />
                  <SelectField label="尺寸" value={imageSize} onValueChange={setImageSize} values={["1920x1080", "1024x1024", "1080x1920"]} />
                  <SelectField label="质量" value={imageQuality} onValueChange={setImageQuality} values={["high", "low"]} />
                  <SelectField label="张数" value={imageCount} onValueChange={setImageCount} values={["1", "2", "3", "4"]} />
                </div>
                <Button className="w-full gap-2" onClick={() => void submitImageRun()} disabled={imageBusy || !workbenchLoaded || imageProviderUnavailable}>
                  {imageBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <ImagePlus className="h-4 w-4" />}
                  生成图片
                </Button>
                {imageProviderUnavailable && (
                  <p className="t-caption text-warning">后端没有检测到图片生成接口配置，暂时不能提交真实生图任务。</p>
                )}
              </div>
            </Card>

            <Card className="border-border bg-card p-5 shadow-soft">
              <SectionTitle icon={<Images className="h-4 w-4" />} title="图片结果" desc="选择后可加入视频参考篮" />
              <AssetGrid
                assets={imageAssets}
                selectedIds={selectedImageIds}
                onToggle={(assetId) =>
                  setSelectedImageIds((current) =>
                    current.includes(assetId)
                      ? current.filter((item) => item !== assetId)
                      : [...current, assetId],
                  )
                }
              />
              <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <p className="t-caption text-muted-foreground">已选择 {selectedCount} 张，视频参考图最多 7 张。</p>
                <Button variant="outline" className="gap-2" onClick={() => void addSelectedImagesToVideoBasket()}>
                  <Send className="h-4 w-4" />
                  加入视频参考篮
                </Button>
              </div>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="videos" className="mt-5">
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
            <Card className="border-border bg-card p-5 shadow-soft">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <SectionTitle icon={<Film className="h-4 w-4" />} title="视频生成" desc="Omni 默认生成 10 秒横版视频" />
                <ToneBadge tone={providerReady.video ? "success" : "neutral"}>
                  {providerReady.video ? "真实接口已连接" : "检测中"}
                </ToneBadge>
              </div>

              <div className="mt-5 rounded-[22px] border border-border bg-background p-4">
                <div className="grid gap-4 lg:grid-cols-[84px_minmax(0,1fr)]">
                  <label className="flex h-[76px] cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card text-muted-foreground hover:border-primary/50 hover:text-primary">
                    <Images className="h-5 w-5" />
                    <span className="mt-2 text-xs font-medium">参考图</span>
                    <span className="text-[11px]">{basketCount}/{maxReferenceImages}</span>
                    <input type="file" accept="image/*" multiple className="sr-only" onChange={(event) => void uploadReferences(event.target.files)} />
                  </label>

                  <Textarea
                    value={videoPrompt}
                    onChange={(event) => setVideoPrompt(event.target.value)}
                    className="min-h-[76px] resize-none border-0 bg-transparent px-0 py-0 text-base shadow-none focus-visible:ring-0"
                    placeholder="描述你想生成的视频内容，例如：温暖明亮的小学数学课堂导入镜头，镜头缓慢推进桌面上的计数棒和卡片。"
                  />
                </div>

                {basketCount > 0 && <MiniAssetList assets={basket?.assets || []} compact />}

                <div className="mt-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                  <div className="flex flex-wrap gap-2">
                    <PillSelect icon={<span className="text-sm font-semibold">O</span>} value={videoModel} onValueChange={setVideoModel} values={[DEFAULT_VIDEO_MODEL]} />
                    <PillSelect icon={<Film className="h-4 w-4" />} value={effectiveVideoMode} onValueChange={(value) => setVideoMode(value as VideoGenerationMode)} values={["text", "reference"]} />
                    <PillSelect icon={<Monitor className="h-4 w-4" />} value={videoSize} onValueChange={setVideoSize} values={["1280x720"]} />
                    <ReadonlyPill icon={<Smartphone className="h-4 w-4" />} value={`${DEFAULT_VIDEO_DURATION} 秒`} />
                  </div>

                  <Button className="h-10 shrink-0 gap-2 px-5" disabled={videoSubmitDisabled} onClick={() => void submitVideoRun()}>
                    {videoBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                    生成 10 秒视频
                  </Button>
                </div>
              </div>

              {videoProviderUnavailable && (
                <p className="mt-3 t-caption text-warning">后端没有检测到视频生成接口配置，暂时不能提交真实视频任务。</p>
              )}
            </Card>

            <Card className="border-border bg-card p-4 shadow-soft">
              <SectionTitle icon={<RefreshCw className="h-4 w-4" />} title="视频任务" desc="创建后可同步状态并下载 mp4" />
              <RunList runs={mediaWorkbench?.video_runs || []} syncingRunId={syncingRunId} onSync={syncRun} />
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="assets" className="mt-5">
          <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
            <Card className="border-border bg-card p-5 shadow-soft">
              <SectionTitle icon={<Images className="h-4 w-4" />} title="素材库" desc="图片、上传参考图和视频输出统一保存" />
              <AssetList assets={[...imageAssets, ...videoAssets]} />
            </Card>
            <Card className="border-border bg-card p-5 shadow-soft">
              <SectionTitle icon={<RefreshCw className="h-4 w-4" />} title="历史任务" desc="图片任务和视频任务" />
              <HistoryList imageRuns={mediaWorkbench?.image_runs || []} videoRuns={mediaWorkbench?.video_runs || []} />
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function StatusTile({ label, value, tone }: { label: string; value: string; tone: "success" | "warning" | "neutral" }) {
  return (
    <Card className="border-border bg-card p-4 shadow-soft">
      <div className="t-caption text-muted-foreground">{label}</div>
      <div className="mt-2 flex items-center justify-between gap-2">
        <div className="t-body font-semibold">{value}</div>
        <ToneBadge tone={tone}>{tone === "success" ? "可用" : tone === "warning" ? "注意" : "状态"}</ToneBadge>
      </div>
    </Card>
  );
}

function SectionTitle({ icon, title, desc }: { icon: ReactNode; title: string; desc: string }) {
  return (
    <div className="flex items-start gap-3">
      <div className="mt-0.5 rounded-md border border-border bg-background p-2 text-primary">{icon}</div>
      <div>
        <h2 className="t-subtitle">{title}</h2>
        <p className="mt-1 t-caption text-muted-foreground">{desc}</p>
      </div>
    </div>
  );
}

function SelectField({
  label,
  value,
  values,
  onValueChange,
}: {
  label: string;
  value: string;
  values: string[];
  onValueChange: (value: string) => void;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <Select value={value} onValueChange={onValueChange}>
        <SelectTrigger className="bg-background">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {values.map((item) => (
            <SelectItem key={item} value={item}>
              {item}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

function PillSelect({
  icon,
  value,
  values,
  onValueChange,
}: {
  icon: ReactNode;
  value: string;
  values: string[];
  onValueChange: (value: string) => void;
}) {
  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger className="h-10 w-auto gap-2 rounded-full border-0 bg-muted px-4 shadow-none">
        <span className="text-muted-foreground">{icon}</span>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {values.map((item) => (
          <SelectItem key={item} value={item}>
            {item}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function ReadonlyPill({ icon, value }: { icon: ReactNode; value: string }) {
  return (
    <div className="inline-flex h-10 items-center gap-2 rounded-full bg-muted px-4 text-sm">
      <span className="text-muted-foreground">{icon}</span>
      <span>{value}</span>
    </div>
  );
}

function AssetGrid({
  assets,
  selectedIds,
  onToggle,
}: {
  assets: MediaAsset[];
  selectedIds: string[];
  onToggle: (assetId: string) => void;
}) {
  if (!assets.length) {
    return (
      <div className="mt-5">
        <EmptyState icon={<Images className="h-5 w-5" />} title="暂无图片素材" desc="先在左侧生成图片，结果会出现在这里。" />
      </div>
    );
  }
  return (
    <div className="mt-5 grid max-h-[520px] gap-3 overflow-y-auto sm:grid-cols-2">
      {assets.map((asset) => {
        const selected = selectedIds.includes(asset.asset_id);
        return (
          <button
            key={asset.asset_id}
            type="button"
            onClick={() => onToggle(asset.asset_id)}
            className={cn(
              "group overflow-hidden rounded-md border bg-background text-left transition-colors focus-ring",
              selected ? "border-primary" : "border-border hover:border-primary/50",
            )}
          >
            <div className="aspect-video bg-muted">
              <img src={downloadMediaWorkbenchAsset(asset.asset_id)} alt={asset.filename} className="h-full w-full object-cover" />
            </div>
            <div className="flex items-start gap-2 p-3">
              <Checkbox checked={selected} className="mt-0.5" aria-label="选择图片素材" />
              <div className="min-w-0">
                <div className="truncate t-body font-medium">{asset.filename}</div>
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
    <div className={cn("mt-4 grid gap-2", compact ? "sm:grid-cols-4" : "sm:grid-cols-2")}>
      {assets.map((asset) => (
        <div key={asset.asset_id} className="flex items-center gap-2 rounded-md border border-border bg-card p-2">
          <img
            src={downloadMediaWorkbenchAsset(asset.asset_id)}
            alt={asset.filename}
            className={cn("rounded object-cover", compact ? "h-9 w-12" : "h-12 w-16")}
          />
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

function RunList({
  runs,
  syncingRunId,
  onSync,
}: {
  runs: Array<{ run_id: string; status: string; prompt?: string; progress?: number; download_path?: string | null; error_message?: string | null }>;
  syncingRunId: string | null;
  onSync: (runId: string) => Promise<void>;
}) {
  if (!runs.length) {
    return (
      <div className="mt-5">
        <EmptyState icon={<Film className="h-5 w-5" />} title="暂无视频任务" desc="提交视频生成后，任务状态会出现在这里。" />
      </div>
    );
  }
  return (
    <div className="mt-5 space-y-3">
      {runs.map((run) => (
        <div key={run.run_id} className="rounded-md border border-border bg-background p-3">
          <div className="flex flex-col gap-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <ToneBadge tone={run.status === "failed" ? "warning" : run.status === "completed" ? "success" : "neutral"}>{run.status}</ToneBadge>
                <span className="t-caption text-muted-foreground">进度 {run.progress || 0}%</span>
              </div>
              <p className="mt-2 line-clamp-2 t-body">{run.prompt || run.run_id}</p>
              {run.error_message && <p className="mt-1 t-caption text-destructive">{run.error_message}</p>}
            </div>
            <div className="flex shrink-0 gap-2">
              <Button variant="outline" size="sm" className="gap-2" onClick={() => void onSync(run.run_id)}>
                {syncingRunId === run.run_id ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                同步
              </Button>
              {run.download_path && (
                <Button asChild size="sm" className="gap-2">
                  <a href={downloadVideoWorkbenchRun(run.run_id)}>
                    <Download className="h-4 w-4" />
                    下载
                  </a>
                </Button>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function AssetList({ assets }: { assets: MediaAsset[] }) {
  if (!assets.length) {
    return <EmptyState icon={<Images className="h-5 w-5" />} title="暂无素材" desc="生成图片或视频后，素材会在这里归档。" />;
  }
  return (
    <div className="mt-5 max-h-[560px] space-y-2 overflow-y-auto">
      {assets.map((asset) => (
        <div key={asset.asset_id} className="flex items-center justify-between gap-3 rounded-md border border-border bg-background p-3">
          <div className="min-w-0">
            <div className="truncate t-body font-medium">{asset.filename}</div>
            <div className="t-caption text-muted-foreground">{asset.asset_type} · {asset.source}</div>
          </div>
          <Button asChild variant="outline" size="sm">
            <a href={downloadMediaWorkbenchAsset(asset.asset_id)}>下载</a>
          </Button>
        </div>
      ))}
    </div>
  );
}

function HistoryList({
  imageRuns,
  videoRuns,
}: {
  imageRuns: Array<{ run_id: string; status: string; prompt?: string; assets?: MediaAsset[] }>;
  videoRuns: Array<{ run_id: string; status: string; prompt?: string; progress?: number }>;
}) {
  const rows = [
    ...imageRuns.map((run) => ({ id: run.run_id, kind: "图片", status: run.status, prompt: run.prompt, meta: `${run.assets?.length || 0} 张` })),
    ...videoRuns.map((run) => ({ id: run.run_id, kind: "视频", status: run.status, prompt: run.prompt, meta: `${run.progress || 0}%` })),
  ];
  if (!rows.length) {
    return <EmptyState icon={<RefreshCw className="h-5 w-5" />} title="暂无历史任务" desc="真实生成任务会在这里保留最近记录。" />;
  }
  return (
    <div className="mt-5 max-h-[560px] space-y-2 overflow-y-auto">
      {rows.map((row) => (
        <div key={row.id} className="rounded-md border border-border bg-background p-3">
          <div className="flex items-center justify-between gap-3">
            <div className="t-caption text-muted-foreground">{row.kind} · {row.meta}</div>
            <ToneBadge tone={row.status === "failed" ? "warning" : row.status === "completed" ? "success" : "neutral"}>{row.status}</ToneBadge>
          </div>
          <p className="mt-2 line-clamp-2 t-body">{row.prompt || row.id}</p>
        </div>
      ))}
    </div>
  );
}

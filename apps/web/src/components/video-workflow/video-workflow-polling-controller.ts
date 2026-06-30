export type VideoWorkflowPollingTimerId = number;

export interface VideoWorkflowPollingTimers {
  setTimeout(callback: () => void, delayMs: number): VideoWorkflowPollingTimerId;
  clearTimeout(timerId: VideoWorkflowPollingTimerId): void;
}

export interface VideoWorkflowPollingEnvironment {
  isVisible(): boolean;
  isOnline(): boolean;
  addEventListener(event: "resume" | "suspend", listener: () => void): void;
  removeEventListener(event: "resume" | "suspend", listener: () => void): void;
}

export type VideoWorkflowPollingState =
  | { state: "idle"; nextRetryInMs?: undefined }
  | { state: "syncing"; nextRetryInMs?: undefined }
  | { state: "waiting"; nextRetryInMs: number }
  | { state: "backoff"; nextRetryInMs: number }
  | { state: "paused"; nextRetryInMs?: undefined };

const browserTimers: VideoWorkflowPollingTimers = {
  setTimeout: (callback, delayMs) => window.setTimeout(callback, delayMs),
  clearTimeout: (timerId) => window.clearTimeout(timerId),
};

export const browserPollingEnvironment: VideoWorkflowPollingEnvironment = {
  isVisible: () => document.visibilityState !== "hidden",
  isOnline: () => navigator.onLine !== false,
  addEventListener: (event, listener) => {
    if (event === "resume") {
      document.addEventListener("visibilitychange", listener);
      window.addEventListener("online", listener);
    } else {
      document.addEventListener("visibilitychange", listener);
      window.addEventListener("offline", listener);
    }
  },
  removeEventListener: (event, listener) => {
    if (event === "resume") {
      document.removeEventListener("visibilitychange", listener);
      window.removeEventListener("online", listener);
    } else {
      document.removeEventListener("visibilitychange", listener);
      window.removeEventListener("offline", listener);
    }
  },
};

export class VideoWorkflowPollingController {
  private readonly projectId: string;
  private readonly getRunIds: () => string[];
  private readonly syncRun: (projectId: string, runId: string) => Promise<unknown>;
  private readonly intervalMs: number;
  private readonly maxBackoffMs: number;
  private readonly jitterRatio: number;
  private readonly onStateChange: (state: VideoWorkflowPollingState) => void;
  private readonly timers: VideoWorkflowPollingTimers;
  private readonly environment: VideoWorkflowPollingEnvironment;
  private timerId: VideoWorkflowPollingTimerId | null = null;
  private stopped = true;
  private inFlight = false;
  private failureCount = 0;

  constructor({
    projectId,
    getRunIds,
    syncRun,
    intervalMs,
    maxBackoffMs = 60000,
    jitterRatio = 0.2,
    onStateChange = () => {},
    timers = browserTimers,
    environment = browserPollingEnvironment,
  }: {
    projectId: string;
    getRunIds: () => string[];
    syncRun: (projectId: string, runId: string) => Promise<unknown>;
    intervalMs: number;
    maxBackoffMs?: number;
    jitterRatio?: number;
    onStateChange?: (state: VideoWorkflowPollingState) => void;
    timers?: VideoWorkflowPollingTimers;
    environment?: VideoWorkflowPollingEnvironment;
  }) {
    this.projectId = projectId;
    this.getRunIds = getRunIds;
    this.syncRun = syncRun;
    this.intervalMs = intervalMs;
    this.maxBackoffMs = maxBackoffMs;
    this.jitterRatio = jitterRatio;
    this.onStateChange = onStateChange;
    this.timers = timers;
    this.environment = environment;
  }

  start() {
    if (!this.stopped) return;
    this.stopped = false;
    this.environment.addEventListener("resume", this.handleResume);
    this.environment.addEventListener("suspend", this.handleSuspend);
    this.schedule(0);
  }

  stop() {
    this.stopped = true;
    this.environment.removeEventListener("resume", this.handleResume);
    this.environment.removeEventListener("suspend", this.handleSuspend);
    this.clearTimer();
    this.onStateChange({ state: "idle" });
  }

  requestSync() {
    if (this.inFlight) return;
    this.clearTimer();
    this.schedule(0);
  }

  private handleResume = () => {
    if (this.canPoll()) this.requestSync();
  };

  private handleSuspend = () => {
    if (!this.environment.isVisible() || !this.environment.isOnline()) {
      this.clearTimer();
      this.onStateChange({ state: "paused" });
    }
  };

  private canPoll() {
    return !this.stopped && this.environment.isVisible() && this.environment.isOnline();
  }

  private schedule(delayMs: number) {
    if (!this.environment.isVisible() || !this.environment.isOnline()) {
      this.onStateChange({ state: "paused" });
      return;
    }
    if (!this.canPoll() || this.timerId !== null) return;
    if (this.getActiveRunIds().length === 0) {
      this.onStateChange({ state: "idle" });
      return;
    }
    this.onStateChange(delayMs > this.intervalMs ? { state: "backoff", nextRetryInMs: delayMs } : { state: "waiting", nextRetryInMs: delayMs });
    this.timerId = this.timers.setTimeout(() => {
      this.timerId = null;
      void this.runCycle();
    }, delayMs);
  }

  private clearTimer() {
    if (this.timerId === null) return;
    this.timers.clearTimeout(this.timerId);
    this.timerId = null;
  }

  private getActiveRunIds() {
    return [...new Set(this.getRunIds())].sort();
  }

  private nextDelayMs(failed: boolean) {
    if (!failed) {
      this.failureCount = 0;
      return this.intervalMs;
    }
    this.failureCount += 1;
    const baseDelay = Math.min(this.intervalMs * 2 ** this.failureCount, this.maxBackoffMs);
    return Math.round(baseDelay + Math.random() * baseDelay * this.jitterRatio);
  }

  private async runCycle() {
    if (!this.canPoll() || this.inFlight) return;
    const runIds = this.getActiveRunIds();
    if (!runIds.length) return;

    this.inFlight = true;
    this.onStateChange({ state: "syncing" });
    const results = await Promise.allSettled(runIds.map((runId) => this.syncRun(this.projectId, runId)));
    this.inFlight = false;

    const failed = results.some((result) => result.status === "rejected" || isFailedSyncResult(result.value));
    this.schedule(this.nextDelayMs(failed));
  }
}

function isFailedSyncResult(result: unknown): boolean {
  return (
    typeof result === "object" &&
    result !== null &&
    "ok" in result &&
    (result as { ok?: unknown }).ok === false
  );
}

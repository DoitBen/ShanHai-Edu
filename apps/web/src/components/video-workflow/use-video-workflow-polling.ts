"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { VideoWorkflowRun } from "@/lib/types";
import { VideoWorkflowPollingController, type VideoWorkflowPollingState } from "./video-workflow-polling-controller";
import { isActiveVideoRun } from "./video-workflow-utils";

export function useVideoWorkflowPolling({
  projectId,
  runs,
  intervalMs,
  syncRun,
}: {
  projectId: string;
  runs: VideoWorkflowRun[];
  intervalMs: number;
  syncRun: (projectId: string, runId: string) => Promise<unknown>;
}) {
  const [pollingState, setPollingState] = useState<VideoWorkflowPollingState>({ state: "idle" });
  const activeIds = useMemo(
    () => runs.filter(isActiveVideoRun).map((run) => run.run_id).sort(),
    [runs],
  );
  const activeKey = activeIds.join(",");
  const activeIdsRef = useRef(activeIds);
  const syncRunRef = useRef(syncRun);
  const controllerRef = useRef<VideoWorkflowPollingController | null>(null);

  useEffect(() => {
    activeIdsRef.current = activeIds;
    syncRunRef.current = syncRun;
  }, [activeIds, syncRun]);

  useEffect(() => {
    if (!activeIds.length) return;
    const controller = new VideoWorkflowPollingController({
      projectId,
      getRunIds: () => activeIdsRef.current,
      syncRun: (id, runId) => syncRunRef.current(id, runId),
      intervalMs,
      onStateChange: setPollingState,
    });
    controllerRef.current = controller;
    controller.start();
    return () => {
      if (controllerRef.current === controller) controllerRef.current = null;
      controller.stop();
    };
  }, [activeKey, intervalMs, projectId]);

  return {
    pollingState,
    requestSync: () => controllerRef.current?.requestSync(),
  };
}

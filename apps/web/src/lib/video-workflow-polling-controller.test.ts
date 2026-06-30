import { VideoWorkflowPollingController } from "@/components/video-workflow/video-workflow-polling-controller";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function deferred<T = void>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
}

class FakeTimers {
  private nextId = 1;
  private tasks = new Map<number, { delay: number; callback: () => void }>();

  setTimeout = (callback: () => void, delay: number) => {
    const id = this.nextId++;
    this.tasks.set(id, { delay, callback });
    return id;
  };

  clearTimeout = (id: number) => {
    this.tasks.delete(id);
  };

  pendingDelays() {
    return [...this.tasks.values()].map((task) => task.delay);
  }

  runNext() {
    const entry = this.tasks.entries().next().value as
      | [number, { delay: number; callback: () => void }]
      | undefined;
    if (!entry) throw new Error("No pending timer");
    const [id, task] = entry;
    this.tasks.delete(id);
    task.callback();
  }
}

class FakeEnvironment {
  visible = true;
  online = true;
  private listeners = new Map<string, Set<() => void>>();

  isVisible = () => this.visible;
  isOnline = () => this.online;

  addEventListener = (event: string, listener: () => void) => {
    const listeners = this.listeners.get(event) || new Set<() => void>();
    listeners.add(listener);
    this.listeners.set(event, listeners);
  };

  removeEventListener = (event: string, listener: () => void) => {
    this.listeners.get(event)?.delete(listener);
  };

  emit(event: string) {
    for (const listener of this.listeners.get(event) || []) listener();
  }
}

async function createStartedController({
  runIds = ["run_a"],
  syncRun,
  timers = new FakeTimers(),
  environment = new FakeEnvironment(),
  intervalMs = 4000,
  onStateChange,
}: {
  runIds?: string[];
  syncRun: (projectId: string, runId: string) => Promise<unknown>;
  timers?: FakeTimers;
  environment?: FakeEnvironment;
  intervalMs?: number;
  onStateChange?: (state: { state: string; nextRetryInMs?: number }) => void;
}) {
  const controller = new VideoWorkflowPollingController({
    projectId: "project_a",
    getRunIds: () => runIds,
    syncRun,
    intervalMs,
    maxBackoffMs: 60000,
    jitterRatio: 0,
    onStateChange,
    timers,
    environment,
  });
  controller.start();
  return { controller, timers, environment };
}

{
  const calls: string[] = [];
  const { timers } = await createStartedController({
    runIds: ["run_a", "run_b"],
    syncRun: async (_projectId, runId) => {
      calls.push(runId);
    },
  });

  assert(calls.length === 0, "initial sync must be scheduled, not run during render");
  assert(JSON.stringify(timers.pendingDelays()) === JSON.stringify([0]), "initial sync must be immediate");
  timers.runNext();
  await flushPromises();

  assert(JSON.stringify(calls) === JSON.stringify(["run_a", "run_b"]), "initial sync must run exactly once");
  assert(
    JSON.stringify(timers.pendingDelays()) === JSON.stringify([4000]),
    "successful sync must schedule the next cycle at the normal interval",
  );
}

{
  const first = deferred();
  let calls = 0;
  const { controller, timers } = await createStartedController({
    syncRun: async () => {
      calls += 1;
      await first.promise;
    },
  });

  timers.runNext();
  await flushPromises();
  controller.requestSync();
  controller.requestSync();
  await flushPromises();

  assert(calls === 1, "slow sync must not overlap with another sync cycle");
  first.resolve();
  await flushPromises();
  assert(JSON.stringify(timers.pendingDelays()) === JSON.stringify([4000]), "next sync is scheduled after completion");
}

{
  let calls = 0;
  const states: Array<{ state: string; nextRetryInMs?: number }> = [];
  const { timers } = await createStartedController({
    syncRun: async () => {
      calls += 1;
      throw new Error("temporary outage");
    },
    onStateChange: (state) => states.push(state),
  });

  timers.runNext();
  await flushPromises();

  assert(calls === 1, "failed sync must still be counted as one cycle");
  assert(
    JSON.stringify(timers.pendingDelays()) === JSON.stringify([8000]),
    "failed sync must use exponential backoff",
  );
  assert(
    states.some((state) => state.state === "backoff" && state.nextRetryInMs === 8000),
    "failed sync must report backoff state and next retry delay",
  );
}

{
  const states: Array<{ state: string; nextRetryInMs?: number }> = [];
  const { timers } = await createStartedController({
    syncRun: async () => ({ ok: false, msg: "同步失败" }),
    onStateChange: (state) => states.push(state),
  });

  timers.runNext();
  await flushPromises();

  assert(
    JSON.stringify(timers.pendingDelays()) === JSON.stringify([8000]),
    "resolved failed sync result must still use exponential backoff",
  );
  assert(
    states.some((state) => state.state === "backoff" && state.nextRetryInMs === 8000),
    "resolved failed sync result must report backoff state",
  );
}

{
  const env = new FakeEnvironment();
  env.visible = false;
  let calls = 0;
  const { timers, environment } = await createStartedController({
    environment: env,
    syncRun: async () => {
      calls += 1;
    },
  });

  assert(timers.pendingDelays().length === 0, "hidden page must not poll");
  environment.visible = true;
  environment.emit("resume");
  timers.runNext();
  await flushPromises();

  assert(calls === 1, "visible page must sync immediately after resume");
}

{
  const env = new FakeEnvironment();
  const states: Array<{ state: string; nextRetryInMs?: number }> = [];
  let calls = 0;
  const { timers, environment } = await createStartedController({
    environment: env,
    syncRun: async () => {
      calls += 1;
    },
    onStateChange: (state) => states.push(state),
  });

  timers.runNext();
  await flushPromises();
  assert(JSON.stringify(timers.pendingDelays()) === JSON.stringify([4000]), "active run must wait for the next cycle");

  environment.online = false;
  environment.emit("suspend");

  assert(timers.pendingDelays().length === 0, "offline transition must clear the pending poll timer");
  assert(states.at(-1)?.state === "paused", "offline transition must report paused state immediately");

  environment.online = true;
  environment.emit("resume");
  timers.runNext();
  await flushPromises();

  assert(calls === 2, "online resume must trigger an immediate sync after offline pause");
}

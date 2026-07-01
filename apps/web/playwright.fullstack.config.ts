import { defineConfig } from "@playwright/test";

const backendURL = process.env.PHASE_E_BACKEND_URL || "http://127.0.0.1:8000";
const frontendURL = process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:3000";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  webServer: [
    {
      command: "cd ../.. && python apps/api/scripts/phase_e_fullstack_server.py",
      url: `${backendURL}/health`,
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: "bun run dev",
      url: frontendURL,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        NEXT_PUBLIC_DEMO_MODE: "false",
        BACKEND_API_BASE_URL: backendURL,
      },
    },
  ],
  use: {
    baseURL: frontendURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
});

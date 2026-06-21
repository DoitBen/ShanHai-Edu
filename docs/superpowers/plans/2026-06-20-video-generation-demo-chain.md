# Video Generation Demo Chain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the current local end-to-end demo from approved lesson plan to fake final video generation.

**Architecture:** Keep the existing node-state workflow as the source of truth. Backend verifies or minimally fills the existing node contracts; frontend wires each node through the existing generate/edit/approve pattern; QA validates one full local fake-provider chain.

**Tech Stack:** FastAPI, SQLite project storage, fake provider, Next.js 16, React 19, Zustand store, Bun.

---

## Work Slices

### Slice 1: Video Intro Selection

**Owner:** Backend T023 + Frontend T024 + QA T025

- [ ] Backend confirms `intro_selection` generate/get/edit/approve.
- [ ] Frontend displays generated intro options and lets the user choose or lightly edit.
- [ ] QA validates the chain through `intro_selection=approved`.

### Slice 2: Video Script To Storyboard

**Owner:** Backend T027 + Frontend T028

- [ ] Backend confirms `intro_video_script`, `intro_video_screenplay`, `intro_video_asset`, and `storyboard` generate/get/edit/approve.
- [ ] Frontend wires these nodes using the same local-demo editor pattern as lesson plan.
- [ ] Each confirmed node advances manifest to the next video node.

### Slice 3: Fake Final Video

**Owner:** Backend T027 + Frontend T029

- [ ] Backend confirms `final_video/generate` creates fake tasks and exposes task list/query.
- [ ] Frontend triggers fake final video generation and shows task/clip status.
- [ ] QA validates final manifest/task state and browser evidence.

### Slice 4: Full Demo Regression

**Owner:** QA T030 + Architect T031

- [ ] QA runs full local demo: project creation -> textbook -> lesson plan -> intro selection -> script -> screenplay -> asset -> storyboard -> fake final video.
- [ ] Architect reviews original tasks, handoffs, code diff, tests, build, browser evidence, and decides whether this local demo stage passes.

## Verification Commands

- Backend: `python -m pytest apps\api\tests -q`
- Frontend: `cd apps\web && bunx tsc --noEmit --pretty false`
- Frontend: `cd apps\web && bun run lint`
- Frontend: `cd apps\web && bun run build`
- Browser: isolated fake API + real API Web mode, no application-level console errors.

## Non-Goals

- No real provider quality validation.
- No production auth or multi-user isolation.
- No formal rich editor.
- No deployment or Cloud Run acceptance.
- No final downloadable MP4 quality guarantee; fake provider task/clip state is enough for this local demo phase.

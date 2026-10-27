import assert from "node:assert/strict";
import test from "node:test";

import worker, { isWithinActiveWindow } from "./index.mjs";

test("HTTP preview responds with worker status without dispatching GitHub", async () => {
  const response = await worker.fetch();

  assert.equal(response.status, 200);
  assert.match(await response.text(), /08:00-21:55 Europe\/Warsaw/);
});

test("active window follows Warsaw daylight saving time", () => {
  assert.equal(isWithinActiveWindow(new Date("2026-01-15T07:00:00Z")), true);
  assert.equal(isWithinActiveWindow(new Date("2026-07-15T06:00:00Z")), true);
});

test("active window includes 21:55 and excludes 22:00 Warsaw time", () => {
  assert.equal(isWithinActiveWindow(new Date("2026-01-15T20:55:00Z")), true);
  assert.equal(isWithinActiveWindow(new Date("2026-01-15T21:00:00Z")), false);
});

test("scheduled handler dispatches only inside the active window", async () => {
  let requestCount = 0;
  let dispatchRequest;
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, options) => {
    requestCount += 1;
    dispatchRequest = { url, options };
    return new Response(null, { status: 204 });
  };
  const env = {
    GH_TOKEN: "test-token",
    GITHUB_REPOSITORY: "owner/repo",
    GITHUB_WORKFLOW: "workflow.yml",
    GITHUB_REF: "main",
  };

  try {
    await worker.scheduled({ scheduledTime: Date.parse("2026-01-15T06:55:00Z") }, env);
    assert.equal(requestCount, 0);
    await worker.scheduled({ scheduledTime: Date.parse("2026-01-15T07:00:00Z") }, env);
    assert.equal(requestCount, 1);
    assert.equal(
      dispatchRequest.url,
      "https://api.github.com/repos/owner/repo/actions/workflows/workflow.yml/dispatches",
    );
    assert.equal(dispatchRequest.options.headers.Authorization, "Bearer test-token");
    assert.deepEqual(JSON.parse(dispatchRequest.options.body), { ref: "main" });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("scheduled handler surfaces failed dispatches", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response("denied", { status: 403 });

  try {
    await assert.rejects(
      worker.scheduled(
        { scheduledTime: Date.parse("2026-01-15T07:00:00Z") },
        {
          GH_TOKEN: "test-token",
          GITHUB_REPOSITORY: "owner/repo",
          GITHUB_WORKFLOW: "workflow.yml",
          GITHUB_REF: "main",
        },
      ),
      /GitHub workflow dispatch failed \(403\)/,
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

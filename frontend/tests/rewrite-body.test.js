// Tests for the rewrite request-body helper in static/app.js.
// Run with: npm test

import { test } from "node:test";
import assert from "node:assert/strict";

import { buildRewriteBody } from "../static/app.js";

test("buildRewriteBody wraps the transcript in the expected JSON shape", () => {
  const body = buildRewriteBody("I missed the bus.");

  assert.deepEqual(JSON.parse(body), { transcript: "I missed the bus." });
});
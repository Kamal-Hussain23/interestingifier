// Tests for the narrate request-body helper in static/app.js.
// Run with: npm test

import { test } from "node:test";
import assert from "node:assert/strict";

import { buildNarrateBody } from "../static/app.js";

test("buildNarrateBody wraps the story in the expected JSON shape", () => {
  const body = buildNarrateBody("THE BUS FEARED HIM.");

  assert.deepEqual(JSON.parse(body), { story: "THE BUS FEARED HIM." });
});

test("buildNarrateBody round-trips unusual text", () => {
  const body = buildNarrateBody('he said "hi"\n\nnew paragraph');

  assert.equal(JSON.parse(body).story, 'he said "hi"\n\nnew paragraph');
});
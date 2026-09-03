// Tests for the transcription upload helper in static/app.js.
// Run with: npm test

import { test } from "node:test";
import assert from "node:assert/strict";

import { buildTranscribeForm } from "../static/app.js";

test("buildTranscribeForm puts the blob in the audio field", async () => {
  const blob = new Blob(["hello"], { type: "audio/webm" });
  const form = buildTranscribeForm(blob);

  const file = form.get("audio");
  assert.ok(file instanceof File);
  assert.equal(await file.text(), "hello");
});

test("buildTranscribeForm uses the audio field name", () => {
  const blob = new Blob(["x"]);
  const form = buildTranscribeForm(blob);

  assert.ok(form.has("audio"));
});
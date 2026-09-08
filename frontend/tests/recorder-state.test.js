// Tests for the pure record-state helpers in static/app.js.
// Run with: npm test

import { test } from "node:test";
import assert from "node:assert/strict";

import { nextState, statusText } from "../static/app.js";

test("idle + start -> recording", () => {
  assert.equal(nextState("idle", "start"), "recording");
});

test("recording + stop -> recorded", () => {
  assert.equal(nextState("recording", "stop"), "recorded");
});

test("recorded + start -> recording (record again)", () => {
  assert.equal(nextState("recorded", "start"), "recording");
});

test("invalid transitions throw", () => {
  assert.throws(() => nextState("recording", "start"));
  assert.throws(() => nextState("recording", "clear"));
  assert.throws(() => nextState("idle", "stop"));
  assert.throws(() => nextState("idle", "clear"));
  assert.throws(() => nextState("recorded", "stop"));
  assert.throws(() => nextState("recorded", "clear"));
  assert.throws(() => nextState("banana", "start"));
  assert.throws(() => nextState("idle", "banana"));
});

test("statusText has a message for every state", () => {
  assert.equal(statusText("idle"), "Tap the button and tell me your boring tale…");
  assert.equal(statusText("recording"), "Recording… keep talking!");
  assert.equal(statusText("recorded"), "Got it! Hit play below.");
});
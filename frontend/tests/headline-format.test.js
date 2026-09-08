// Tests for the clickbait headline formatter in static/app.js.
// Run with: npm test

import { test } from "node:test";
import assert from "node:assert/strict";

import { formatHeadline } from "../static/app.js";

test("formatHeadline keeps a present headline as-is", () => {
  assert.equal(formatHeadline("BUSES TREMBLE!"), "BUSES TREMBLE!");
});

test("formatHeadline returns an empty string when the headline is missing", () => {
  assert.equal(formatHeadline(null), "");
  assert.equal(formatHeadline(undefined), "");
  assert.equal(formatHeadline(""), "");
});
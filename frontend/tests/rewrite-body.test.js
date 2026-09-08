// Tests for the rewrite request-body helper in static/app.js.
// Run with: npm test

import { test } from "node:test";
import assert from "node:assert/strict";

import { ABSURDITIES, buildRewriteBody, curAbsurdity } from "../static/app.js";

test("buildRewriteBody wraps the transcript in the expected JSON shape", () => {
  const body = buildRewriteBody("I missed the bus.");

  assert.deepEqual(JSON.parse(body), { transcript: "I missed the bus." });
});

test("buildRewriteBody includes absurdity when a level is given", () => {
  const body = buildRewriteBody("I missed the bus.", "total_fever_dream");

  assert.deepEqual(JSON.parse(body), {
    transcript: "I missed the bus.",
    absurdity: "total_fever_dream",
  });
});

test("buildRewriteBody with absurdity and no drama matches the legacy body", () => {
  const body = buildRewriteBody("I missed the bus.", "unhinged");

  assert.deepEqual(JSON.parse(body), {
    transcript: "I missed the bus.",
    absurdity: "unhinged",
  });
});

test("buildRewriteBody adds a drama flag when requested", () => {
  const body = buildRewriteBody("I missed the bus.", "unhinged", true);

  assert.deepEqual(JSON.parse(body), {
    transcript: "I missed the bus.",
    absurdity: "unhinged",
    drama: true,
  });
});

test("buildRewriteBody supports drama without an absurdity choice", () => {
  const body = buildRewriteBody("I missed the bus.", null, true);

  assert.deepEqual(JSON.parse(body), {
    transcript: "I missed the bus.",
    drama: true,
  });
});

test("absurdity tokens match the backend contract levels", () => {
  assert.deepEqual(ABSURDITIES, ["slightly_weird", "unhinged", "total_fever_dream"]);
});

test("curAbsurdity keeps a known token", () => {
  assert.equal(curAbsurdity("slightly_weird"), "slightly_weird");
});

test("curAbsurdity falls back to unhinged for missing or unknown values", () => {
  assert.equal(curAbsurdity(null), "unhinged");
  assert.equal(curAbsurdity("chaotic"), "unhinged");
});
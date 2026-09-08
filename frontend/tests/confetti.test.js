// Tests for the confetti-piece generator in static/app.js.
// Run with: npm test

import { test } from "node:test";
import assert from "node:assert/strict";

import { CONFETTI_PALETTE, makeConfettiPieces } from "../static/app.js";

test("makeConfettiPieces returns exactly the requested count", () => {
  const pieces = makeConfettiPieces(60);

  assert.equal(pieces.length, 60);
});

test("makeConfettiPieces with a deterministic pick stays in contract ranges", () => {
  const pieces = makeConfettiPieces(60, () => 0.5);

  for (const piece of pieces) {
    const left = parseFloat(piece.left);
    const delay = parseFloat(piece.delay);
    const duration = parseFloat(piece.duration);
    const size = parseFloat(piece.size);
    const spin = parseFloat(piece.spin);

    assert.ok(left >= 0 && left <= 100, `left ${left} out of range`);
    assert.ok(delay >= 0 && delay <= 0.4, `delay ${delay} out of range`);
    assert.ok(duration >= 1.2 && duration <= 2.5, `duration ${duration} out of range`);
    assert.ok(size >= 6 && size <= 14, `size ${size} out of range`);
    assert.ok(spin >= -420 && spin <= 420, `spin ${spin} out of range`);
    assert.equal(piece.delay.endsWith("s"), true);
    assert.equal(piece.duration.endsWith("s"), true);
    assert.equal(piece.size.endsWith("px"), true);
    assert.equal(piece.spin.endsWith("deg"), true);
    assert.equal(piece.left.endsWith("%"), true);
  }
});

test("every piece colour comes from the kitsch palette", () => {
  const pieces = makeConfettiPieces(60);

  for (const piece of pieces) {
    assert.ok(CONFETTI_PALETTE.includes(piece.color), `colour ${piece.color} not in palette`);
  }
});

test("makeConfettiPieces returns an empty list for zero pieces", () => {
  assert.deepEqual(makeConfettiPieces(0), []);
});
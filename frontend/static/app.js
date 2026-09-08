// Interestingifier™ frontend logic.
//
// The big button captures your voice with MediaRecorder and lets you preview
// the clip. The recorded Blob is held "ready to POST" — a later milestone will
// upload it for transcription. The pure state helpers are exported so the
// node:test suite can check them without a browser.

// ---------------------------------------------------------------------------
// Pure record-state helpers (tested by frontend/tests/recorder-state.test.js)
// ---------------------------------------------------------------------------

export const RECORD_STATES = {
  IDLE: "idle",
  RECORDING: "recording",
  RECORDED: "recorded",
};

export const ACTIONS = {
  START: "start",
  STOP: "stop",
};

// The three Absurdity levels, matching the backend /api/rewrite wire tokens.
export const ABSURDITIES = ["slightly_weird", "unhinged", "total_fever_dream"];

export const DEFAULT_ABSURDITY = "unhinged";

// The only legal moves: idle --start--> recording --stop--> recorded, and
// recorded --start--> recording so "Record again" starts a fresh take at once
// (the old clip is simply replaced).
const TRANSITIONS = {
  [RECORD_STATES.IDLE]: { [ACTIONS.START]: RECORD_STATES.RECORDING },
  [RECORD_STATES.RECORDING]: { [ACTIONS.STOP]: RECORD_STATES.RECORDED },
  [RECORD_STATES.RECORDED]: { [ACTIONS.START]: RECORD_STATES.RECORDING },
};

const STATUS_TEXT = {
  [RECORD_STATES.IDLE]: "Tap the button and tell me your boring tale…",
  [RECORD_STATES.RECORDING]: "Recording… keep talking!",
  [RECORD_STATES.RECORDED]: "Got it! Hit play below.",
};

// Returns the state that follows `action` from `state`, or throws if the move
// is not allowed.
// Packages a recorded audio Blob as a multipart/form-data upload body for the
// /api/transcribe endpoint, using the "audio" field name the backend expects.
// Pure and browser-free so the node:test suite can check it.
export function buildTranscribeForm(blob) {
  const form = new FormData();
  form.append("audio", blob, "recording.webm");
  return form;
}

// Builds the JSON request body for POST /api/rewrite. Pure and browser-free so
// the node:test suite can check it. When an absurdity level is given it is
// included; without one the body stays exactly as before (backward compatible).
// A truthy drama flag adds the "More Drama!" re-roll marker.
export function buildRewriteBody(transcript, absurdity, drama = false) {
  const body = { transcript };
  if (ABSURDITIES.includes(absurdity)) {
    body.absurdity = absurdity;
  }
  if (drama) {
    body.drama = true;
  }
  return JSON.stringify(body);
}

// Normalises a radio button's value into one of the three contract tokens,
// falling back to the Unhinged default for missing or unknown values. The
// single point where the UI guards against an invalid level before it reaches
// the backend.
export function curAbsurdity(checkedValue) {
  return ABSURDITIES.includes(checkedValue) ? checkedValue : DEFAULT_ABSURDITY;
}

// The backend may skip a headline when the title model misbehaves, so the
// page guards against undefined/empty values before rendering them as text.
export function formatHeadline(headline) {
  return headline ? String(headline) : "";
}

// Kitsch confetti palette — the same neon hexes the stylesheet already uses,
// so the burst matches the brand. Exported so tests can pin every piece.
export const CONFETTI_PALETTE = [
  "#ff2ea6",
  "#39ff14",
  "#00e5ff",
  "#ffd700",
  "#ff6d00",
];

export const CONFETTI_COUNT = 60;
export const CONFETTI_WINDOW_MS = 2500;

// Pure descriptor generator for one confetti burst. The random source is
// injectable so tests can assert exact, deterministic ranges without a browser.
// Each piece carries values formatted for CSS custom properties, plus a drift
// for the horizontal sway in the keyframes.
export function makeConfettiPieces(count, pick = Math.random) {
  const pieces = [];
  for (let i = 0; i < count; i += 1) {
    pieces.push({
      left: `${Math.floor(pick() * 101)}%`,
      delay: `${(pick() * 0.4).toFixed(2)}s`,
      duration: `${(1.2 + pick() * 1.3).toFixed(2)}s`,
      size: `${Math.floor(6 + pick() * 8)}px`,
      spin: `${Math.floor(pick() * 840 - 420)}deg`,
      drift: `${(pick() * 40 - 20).toFixed(1)}%`,
      color: CONFETTI_PALETTE[Math.floor(pick() * CONFETTI_PALETTE.length)],
    });
  }
  return pieces;
}

// Builds the JSON request body for POST /api/narrate. Pure and browser-free so
// the node:test suite can check it.
export function buildNarrateBody(story) {
  return JSON.stringify({ story });
}

export function nextState(state, action) {
  const next = TRANSITIONS[state]?.[action];
  if (next === undefined) {
    throw new Error(`No transition from "${state}" with action "${action}"`);
  }
  return next;
}

// The status-line message for a state.
export function statusText(state) {
  return STATUS_TEXT[state];
}

// ---------------------------------------------------------------------------
// Browser-only DOM wiring (skipped when imported under Node for tests)
// ---------------------------------------------------------------------------

// Timestamp handle for the celebration's teardown, shared by every burst so a
// new celebration can cancel the old timer before starting fresh.
let confettiTeardownTimer = null;

// Fires one confetti burst across the stage and flashes the story panel's
// border for the celebration window. Idempotent by design: any running
// celebration is torn down first, so rapid re-rewrites never stack layers or
// leave the rainbow border stuck.
function celebrateStory() {
  if (typeof document === "undefined") {
    return;
  }
  const storyPanel = document.getElementById("story-panel");
  const stage = document.querySelector("main.stage");
  if (!storyPanel || !stage) {
    return;
  }

  const oldLayer = document.querySelector(".confetti-layer");
  if (oldLayer) {
    oldLayer.remove();
  }
  if (confettiTeardownTimer !== null) {
    clearTimeout(confettiTeardownTimer);
    confettiTeardownTimer = null;
  }
  storyPanel.classList.remove("panel--celebrating");

  const layer = document.createElement("div");
  layer.className = "confetti-layer";

  function teardown() {
    layer.remove();
    storyPanel.classList.remove("panel--celebrating");
    if (confettiTeardownTimer !== null) {
      clearTimeout(confettiTeardownTimer);
      confettiTeardownTimer = null;
    }
  }

  for (const piece of makeConfettiPieces(CONFETTI_COUNT)) {
    const span = document.createElement("span");
    span.className = "confetti-piece";
    span.style.setProperty("--left", piece.left);
    span.style.setProperty("--delay", piece.delay);
    span.style.setProperty("--duration", piece.duration);
    span.style.setProperty("--size", piece.size);
    span.style.setProperty("--spin", piece.spin);
    span.style.setProperty("--drift", piece.drift);
    span.style.setProperty("--color", piece.color);
    layer.appendChild(span);
  }
  stage.appendChild(layer);
  storyPanel.classList.add("panel--celebrating");
  layer.lastChild.addEventListener("animationend", teardown, { once: true });
  confettiTeardownTimer = setTimeout(teardown, CONFETTI_WINDOW_MS);
}

function main() {
  const recordBtn = document.getElementById("record-btn");
  const recordBtnLabel = document.getElementById("record-btn-label");
  const statusLine = document.getElementById("status-line");
  const playbackPanel = document.getElementById("playback-panel");
  const previewAudio = document.getElementById("preview-audio");
  const transcriptText = document.getElementById("transcript-text");
  const storyText = document.getElementById("story-text");
  const storyHeadline = document.getElementById("story-headline");
  const moreDramaBtn = document.getElementById("more-drama-btn");

  let state = RECORD_STATES.IDLE;
  let stream = null;
  let mediaRecorder = null;
  let audioChunks = [];
  let starting = false;
  // The latest transcript, remembered so flipping the Absurdity slider can
  // re-rewrite the same anecdote at a new level without re-recording.
  let currentTranscript = "";

  function checkedAbsurdity() {
    const checked = document.querySelector('input[name="absurdity"]:checked');
    return curAbsurdity(checked ? checked.value : null);
  }

  function updateUi() {
    recordBtn.classList.toggle("recording", state === RECORD_STATES.RECORDING);
    recordBtn.classList.toggle("recorded", state === RECORD_STATES.RECORDED);
    recordBtn.setAttribute("aria-pressed", String(state === RECORD_STATES.RECORDING));
    recordBtnLabel.textContent =
      state === RECORD_STATES.RECORDING
        ? "Stop recording"
        : state === RECORD_STATES.RECORDED
          ? "Record again"
          : "Record your story";
    statusLine.textContent = statusText(state);
    playbackPanel.hidden = previewAudio.src === "";
  }

  function canRecord() {
    return (
      typeof window.MediaRecorder !== "undefined" &&
      Boolean(navigator.mediaDevices?.getUserMedia)
    );
  }

  async function startRecording() {
    // Guard against a double-click while the mic request is still in flight.
    if (starting || state === RECORD_STATES.RECORDING) {
      return;
    }
    if (!canRecord()) {
      statusLine.textContent = "Sorry — this browser can't record audio.";
      return;
    }
    starting = true;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunks = [];
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.addEventListener("dataavailable", (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      });
      mediaRecorder.addEventListener("stop", onStop);
      mediaRecorder.start();
      state = nextState(state, ACTIONS.START);
    } catch {
      statusLine.textContent = "Microphone unavailable — please allow mic access.";
    } finally {
      starting = false;
    }
    updateUi();
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === "recording") {
      mediaRecorder.stop();
    }
    state = nextState(state, ACTIONS.STOP);
    updateUi();
  }

  // Upload a recorded Blob for transcription and drop the result into the
  // transcript text. Kept small and separate so the API call doesn't inherit
  // the MediaRecorder plumbing.
  async function uploadForTranscription(blob) {
    try {
      const response = await fetch("/api/transcribe", {
        method: "POST",
        body: buildTranscribeForm(blob),
      });
      if (!response.ok) {
        const error = await response.json().catch(() => null);
        throw new Error(error?.error?.message ?? `Transcribe failed (${response.status})`);
      }
      const data = await response.json();
      transcriptText.textContent = data.transcript;
      currentTranscript = data.transcript;
      moreDramaBtn.disabled = false;
      await rewriteStory(data.transcript);
    } catch (error) {
      transcriptText.textContent = `Transcription failed: ${error.message}`;
    }
  }

  async function rewriteStory(transcript, drama = false) {
    try {
      const response = await fetch("/api/rewrite", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: buildRewriteBody(transcript, checkedAbsurdity(), drama),
      });
      if (!response.ok) {
        const error = await response.json().catch(() => null);
        throw new Error(error?.error?.message ?? `Rewrite failed (${response.status})`);
      }
      const data = await response.json();
      storyHeadline.hidden = !data.headline;
      storyHeadline.textContent = formatHeadline(data.headline);
      storyText.textContent = data.story;
      celebrateStory();
      await narrateStory(data.story);
    } catch (error) {
      storyHeadline.hidden = true;
      storyHeadline.textContent = "";
      storyText.textContent = `Story rewrite failed: ${error.message}`;
    }
  }

  async function narrateStory(story) {
    try {
      const response = await fetch("/api/narrate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: buildNarrateBody(story),
      });
      if (!response.ok) {
        const error = await response.json().catch(() => null);
        throw new Error(error?.error?.message ?? `Narration failed (${response.status})`);
      }
      const audioBlob = await response.blob();
      if (previewAudio.src) {
        URL.revokeObjectURL(previewAudio.src);
      }
      previewAudio.src = URL.createObjectURL(audioBlob);
      playbackPanel.hidden = false;
    } catch (error) {
      console.error("Narration error:", error);
    }
  }

  // Fired by MediaRecorder once it has finished capturing.
  function onStop() {
    stream?.getTracks().forEach((track) => track.stop());
    const blob = new Blob(audioChunks, {
      type: mediaRecorder?.mimeType ?? "audio/webm",
    });
    if (previewAudio.src) {
      URL.revokeObjectURL(previewAudio.src);
    }
    previewAudio.src = URL.createObjectURL(blob);
    uploadForTranscription(blob);
    updateUi();
  }

  recordBtn.addEventListener("click", () => {
    if (state === RECORD_STATES.RECORDING) {
      stopRecording();
    } else {
      // idle, or recorded — start a fresh take (recorded covers "Record again").
      startRecording();
    }
  });

  // A small helper that highlights whichever Absurdity option is checked.
  // Browser-agnostic (no :has()): the labels get an .is-selected class driven
  // from JS, so the slider reads correctly even on older Codio browsers.
  function syncAbsurdityHighlight() {
    document.querySelectorAll(".absurdity-slider__option").forEach((option) => {
      const checked = option.querySelector('input[name="absurdity"]:checked');
      option.classList.toggle("is-selected", Boolean(checked));
    });
  }

  // Flipping the slider re-rewrites the last transcript at the new level
  // (which re-narrates the fresh story too) — or does nothing if there is no
  // transcript yet.
  document.querySelectorAll('input[name="absurdity"]').forEach((input) => {
    input.addEventListener("change", () => {
      syncAbsurdityHighlight();
      if (currentTranscript) {
        rewriteStory(currentTranscript);
      }
    });
  });

  // "More Drama!" re-rolls the last transcript into a fresh, differently-spun
  // story — no re-recording needed. Disabled until a transcript exists.
  moreDramaBtn.addEventListener("click", () => {
    if (currentTranscript) {
      rewriteStory(currentTranscript, true);
    }
  });

  syncAbsurdityHighlight();
}

// Only wire up the DOM when a browser is available; Node (the test runner)
// imports this module without a document and just uses the pure helpers.
if (typeof document !== "undefined") {
  main();
}
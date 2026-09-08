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
  CLEAR: "clear",
};

// The only legal moves: idle --start--> recording --stop--> recorded --clear--> idle.
const TRANSITIONS = {
  [RECORD_STATES.IDLE]: { [ACTIONS.START]: RECORD_STATES.RECORDING },
  [RECORD_STATES.RECORDING]: { [ACTIONS.STOP]: RECORD_STATES.RECORDED },
  [RECORD_STATES.RECORDED]: { [ACTIONS.CLEAR]: RECORD_STATES.IDLE },
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

function main() {
  const recordBtn = document.getElementById("record-btn");
  const recordBtnLabel = document.getElementById("record-btn-label");
  const statusLine = document.getElementById("status-line");
  const playbackPanel = document.getElementById("playback-panel");
  const previewAudio = document.getElementById("preview-audio");
  const transcriptText = document.getElementById("transcript-text");
  const storyText = document.getElementById("story-text");

  let state = RECORD_STATES.IDLE;
  let stream = null;
  let mediaRecorder = null;
  let audioChunks = [];

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
    if (!canRecord()) {
      statusLine.textContent = "Sorry — this browser can't record audio.";
      return;
    }
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
      await rewriteStory(data.transcript);
    } catch (error) {
      transcriptText.textContent = `Transcription failed: ${error.message}`;
    }
  }

  async function rewriteStory(transcript) {
    try {
      const response = await fetch("/api/rewrite", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript }),
      });
      if (!response.ok) {
        const error = await response.json().catch(() => null);
        throw new Error(error?.error?.message ?? `Rewrite failed (${response.status})`);
      }
      const data = await response.json();
      storyText.textContent = data.story;
      await narrateStory(data.story);
    } catch (error) {
      storyText.textContent = `Story rewrite failed: ${error.message}`;
    }
  }

  async function narrateStory(story) {
    try {
      const response = await fetch("/api/narrate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ story }),
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

  function reset() {
    state = nextState(state, ACTIONS.CLEAR);
    if (previewAudio.src) {
      URL.revokeObjectURL(previewAudio.src);
    }
    previewAudio.removeAttribute("src");
    updateUi();
  }

  recordBtn.addEventListener("click", () => {
    if (state === RECORD_STATES.IDLE) {
      startRecording();
    } else if (state === RECORD_STATES.RECORDING) {
      stopRecording();
    } else {
      reset();
    }
  });
}

// Only wire up the DOM when a browser is available; Node (the test runner)
// imports this module without a document and just uses the pure helpers.
if (typeof document !== "undefined") {
  main();
}
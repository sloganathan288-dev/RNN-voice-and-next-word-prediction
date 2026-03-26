/**
 * script.js — Speech-to-Text + Next Word Prediction
 * Handles: Web Speech API, fetch to Flask /predict, UI updates
 */

const BACKEND = 'http://localhost:5000/predict';

// ── DOM refs ──────────────────────────────────────────────────────────────
const micBtn       = document.getElementById('micBtn');
const micLabel     = document.getElementById('micLabel');
const micStatus    = document.getElementById('micStatus');
const interimBox   = document.getElementById('interimBox');
const interimText  = document.getElementById('interimText');
const textInput    = document.getElementById('textInput');
const clearBtn     = document.getElementById('clearBtn');
const predictionsBox = document.getElementById('predictionsBox');
const predStatus   = document.getElementById('predStatus');
const errorBanner  = document.getElementById('errorBanner');
const langSelect   = document.getElementById('langSelect');

// ── State ─────────────────────────────────────────────────────────────────
let recognition   = null;
let isRecording   = false;
let debounceTimer = null;

// ── Speech Recognition Setup ──────────────────────────────────────────────
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {
  micBtn.disabled = true;
  micBtn.title = 'Speech recognition not supported in this browser';
  setStatus('⚠️ Speech recognition not supported. Use Chrome or Edge.', true);
}

function createRecognition() {
  const r = new SpeechRecognition();
  r.continuous      = true;   // keep listening until stopped
  r.interimResults  = true;   // show live partial results
  r.lang            = langSelect.value;

  r.onstart = () => {
    isRecording = true;
    micBtn.classList.add('recording');
    micLabel.textContent = 'Stop Recording';
    setStatus('🔴 Listening… speak now');
    interimBox.style.display = 'block';
    hideError();
  };

  r.onend = () => {
    // Auto-restart if user hasn't manually stopped
    if (isRecording) {
      r.start();
    } else {
      stopUI();
    }
  };

  r.onerror = (e) => {
    const msgs = {
      'no-speech'       : 'No speech detected. Try again.',
      'audio-capture'   : 'Microphone not found or blocked.',
      'not-allowed'     : 'Microphone permission denied.',
      'network'         : 'Network error during recognition.',
    };
    showError(msgs[e.error] || `Speech error: ${e.error}`);
    isRecording = false;
    stopUI();
  };

  r.onresult = (e) => {
    let interim = '';
    let finalChunk = '';

    for (let i = e.resultIndex; i < e.results.length; i++) {
      const transcript = e.results[i][0].transcript;
      if (e.results[i].isFinal) {
        finalChunk += transcript + ' ';
      } else {
        interim += transcript;
      }
    }

    // Show live interim text
    interimText.textContent = interim;

    // Append final chunk to textarea
    if (finalChunk.trim()) {
      textInput.value = (textInput.value + ' ' + finalChunk).trim() + ' ';
      triggerPrediction();
    }
  };

  return r;
}

// ── Mic Button ────────────────────────────────────────────────────────────
micBtn.addEventListener('click', () => {
  if (!SpeechRecognition) return;

  if (isRecording) {
    // Stop
    isRecording = false;
    recognition.stop();
  } else {
    // Start
    recognition = createRecognition();
    try {
      recognition.start();
    } catch (err) {
      showError('Could not start microphone: ' + err.message);
    }
  }
});

// Update language when selector changes (restarts if active)
langSelect.addEventListener('change', () => {
  if (isRecording) {
    isRecording = false;
    recognition.stop();
    setTimeout(() => {
      recognition = createRecognition();
      isRecording = true;
      recognition.start();
    }, 300);
  }
});

function stopUI() {
  micBtn.classList.remove('recording');
  micLabel.textContent = 'Start Recording';
  setStatus('Recording stopped.');
  interimBox.style.display = 'none';
  interimText.textContent  = '';
}

// ── Text Input → Prediction ───────────────────────────────────────────────
textInput.addEventListener('input', () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(triggerPrediction, 400); // debounce 400ms
});

// ── Clear Button ──────────────────────────────────────────────────────────
clearBtn.addEventListener('click', () => {
  textInput.value = '';
  resetPredictions();
  hideError();
  textInput.focus();
});

// ── Prediction Logic ──────────────────────────────────────────────────────
function triggerPrediction() {
  const text = textInput.value.trim();
  if (!text) { resetPredictions(); return; }
  fetchPredictions(text);
}

async function fetchPredictions(text) {
  showLoading();
  try {
    const res = await fetch(BACKEND, {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ text }),
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);

    const data = await res.json();
    if (data.error) throw new Error(data.error);

    renderPredictions(data.predictions || []);
    hideError();
  } catch (err) {
    showError('Prediction failed: ' + err.message + '. Is the Flask server running?');
    resetPredictions();
  }
}

function renderPredictions(words) {
  if (!words.length) { resetPredictions(); return; }

  predStatus.textContent = 'Top 3 suggestions';
  predictionsBox.innerHTML = '';

  words.forEach((word) => {
    const chip = document.createElement('button');
    chip.className   = 'pred-chip';
    chip.textContent = word;
    chip.title       = `Click to append "${word}"`;

    // Click chip → append word to textarea and re-predict
    chip.addEventListener('click', () => {
      textInput.value = textInput.value.trimEnd() + ' ' + word + ' ';
      textInput.focus();
      triggerPrediction();
    });

    predictionsBox.appendChild(chip);
  });
}

function showLoading() {
  predStatus.textContent = '';
  predictionsBox.innerHTML = `
    <div class="pred-loading">
      <div class="spinner"></div> Predicting…
    </div>`;
}

function resetPredictions() {
  predStatus.textContent = '';
  predictionsBox.innerHTML = '<div class="pred-placeholder">Start typing or speaking to see predictions…</div>';
}

// ── Helpers ───────────────────────────────────────────────────────────────
function setStatus(msg, isWarn = false) {
  micStatus.textContent = msg;
  micStatus.style.color = isWarn ? '#f87171' : '#64748b';
}

function showError(msg) {
  errorBanner.textContent = '⚠️ ' + msg;
  errorBanner.style.display = 'block';
}

function hideError() {
  errorBanner.style.display = 'none';
}

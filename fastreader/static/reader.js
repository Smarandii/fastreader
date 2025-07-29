/*
 * Front‑end script for the FastReader speed‑reading interface.
 *
 * Once initialized with a PDF ID, this script fetches the full text
 * associated with the document, splits it into words and controls the
 * rapid serial visual presentation (RSVP). The user can adjust the
 * words‑per‑minute (WPM) and the number of words to display at each
 * step (chunk size). A reading log is created when the user starts
 * reading; this log records the requested speed and chunk size. At the
 * end of the document the timer stops automatically.
 */

window.initReader = function initReader(pdfId) {
  const displayEl = document.getElementById('display');
  const speedInput = document.getElementById('speedInput');
  const chunkInput = document.getElementById('chunkInput');
  const startBtn = document.getElementById('startBtn');
  const pauseBtn = document.getElementById('pauseBtn');
  const resetBtn = document.getElementById('resetBtn');

  let words = [];
  let position = 0;
  let timer = null;
  let logId = null;

  /**
   * Calculate the interval (in ms) between chunks based on WPM and chunk size.
   * WPM refers to the number of words shown per minute; if multiple words
   * are shown per interval, we scale the interval accordingly.
   *
   * @param {number} wpm
   * @param {number} chunkSize
   */
  function calculateStepDuration(wpm, chunkSize) {
    // Steps per minute = wpm / chunkSize; interval ms = 60000 / steps
    const stepsPerMinute = wpm / Math.max(chunkSize, 1);
    return 60000 / stepsPerMinute;
  }

  /**
   * Fetch the PDF text from the server and split into words.
   */
  function loadText() {
    fetch(`/api/text/${pdfId}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error('Failed to fetch text');
        }
        return response.json();
      })
      .then((data) => {
        const text = data.content || '';
        // Split on whitespace and remove empty strings
        words = text.split(/\s+/).filter((w) => w.length > 0);
      })
      .catch((err) => {
        console.error(err);
        displayEl.textContent = 'Error loading document.';
      });
  }

  /**
   * Show the next chunk of words and update position. If the end is
   * reached, stop the timer and disable controls.
   */
  function showNextChunk() {
    const chunkSize = parseInt(chunkInput.value, 10);
    if (position >= words.length) {
      clearInterval(timer);
      timer = null;
      displayEl.textContent = 'Finished';
      startBtn.disabled = true;
      pauseBtn.disabled = true;
      resetBtn.disabled = false;
      return;
    }
    const chunk = words.slice(position, position + chunkSize);
    displayEl.textContent = chunk.join(' ');
    position += chunkSize;
  }

  /**
   * Start or resume the RSVP display. Creates a reading log on first start.
   */
  function start() {
    if (timer) {
      return;
    }
    const wpm = parseInt(speedInput.value, 10) || 250;
    const chunkSize = parseInt(chunkInput.value, 10) || 1;
    const stepMs = calculateStepDuration(wpm, chunkSize);
    timer = setInterval(showNextChunk, stepMs);

    // Disable/enable buttons
    startBtn.disabled = true;
    pauseBtn.disabled = false;
    resetBtn.disabled = false;

    // Create log record only once per session start
    if (!logId) {
      fetch(`/api/log/${pdfId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ speed_wpm: wpm, chunk_size: chunkSize }),
      })
        .then((res) => res.json())
        .then((data) => {
          logId = data.log_id;
        })
        .catch((err) => console.error(err));
    }
  }

  /**
   * Pause the RSVP display. Does not reset the position.
   */
  function pause() {
    if (timer) {
      clearInterval(timer);
      timer = null;
      startBtn.disabled = false;
      pauseBtn.disabled = true;
      resetBtn.disabled = false;
    }
  }

  /**
   * Reset the session to the beginning.
   */
  function reset() {
    pause();
    position = 0;
    displayEl.textContent = '';
    startBtn.disabled = false;
    pauseBtn.disabled = true;
    resetBtn.disabled = true;
    // Create a new log when started again
    logId = null;
  }

  // Event listeners
  startBtn.addEventListener('click', start);
  pauseBtn.addEventListener('click', pause);
  resetBtn.addEventListener('click', reset);

  // Immediately load the text when the reader is initialized
  loadText();
};
// Onboarding: timezone capture, Korean audio, and local-only voice recording.
document.addEventListener("DOMContentLoaded", function () {
  const timezoneInput = document.getElementById("timezone");
  if (timezoneInput) {
    try {
      timezoneInput.value =
        Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
    } catch (_error) {
      timezoneInput.value = "UTC";
    }
  }

  document.querySelectorAll("[data-speak]").forEach(function (button) {
    button.addEventListener("click", function () {
      const text = button.getAttribute("data-speak");
      if (!text || !("speechSynthesis" in window)) {
        button.textContent = "Audio unavailable";
        button.disabled = true;
        return;
      }
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = button.getAttribute("data-lang") || "ko-KR";
      utterance.rate = 0.8;
      window.speechSynthesis.speak(utterance);
    });
  });

  const panel = document.getElementById("record-panel");
  const recordBtn = document.getElementById("record-btn");
  const stopBtn = document.getElementById("stop-btn");
  const playback = document.getElementById("playback");
  const status = document.getElementById("record-status");
  if (!panel || !recordBtn || !stopBtn || !playback || !status) {
    return;
  }

  if (!navigator.mediaDevices || !window.MediaRecorder) {
    panel.hidden = true;
    return;
  }

  let recorder = null;
  let stream = null;
  let chunks = [];

  function setStatus(message) {
    status.textContent = message;
  }

  function stopTracks() {
    if (stream) {
      stream.getTracks().forEach(function (track) {
        track.stop();
      });
      stream = null;
    }
  }

  recordBtn.addEventListener("click", async function () {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunks = [];
      recorder = new MediaRecorder(stream);

      recorder.addEventListener("dataavailable", function (event) {
        if (event.data && event.data.size > 0) {
          chunks.push(event.data);
        }
      });

      recorder.addEventListener("stop", function () {
        stopTracks();
        recordBtn.hidden = false;
        stopBtn.hidden = true;
        if (chunks.length === 0) {
          setStatus("No audio captured. Try again or continue without recording.");
          return;
        }
        const blob = new Blob(chunks, {
          type: recorder.mimeType || "audio/webm",
        });
        playback.src = URL.createObjectURL(blob);
        playback.hidden = false;
        setStatus("Listen back. Notice one thing you would change.");
      });

      recorder.start();
      recordBtn.hidden = true;
      stopBtn.hidden = false;
      setStatus("Recording… say " + (panel.dataset.firstWord || "the phrase") + ".");
    } catch (_error) {
      stopTracks();
      setStatus(
        "Microphone access was blocked. You can still say it out loud and continue."
      );
    }
  });

  stopBtn.addEventListener("click", function () {
    if (recorder && recorder.state === "recording") {
      recorder.stop();
    }
  });
});

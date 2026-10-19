// Scene page: Korean audio for the character line and a focused answer field.
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("[data-speak]").forEach(function (button) {
    button.addEventListener("click", function () {
      const text = button.getAttribute("data-speak");
      if (!text || !("speechSynthesis" in window)) {
        button.disabled = true;
        button.textContent = "Audio unavailable";
        return;
      }
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "ko-KR";
      utterance.rate = 0.85;
      window.speechSynthesis.speak(utterance);
    });
  });

  const input = document.getElementById("scene-answer");
  if (input) {
    input.focus();
  }

  const panel = document.getElementById("scene-speak-panel");
  if (!panel) {
    return;
  }
  const slug = panel.getAttribute("data-scene");
  const csrfToken = panel.getAttribute("data-csrf") || "";
  const recordBtn = document.getElementById("scene-record");
  const stopBtn = document.getElementById("scene-stop");
  const useBtn = document.getElementById("scene-use");
  const playback = document.getElementById("scene-playback");
  const status = document.getElementById("scene-speech-status");

  if (!navigator.mediaDevices || !window.MediaRecorder) {
    panel.hidden = true;
    return;
  }

  let recorder = null;
  let stream = null;
  let chunks = [];
  let blob = null;
  let startedAt = 0;

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
      blob = null;
      useBtn.disabled = true;
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
          setStatus("No audio captured. Try again or type the line.");
          return;
        }
        blob = new Blob(chunks, {
          type: recorder.mimeType || "audio/webm",
        });
        playback.src = URL.createObjectURL(blob);
        playback.hidden = false;
        useBtn.disabled = false;
        setStatus("Listen back, then use this take or record again.");
      });
      startedAt = Date.now();
      recorder.start();
      recordBtn.hidden = true;
      stopBtn.hidden = false;
      setStatus("Recording… say your line.");
    } catch (_error) {
      stopTracks();
      panel.hidden = true;
      if (input) {
        input.focus();
      }
    }
  });

  stopBtn.addEventListener("click", function () {
    if (recorder && recorder.state === "recording") {
      recorder.stop();
    }
  });

  useBtn.addEventListener("click", async function () {
    if (!blob) {
      return;
    }
    useBtn.disabled = true;
    setStatus("Checking what the model heard…");
    const form = new FormData();
    form.append("audio", blob, "answer.webm");
    form.append("csrf_token", csrfToken);
    form.append("duration_ms", String(Date.now() - startedAt));

    try {
      const response = await fetch(
        "/learn/scenes/" + encodeURIComponent(slug) + "/speak",
        { method: "POST", body: form }
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Speech check failed");
      }
      if (data.accepted) {
        window.location.href = data.redirect_url;
        return;
      }
      setStatus(
        "We heard: " +
          (data.transcript || "(nothing)") +
          ". Try: " +
          (data.hint || "say it once more, slower.")
      );
    } catch (error) {
      setStatus(
        error.message ||
          "Speech checking is unavailable. Type the line instead."
      );
    } finally {
      useBtn.disabled = false;
    }
  });
});

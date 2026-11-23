// Sound Gym: browser TTS perception drills and transcript-based speech checks.
document.addEventListener("DOMContentLoaded", function () {
  const root = document.querySelector(".sound-gym");
  if (!root) {
    return;
  }
  const csrfToken = root.getAttribute("data-csrf") || "";
  const scoreUrl =
    root.getAttribute("data-score-url") || "/ko/learn/api/speech-score";

  function speak(text, button) {
    if (!text || !("speechSynthesis" in window)) {
      if (button) {
        button.textContent = "Audio unavailable";
        button.disabled = true;
      }
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "ko-KR";
    utterance.rate = 0.8;
    window.speechSynthesis.speak(utterance);
  }

  document.querySelectorAll("[data-speak]").forEach(function (button) {
    button.addEventListener("click", function () {
      speak(button.getAttribute("data-speak"), button);
    });
  });

  // Perception: choose a random word, speak it, then let the learner answer.
  document.querySelectorAll(".pair-card").forEach(function (card) {
    const options = Array.from(card.querySelectorAll(".pair-option"));
    const play = card.querySelector(".pair-play");
    const feedback = card.querySelector(".pair-feedback");
    let current = null;

    play.addEventListener("click", function () {
      const choice = options[Math.floor(Math.random() * options.length)];
      current = choice.getAttribute("data-target");
      options.forEach(function (option) {
        option.classList.remove("correct", "incorrect");
        option.disabled = false;
      });
      feedback.hidden = true;
      speak(current);
    });

    options.forEach(function (option) {
      option.addEventListener("click", function () {
        if (!current) {
          feedback.textContent = "Play a word first.";
          feedback.hidden = false;
          return;
        }
        const chosen = option.getAttribute("data-target");
        const correct = chosen === current;
        option.classList.remove("correct", "incorrect");
        option.classList.add(correct ? "correct" : "incorrect");
        if (correct) {
          options.forEach(function (item) {
            item.disabled = true;
            if (item.getAttribute("data-target") === current) {
              item.classList.add("correct");
            }
          });
          feedback.textContent =
            "Correct: " +
            current +
            ". " +
            card.querySelector(".pair-tip").textContent.trim();
        } else {
          feedback.textContent = "Not quite. Listen again and retry.";
        }
        feedback.hidden = false;
      });
    });
  });

  // Production: record locally, upload for a transcript check, never store audio.
  document.querySelectorAll(".production-card").forEach(function (card) {
    const target = card.getAttribute("data-target");
    const recordBtn = card.querySelector(".record-btn");
    const stopBtn = card.querySelector(".stop-btn");
    const checkBtn = card.querySelector(".check-btn");
    const playback = card.querySelector(".playback");
    const feedback = card.querySelector(".production-feedback");

    if (!navigator.mediaDevices || !window.MediaRecorder) {
      recordBtn.disabled = true;
      feedback.textContent =
        "Recording is not available in this browser. You can still shadow the audio.";
      return;
    }

    let recorder = null;
    let stream = null;
    let chunks = [];
    let blob = null;
    let startedAt = 0;

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
            feedback.textContent = "No audio captured. Try again.";
            return;
          }
          blob = new Blob(chunks, {
            type: recorder.mimeType || "audio/webm",
          });
          playback.src = URL.createObjectURL(blob);
          playback.hidden = false;
          checkBtn.disabled = false;
          feedback.textContent = "Listen back, then check what the model heard.";
        });
        startedAt = Date.now();
        recorder.start();
        recordBtn.hidden = true;
        stopBtn.hidden = false;
        feedback.textContent = "Recording… say the phrase.";
      } catch (_error) {
        stopTracks();
        feedback.textContent =
          "Microphone access was blocked. You can still record later.";
      }
    });

    stopBtn.addEventListener("click", function () {
      if (recorder && recorder.state === "recording") {
        recorder.stop();
      }
    });

    checkBtn.addEventListener("click", async function () {
      if (!blob) {
        return;
      }
      checkBtn.disabled = true;
      feedback.textContent = "Checking what the model heard…";
      const form = new FormData();
      form.append("audio", blob, "answer.webm");
      form.append("target_text", target);
      form.append("csrf_token", csrfToken);
      form.append("duration_ms", String(Date.now() - startedAt));

      try {
        const response = await fetch(scoreUrl, {
          method: "POST",
          body: form,
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "Speech check failed");
        }
        const band = data.band || "try_again";
        feedback.className = "production-feedback band-" + band;
        feedback.textContent =
          "We heard: " +
          (data.transcript || "(nothing)") +
          ". Transcript match: " +
          Math.round((data.match_score || 0) * 100) +
          "%. " +
          (data.acceptable
            ? "The target words came through."
            : "Try once more, slower and clearer.") +
          " This is transcript match, not an accent grade.";
      } catch (error) {
        feedback.className = "production-feedback";
        feedback.textContent =
          error.message ||
          "Speech checking is unavailable. You can still compare by ear.";
      } finally {
        checkBtn.disabled = false;
      }
    });
  });
});

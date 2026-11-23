document.addEventListener("DOMContentLoaded", function () {
  const csrfToken =
    (document.querySelector('meta[name="csrf-token"]') || {}).content || "";
  const form = document.getElementById("phrase-form");
  const resultDiv = document.getElementById("result");
  const loadingDiv = document.getElementById("loading");
  const translateBtn = document.getElementById("translate-btn");
  const resultAudio = resultDiv.querySelector("audio");

  // The listener is attached once, before any src is assigned, so a cached
  // audio file cannot fire canplay before we are listening. autoplayPending is
  // cleared before play(), so play() can never run twice for one translation.
  let autoplayPending = false;
  if (resultAudio) {
    resultAudio.addEventListener("canplay", function () {
      if (!autoplayPending) {
        return;
      }
      autoplayPending = false;
      playAudioWithFallback(resultAudio);
    });
  }

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const englishText = document.getElementById("english-text").value.trim();

    // Basic validation
    if (!englishText) {
      showError("Please enter a phrase to translate.");
      return;
    }

    // Show loading state
    translateBtn.disabled = true;
    resultDiv.classList.add("hidden");
    loadingDiv.classList.remove("hidden");

    try {
      const form = document.getElementById("phrase-form");
      const lang = (form && form.dataset.lang) || "ko";
      const response = await fetch("/api/translate?lang=" + encodeURIComponent(lang), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ text: englishText }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Translation failed");
      }

      const koreanText = data.target_text || "";
      const pronunciationLabel = koreanText || "this phrase";

      // Update the result div
      resultDiv.querySelector(".phrase-english").textContent =
        data.source_text || "";
      const targetEl = resultDiv.querySelector(".phrase-korean");
      targetEl.textContent = data.target_text || koreanText;
      if (data.target_lang) {
        targetEl.setAttribute("lang", data.target_lang);
      }

      const audio = resultDiv.querySelector("audio");
      const repeatBtn = resultDiv.querySelector(".repeat-btn");

      if (repeatBtn) {
        repeatBtn.setAttribute(
          "aria-label",
          "Repeat pronunciation for " + pronunciationLabel
        );
      }

      if (audio) {
        audio.setAttribute(
          "aria-label",
          "Play pronunciation for " + pronunciationLabel
        );

        if (data.audio_path) {
          autoplayPending = true;
          audio.src = data.audio_path;
          audio.load();
        }
      }

      // Show result
      resultDiv.classList.remove("hidden");
    } catch (error) {
      console.error("Error:", error);
      showError(error.message || "Failed to translate. Please try again.");
    } finally {
      // Hide loading state
      translateBtn.disabled = false;
      loadingDiv.classList.add("hidden");
    }
  });
});

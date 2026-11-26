document.addEventListener("DOMContentLoaded", function () {
  const csrfToken =
    (document.querySelector('meta[name="csrf-token"]') || {}).content || "";
  const stateTools = window.KikuTranslateState || {};
  const form = document.getElementById("phrase-form");
  const resultDiv = document.getElementById("result");
  const loadingDiv = document.getElementById("loading");
  const translateBtn = document.getElementById("translate-btn");
  const resultAudio = resultDiv.querySelector("audio");
  const noticeEl = document.getElementById("lookup-notice");
  let oneShotRun = !!(form && form.dataset.run === "1");
  let renderedUrl = location.pathname + location.search;

  function showNotice(message) {
    if (!noticeEl) {
      return;
    }
    noticeEl.textContent = message || "";
    noticeEl.hidden = !message;
  }

  ["english-text", "register", "addressee"].forEach(function (id) {
    const field = document.getElementById(id);
    if (!field) {
      return;
    }
    field.addEventListener("input", function () {
      showNotice("");
    });
    field.addEventListener("change", function () {
      showNotice("");
    });
  });

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

    const addresseeInput = document.getElementById("addressee");
    const addressee = addresseeInput ? addresseeInput.value : "any";
    const registerInput = document.getElementById("register");
    const register = registerInput ? registerInput.value : null;
    const currentRegister = register || "";
    const currentAddressee = addressee || "any";

    showNotice("");
    if (
      !resultDiv.classList.contains("hidden") &&
      stateTools.isRenderedResult &&
      stateTools.isRenderedResult(
        resultDiv.dataset,
        englishText,
        currentRegister,
        currentAddressee
      )
    ) {
      showNotice(
        "Already showing this result. Change the phrase or options to look up again."
      );
      resultDiv.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }

    const oneShot = oneShotRun;
    oneShotRun = false;

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
        body: JSON.stringify({ text: englishText, addressee, register }),
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
      const romanizationEl = resultDiv.querySelector(".phrase-romanization");

      if (romanizationEl) {
        romanizationEl.textContent = data.romanization || "";
        romanizationEl.hidden = !data.romanization;
      }

      const addresseeOut = resultDiv.querySelector(".phrase-addressee");
      if (addresseeOut) {
        const label = data.addressee_label || "";
        addresseeOut.textContent = label;
        addresseeOut.hidden = !label;
      }

      const registerOut = resultDiv.querySelector(".phrase-register");
      if (registerOut) {
        const label = data.register_label || "";
        registerOut.textContent = label;
        registerOut.hidden = !label;
      }

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

      // Make the URL the state of the result we are showing. The id points at
      // the saved phrase, so back/forward and reload render from SQLite and
      // never re-call the model or regenerate audio.
      const phraseUuid = data.uuid || "";
      resultDiv.dataset.phraseUuid = phraseUuid;
      resultDiv.dataset.phraseSource = englishText;
      resultDiv.dataset.phraseRegister = data.register || currentRegister;
      resultDiv.dataset.phraseAddressee = data.addressee || currentAddressee;
      if (phraseUuid && window.history && window.history.pushState) {
        const phraseUrl = stateTools.phraseUrl
          ? stateTools.phraseUrl(location.pathname, phraseUuid)
          : location.pathname + "?phrase=" + encodeURIComponent(phraseUuid);
        if (oneShot) {
          window.history.replaceState({ phrase: phraseUuid }, "", phraseUrl);
        } else {
          const params = new URLSearchParams(location.search);
          if (!params.get("phrase") && !params.get("q")) {
            // Keep the typed query on the entry we are leaving, so Back shows
            // the form filled in rather than empty.
            window.history.replaceState(
              null,
              "",
              location.pathname + "?q=" + encodeURIComponent(englishText)
            );
          }
          window.history.pushState({ phrase: phraseUuid }, "", phraseUrl);
        }
        renderedUrl = phraseUrl;
      }
    } catch (error) {
      console.error("Error:", error);
      showError(error.message || "Failed to translate. Please try again.");
    } finally {
      // Hide loading state
      translateBtn.disabled = false;
      loadingDiv.classList.add("hidden");
      oneShotRun = false;
    }
  });

  // A header lookup lands here with ?q=…&run=1. Run it once, then strip the
  // one-shot flag so a reload cannot re-translate or re-bill the audio call.
  if (form && form.dataset.run === "1") {
    const initial = document.getElementById("english-text");
    if (initial && initial.value.trim()) {
      if (form.requestSubmit) {
        form.requestSubmit();
      } else {
        form.dispatchEvent(new Event("submit", { cancelable: true }));
      }
      form.dataset.run = "0";
      if (window.history && window.history.replaceState) {
        window.history.replaceState(
          null,
          "",
          location.pathname + "?q=" + encodeURIComponent(initial.value)
        );
      }
    }
  }

  // History entries are canonical phrase URLs, so back/forward is a server
  // render from SQLite: no model call and no new audio. Ignore same-document
  // fragment traversals (such as the skip link), which do not change the page.
  window.addEventListener("popstate", function () {
    const currentUrl = location.pathname + location.search;
    const reload = stateTools.shouldReload
      ? stateTools.shouldReload(currentUrl, renderedUrl)
      : currentUrl !== renderedUrl;
    if (reload) {
      window.location.reload();
    }
  });
});

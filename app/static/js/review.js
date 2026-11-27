// Review keyboard shortcuts, stored audio, and a Korean speech fallback.
document.addEventListener("DOMContentLoaded", function () {
  const csrfToken =
    (document.querySelector('meta[name="csrf-token"]') || {}).content || "";
  const reviewShell = document.querySelector(".review-shell");
  const languageCode =
    (reviewShell && reviewShell.dataset.languageCode) || "ko";
  const form = document.querySelector(".grade-form");
  const answer = document.querySelector(".review-answer");
  const card = document.querySelector(".review-card");
  const shortcutToggle = document.getElementById("shortcuts-toggle");
  const elapsedInput = document.getElementById("elapsed-ms");
  const startedAt = Date.now();
  const gradeButtons = form
    ? Array.from(form.querySelectorAll('button[name="rating"]'))
    : [];

  // Retrieval first: the grade buttons stay disabled until the learner has
  // revealed the answer. Without JS, the server-rendered buttons still work.
  function syncGradeLock() {
    if (!answer) {
      return;
    }
    gradeButtons.forEach(function (button) {
      button.disabled = !answer.open;
    });
    if (card) {
      card.classList.toggle("is-revealable", !answer.open);
    }
  }

  if (answer) {
    syncGradeLock();
    answer.addEventListener("toggle", syncGradeLock);
  }

  // Listen-first mode: hide the written prompt, play the clip, and reveal both
  // together. Off by default; the choice sticks for this browser.
  const listenToggle = document.getElementById("review-listen");
  const promptAudio =
    card && card.querySelector("audio.review-audio");

  function listenFirstEnabled() {
    if (!listenToggle) {
      return false;
    }
    try {
      return window.localStorage.getItem("kiku-review-listen") === "1";
    } catch (_error) {
      return false;
    }
  }

  function applyListenFirst() {
    const on = !!(listenToggle && listenToggle.checked);
    if (card) {
      card.classList.toggle("is-listen-first", on);
    }
    try {
      window.localStorage.setItem("kiku-review-listen", on ? "1" : "0");
    } catch (_error) {
      /* private mode */
    }
    if (on && promptAudio) {
      promptAudio.play().catch(function () {
        /* autoplay may be blocked; the player is still there */
      });
    }
  }

  if (listenToggle) {
    listenToggle.checked = listenFirstEnabled();
    if (listenToggle.checked) {
      applyListenFirst();
    }
    listenToggle.addEventListener("change", applyListenFirst);
  }

  if (answer && card) {
    answer.addEventListener("toggle", function () {
      if (answer.open) {
        card.classList.remove("is-listen-first");
      }
    });
  }

  // The summary remains the semantic control; this just makes the whole prompt
  // card a larger target for touch and mouse.
  if (card && answer) {
    card.addEventListener("click", function (event) {
      if (answer.open) return;
      if (
        event.target.closest(
          "a, button, audio, summary, input, select, textarea, label"
        )
      ) {
        return;
      }
      answer.open = true;
    });
  }

  function shortcutsEnabled() {
    try {
      return window.localStorage.getItem("kiku-review-shortcuts") !== "0";
    } catch (_error) {
      return true;
    }
  }

  if (shortcutToggle) {
    shortcutToggle.checked = shortcutsEnabled();
    shortcutToggle.addEventListener("change", function () {
      try {
        window.localStorage.setItem(
          "kiku-review-shortcuts",
          shortcutToggle.checked ? "1" : "0"
        );
      } catch (_error) {
        /* ignore */
      }
    });
  }

  if (form && elapsedInput) {
    form.addEventListener("submit", function () {
      elapsedInput.value = String(Date.now() - startedAt);
    });

    document.addEventListener("keydown", function (event) {
      if (
        event.target.closest(
          "input, textarea, select, button, audio, video, [role='slider']"
        ) ||
        event.target.matches("summary") ||
        event.metaKey ||
        event.ctrlKey ||
        event.altKey
      ) {
        return;
      }

      if (!shortcutsEnabled()) {
        return;
      }

      const rating = ["1", "2", "3", "4"].indexOf(event.key);
      if (rating !== -1) {
        event.preventDefault();
        if (answer && !answer.open) {
          answer.open = true;
          return;
        }
        if (event.repeat) {
          return;
        }
        const button = form.querySelector(
          'button[name="rating"][value="' + (rating + 1) + '"]'
        );
        if (button && !button.disabled) {
          button.click();
        }
      }
    });
  }

  document.querySelectorAll("[data-variant-audio]").forEach(function (button) {
    button.addEventListener("click", async function () {
      const text = button.getAttribute("data-text");
      const itemId = button.getAttribute("data-item-id");
      if (!text || !itemId) {
        return;
      }
      const original = button.textContent;
      button.disabled = true;
      button.textContent = "Generating…";
      try {
        const response = await fetch(
          "/api/variants/audio?lang=" + encodeURIComponent(languageCode),
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": csrfToken,
            },
            body: JSON.stringify({ item_id: Number(itemId), text: text }),
          }
        );
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "Audio generation failed");
        }

        const audio = document.createElement("audio");
        audio.controls = true;
        audio.preload = "none";
        audio.className = "review-audio";
        audio.src = data.audio_path;
        audio.setAttribute("aria-label", "Play pronunciation for " + text);
        button.replaceWith(audio);
        const started = audio.play();
        if (started && started.catch) {
          started.catch(function () {});
        }
      } catch (error) {
        console.error("Variant audio failed:", error);
        button.disabled = false;
        button.textContent = original;
      }
    });
  });

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
      const shell = document.querySelector(".review-shell");
      utterance.lang = (shell && shell.dataset.ttsLang) || "ko-KR";
      utterance.rate = 0.85;
      window.speechSynthesis.speak(utterance);
    });
  });
});

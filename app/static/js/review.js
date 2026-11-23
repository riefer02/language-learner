// Review keyboard shortcuts and a no-cost Korean audio fallback.
document.addEventListener("DOMContentLoaded", function () {
  const form = document.querySelector(".grade-form");
  const answer = document.querySelector(".review-answer");
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
  }

  if (answer) {
    syncGradeLock();
    answer.addEventListener("toggle", syncGradeLock);
  }

  if (form && elapsedInput) {
    form.addEventListener("submit", function () {
      elapsedInput.value = String(Date.now() - startedAt);
    });

    document.addEventListener("keydown", function (event) {
      if (
        event.target.matches("input, textarea, select, button") ||
        (event.target.matches("summary") && event.code === "Space") ||
        event.metaKey ||
        event.ctrlKey ||
        event.altKey
      ) {
        return;
      }

      if (event.code === "Space" && answer) {
        event.preventDefault();
        answer.open = !answer.open;
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

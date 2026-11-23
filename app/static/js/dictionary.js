// Speak dictionary entries with the browser when no pre-generated audio exists.
(function () {
  "use strict";
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
      utterance.lang = button.getAttribute("data-lang") || "ko-KR";
      utterance.rate = 0.85;
      window.speechSynthesis.speak(utterance);
    });
  });
})();

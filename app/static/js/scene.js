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
});

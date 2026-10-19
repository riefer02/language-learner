// Hangul drills: immediate feedback, retry on mistakes, no server round trip.
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".drill").forEach(function (drill) {
    const answer = drill.getAttribute("data-answer");
    const feedback = drill.querySelector(".drill-feedback");
    const explanation = feedback.getAttribute("data-explanation") || "";
    const options = Array.from(drill.querySelectorAll(".drill-option"));

    options.forEach(function (button) {
      button.addEventListener("click", function () {
        const correct = button.getAttribute("data-option") === answer;
        button.classList.remove("correct", "incorrect");
        button.classList.add(correct ? "correct" : "incorrect");

        if (correct) {
          options.forEach(function (option) {
            option.disabled = true;
            if (option.getAttribute("data-option") === answer) {
              option.classList.add("correct");
            }
          });
          feedback.textContent = "Correct. " + explanation;
        } else {
          feedback.textContent = "Not quite. Try again. " + explanation;
        }
        feedback.hidden = false;
      });
    });
  });

  document.querySelectorAll("[data-speak]").forEach(function (button) {
    button.addEventListener("click", function () {
      const text = button.getAttribute("data-speak");
      if (!text || !("speechSynthesis" in window)) {
        return;
      }
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "ko-KR";
      utterance.rate = 0.8;
      window.speechSynthesis.speak(utterance);
    });
  });
});

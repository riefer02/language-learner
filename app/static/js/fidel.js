// Fidel bootcamp: type the sound for each glyph.
(function () {
  "use strict";

  const root = document.getElementById("fidel-lesson");
  if (!root) return;

  const dataEl = document.getElementById("fidel-data");
  const drills = JSON.parse((dataEl && dataEl.textContent) || "[]");
  const glyphEl = document.getElementById("fidel-glyph");
  const form = document.getElementById("fidel-form");
  const input = document.getElementById("fidel-answer");
  const feedback = document.getElementById("fidel-feedback");
  const progress = document.getElementById("fidel-progress");
  const revealBtn = document.getElementById("fidel-reveal");
  const nextBtn = document.getElementById("fidel-next");

  let index = 0;
  let correct = 0;
  let answered = false;

  function normalize(value) {
    return (value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/ə/g, "e")
      .replace(/[^a-z]/g, "");
  }

  function render() {
    const drill = drills[index];
    if (!drill) {
      glyphEl.textContent = "✓";
      feedback.textContent =
        "Lesson complete — " + correct + " of " + drills.length + " correct.";
      input.hidden = true;
      form.querySelector("button").hidden = true;
      revealBtn.hidden = true;
      nextBtn.textContent = "Start again";
      nextBtn.dataset.done = "1";
      return;
    }
    glyphEl.textContent = drill.glyph;
    input.value = "";
    input.hidden = false;
    form.querySelector("button").hidden = false;
    feedback.textContent = "";
    progress.textContent = index + " / " + drills.length;
    answered = false;
    input.focus();
  }

  function reveal(message) {
    const drill = drills[index];
    feedback.textContent = message + " Answer: " + drill.roman;
    answered = true;
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    if (answered || !drills[index]) return;
    const value = normalize(input.value);
    const expected = normalize(drills[index].roman);
    if (value === expected) {
      correct += 1;
      reveal("Correct.");
    } else {
      reveal("Not quite.");
    }
  });

  revealBtn.addEventListener("click", function () {
    if (!drills[index] || answered) return;
    reveal("");
  });

  nextBtn.addEventListener("click", function () {
    if (nextBtn.dataset.done === "1") {
      index = 0;
      correct = 0;
      nextBtn.textContent = "Next";
      delete nextBtn.dataset.done;
      render();
      return;
    }
    index += 1;
    render();
  });

  render();
})();

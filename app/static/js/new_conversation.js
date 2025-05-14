document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("conversation-form");
  const resultDiv = document.getElementById("result");
  const loadingDiv = document.getElementById("loading");
  const errorDiv = document.getElementById("error-message");
  const generateBtn = document.getElementById("generate-btn");

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    const prompt = document.getElementById("scenario-prompt").value.trim();
    if (!prompt) {
      showError("Please enter a scenario prompt.");
      return;
    }
    // Show loading
    generateBtn.disabled = true;
    resultDiv.classList.add("hidden");
    errorDiv.classList.add("hidden");
    loadingDiv.classList.remove("hidden");
    loadingDiv.setAttribute("aria-hidden", "false");
    try {
      const response = await fetch("/api/conversation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Failed to generate conversation");
      }
      // Render result
      renderConversation(data);
      resultDiv.classList.remove("hidden");
    } catch (error) {
      showError(
        error.message || "Failed to generate conversation. Please try again."
      );
    } finally {
      generateBtn.disabled = false;
      loadingDiv.classList.add("hidden");
      loadingDiv.setAttribute("aria-hidden", "true");
    }
  });

  function showError(message) {
    errorDiv.textContent = message;
    errorDiv.classList.remove("hidden");
    errorDiv.setAttribute("tabindex", "-1");
    errorDiv.focus();
    setTimeout(() => {
      errorDiv.classList.add("hidden");
    }, 5000);
  }

  function renderConversation(conv) {
    let html = `<h3>${conv.title}</h3>`;
    if (conv.description) {
      html += `<p>${conv.description}</p>`;
    }
    html += `<div class='audio-player' style='margin-bottom: 20px;'><audio src='${conv.audio_path}' controls preload='none'></audio> <span style='margin-left: 10px; font-weight: bold;'>Full Conversation</span></div>`;
    html += `<h4>Lines</h4>`;
    for (const line of conv.lines) {
      html += `<div class='phrase-card'>`;
      html += `<div class='phrase-english'><strong>${line.speaker}</strong>: ${line.phrase.english_text}</div>`;
      html += `<div class='phrase-korean'>${line.phrase.korean_text}</div>`;
      html += `<div class='audio-player'><audio src='${line.phrase.audio_path}' controls preload='none'></audio> <button class='repeat-btn' aria-label='Repeat audio'>Repeat</button></div>`;
      html += `</div>`;
    }
    resultDiv.innerHTML = html;
  }

  // Delegate repeat button clicks
  resultDiv.addEventListener("click", function (e) {
    if (e.target.classList.contains("repeat-btn")) {
      const audio = e.target.closest(".audio-player").querySelector("audio");
      audio.currentTime = 0;
      if (audio) {
        const playPromise = audio.play();
        if (playPromise !== undefined) {
          playPromise.catch(() => {});
        }
      }
    }
  });
});

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
    try {
      const form = document.getElementById("conversation-form");
      const lang = (form && form.dataset.lang) || "ko";
      const response = await fetch("/api/conversation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, lang }),
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

  // Build the audio player without ever injecting markup. All content from the
  // API (titles, descriptions, speakers, phrases, paths) is set via
  // textContent or DOM properties.
  function createAudioPlayer(options) {
    const player = document.createElement("div");
    player.className = "audio-player";

    const audio = document.createElement("audio");
    audio.controls = true;
    audio.preload = "none";
    audio.setAttribute("aria-label", options.audioLabel);
    if (options.src) {
      audio.src = options.src;
    }
    player.appendChild(audio);

    if (options.repeatLabel) {
      const repeatBtn = document.createElement("button");
      repeatBtn.type = "button";
      repeatBtn.className = "repeat-btn";
      repeatBtn.textContent = "Repeat";
      repeatBtn.setAttribute("aria-label", options.repeatLabel);
      player.appendChild(repeatBtn);
    }

    return player;
  }

  function renderConversation(conv) {
    // Clear any previous render. textContent never interprets HTML.
    resultDiv.textContent = "";

    const title = document.createElement("h3");
    title.textContent = conv.title || "";
    title.setAttribute("lang", "en");
    resultDiv.appendChild(title);

    if (conv.description) {
      const description = document.createElement("p");
      description.textContent = conv.description;
      description.setAttribute("lang", "en");
      resultDiv.appendChild(description);
    }

    if (conv.audio_path) {
      const fullPlayer = createAudioPlayer({
        src: conv.audio_path,
        audioLabel:
          "Play full conversation: " + (conv.title || "conversation"),
      });
      fullPlayer.classList.add("audio-player-spaced");

      const fullLabel = document.createElement("span");
      fullLabel.className = "conversation-label";
      fullLabel.textContent = "Full Conversation";
      fullPlayer.appendChild(fullLabel);

      resultDiv.appendChild(fullPlayer);
    }

    const linesHeading = document.createElement("h4");
    linesHeading.textContent = "Lines";
    resultDiv.appendChild(linesHeading);

    const lines = Array.isArray(conv.lines) ? conv.lines : [];

    for (const line of lines) {
      const phrase = (line && line.phrase) || {};
      const koreanText = phrase.target_text || "";
      const englishText = phrase.source_text || "";
      const phraseLabel = koreanText || "this phrase";

      const card = document.createElement("div");
      card.className = "phrase-card";

      const english = document.createElement("div");
      english.className = "phrase-english";
      english.setAttribute("lang", "en");

      const speaker = document.createElement("strong");
      speaker.textContent =
        line && line.speaker !== undefined && line.speaker !== null
          ? String(line.speaker)
          : "";
      english.appendChild(speaker);
      english.appendChild(document.createTextNode(": " + englishText));
      card.appendChild(english);

      const korean = document.createElement("div");
      korean.className = "phrase-korean";
      korean.setAttribute("lang", "ko");
      korean.textContent = koreanText;
      card.appendChild(korean);

      card.appendChild(
        createAudioPlayer({
          src: phrase.audio_path || "",
          audioLabel: "Play pronunciation for " + phraseLabel,
          repeatLabel: "Repeat pronunciation for " + phraseLabel,
        })
      );

      resultDiv.appendChild(card);
    }
  }

  // Delegate repeat button clicks
  resultDiv.addEventListener("click", function (e) {
    const repeatBtn = e.target.closest(".repeat-btn");
    if (!repeatBtn) {
      return;
    }

    const player = repeatBtn.closest(".audio-player");
    const audio = player ? player.querySelector("audio") : null;
    if (!audio) {
      return;
    }

    audio.currentTime = 0;
    const playPromise = audio.play();
    if (playPromise !== undefined) {
      playPromise.catch(() => {});
    }
  });
});

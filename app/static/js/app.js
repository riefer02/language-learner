// Register the PWA service worker for installability and reminders.
if ("serviceWorker" in navigator) {
  window.addEventListener("load", function () {
    navigator.serviceWorker.register("/sw.js").catch(function () {
      // The app still works without the service worker.
    });
  });
}

// Common utility functions for Kiku

// Safely play audio with error handling
function playAudioWithFallback(audioElement) {
  if (!audioElement) {
    return;
  }

  const playPromise = audioElement.play();

  if (playPromise !== undefined) {
    playPromise.catch((error) => {
      // Autoplay can be blocked before a gesture; leave the controls visible
      // instead of showing a failure alert for a successful lookup.
      if (error && error.name === "NotAllowedError") {
        return;
      }
      console.error("Audio playback error:", error);
      const errorContainer = document.getElementById("error-message");
      if (errorContainer) {
        errorContainer.textContent = "Audio playback failed. Please try again.";
        errorContainer.classList.remove("hidden");
        setTimeout(() => {
          errorContainer.classList.add("hidden");
        }, 3000);
      }
    });
  }
}

// Show error message
function showError(message) {
  const errorContainer = document.getElementById("error-message");
  if (errorContainer) {
    errorContainer.textContent = message;
    errorContainer.classList.remove("hidden");
    // Focus the error message for screen readers
    errorContainer.setAttribute("tabindex", "-1");
    errorContainer.focus();

    // Auto-hide after 5 seconds
    setTimeout(() => {
      errorContainer.classList.add("hidden");
    }, 5000);
  }
}

// Handle repeat button clicks
document.addEventListener("click", function (e) {
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
  playAudioWithFallback(audio);
});

// Play a looked-up phrase straight from its collapsed row. The button lives
// inside <summary>, so the click must not also open the row.
document.addEventListener("click", function (e) {
  const playBtn = e.target.closest(".phrase-entry-play");
  if (!playBtn) {
    return;
  }

  e.preventDefault();
  e.stopPropagation();

  const entry = playBtn.closest(".phrase-entry");
  const audio = entry ? entry.querySelector("audio") : null;
  if (!audio) {
    return;
  }

  function setLabel(playing) {
    const label = playing
      ? playBtn.dataset.labelPause
      : playBtn.dataset.labelPlay;
    if (label) {
      playBtn.setAttribute("aria-label", label);
    }
  }

  if (!audio.paused) {
    audio.pause();
    playBtn.classList.remove("is-playing");
    setLabel(false);
    return;
  }

  audio.currentTime = 0;
  audio.addEventListener(
    "ended",
    function () {
      playBtn.classList.remove("is-playing");
      setLabel(false);
    },
    { once: true }
  );
  playBtn.classList.add("is-playing");
  setLabel(true);
  playAudioWithFallback(audio);
});

// Handle keyboard accessibility
document.addEventListener("keydown", function (e) {
  // Space or Enter on repeat buttons
  if (
    (e.key === " " || e.key === "Enter") &&
    document.activeElement &&
    document.activeElement.classList.contains("repeat-btn")
  ) {
    e.preventDefault();
    document.activeElement.click();
  }
});

// Responsive navigation disclosure.
(function () {
  const toggle = document.getElementById("nav-toggle");
  const menu = document.getElementById("primary-nav");
  if (!toggle || !menu) return;

  function setOpen(open) {
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    menu.classList.toggle("is-open", open);
  }

  toggle.addEventListener("click", function () {
    setOpen(toggle.getAttribute("aria-expanded") !== "true");
  });

  menu.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", function () {
      setOpen(false);
    });
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
      setOpen(false);
      toggle.focus();
    }
  });
})();

// One-time page help: show it inline on the first visit, then behind the ?.
(function () {
  document.querySelectorAll("details[data-first-visit]").forEach(function (details) {
    const key = details.getAttribute("data-first-visit");
    const block = details.nextElementSibling;
    const hasBlock = block && block.hasAttribute("data-first-visit-block");
    let seen = false;
    try {
      seen = window.localStorage.getItem(key) === "1";
    } catch (_error) {
      /* localStorage can be unavailable in private mode. */
    }
    if (!seen) {
      details.hidden = true;
      if (hasBlock) block.hidden = false;
      try {
        window.localStorage.setItem(key, "1");
      } catch (_error) {
        /* ignore */
      }
    }
    if (hasBlock) {
      const done = block.querySelector("[data-first-visit-done]");
      if (done) {
        done.addEventListener("click", function () {
          block.hidden = true;
          details.hidden = false;
          details.open = false;
        });
      }
    }
  });

  document.addEventListener("click", function (event) {
    document.querySelectorAll("details.page-help[open]").forEach(function (details) {
      if (!details.contains(event.target)) {
        details.open = false;
      }
    });
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    document.querySelectorAll("details.page-help[open]").forEach(function (details) {
      details.open = false;
      const summary = details.querySelector("summary");
      if (summary) summary.focus();
    });
  });
})();

// Language switch: submit the header form when the selection changes.
(function () {
  document.querySelectorAll(".language-switch select").forEach(function (select) {
    select.addEventListener("change", function () {
      if (select.form) {
        if (select.form.requestSubmit) select.form.requestSubmit();
        else select.form.submit();
      }
    });
  });
})();

// Close open nav menus on Escape or an outside click.
(function () {
  const groups = [...document.querySelectorAll(".nav-group details")];
  if (!groups.length) return;

  document.addEventListener("click", function (event) {
    if (event.target.closest(".nav-group")) return;
    groups.forEach(function (details) {
      details.open = false;
    });
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    groups.forEach(function (details) {
      details.open = false;
    });
  });
})();

// Content reports: capture a correction without leaving the page. The server
// keeps a snapshot and triage stays manual, so nothing here edits content.
(function () {
  const forms = document.querySelectorAll("form[data-content-flag]");
  if (!forms.length) return;
  const csrf =
    (document.querySelector('meta[name="csrf-token"]') || {}).content || "";

  forms.forEach(function (form) {
    form.hidden = false;
    const status = form.querySelector(".content-flag-status");
    const button = form.querySelector('button[type="submit"]');
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      const payload = {};
      new FormData(form).forEach(function (value, key) {
        if (typeof value === "string" && value.trim()) {
          payload[key] = value.trim();
        }
      });
      if (button) button.disabled = true;
      if (status) status.textContent = "Sending…";
      try {
        const response = await fetch("/api/content-reports", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrf,
          },
          body: JSON.stringify(payload),
        });
        const data = await response.json().catch(function () {
          return {};
        });
        if (!response.ok) {
          throw new Error(data.error || "Could not send the report.");
        }
        // The learner never sees these reports again, so say where they go.
        if (status) {
          status.textContent =
            "Reported. It is queued for triage — thanks.";
        }
        if (button) button.textContent = "Reported";
        form.reset();
      } catch (error) {
        if (status) status.textContent = error.message;
        if (button) button.disabled = false;
      }
    });
  });
})();

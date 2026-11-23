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
      console.error("Audio playback error:", error);
      // Show a message to the user, if appropriate
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

// Dismissible first-run guidance. State is local to the browser.
(function () {
  document.querySelectorAll("[data-dismissible]").forEach(function (card) {
    const key = card.getAttribute("data-dismissible");
    try {
      if (key && window.localStorage.getItem(key) === "1") {
        card.hidden = true;
        return;
      }
    } catch (_error) {
      /* localStorage can be unavailable in private mode. */
    }
    const button = card.querySelector("[data-dismiss]");
    if (button) {
      button.addEventListener("click", function () {
        card.hidden = true;
        try {
          if (key) window.localStorage.setItem(key, "1");
        } catch (_error) {
          /* ignore */
        }
      });
    }
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

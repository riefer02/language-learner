// Voice-first teacher: WebRTC to the realtime provider, tools via Flask.
(function () {
  "use strict";

  const root = document.getElementById("teacher-app");
  if (!root) return;

  const startBtn = document.getElementById("teacher-start");
  const stopBtn = document.getElementById("teacher-stop");
  const statusEl = document.getElementById("teacher-status");
  const planEl = document.getElementById("teacher-plan");
  const transcriptEl = document.getElementById("teacher-transcript");
  const debriefEl = document.getElementById("teacher-debrief");
  const summaryEl = document.getElementById("teacher-summary");
  const drillsEl = document.getElementById("teacher-drills");
  const termsEl = document.getElementById("teacher-terms");
  const audioEl = document.getElementById("teacher-audio");
  const stateEl = document.getElementById("teacher-state");
  const countdownEl = document.getElementById("teacher-countdown");
  const meterEl = document.getElementById("teacher-meter");
  const meterFill = document.getElementById("teacher-meter-fill");
  const quickEl = document.getElementById("teacher-quick");
  const slowerBtn = document.getElementById("teacher-slower");
  const repeatBtn = document.getElementById("teacher-repeat");
  const callPanel = document.getElementById("teacher-call-panel");
  const againBtn = document.getElementById("teacher-again");
  const suggestToggle = document.getElementById("teacher-suggest-toggle");
  const suggestionEl = document.getElementById("teacher-suggestion");
  const suggestionTarget = document.getElementById("teacher-suggestion-target");
  const suggestionRoman = document.getElementById(
    "teacher-suggestion-romanization"
  );
  const suggestionGloss = document.getElementById("teacher-suggestion-gloss");
  const suggestionError = document.getElementById(
    "teacher-suggestion-error"
  );
  const suggestionRetry = document.getElementById(
    "teacher-suggestion-retry"
  );
  const suggestionHelp = document.getElementById("teacher-suggest-help");
  const csrf =
    (document.querySelector('meta[name="csrf-token"]') || {}).content || "";

  function connectedMessage() {
    const greeting = root.dataset.greeting || "";
    const name = root.dataset.speechName || "the target language";
    return greeting
      ? "Connected. Say “" + greeting + "”."
      : "Connected. Say hello in " + name + ".";
  }

  let peer = null;
  let channel = null;
  let mic = null;
  const provider = root.dataset.provider || "openai_realtime";
  let sessionId = null;
  let suggestToken = 0;
  let expiryTimer = null;
  let clockTimer = null;
  let socket = null;
  let audioContext = null;
  let playbackCursor = 0;
  let micSource = null;
  let micProcessor = null;
  let micWorklet = null;
  const geminiToolResults = new Map();
  let ending = false;
  let userEnded = false;
  const handledCalls = new Set();
  const transcriptBuffer = { teacher: "", learner: "" };

  function setStatus(text) {
    statusEl.textContent = text;
  }

  // The state chip is the primary signal; the status line carries the detail.
  function setCallState(state, label) {
    if (!stateEl) {
      return;
    }
    stateEl.dataset.state = state;
    stateEl.textContent = label;
  }

  function setCallActive(active) {
    if (startBtn && stopBtn) {
      startBtn.classList.toggle("btn-primary", !active);
      stopBtn.classList.toggle("btn-primary", active);
    }
    if (meterEl) {
      meterEl.hidden = !active;
    }
    if (quickEl) {
      quickEl.hidden = !active;
    }
  }

  // A text turn for the things a beginner cannot say yet in the target
  // language: asking Kiku to repeat or slow down.
  function sendTextTurn(text) {
    if (provider === "gemini_live") {
      if (socket && socket.readyState === window.WebSocket.OPEN) {
        socket.send(
          JSON.stringify({
            clientContent: {
              turns: [{ role: "user", parts: [{ text: text }] }],
              turnComplete: true,
            },
          })
        );
      }
      return;
    }
    if (channel && channel.readyState === "open") {
      channel.send(
        JSON.stringify({
          type: "conversation.item.create",
          item: {
            type: "message",
            role: "user",
            content: [{ type: "input_text", text: text }],
          },
        })
      );
      channel.send(JSON.stringify({ type: "response.create" }));
    }
  }

  if (slowerBtn) {
    slowerBtn.addEventListener("click", function () {
      sendTextTurn("Say that again more slowly, please.");
    });
  }
  if (repeatBtn) {
    repeatBtn.addEventListener("click", function () {
      sendTextTurn("Please repeat what you just said.");
    });
  }
  if (againBtn) {
    againBtn.addEventListener("click", function () {
      if (debriefEl) {
        debriefEl.hidden = true;
      }
      if (callPanel) {
        callPanel.hidden = false;
      }
      setCallState("idle", "Ready");
      setStatus("Ready when you are. Allow the microphone, then start.");
      transcriptEl.innerHTML = "";
      startBtn.focus();
    });
  }

  // Microphone level: the one signal that answers "is it hearing me?".
  let meterContext = null;
  let meterAnalyser = null;
  let meterFrame = null;
  let meterOwnsContext = false;
  let meterSource = null;

  function startMicMeter(stream, existingContext) {
    stopMicMeter();
    try {
      meterContext =
        existingContext ||
        new (window.AudioContext || window.webkitAudioContext)();
      meterOwnsContext = !existingContext;
      meterSource = meterContext.createMediaStreamSource(stream);
      meterAnalyser = meterContext.createAnalyser();
      meterAnalyser.fftSize = 1024;
      meterSource.connect(meterAnalyser);
      const samples = new Uint8Array(meterAnalyser.fftSize);
      const tick = function () {
        if (!meterAnalyser || !meterFill) {
          return;
        }
        meterAnalyser.getByteTimeDomainData(samples);
        let sum = 0;
        for (let i = 0; i < samples.length; i += 1) {
          const value = (samples[i] - 128) / 128;
          sum += value * value;
        }
        const rms = Math.sqrt(sum / samples.length);
        const level = Math.min(1, rms * 6);
        meterFill.style.transform = "scaleX(" + level.toFixed(3) + ")";
        meterFrame = window.requestAnimationFrame(tick);
      };
      tick();
    } catch (_error) {
      // A meter is nice to have; never let it stop a call.
    }
  }

  function stopMicMeter() {
    if (meterFrame) {
      window.cancelAnimationFrame(meterFrame);
      meterFrame = null;
    }
    if (meterFill) {
      meterFill.style.transform = "scaleX(0)";
    }
    meterAnalyser = null;
    if (meterSource) {
      try {
        meterSource.disconnect();
      } catch (_error) {
        /* already disconnected */
      }
      meterSource = null;
    }
    if (meterOwnsContext && meterContext) {
      meterContext.close().catch(function () {
        /* already closed */
      });
    }
    meterContext = null;
    meterOwnsContext = false;
  }

  function formatClock(ms) {
    const total = Math.max(0, Math.round(ms / 1000));
    const minutes = Math.floor(total / 60);
    const seconds = total % 60;
    return (
      String(minutes).padStart(2, "0") + ":" + String(seconds).padStart(2, "0")
    );
  }

  async function api(path, body) {
    const response = await fetch(path, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf,
      },
      body: JSON.stringify(body || {}),
    });
    const data = await response.json().catch(function () {
      return {};
    });
    if (!response.ok) {
      throw new Error(data.error || "Request failed (" + response.status + ")");
    }
    return data;
  }

  // --- Coach hint: what Kiku said, and what to say back ------------------
  const SUGGEST_KEY = "kiku-teacher-suggest";
  let lastTeacherTurn = null;
  let replyWatch = null;
  // Newest first: a turn goes on top, so the live line is always visible
  // without scrolling and there is no scroll position to maintain.
  function addTurnElement(element) {
    const placeholder = transcriptEl.querySelector(".teacher-empty");
    if (placeholder) {
      placeholder.remove();
    }
    transcriptEl.insertBefore(element, transcriptEl.firstChild);
  }

  function suggestionEnabled() {
    return !!(suggestToggle && suggestToggle.checked);
  }

  function syncSuggestionHelp() {
    if (suggestionHelp) {
      suggestionHelp.hidden = !suggestionEnabled();
    }
  }

  function hideSuggestion() {
    if (suggestionEl) {
      suggestionEl.hidden = true;
    }
  }

  // A failed hint should not look like "the app forgot"; say so and offer a
  // retry, because the text model can be momentarily busy.
  function showSuggestionError() {
    if (!suggestionEnabled()) {
      return;
    }
    if (suggestionEl) {
      suggestionEl.hidden = false;
    }
    if (suggestionTarget) {
      suggestionTarget.textContent = "";
    }
    if (suggestionRoman) {
      suggestionRoman.textContent = "";
    }
    if (suggestionGloss) {
      suggestionGloss.textContent = "";
    }
    if (suggestionError) {
      suggestionError.hidden = false;
    }
    if (suggestionRetry) {
      suggestionRetry.hidden = false;
    }
  }

  function fillSuggestion(data) {
    if (!suggestionEnabled() || !data.target) {
      hideSuggestion();
      return;
    }
    if (suggestionEl) {
      suggestionEl.hidden = false;
    }
    if (suggestionError) {
      suggestionError.hidden = true;
    }
    if (suggestionRetry) {
      suggestionRetry.hidden = true;
    }
    if (suggestionTarget) {
      suggestionTarget.textContent = data.target || "";
    }
    if (suggestionRoman) {
      suggestionRoman.textContent = data.romanization || "";
    }
    if (suggestionGloss) {
      suggestionGloss.textContent = data.gloss || "";
    }
  }

  function attachTranslation(turnEl, hint) {
    if (!hint || !hint.translation || !turnEl || !turnEl.isConnected) {
      return;
    }
    let line = turnEl.querySelector(".teacher-translation");
    if (!line) {
      line = document.createElement("span");
      line.className = "teacher-translation";
      line.setAttribute("lang", "en");
      turnEl.appendChild(line);
    }
    line.textContent = hint.translation;
  }

  async function requestCoach() {
    if (!sessionId) {
      return;
    }
    const requestSession = sessionId;
    const turn = lastTeacherTurn;
    try {
      const data = await api(
        "/api/teacher/sessions/" + requestSession + "/coach",
        {}
      );
      if (sessionId !== requestSession) {
        return;
      }
      // The translation belongs to the turn it was requested for, even if a
      // newer turn landed while the call was in flight.
      attachTranslation(turn, data);
      if (turn === lastTeacherTurn) {
        fillSuggestion(data);
      }
    } catch (_error) {
      showSuggestionError();
    }
  }

  function stopReplyWatch() {
    if (replyWatch) {
      clearTimeout(replyWatch);
      replyWatch = null;
    }
  }

  // Silence after a learner turn is a real failure mode (feedback, a dropped
  // session); say so instead of leaving the panel quiet.
  function startReplyWatch() {
    stopReplyWatch();
    replyWatch = setTimeout(function () {
      replyWatch = null;
      if (sessionId && !userEnded) {
        setStatus(
          "Kiku has not replied. If you are on speakers, use headphones so it " +
            "cannot hear itself, or end the lesson and start again."
        );
      }
    }, 15000);
  }

  if (suggestionRetry) {
    suggestionRetry.addEventListener("click", function () {
      if (suggestionError) {
        suggestionError.hidden = true;
      }
      suggestionRetry.hidden = true;
      requestCoach();
    });
  }

  if (suggestToggle) {
    try {
      if (window.localStorage.getItem(SUGGEST_KEY) === "off") {
        suggestToggle.checked = false;
      }
    } catch (_error) {
      // Private mode: keep the default.
    }
    syncSuggestionHelp();
    suggestToggle.addEventListener("change", function () {
      try {
        window.localStorage.setItem(
          SUGGEST_KEY,
          suggestToggle.checked ? "on" : "off"
        );
      } catch (_error) {
        // Not fatal.
      }
      if (!suggestToggle.checked) {
        hideSuggestion();
      }
      syncSuggestionHelp();
    });
  }

  function announceTurn(role, text) {
    const announcer = document.getElementById("teacher-announcer");
    if (announcer) {
      announcer.textContent =
        (role === "teacher" ? "Kiku: " : "You: ") + text;
    }
  }

  function appendTurn(role, text) {
    if (!text) return;
    announceTurn(role, text);
    const item = document.createElement("li");
    item.className = "teacher-turn teacher-turn-" + role;
    const who = document.createElement("span");
    who.className = "teacher-who";
    who.textContent = role === "learner" ? "You" : "Kiku";
    const line = document.createElement("span");
    line.className = "teacher-line";
    line.textContent = text;
    if (role === "teacher") {
      stopReplyWatch();
      // The previous suggestion answers the previous turn; clear it the moment
      // Kiku speaks again so a stale line never reads as the next thing to say.
      hideSuggestion();
    }
    item.append(who, line);
    addTurnElement(item);
    if (role === "teacher") {
      lastTeacherTurn = item;
    } else {
      startReplyWatch();
    }
  }

  function saveTurn(role, text) {
    if (!sessionId || !text) {
      return Promise.resolve();
    }
    return api("/api/teacher/sessions/" + sessionId + "/turns", {
      role: role,
      text: text,
    }).catch(function () {
      /* Transcript persistence is best-effort; the call must not break. */
    });
  }

  function finishBuffered(role) {
    const text = (transcriptBuffer[role] || "").trim();
    transcriptBuffer[role] = "";
    if (!text) {
      return Promise.resolve();
    }
    appendTurn(role, text);
    return saveTurn(role, text);
  }

  function bufferDelta(role, delta) {
    if (!delta) return;
    transcriptBuffer[role] += delta;
    const live = document.getElementById("teacher-live-" + role);
    if (live) {
      live.textContent = transcriptBuffer[role];
    } else {
      const item = document.createElement("li");
      item.className = "teacher-turn teacher-turn-" + role;
      item.id = "teacher-live-" + role;
      const who = document.createElement("span");
      who.className = "teacher-who";
      who.textContent = role === "learner" ? "You" : "Kiku";
      const line = document.createElement("span");
      line.className = "teacher-line";
      line.textContent = transcriptBuffer[role];
      item.append(who, line);
      addTurnElement(item);
    }
  }

  function clearLive(role) {
    const live = document.getElementById("teacher-live-" + role);
    if (live) live.remove();
  }

  // Repeating a write can duplicate a drill or a saved term, so only the
  // read-only tools (and log_attempt, which carries a client id) are retried.
  const RETRYABLE_TOOLS = {
    get_due_items: true,
    lookup_dictionary: true,
    log_attempt: true,
  };

  async function postToolWithRetry(name, args) {
    const attempts = RETRYABLE_TOOLS[name] ? 2 : 1;
    let lastError;
    for (let attempt = 0; attempt < attempts; attempt += 1) {
      const controller = new AbortController();
      const timer = setTimeout(function () {
        controller.abort();
      }, 8000);
      try {
        const response = await fetch("/api/teacher/tools/" + name, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrf,
          },
          body: JSON.stringify({ session_id: sessionId, args: args }),
          signal: controller.signal,
        });
        const data = await response.json().catch(function () {
          return {};
        });
        if (!response.ok) {
          throw new Error(data.error || "Tool failed (" + response.status + ")");
        }
        return data;
      } catch (error) {
        lastError = error;
      } finally {
        clearTimeout(timer);
      }
    }
    throw lastError || new Error("Tool failed");
  }

  async function runTool(name, args, callId) {
    if (handledCalls.has(callId)) return;
    handledCalls.add(callId);
    if (name === "log_attempt" && !args.client_attempt_id) {
      args.client_attempt_id = "voice-" + Date.now() + "-" + callId.slice(-6);
    }
    setStatus("Kiku is preparing " + name.replaceAll("_", " ") + "…");
    let result;
    try {
      const data = await postToolWithRetry(name, args);
      result = data.result;
    } catch (error) {
      result = { error: error.message };
    }
    if (channel && channel.readyState === "open") {
      channel.send(
        JSON.stringify({
          type: "conversation.item.create",
          item: {
            type: "function_call_output",
            call_id: callId,
            output: JSON.stringify(result),
          },
        })
      );
      channel.send(JSON.stringify({ type: "response.create" }));
    }
    setStatus("Listening…");
  }

  function handleEvent(event) {
    const type = event.type || "";

    if (type === "error") {
      const message =
        (event.error && event.error.message) || "The teacher hit an error.";
      setCallState("error", "Needs attention");
      // Barge-in off + a learner turn can race an in-flight response. Benign:
      // the reply already plays, and the next turn works.
      if (/active response/i.test(message)) {
        return;
      }
      setStatus(message);
      return;
    }

    if (type === "session.created" || type === "session.started") {
      setStatus(connectedMessage());
      return;
    }

    if (type === "response.done") {
      const status = event.response && event.response.status;
      if (status === "failed") {
        setStatus(
          "Kiku could not answer that. Ask again, or end the lesson and restart."
        );
        return;
      }
      if (status === "incomplete") {
        setStatus("Kiku's reply was cut short. Ask it to continue.");
        return;
      }
      if (status === "cancelled") {
        clearLive("teacher");
      }
      // A completed response falls through to the Listening status below.
    }

    if (type === "input_audio_buffer.speech_started") {
      setCallState("listening", "Listening");
      setStatus("Listening…");
      return;
    }

    if (type === "response.output_audio.delta" || type === "response.audio.delta") {
      if (statusEl.textContent !== "Kiku is speaking…") {
        setCallState("speaking", "Kiku speaking");
        setStatus("Kiku is speaking…");
      }
      return;
    }

    if (type === "conversation.item.input_audio_transcription.completed") {
      clearLive("learner");
      const text = event.transcript || "";
      transcriptBuffer.learner = "";
      if (text) {
        appendTurn("learner", text);
        saveTurn("learner", text);
      }
      return;
    }

    if (
      type.endsWith("audio_transcript.delta") ||
      type.endsWith("audio_transcript.done")
    ) {
      const role = type.indexOf("input") === -1 ? "teacher" : "learner";
      if (type.endsWith(".delta")) {
        bufferDelta(role, event.delta || "");
      } else {
        clearLive(role);
        let stored;
        if (event.transcript) {
          transcriptBuffer[role] = "";
          appendTurn(role, event.transcript);
          stored = saveTurn(role, event.transcript);
        } else {
          stored = finishBuffered(role);
        }
        if (role === "teacher") {
          // Translate only once the turn exists; the coach reads the transcript.
          stored.then(requestCoach);
        } else {
          hideSuggestion();
        }
      }
      return;
    }

    if (type === "response.function_call_arguments.done") {
      let args = {};
      try {
        args = JSON.parse(event.arguments || "{}");
      } catch (_error) {
        args = {};
      }
      runTool(event.name, args, event.call_id);
      return;
    }

    if (type === "response.output_item.done") {
      const item = event.item || {};
      if (item.type === "function_call") {
        let args = {};
        try {
          args = JSON.parse(item.arguments || "{}");
        } catch (_error) {
          args = {};
        }
        runTool(item.name, args, item.call_id);
      }
      return;
    }

    if (type === "response.done") {
      setCallState("listening", "Listening");
      setStatus("Listening…");
    }
  }

  function waitForIce(connection) {
    if (connection.iceGatheringState === "complete") {
      return Promise.resolve();
    }
    return new Promise(function (resolve) {
      const timer = setTimeout(function () {
        cleanup();
        resolve();
      }, 3000);
      function onChange() {
        if (connection.iceGatheringState === "complete") {
          cleanup();
          resolve();
        }
      }
      function cleanup() {
        clearTimeout(timer);
        connection.removeEventListener("icegatheringstatechange", onChange);
      }
      connection.addEventListener("icegatheringstatechange", onChange);
    });
  }

  // A dropped call used to leave the row "active". The next visit then charged
  // the whole gap against the daily minutes, because the row was never closed.
  function closeSessionOnServer() {
    if (!sessionId) {
      return;
    }
    const id = sessionId;
    sessionId = null;
    api("/api/teacher/sessions/" + id + "/close", {}).catch(function () {
      /* Best effort: the server expires it at the cap anyway. */
    });
  }

  function stopExpiryTimer() {
    if (expiryTimer) {
      clearTimeout(expiryTimer);
      expiryTimer = null;
    }
  }

  function stopClock() {
    if (clockTimer) {
      clearInterval(clockTimer);
      clockTimer = null;
    }
  }

  function scheduleExpiry(expiresAt) {
    stopExpiryTimer();
    stopClock();
    if (!expiresAt) {
      return;
    }
    const endsAt = new Date(expiresAt).getTime();
    const remaining = endsAt - Date.now();
    if (!(remaining > 0)) {
      return;
    }
    if (countdownEl) {
      countdownEl.hidden = false;
      const paint = function () {
        const left = endsAt - Date.now();
        countdownEl.textContent = formatClock(left);
        countdownEl.classList.toggle("is-warning", left < 60000);
      };
      paint();
      clockTimer = setInterval(paint, 1000);
    }
    expiryTimer = setTimeout(function () {
      expiryTimer = null;
      setStatus("Time is up — finishing the lesson.");
      endSession();
    }, remaining);
  }

  function teardown(keepState) {
    stopExpiryTimer();
    stopClock();
    stopMicMeter();
    setCallActive(false);
    // Leave a failure or a drop on screen; the learner needs to see why the
    // call ended. A normal end goes back to Ready.
    if (!keepState) {
      setCallState("idle", "Ready");
    }
    if (countdownEl) {
      countdownEl.hidden = true;
    }
    if (mic) {
      mic.getTracks().forEach(function (track) {
        track.stop();
      });
      mic = null;
    }
    if (channel) {
      try {
        channel.close();
      } catch (_error) {
        /* already closed */
      }
      channel = null;
    }
    if (peer) {
      try {
        peer.close();
      } catch (_error) {
        /* already closed */
      }
      peer = null;
    }
    if (socket) {
      try {
        socket.close();
      } catch (_error) {
        /* already closed */
      }
      socket = null;
    }
    if (micWorklet) {
      try {
        micWorklet.port.onmessage = null;
        micWorklet.disconnect();
      } catch (_error) {
        /* already disconnected */
      }
      micWorklet = null;
    }
    if (micProcessor) {
      micProcessor.disconnect();
      micProcessor = null;
    }
    if (micSource) {
      micSource.disconnect();
      micSource = null;
    }
    if (audioContext) {
      audioContext.close().catch(function () {
        /* already closed */
      });
      audioContext = null;
    }
    playbackCursor = 0;
    audioEl.srcObject = null;
    audioEl.hidden = true;
    startBtn.disabled = false;
    stopBtn.disabled = true;
    root.setAttribute("data-session-active", "0");
  }

  async function startSession() {
    if (!navigator.mediaDevices) {
      setStatus("This browser cannot record audio. Try Chrome or Safari.");
      return;
    }
    if (provider === "gemini_live") {
      return startGeminiSession();
    }
    if (!window.RTCPeerConnection) {
      setStatus("This browser cannot open a voice call. Try Chrome or Safari.");
      return;
    }
    startBtn.disabled = true;
    setStatus("Requesting the microphone…");
    transcriptEl.innerHTML = "";
    debriefEl.hidden = true;
    handledCalls.clear();
    userEnded = false;

    try {
      peer = new RTCPeerConnection();
      peer.addEventListener("track", function (event) {
        audioEl.hidden = false;
        audioEl.srcObject = new MediaStream([event.track]);
        audioEl.play().catch(function () {
          setStatus("Press play on the audio player to hear Kiku.");
        });
      });

      mic = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      mic.getTracks().forEach(function (track) {
        peer.addTrack(track, mic);
      });
      startMicMeter(mic);
      setCallState("connecting", "Connecting");

      channel = peer.createDataChannel("oai-events");
      channel.addEventListener("message", function (message) {
        try {
          handleEvent(JSON.parse(message.data));
        } catch (_error) {
          /* Ignore malformed provider events. */
        }
      });
      channel.addEventListener("close", function () {
        if (!ending && !userEnded) {
          setCallState("offline", "Offline");
          setStatus("The call disconnected. Press Start speaking to reconnect.");
          closeSessionOnServer();
          teardown(true);
        }
      });

      peer.addEventListener("connectionstatechange", function () {
        const state = peer ? peer.connectionState : "closed";
        if (ending || userEnded) {
          return;
        }
        if (state === "failed" || state === "disconnected") {
          setStatus("The call dropped. Press Start speaking to reconnect.");
          closeSessionOnServer();
          teardown(true);
        }
      });

      const offer = await peer.createOffer();
      await peer.setLocalDescription(offer);
      await waitForIce(peer);

      setStatus("Connecting to Kiku…");
      const data = await api("/api/teacher/sessions", {
        sdp: peer.localDescription.sdp,
        plan: planEl.value,
      });
      sessionId = data.session_id;
      if (data.transport && data.transport !== "webrtc") {
        // The server can mint a Gemini Live session, but this page still speaks
        // WebRTC. Fail loudly instead of hanging in "Connecting…".
        closeSessionOnServer();
        teardown(true);
        setStatus(
          "Gemini Live is configured, but the browser transport is not wired " +
            "yet. Set TEACHER_PROVIDER=openai_realtime to keep talking."
        );
        return;
      }
      await peer.setRemoteDescription({ type: "answer", sdp: data.sdp });
      scheduleExpiry(data.expires_at);

      root.setAttribute("data-session-active", "1");
      stopBtn.disabled = false;
      setCallActive(true);
      setCallState("listening", "Listening");
      setStatus(connectedMessage());
    } catch (error) {
      setCallState("error", "Needs attention");
      setStatus(error.message || "Could not start the lesson.");
      teardown(true);
    }
  }

  async function loadDebrief(sessionIdArg) {
    const id = sessionIdArg || sessionId;
    if (!id) return;
    try {
      const response = await fetch("/api/teacher/sessions/" + id);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Could not load debrief");

      summaryEl.textContent =
        data.summary ||
        "Lesson finished. Here is what to practice next.";
      drillsEl.innerHTML = "";
      (data.drills || []).forEach(function (drill) {
        const card = document.createElement("article");
        card.className = "teacher-drill";
        const prompt = document.createElement("p");
        prompt.textContent = drill.prompt;

        const form = document.createElement("form");
        form.className = "teacher-drill-form";
        const input = document.createElement("input");
        input.type = "text";
        input.placeholder = "Type your answer";
        input.setAttribute("aria-label", "Your answer");
        const check = document.createElement("button");
        check.type = "submit";
        check.className = "btn";
        check.textContent = "Check";
        form.append(input, check);

        const feedback = document.createElement("p");
        feedback.className = "teacher-answer";
        feedback.setAttribute("role", "status");

        form.addEventListener("submit", async function (event) {
          event.preventDefault();
          if (!input.value.trim()) return;
          check.disabled = true;
          try {
            const result = await api(
              "/api/teacher/drills/" + drill.id + "/attempt",
              {
                response: input.value.trim(),
                client_attempt_id:
                  "debrief-" + drill.id + "-" + Date.now(),
              }
            );
            feedback.textContent =
              (result.acceptable ? "Correct. " : "Not yet. ") +
              (result.feedback || "");
            feedback.classList.toggle("is-correct", result.acceptable);
            if (result.acceptable) {
              input.disabled = true;
              check.textContent = "Added to review";
            } else {
              check.disabled = false;
            }
          } catch (error) {
            feedback.textContent = error.message;
            check.disabled = false;
          }
        });

        card.append(prompt, form, feedback);
        drillsEl.appendChild(card);
      });
      if (!(data.drills || []).length) {
        const empty = document.createElement("p");
        empty.className = "learn-meta";
        empty.textContent =
          "No drills this time. Ask Kiku for two drills next session.";
        drillsEl.appendChild(empty);
      }

      termsEl.innerHTML = "";
      (data.terms || []).forEach(function (term) {
        const li = document.createElement("li");
        li.textContent = term.text + " — " + term.gloss;
        if (term.context_sentence) {
          li.textContent += " (" + term.context_sentence + ")";
        }
        termsEl.appendChild(li);
      });
      if (!(data.terms || []).length) {
        const li = document.createElement("li");
        li.className = "learn-meta";
        li.textContent = "Nothing saved this session.";
        termsEl.appendChild(li);
      }
      if (callPanel) {
        callPanel.hidden = true;
      }
      debriefEl.hidden = false;
      debriefEl.scrollIntoView({ behavior: "smooth", block: "start" });
      if (againBtn) {
        againBtn.focus();
      }
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function endSession() {
    if (!sessionId) {
      teardown();
      return;
    }
    const finishedId = sessionId;
    sessionId = null;
    ending = true;
    userEnded = true;
    stopBtn.disabled = true;
    setCallState("connecting", "Finishing…");
    setStatus("Finishing the lesson…");
    if (channel && channel.readyState === "open") {
      try {
        channel.send(JSON.stringify({ type: "session.close" }));
      } catch (_error) {
        /* ignore */
      }
    }
    if (socket) {
      try {
        socket.close();
      } catch (_error) {
        /* ignore */
      }
    }
    try {
      await api("/api/teacher/sessions/" + finishedId + "/end", {});
    } catch (_error) {
      /* The local close endpoint is a fallback below. */
      try {
        await api("/api/teacher/sessions/" + finishedId + "/close", {});
      } catch (_ignored) {
        /* nothing else to do */
      }
    }
    teardown();
    ending = false;
    setStatus("Lesson finished.");
    await loadDebrief(finishedId);
  }


  // --- Gemini Live transport (WebSocket + streamed PCM) ------------------
  // The server mints a constrained token; this side owns microphone capture,
  // playback, and the event mapping. Everything else (transcript, coach hint,
  // expiry, debrief) reuses the WebRTC path's helpers.

  const GEMINI_INPUT_RATE = 16000;
  const GEMINI_OUTPUT_RATE = 24000;
  let playingSources = [];

  function bytesToBase64(bytes) {
    let binary = "";
    const chunk = 0x8000;
    for (let i = 0; i < bytes.length; i += chunk) {
      binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
    }
    return window.btoa(binary);
  }

  function base64ToBytes(value) {
    const binary = window.atob(value || "");
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
  }

  function toPcm16(floatSamples, sourceRate, targetRate) {
    const ratio = sourceRate / targetRate;
    const length = Math.floor(floatSamples.length / ratio);
    const out = new Int16Array(length);
    for (let i = 0; i < length; i += 1) {
      const start = Math.floor(i * ratio);
      const end = Math.min(start + Math.ceil(ratio), floatSamples.length);
      let sum = 0;
      for (let j = start; j < end; j += 1) {
        sum += floatSamples[j];
      }
      const sample = Math.max(-1, Math.min(1, sum / Math.max(1, end - start)));
      out[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
    }
    return out;
  }

  function stopPlayback() {
    playingSources.forEach(function (source) {
      try {
        source.stop();
      } catch (_error) {
        /* already stopped */
      }
    });
    playingSources = [];
    playbackCursor = 0;
  }

  function playPcmChunk(base64Data, mimeType) {
    if (!audioContext || !base64Data) {
      return;
    }
    const rateMatch = /rate=(\d+)/.exec(mimeType || "");
    const chunkRate = rateMatch ? Number(rateMatch[1]) : GEMINI_OUTPUT_RATE;
    const bytes = base64ToBytes(base64Data);
    const samples = new Int16Array(bytes.buffer, 0, Math.floor(bytes.length / 2));
    if (!samples.length) {
      return;
    }
    const buffer = audioContext.createBuffer(1, samples.length, chunkRate);
    const channel = buffer.getChannelData(0);
    for (let i = 0; i < samples.length; i += 1) {
      channel[i] = samples[i] / 32768;
    }
    const source = audioContext.createBufferSource();
    source.buffer = buffer;
    source.connect(audioContext.destination);
    const now = audioContext.currentTime;
    if (playbackCursor < now) {
      playbackCursor = now + 0.04;
    }
    source.start(playbackCursor);
    playbackCursor += buffer.duration;
    playingSources.push(source);
    source.onended = function () {
      playingSources = playingSources.filter(function (item) {
        return item !== source;
      });
    };
  }

  function sendMicSamples(samples) {
    if (
      !audioContext ||
      !socket ||
      socket.readyState !== window.WebSocket.OPEN ||
      !samples
    ) {
      return;
    }
    const pcm = toPcm16(samples, audioContext.sampleRate, GEMINI_INPUT_RATE);
    socket.send(
      JSON.stringify({
        realtimeInput: {
          audio: {
            data: bytesToBase64(new Uint8Array(pcm.buffer)),
            mimeType: "audio/pcm;rate=" + GEMINI_INPUT_RATE,
          },
        },
      })
    );
  }

  async function startMicCapture() {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    micSource = audioContext.createMediaStreamSource(mic);
    // The processor only runs while connected; a muted gain keeps it silent.
    const mute = audioContext.createGain();
    mute.gain.value = 0;
    mute.connect(audioContext.destination);

    const workletUrl = root.dataset.workletUrl;
    if (audioContext.audioWorklet && workletUrl) {
      try {
        await audioContext.audioWorklet.addModule(workletUrl);
        micWorklet = new AudioWorkletNode(audioContext, "pcm-tap");
        micWorklet.port.onmessage = function (event) {
          sendMicSamples(event.data);
        };
        micSource.connect(micWorklet);
        micWorklet.connect(mute);
        return;
      } catch (_error) {
        micWorklet = null;
      }
    }

    // Fallback for browsers without AudioWorklet.
    micProcessor = audioContext.createScriptProcessor(4096, 1, 1);
    micProcessor.onaudioprocess = function (event) {
      sendMicSamples(event.inputBuffer.getChannelData(0));
    };
    micSource.connect(micProcessor);
    micProcessor.connect(mute);
  }

  // Gemini's transcript events carry only text, no `finished` flag, so the end
  // of a turn is the signal to close both lines and persist them.
  function finalizeGeminiTurn() {
    const hadTeacher = (transcriptBuffer.teacher || "").trim().length > 0;
    const saves = [];
    ["learner", "teacher"].forEach(function (role) {
      if ((transcriptBuffer[role] || "").trim()) {
        clearLive(role);
        saves.push(finishBuffered(role));
      }
    });
    if (hadTeacher) {
      Promise.all(saves).then(requestCoach);
    } else if (saves.length) {
      Promise.all(saves).then(hideSuggestion);
    }
  }

  function handleTranscription(role, transcription) {
    if (!transcription) {
      return;
    }
    if (transcription.finished) {
      clearLive(role);
      const stored = finishBuffered(role);
      if (role === "teacher") {
        stored.then(requestCoach);
      } else {
        hideSuggestion();
      }
      return;
    }
    if (transcription.text) {
      bufferDelta(role, transcription.text);
    }
  }

  async function sendToolResponses(functionCalls) {
    if (!functionCalls || !functionCalls.length) {
      return;
    }
    pendingToolCalls += functionCalls.length;
    const responses = [];
    for (const call of functionCalls) {
      if (geminiToolResults.has(call.id)) {
        responses.push(geminiToolResults.get(call.id));
        continue;
      }
      let result;
      try {
        const data = await api("/api/teacher/tools/" + call.name, {
          session_id: sessionId,
          args: call.args || {},
        });
        result = data.result;
      } catch (error) {
        result = { error: error.message };
      }
      const entry = {
        id: call.id,
        name: call.name,
        response: { result: result },
      };
      geminiToolResults.set(call.id, entry);
      responses.push(entry);
    }
    pendingToolCalls -= functionCalls.length;
    if (socket && socket.readyState === window.WebSocket.OPEN) {
      socket.send(
        JSON.stringify({ toolResponse: { functionResponses: responses } })
      );
    }
  }

  function handleGeminiEvent(event) {
    if (!event || typeof event !== "object") {
      return;
    }
    if (event.setupComplete) {
      setCallActive(true);
      setCallState("listening", "Listening");
      setStatus(connectedMessage());
      return;
    }
    if (event.goAway) {
      setCallState("connecting", "Wrapping up");
      setStatus("The session is closing. Finishing the lesson…");
      window.setTimeout(function () {
        if (sessionId && !ending) {
          endSession();
        }
      }, 1200);
      return;
    }
    if (event.toolCall) {
      sendToolResponses(event.toolCall.functionCalls);
      return;
    }
    const content = event.serverContent;
    if (!content) {
      return;
    }
    if (content.interrupted) {
      stopPlayback();
      clearLive("teacher");
    }
    if (content.inputTranscription) {
      handleTranscription("learner", content.inputTranscription);
    }
    if (content.outputTranscription) {
      handleTranscription("teacher", content.outputTranscription);
    }
    (content.modelTurn && content.modelTurn.parts
      ? content.modelTurn.parts
      : []
    ).forEach(function (part) {
      if (part.inlineData && part.inlineData.data) {
        if (statusEl.textContent !== "Kiku is speaking…") {
          setCallState("speaking", "Kiku speaking");
          setStatus("Kiku is speaking…");
        }
        playPcmChunk(part.inlineData.data, part.inlineData.mimeType);
      }
    });
    if (content.turnComplete) {
      finalizeGeminiTurn();
      // The reply-watch timer belongs to learner turns; starting it here would
      // nag during ordinary quiet after every tutor line.
      setCallState("listening", "Listening");
      setStatus("Listening…");
    }
  }

  async function startGeminiSession() {
    startBtn.disabled = true;
    setStatus("Requesting the microphone…");
    transcriptEl.innerHTML = "";
    debriefEl.hidden = true;
    handledCalls.clear();
    geminiToolResults.clear();
    userEnded = false;

    try {
      mic = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      const data = await api("/api/teacher/sessions", { plan: planEl.value });
      sessionId = data.session_id;
      if (data.transport !== "websocket" || !data.token || !data.url) {
        closeSessionOnServer();
        teardown(true);
        setStatus(
          "The server did not return a Gemini session. Check TEACHER_PROVIDER."
        );
        return;
      }
      scheduleExpiry(data.expires_at);
      await startMicCapture();
      startMicMeter(mic, audioContext);
      setCallState("connecting", "Connecting");

      socket = new WebSocket(
        data.url + "?access_token=" + encodeURIComponent(data.token)
      );
      socket.addEventListener("open", function () {
        setStatus("Connecting to Kiku…");
        // The token is constrained to the full config server-side; sending the
        // model is enough and keeps the prompt out of the browser.
        socket.send(JSON.stringify({ setup: { model: data.model } }));
      });
      socket.addEventListener("message", async function (message) {
        let text = message.data;
        if (text instanceof Blob) {
          text = await text.text();
        }
        let event;
        try {
          event = JSON.parse(text);
        } catch (_error) {
          return;
        }
        handleGeminiEvent(event);
      });
      socket.addEventListener("error", function () {
        setCallState("error", "Needs attention");
        setStatus(
          "The Gemini call failed. Check GEMINI_API_KEY and try again."
        );
      });
      socket.addEventListener("close", function () {
        if (!ending && !userEnded) {
          setCallState("offline", "Offline");
          setStatus("The call disconnected. Press Start speaking to reconnect.");
          closeSessionOnServer();
          teardown(true);
        }
      });

      root.setAttribute("data-session-active", "1");
      stopBtn.disabled = false;
    } catch (error) {
      setCallState("error", "Needs attention");
      setStatus(error.message || "Could not start the lesson.");
      teardown(true);
    }
  }

  window.addEventListener("pagehide", function () {
    if (!sessionId || ending || userEnded) {
      return;
    }
    const id = sessionId;
    sessionId = null;
    try {
      // keepalive lets the request finish while the page is unloading.
      window.fetch("/api/teacher/sessions/" + id + "/close", {
        method: "POST",
        keepalive: true,
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf,
        },
        body: "{}",
      });
    } catch (_error) {
      /* the server expires the row at the cap anyway */
    }
  });

  startBtn.addEventListener("click", startSession);
  stopBtn.addEventListener("click", endSession);
})();

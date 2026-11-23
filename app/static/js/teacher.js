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
  const csrf =
    (document.querySelector('meta[name="csrf-token"]') || {}).content || "";

  let peer = null;
  let channel = null;
  let mic = null;
  let sessionId = null;
  let ending = false;
  let userEnded = false;
  const handledCalls = new Set();
  const transcriptBuffer = { teacher: "", learner: "" };

  function setStatus(text) {
    statusEl.textContent = text;
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

  function appendTurn(role, text) {
    if (!text) return;
    const item = document.createElement("li");
    item.className = "teacher-turn teacher-turn-" + role;
    const who = document.createElement("span");
    who.className = "teacher-who";
    who.textContent = role === "learner" ? "You" : "Kiku";
    const line = document.createElement("span");
    line.className = "teacher-line";
    line.textContent = text;
    item.append(who, line);
    transcriptEl.appendChild(item);
    item.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  function saveTurn(role, text) {
    if (!sessionId || !text) return;
    api("/api/teacher/sessions/" + sessionId + "/turns", {
      role: role,
      text: text,
    }).catch(function () {
      /* Transcript persistence is best-effort; the call must not break. */
    });
  }

  function finishBuffered(role) {
    const text = (transcriptBuffer[role] || "").trim();
    transcriptBuffer[role] = "";
    if (!text) return;
    appendTurn(role, text);
    saveTurn(role, text);
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
      transcriptEl.appendChild(item);
    }
  }

  function clearLive(role) {
    const live = document.getElementById("teacher-live-" + role);
    if (live) live.remove();
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
      const data = await api("/api/teacher/tools/" + name, {
        session_id: sessionId,
        args: args,
      });
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
      setStatus(message);
      return;
    }

    if (type === "session.created" || type === "session.started") {
      setStatus("Connected. Say hello in Korean.");
      return;
    }

    if (type === "input_audio_buffer.speech_started") {
      setStatus("Listening…");
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
        if (event.transcript) {
          transcriptBuffer[role] = "";
          appendTurn(role, event.transcript);
          saveTurn(role, event.transcript);
        } else {
          finishBuffered(role);
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

  function teardown() {
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
    audioEl.srcObject = null;
    audioEl.hidden = true;
    startBtn.disabled = false;
    stopBtn.disabled = true;
    root.setAttribute("data-session-active", "0");
  }

  async function startSession() {
    if (!navigator.mediaDevices || !window.RTCPeerConnection) {
      setStatus("This browser cannot record audio. Try Chrome or Safari.");
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
          setStatus("The call disconnected.");
          teardown();
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
      await peer.setRemoteDescription({ type: "answer", sdp: data.sdp });

      root.setAttribute("data-session-active", "1");
      stopBtn.disabled = false;
      setStatus("Connected. Say hello in Korean.");
    } catch (error) {
      setStatus(error.message || "Could not start the lesson.");
      teardown();
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
      debriefEl.hidden = false;
      debriefEl.scrollIntoView({ behavior: "smooth", block: "start" });
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
    setStatus("Finishing the lesson…");
    if (channel && channel.readyState === "open") {
      try {
        channel.send(JSON.stringify({ type: "session.close" }));
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

  startBtn.addEventListener("click", startSession);
  stopBtn.addEventListener("click", endSession);
})();

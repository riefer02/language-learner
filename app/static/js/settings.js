// Settings: browser push subscription for the daily reminder.
document.addEventListener("DOMContentLoaded", function () {
  const panel = document.querySelector(".push-panel");
  if (!panel) {
    return;
  }
  const vapid = panel.getAttribute("data-vapid") || "";
  const csrf = panel.getAttribute("data-csrf") || "";
  const enable = document.getElementById("push-enable");
  const disable = document.getElementById("push-disable");
  const test = document.getElementById("push-test");
  const status = document.getElementById("push-status");

  if (!enable || !disable || !test || !status) {
    return;
  }

  function setStatus(message) {
    status.textContent = message;
  }

  function urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, "+")
      .replace(/_/g, "/");
    const raw = window.atob(base64);
    const output = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; i += 1) {
      output[i] = raw.charCodeAt(i);
    }
    return output;
  }

  async function getRegistration() {
    if (!("serviceWorker" in navigator)) {
      throw new Error("This browser does not support service workers.");
    }
    return navigator.serviceWorker.ready;
  }

  async function refreshState() {
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
      enable.hidden = true;
      setStatus("Push notifications are not supported in this browser.");
      return;
    }
    try {
      const registration = await getRegistration();
      const subscription = await registration.pushManager.getSubscription();
      if (subscription) {
        enable.hidden = true;
        disable.hidden = false;
        test.hidden = false;
        setStatus("Notifications are on for this browser.");
      } else {
        enable.hidden = false;
        disable.hidden = true;
        test.hidden = true;
        setStatus("Notifications are off for this browser.");
      }
    } catch (error) {
      setStatus(error.message);
    }
  }

  enable.addEventListener("click", async function () {
    enable.disabled = true;
    try {
      if (!vapid) {
        throw new Error("Push is not configured on this server.");
      }
      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        throw new Error("Notification permission was not granted.");
      }
      const registration = await getRegistration();
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapid),
      });
      const response = await fetch("/api/push/subscribe", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf,
        },
        body: JSON.stringify(subscription),
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || "Could not save the subscription.");
      }
      await refreshState();
    } catch (error) {
      setStatus(error.message || "Could not enable notifications.");
    } finally {
      enable.disabled = false;
    }
  });

  disable.addEventListener("click", async function () {
    disable.disabled = true;
    try {
      const registration = await getRegistration();
      const subscription = await registration.pushManager.getSubscription();
      if (subscription) {
        await fetch("/api/push/unsubscribe", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrf,
          },
          body: JSON.stringify({ endpoint: subscription.endpoint }),
        });
        await subscription.unsubscribe();
      }
      await refreshState();
    } catch (error) {
      setStatus(error.message || "Could not disable notifications.");
    } finally {
      disable.disabled = false;
    }
  });

  test.addEventListener("click", async function () {
    try {
      const registration = await getRegistration();
      registration.active.postMessage({ type: "test" });
      setStatus("Test notification requested.");
    } catch (error) {
      setStatus(error.message || "Could not send a test notification.");
    }
  });

  refreshState();
});

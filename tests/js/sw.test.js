const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const SW_SOURCE = fs.readFileSync(
  path.join(__dirname, "../../app/static/sw.js"),
  "utf8"
);

function loadWorker({ status = 200 } = {}) {
  const listeners = {};
  const puts = [];
  const fetched = [];
  const self = {
    location: { origin: "http://app" },
    addEventListener(name, handler) {
      listeners[name] = handler;
    },
    skipWaiting() {},
    clients: { claim() {} },
    registration: { showNotification() {} },
  };
  const caches = {
    match: async () => null,
    open: async () => ({
      put: async (request) => {
        puts.push(request.url);
      },
    }),
    keys: async () => [],
    delete: async () => true,
  };
  const fetch = async (request) => {
    fetched.push(request.url);
    return {
      ok: status >= 200 && status < 300,
      status,
      clone() {
        return this;
      },
    };
  };
  const context = vm.createContext({
    self,
    caches,
    fetch,
    URL,
    Promise,
    console,
    setTimeout,
    clearTimeout,
  });
  vm.runInContext(SW_SOURCE, context);
  return { listeners, puts, fetched };
}

function request(url, { mode = "no-cors", method = "GET" } = {}) {
  return { url, mode, method };
}

async function dispatch(handler, req) {
  let responsePromise = null;
  handler({
    request: req,
    respondWith(promise) {
      responsePromise = promise;
    },
  });
  if (responsePromise) {
    await responsePromise;
  }
  return responsePromise !== null;
}

test("audio bypasses the service-worker cache", async () => {
  const worker = loadWorker();

  const responded = await dispatch(
    worker.listeners.fetch,
    request("http://app/static/audio/a.mp3")
  );

  assert.equal(responded, false);
  assert.deepEqual(worker.fetched, []);
  assert.deepEqual(worker.puts, []);
});

test("versioned static assets are fetched and cached by exact URL", async () => {
  const worker = loadWorker();

  const responded = await dispatch(
    worker.listeners.fetch,
    request("http://app/static/css/style.css?v=20261126r6")
  );

  assert.equal(responded, true);
  assert.deepEqual(worker.fetched, [
    "http://app/static/css/style.css?v=20261126r6",
  ]);
  assert.deepEqual(worker.puts, [
    "http://app/static/css/style.css?v=20261126r6",
  ]);
});

test("partial and cross-origin responses are not cached", async () => {
  const partial = loadWorker({ status: 206 });
  assert.equal(
    await dispatch(
      partial.listeners.fetch,
      request("http://app/static/js/app.js?v=1")
    ),
    true
  );
  assert.deepEqual(partial.puts, []);

  const other = loadWorker();
  assert.equal(
    await dispatch(
      other.listeners.fetch,
      request("http://elsewhere/static/js/app.js?v=1")
    ),
    false
  );
  assert.deepEqual(other.fetched, []);
});

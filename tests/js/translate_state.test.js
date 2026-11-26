const test = require("node:test");
const assert = require("node:assert/strict");

const {
  phraseUrl,
  isRenderedResult,
  shouldReload,
} = require("../../app/static/js/translate_state.js");

test("phraseUrl keeps the language path and escapes the id", () => {
  assert.equal(
    phraseUrl("/am/translate", "abc 123"),
    "/am/translate?phrase=abc%20123"
  );
});

test("isRenderedResult only matches the visible saved result", () => {
  const state = {
    phraseUuid: "abc",
    phraseSource: "Hello",
    phraseRegister: "formal",
    phraseAddressee: "any",
  };

  assert.equal(isRenderedResult(state, "Hello", "formal", "any"), true);
  assert.equal(isRenderedResult(state, "Hello", "casual", "any"), false);
  assert.equal(isRenderedResult(state, "Goodbye", "formal", "any"), false);
  assert.equal(isRenderedResult(state, "Hello", "formal", "female"), false);
  assert.equal(isRenderedResult({ ...state, phraseUuid: "" }, "Hello", "formal", "any"), false);
});

test("isRenderedResult treats an empty register and addressee as defaults", () => {
  const state = {
    phraseUuid: "abc",
    phraseSource: "Hello",
    phraseRegister: "",
    phraseAddressee: "",
  };

  assert.equal(isRenderedResult(state, "Hello", null, null), true);
  assert.equal(isRenderedResult(state, "Hello", "polite", "any"), false);
});

test("shouldReload ignores same-document fragment traversals", () => {
  const url = "/am/translate?phrase=abc";
  assert.equal(shouldReload(url, url), false);
  assert.equal(shouldReload(url, "/am/translate?phrase=def"), true);
  assert.equal(shouldReload("/am/translate?q=Hello", url), true);
});

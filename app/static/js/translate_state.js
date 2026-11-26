// Pure decisions behind Look up history, shared by the browser and Node tests.
(function (root) {
  "use strict";

  function phraseUrl(pathname, uuid) {
    return pathname + "?phrase=" + encodeURIComponent(uuid);
  }

  function isRenderedResult(state, text, register, addressee) {
    if (!state || !state.phraseUuid) {
      return false;
    }
    return (
      text === (state.phraseSource || "") &&
      (register || "") === (state.phraseRegister || "") &&
      (addressee || "any") === (state.phraseAddressee || "any")
    );
  }

  function shouldReload(currentUrl, renderedUrl) {
    return currentUrl !== renderedUrl;
  }

  const api = { phraseUrl, isRenderedResult, shouldReload };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  } else {
    root.KikuTranslateState = api;
  }
})(typeof globalThis !== "undefined" ? globalThis : this);

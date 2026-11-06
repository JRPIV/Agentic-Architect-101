(function () {
  var api = window.RecruitmentApi;
  var view = window.RecruitmentView;
  var POLL_MS = 2000;

  var statusNode = document.getElementById("status");
  var notice = document.getElementById("notice");
  var ranking = document.getElementById("ranking");
  var runInput = document.getElementById("run-id-input");
  var pollToken = 0;
  var pollTimer = null;
  var activeRunId = "";

  function clearRanking() {
    ranking.replaceChildren();
  }

  function show(status, message) {
    statusNode.textContent = status;
    notice.textContent = message || "";
  }

  function stopPoll() {
    pollToken += 1;
    if (pollTimer) window.clearTimeout(pollTimer);
    pollTimer = null;
  }

  function renderAccepted(runId) {
    return api.getRecommendation(runId).then(function (payload) {
      show("Status: accepted.", "Accepted ranking for this run.");
      view.renderRanking(ranking, payload.ranking);
    });
  }

  function renderDocument(doc) {
    clearRanking();
    var status = doc.status;
    if (status === "accepted") return renderAccepted(doc.run_id);
    if (api.ACTIVE_STATUSES.indexOf(status) !== -1) {
      show(view.statusText(doc), "The ranking is not ready.");
      return null;
    }
    if (status === "draft") {
      show("Status: draft.", "This run is not accepted yet.");
      return null;
    }
    if (status === "discarded") {
      show("Status: discarded.", "This run was discarded. It is not a recommendation.");
      return null;
    }
    if (status === "failed") {
      var error = doc.error || {};
      show(
        "Status: failed. Stage: " + view.stageName(status, error) + ".",
        error.message || "The run failed."
      );
      return null;
    }
    show(view.statusText(doc), "This run is not an accepted recommendation.");
    return null;
  }

  function watch(runId) {
    activeRunId = runId;
    runInput.value = runId;
    stopPoll();
    var token = pollToken;
    var tick = function () {
      api.getRun(runId).then(function (doc) {
        if (token !== pollToken) return;
        return Promise.resolve(renderDocument(doc)).then(function () {
          if (token !== pollToken) return;
          if (api.ACTIVE_STATUSES.indexOf(doc.status) !== -1) {
            pollTimer = window.setTimeout(tick, POLL_MS);
          }
        });
      }).catch(function (error) {
        if (token !== pollToken) return;
        clearRanking();
        show("Status: unavailable.", error.message);
        if (error.status !== 404) pollTimer = window.setTimeout(tick, POLL_MS);
      });
    };
    tick();
  }

  document.getElementById("open-run").addEventListener("submit", function (event) {
    event.preventDefault();
    var runId = runInput.value.trim();
    if (!runId) {
      show("Status: no run selected.", "Enter the run id from the recruiter.");
      clearRanking();
      return;
    }
    var url = new URL(window.location.href);
    url.searchParams.set("run_id", runId);
    window.history.replaceState(null, "", url);
    watch(runId);
  });

  document.getElementById("check-again").addEventListener("click", function () {
    var runId = activeRunId || runInput.value.trim();
    if (runId) watch(runId);
  });

  var params = new URLSearchParams(window.location.search);
  var initial = params.get("run_id");
  if (initial) watch(initial);
})();

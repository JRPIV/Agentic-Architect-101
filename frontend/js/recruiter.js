(function () {
  var api = window.RecruitmentApi;
  var view = window.RecruitmentView;
  var FIELDS = [
    "title",
    "description",
    "responsibilities",
    "requirements",
    "preferred_qualifications",
    "perks_and_benefits",
  ];
  var POLL_MS = 2000;

  var form = document.getElementById("requisition-form");
  var runButton = document.getElementById("run");
  var runHint = document.getElementById("run-hint");
  var formError = document.getElementById("form-error");
  var statusNode = document.getElementById("status");
  var sourceTimeNode = document.getElementById("source-time");
  var runIdNode = document.getElementById("run-id");
  var managerLink = document.getElementById("manager-link");
  var acceptButton = document.getElementById("accept");
  var discardButton = document.getElementById("discard");
  var discardConfirm = document.getElementById("discard-confirm");
  var decisionError = document.getElementById("decision-error");
  var labelInput = document.getElementById("recruiter-label");
  var saveScore = document.getElementById("save-score");
  var scoreMessage = document.getElementById("score-message");
  var previewMessage = document.getElementById("preview-message");

  var current = null;
  var filledRunId = "";
  var pollToken = 0;
  var pollTimer = null;
  var submitting = false;

  function fieldValue(id) {
    return document.getElementById(id).value.trim();
  }

  function requisition() {
    var body = {};
    FIELDS.forEach(function (name) {
      body[name] = fieldValue(name);
    });
    return body;
  }

  function showAlert(node, message) {
    if (!message) {
      node.textContent = "";
      node.classList.add("hidden");
      return;
    }
    node.textContent = message;
    node.classList.remove("hidden");
  }

  function canRun() {
    var active = current && api.ACTIVE_STATUSES.indexOf(current.status) !== -1;
    return !submitting && !active && fieldValue("title") && fieldValue("requirements");
  }

  function syncRunControl() {
    var active = current && api.ACTIVE_STATUSES.indexOf(current.status) !== -1;
    runButton.disabled = !canRun();
    if (active) {
      runHint.textContent = "A run is already in progress.";
    } else if (!fieldValue("title") || !fieldValue("requirements")) {
      runHint.textContent = "Add a title and requirements before running.";
    } else {
      runHint.textContent = "Run starts research for this requisition.";
    }
  }

  function selectedScore() {
    var selected = document.querySelector('input[name="score"]:checked');
    if (!selected) return null;
    var score = Number(selected.value);
    return Number.isInteger(score) ? score : null;
  }

  function syncDecisionControls() {
    var status = current ? current.status : "";
    var draft = status === "draft";
    acceptButton.disabled = !(draft && fieldValue("recruiter-label"));
    discardButton.disabled = !draft;
    if (!draft) discardConfirm.classList.add("hidden");
    var scoreReady = current && api.SCORE_STATUSES.indexOf(status) !== -1;
    saveScore.disabled = !(scoreReady && selectedScore());
  }

  function rememberRun(runId) {
    var url = new URL(window.location.href);
    url.searchParams.set("run_id", runId);
    window.history.replaceState(null, "", url);
    runIdNode.textContent = "Run id: " + runId;
    managerLink.replaceChildren();
    var link = document.createElement("a");
    link.href = "/hiring-manager?run_id=" + encodeURIComponent(runId);
    link.textContent = "Hiring manager view";
    managerLink.append(link);
  }

  function fillForm(doc) {
    var req = doc.requisition || {};
    FIELDS.forEach(function (name) {
      var node = document.getElementById(name);
      if (document.activeElement !== node) node.value = req[name] || "";
    });
    var leads = document.getElementById("pasted_leads");
    if (document.activeElement !== leads) leads.value = doc.pasted_leads || "";
  }

  function showSatisfaction(doc) {
    var saved = doc.satisfaction;
    if (!saved) {
      scoreMessage.textContent = "";
      return;
    }
    var radios = document.querySelectorAll('input[name="score"]');
    radios.forEach(function (radio) {
      radio.checked = Number(radio.value) === saved.score;
    });
    var comment = document.getElementById("comment");
    if (document.activeElement !== comment) comment.value = saved.comment || "";
    scoreMessage.textContent = "Saved satisfaction score: " + saved.score + " of 5.";
  }

  function render(doc) {
    current = doc;
    statusNode.textContent = view.statusText(doc);
    sourceTimeNode.textContent = view.sourceTimeText(doc.source_elapsed_ms);
    rememberRun(doc.run_id);
    if (filledRunId !== doc.run_id) {
      fillForm(doc);
      filledRunId = doc.run_id;
    }
    view.renderCandidates(document.getElementById("candidates"), doc.candidates);
    view.renderEvaluations(document.getElementById("evaluations"), doc.evaluations, doc.candidates);
    view.renderRanking(document.getElementById("ranking"), doc.ranking);
    showSatisfaction(doc);
    syncRunControl();
    syncDecisionControls();
  }

  function stopPoll() {
    pollToken += 1;
    if (pollTimer) window.clearTimeout(pollTimer);
    pollTimer = null;
  }

  function watch(runId) {
    stopPoll();
    var token = pollToken;
    var tick = function () {
      api.getRun(runId).then(function (doc) {
        if (token !== pollToken) return;
        showAlert(formError, "");
        render(doc);
        if (api.ACTIVE_STATUSES.indexOf(doc.status) !== -1) {
          pollTimer = window.setTimeout(tick, POLL_MS);
        }
      }).catch(function (error) {
        if (token !== pollToken) return;
        showAlert(formError, error.message);
        if (error.status !== 404) pollTimer = window.setTimeout(tick, POLL_MS);
      });
    };
    tick();
  }

  function applyPreview(payload) {
    var req = payload.requisition || {};
    FIELDS.forEach(function (name) {
      document.getElementById(name).value = req[name] || "";
    });
    previewMessage.textContent = "Fields filled from the posting. The crew has not started.";
    syncRunControl();
  }

  document.getElementById("preview-posting").addEventListener("click", function () {
    var url = fieldValue("posting-url");
    var text = fieldValue("posting-text");
    previewMessage.textContent = "";
    if ((url && text) || (!url && !text)) {
      previewMessage.textContent = "Provide a posting url or pasted posting text, not both.";
      return;
    }
    var payload = url ? { url: url } : { text: text };
    api.previewPosting(payload).then(applyPreview).catch(function (error) {
      previewMessage.textContent = error.message + " The form is still editable, and the crew has not started.";
    });
  });

  ["title", "requirements"].forEach(function (id) {
    document.getElementById(id).addEventListener("input", syncRunControl);
  });
  labelInput.addEventListener("input", syncDecisionControls);
  document.getElementById("satisfaction-form").addEventListener("change", syncDecisionControls);

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    showAlert(formError, "");
    var body = requisition();
    if (!body.title) {
      showAlert(formError, "title is required.");
      return;
    }
    if (!body.requirements) {
      showAlert(formError, "requirements is required.");
      return;
    }
    submitting = true;
    syncRunControl();
    api.createRun(body, fieldValue("pasted_leads")).then(function (created) {
      submitting = false;
      watch(created.run_id);
    }).catch(function (error) {
      submitting = false;
      syncRunControl();
      var stage = error.stage ? " Stage: " + error.stage + "." : "";
      showAlert(formError, error.message + stage);
    });
  });

  document.getElementById("decision-form").addEventListener("submit", function (event) {
    event.preventDefault();
    if (!acceptButton.disabled) acceptButton.click();
  });

  acceptButton.addEventListener("click", function () {
    if (!current) return;
    showAlert(decisionError, "");
    var label = fieldValue("recruiter-label");
    if (!label) {
      showAlert(decisionError, "recruiter_label is required.");
      return;
    }
    api.accept(current.run_id, label).then(render).catch(function (error) {
      showAlert(decisionError, error.message);
    });
  });

  discardButton.addEventListener("click", function () {
    discardConfirm.classList.remove("hidden");
  });
  document.getElementById("discard-no").addEventListener("click", function () {
    discardConfirm.classList.add("hidden");
  });
  document.getElementById("discard-yes").addEventListener("click", function () {
    if (!current) return;
    showAlert(decisionError, "");
    api.discard(current.run_id).then(function (doc) {
      discardConfirm.classList.add("hidden");
      render(doc);
    }).catch(function (error) {
      showAlert(decisionError, error.message);
    });
  });

  document.getElementById("satisfaction-form").addEventListener("submit", function (event) {
    event.preventDefault();
    if (!current) return;
    var score = selectedScore();
    if (!Number.isInteger(score) || score < 1 || score > 5) {
      scoreMessage.textContent = "score must be an integer from 1 to 5.";
      return;
    }
    api.saveSatisfaction(current.run_id, score, fieldValue("comment")).then(function (doc) {
      render(doc);
    }).catch(function (error) {
      scoreMessage.textContent = error.message;
    });
  });

  syncRunControl();
  syncDecisionControls();
  var params = new URLSearchParams(window.location.search);
  var existing = params.get("run_id");
  if (existing) watch(existing);
})();

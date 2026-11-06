(function (global) {
  var STAGE_BY_STATUS = {
    researching: "research",
    evaluating: "evaluation",
    recommending: "recommendation",
  };

  var DISCLAIMER =
    "This ranking supports the recruiter and the hiring manager. Contact decisions happen outside this product.";

  function el(tag, text) {
    var node = document.createElement(tag);
    if (text != null) node.textContent = String(text);
    return node;
  }

  function httpUrl(value) {
    if (!value) return "";
    try {
      var url = new URL(value);
      if (url.protocol === "http:" || url.protocol === "https:") return url.href;
    } catch (error) {
      return "";
    }
    return "";
  }

  function joinList(values) {
    if (!values || !values.length) return "None recorded";
    return values.join(", ");
  }

  function stageName(status, error) {
    if (STAGE_BY_STATUS[status]) return STAGE_BY_STATUS[status];
    if (status === "failed") {
      if (error && error.stage) return error.stage;
      return "unknown";
    }
    return "";
  }

  function statusText(doc) {
    var status = doc && doc.status ? doc.status : "unknown";
    if (STAGE_BY_STATUS[status]) {
      return "Status: " + STAGE_BY_STATUS[status] + ". The crew is working on this requisition.";
    }
    if (status === "draft") {
      return "Status: draft. The ranking is a draft until you accept it.";
    }
    if (status === "accepted") {
      return (
        "Status: accepted. Accepted at " +
        (doc.accepted_at || "unknown time") +
        " by " +
        (doc.recruiter_label || "unknown recruiter") +
        "."
      );
    }
    if (status === "discarded") {
      return (
        "Status: discarded. The draft stays readable here and is not a recommendation for the hiring manager. Discarded at " +
        (doc.discarded_at || "unknown time") +
        "."
      );
    }
    if (status === "failed") {
      var error = doc.error || {};
      return (
        "Status: failed. Stage: " +
        stageName(status, error) +
        ". " +
        (error.message || "The run failed.")
      );
    }
    return "Status: " + status + ".";
  }

  function sourceTimeText(ms) {
    if (ms == null) return "Source time: not recorded yet.";
    return "Source time: " + (ms / 1000).toFixed(1) + " s (" + ms + " ms).";
  }

  function sourceLine(sourceType, sourceUrl) {
    var label = sourceType || "not recorded";
    var href = httpUrl(sourceUrl);
    var node = el("p", "Source: " + label);
    if (!href) return node;
    node.append(" ");
    var link = el("a", href);
    link.href = href;
    link.rel = "noreferrer";
    node.append(link);
    return node;
  }

  function renderCandidates(container, candidates) {
    container.replaceChildren();
    if (!candidates || !candidates.length) {
      container.append(el("p", "No sourced candidates yet."));
      return;
    }
    var list = document.createElement("ol");
    candidates.forEach(function (candidate) {
      var item = document.createElement("li");
      item.append(el("strong", candidate.name || "Unnamed candidate"));
      item.append(sourceLine(candidate.source_type, candidate.source_url));
      if (candidate.summary) item.append(el("p", candidate.summary));
      if (candidate.email) item.append(el("p", "Email: " + candidate.email));
      if (candidate.phone) item.append(el("p", "Phone: " + candidate.phone));
      list.append(item);
    });
    container.append(list);
  }

  function candidateName(candidates, candidateId) {
    var match = (candidates || []).find(function (candidate) {
      return candidate.id === candidateId;
    });
    return match && match.name ? match.name : candidateId || "Unknown candidate";
  }

  function renderEvaluations(container, evaluations, candidates) {
    container.replaceChildren();
    if (!evaluations || !evaluations.length) {
      container.append(el("p", "No evaluations yet."));
      return;
    }
    var list = document.createElement("ol");
    evaluations.forEach(function (row) {
      var item = document.createElement("li");
      item.append(el("strong", candidateName(candidates, row.candidate_id)));
      item.append(el("p", "Score: " + row.score + " of 5"));
      item.append(el("p", "Met requirements: " + joinList(row.met_requirements)));
      item.append(el("p", "Missing requirements: " + joinList(row.missing_requirements)));
      if (row.evidence_note) item.append(el("p", row.evidence_note));
      list.append(item);
    });
    container.append(list);
  }

  function renderRanking(container, ranking) {
    container.replaceChildren();
    container.append(el("p", DISCLAIMER));
    if (!ranking) {
      container.append(el("p", "No ranking yet."));
      return;
    }
    if (ranking.summary) container.append(el("p", ranking.summary));
    var rows = ranking.rows || [];
    if (!rows.length) {
      container.append(el("p", "No ranked candidates yet."));
      return;
    }
    var table = document.createElement("table");
    var head = document.createElement("thead");
    var headRow = document.createElement("tr");
    ["Rank", "Candidate", "Source", "Score", "Met requirements", "Missing requirements"].forEach(function (label) {
      headRow.append(el("th", label));
    });
    head.append(headRow);
    var body = document.createElement("tbody");
    rows.forEach(function (row, index) {
      var tr = document.createElement("tr");
      tr.append(el("td", String(index + 1)));
      tr.append(el("td", row.name || row.candidate_id || "Unnamed candidate"));
      var source = el("td");
      source.append(sourceLine(row.source_type, row.source_url));
      tr.append(source);
      tr.append(el("td", row.score + " of 5"));
      tr.append(el("td", joinList(row.met_requirements)));
      tr.append(el("td", joinList(row.missing_requirements)));
      body.append(tr);
    });
    table.append(head, body);
    container.append(table);
  }

  global.RecruitmentView = {
    stageName: stageName,
    statusText: statusText,
    sourceTimeText: sourceTimeText,
    renderCandidates: renderCandidates,
    renderEvaluations: renderEvaluations,
    renderRanking: renderRanking,
  };
})(window);

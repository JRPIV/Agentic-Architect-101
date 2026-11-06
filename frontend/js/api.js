(function (global) {
  var ACTIVE_STATUSES = ["researching", "evaluating", "recommending"];
  var SCORE_STATUSES = ["draft", "accepted", "discarded"];

  function ApiError(status, error) {
    this.name = "ApiError";
    this.status = status;
    this.code = error.code || "request_failed";
    this.message = error.message || "Request failed.";
    this.stage = error.stage == null ? null : error.stage;
  }

  ApiError.prototype = Object.create(Error.prototype);

  function request(path, options) {
    var settings = options || {};
    var headers = { Accept: "application/json" };
    var init = { method: settings.method || "GET", headers: headers };
    if (settings.body) {
      headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(settings.body);
    }
    return fetch(path, init).then(function (response) {
      return response.text().then(function (text) {
        var payload = null;
        if (text) {
          try {
            payload = JSON.parse(text);
          } catch (error) {
            payload = null;
          }
        }
        if (!response.ok) {
          var body = payload && payload.error ? payload.error : {};
          throw new ApiError(response.status, body);
        }
        return payload;
      });
    });
  }

  function runPath(runId, suffix) {
    return "/api/runs/" + encodeURIComponent(runId) + suffix;
  }

  global.RecruitmentApi = {
    ACTIVE_STATUSES: ACTIVE_STATUSES,
    SCORE_STATUSES: SCORE_STATUSES,
    createRun: function (requisition, pastedLeads) {
      return request("/api/runs", {
        method: "POST",
        body: { requisition: requisition, pasted_leads: pastedLeads },
      });
    },
    getRun: function (runId) {
      return request(runPath(runId, ""));
    },
    accept: function (runId, recruiterLabel) {
      return request(runPath(runId, "/accept"), {
        method: "POST",
        body: { recruiter_label: recruiterLabel },
      });
    },
    discard: function (runId) {
      return request(runPath(runId, "/discard"), { method: "POST" });
    },
    saveSatisfaction: function (runId, score, comment) {
      return request(runPath(runId, "/satisfaction"), {
        method: "POST",
        body: { score: score, comment: comment },
      });
    },
    getRecommendation: function (runId) {
      return request(runPath(runId, "/recommendation"));
    },
    previewPosting: function (payload) {
      return request("/api/postings/preview", { method: "POST", body: payload });
    },
  };
})(window);

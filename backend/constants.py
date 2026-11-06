"""Limits from the SAD. They are engineering caps, not product SLAs."""

MAX_REQUISITION_CHARS = 20_000
MAX_PASTED_LEADS_CHARS = 50_000
MAX_COMMENT_CHARS = 2_000
MAX_LABEL_CHARS = 200
MAX_CANDIDATES = 10
CREW_BUDGET_SECONDS = 900
MAX_ITER = 12
MAX_RETRY_LIMIT = 2
MAX_RPM = 10
LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 4096
POSTING_TIMEOUT_SECONDS = 10.0
POSTING_MAX_BYTES = 1_000_000
POSTING_MAX_REDIRECTS = 3

ACTIVE_STATUSES = ("researching", "evaluating", "recommending")
DRAFT_STATUSES = ("draft", "accepted", "discarded")
STAGE_BY_STATUS = {
    "researching": "research",
    "evaluating": "evaluation",
    "recommending": "recommendation",
}

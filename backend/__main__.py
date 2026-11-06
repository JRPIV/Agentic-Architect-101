"""Listen on localhost only."""

import os

import uvicorn

os.environ.setdefault("CREWAI_TELEMETRY_OPT_OUT", "true")

if __name__ == "__main__":
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False)

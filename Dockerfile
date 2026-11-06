# Local package of the existing process. It is not a cloud service.
# backend/__main__.py binds 127.0.0.1:8000, so a published container port
# does not reach the server. The Tier-0 procedure is the virtualenv in
# project-context/3.deliver/deploy.md.

FROM python:3.13-slim

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser

COPY backend/requirements.lock.txt backend/requirements.lock.txt
RUN pip install --no-cache-dir -r backend/requirements.lock.txt

COPY backend backend
COPY frontend frontend
COPY pytest.ini pytest.ini

RUN mkdir -p backend/runs project-context/2.build/logs \
    && chown -R appuser:appuser /app

USER appuser

ENV CREWAI_TELEMETRY_OPT_OUT=true

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["python", "-m", "backend"]

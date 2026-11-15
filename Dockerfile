FROM node:22-bookworm-slim AS frontend
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    LUNASCOPE_DATA_DIR=/app/data/nasa \
    LUNASCOPE_AUTO_FETCH=true \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1
WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt \
    && useradd --create-home --uid 10001 luna
COPY --chown=luna:luna backend/ ./backend/
COPY --chown=luna:luna data/nasa_provenance.json ./data/nasa_provenance.json
COPY --chown=luna:luna data/validation/ ./data/validation/
COPY --chown=luna:luna run.py run_lunascope.py pyproject.toml ./
COPY --from=frontend --chown=luna:luna /build/frontend/dist ./frontend/dist
RUN mkdir -p /app/data/nasa /app/frontend/public/assets \
    && chown -R luna:luna /app
USER luna
EXPOSE 8000
VOLUME ["/app/data/nasa"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=300s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/api/ready',timeout=4)"
CMD ["python", "-u", "backend/scripts/start_cloud.py"]

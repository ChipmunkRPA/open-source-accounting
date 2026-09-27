# Review and pin base-image digests in your deployment pipeline.
FROM node:22-bookworm-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts
COPY frontend/tsconfig.json ./
COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/scripts ./scripts
COPY frontend/vendor ./vendor
RUN npm run build

FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PORT=8080
WORKDIR /app
COPY backend/pyproject.toml ./
COPY backend/requirements.lock ./
COPY backend/app ./app
RUN pip install --no-cache-dir --require-hashes -r requirements.lock \
    && pip install --no-cache-dir --no-deps . \
    && useradd --uid 10001 --create-home appuser
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
COPY --from=web /web/dist ./frontend_dist
RUN mkdir -p /app/data && chown -R appuser:appuser /app
USER appuser
EXPOSE 8080
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]

# Original public library is a versioned application asset, not a licensed-source cache.
COPY content /app/content
ENV CONTENT_DIR=/app/content

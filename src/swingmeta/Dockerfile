# syntax=docker/dockerfile:1.6

# ----------------------------------------------------
# Stage 1: Build Vue 3 Frontend
# ----------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ----------------------------------------------------
# Stage 2: Runtime Python Backend
# ----------------------------------------------------
FROM python:3.11-slim AS runtime

WORKDIR /app

# System dependencies (gcc/libev for fast I/O if needed)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy Backend source code
COPY backend/ ./backend/

# Copy built frontend assets to the distribution folder
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# SwingMeta Port
EXPOSE 1971

# Volumes expected to be shared with SwingMusic
VOLUME /config
VOLUME /music

ENV PYTHONUNBUFFERED=1
ENV SWINGMETA_PORT=1971
ENV SWING_CONFIG_DIR=/config
ENV SWING_MUSIC_DIR=/music

WORKDIR /app/backend

CMD ["python", "-m", "waitress", "--port=1971", "--host=0.0.0.0", "app:app"]

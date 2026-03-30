# ============================================
# STAGE 1: Builder
# ============================================
FROM python:3.13-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dépendances build nécessaires pour compiler certains packages Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copier uniquement les requirements (cache Docker optimisé)
COPY requirements.txt .

# Créer venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Installer dépendances
RUN pip install --upgrade pip \
    && pip install -r requirements.txt


# ============================================
# STAGE 2: Runtime
# ============================================
FROM python:3.13-slim AS final

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app

# Installer uniquement les libs runtime nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Créer utilisateur non-root
RUN groupadd -g 10001 calltrack && \
    useradd -u 10001 -g calltrack -m -d /app -s /usr/sbin/nologin calltrack

WORKDIR /app

# Copier environnement Python
COPY --from=builder /opt/venv /opt/venv

# Copier code
COPY --chown=calltrack:calltrack ./app /app/app

# Créer dossiers runtime
RUN mkdir -p /app/uploads /app/recordings && \
    chown -R calltrack:calltrack /app

USER calltrack

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# FastAPI avec Uvicorn
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--workers","4"]

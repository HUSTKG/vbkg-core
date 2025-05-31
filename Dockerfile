FROM python:3.10-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on 

# Install system dependencies as root
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies as root
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install Vietnamese language model for spaCy
RUN pip install https://github.com/explosion/spacy-models/releases/download/xx_ent_wiki_sm-3.5.0/xx_ent_wiki_sm-3.5.0-py3-none-any.whl

# Create non-root user and app directory
RUN adduser --disabled-password --gecos "" appuser \
    && mkdir -p /app \
    && chown appuser:appuser /app

# Switch to non-root user
USER appuser
WORKDIR /app

# Copy application code with correct ownership (this avoids slow chown -R)
COPY --chown=appuser:appuser . .

# Expose port
EXPOSE 8000

# Command to run on container start
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

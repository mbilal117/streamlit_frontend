FROM python:3.12-slim
LABEL authors="bilal"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH" \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# Create and activate virtual environment
RUN python -m venv /opt/venv

# System deps (build tools), install Python deps, then clean up build tools
COPY requirements.txt /app/requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && pip install --upgrade pip \
    && pip install -r /app/requirements.txt \
    && apt-get purge -y build-essential \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . /app

# Create unprivileged user and fix ownership
RUN addgroup --system app && adduser --system --ingroup app appuser \
    && chown -R appuser:app /app /opt/venv

USER appuser


EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

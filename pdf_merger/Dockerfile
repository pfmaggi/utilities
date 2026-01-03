# Use a clean Python 3.13 image
FROM python:3.13-slim-bookworm

# 1. Install 'uv' explicitly
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# 2. Copy dependency files
COPY pyproject.toml uv.lock ./

# 3. Install dependencies DIRECTLY into the system Python
RUN uv pip install --system --no-cache -r pyproject.toml

# 4. Copy your application code
COPY . .

# 5. Security & Permissions Fix
# Create the user AND the home directory manually
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN mkdir -p /home/appuser && chown -R appuser:appuser /home/appuser
RUN chown -R appuser:appuser /app

# 6. Configure the environment
USER appuser
ENV HOME=/home/appuser
# Optional: Disable Streamlit's usage stats to silence the startup message/network call
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "merge_pdf_web.py", "--server.port=8501", "--server.address=0.0.0.0"]

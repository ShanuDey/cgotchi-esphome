# The base image ships Chromium for this Playwright version but not the Python package.
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir uv && uv pip install --system --no-cache -r pyproject.toml
COPY server.py .
COPY pages pages

EXPOSE 28240
# The server is single-threaded, so /health waits while a slow page renders (up to 20 s).
HEALTHCHECK --interval=30s --timeout=25s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:28240/health', timeout=24)"
CMD ["python", "server.py"]

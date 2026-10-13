FROM python:3.12-slim
WORKDIR /app
COPY requirements-lock.txt ./
RUN pip install --no-cache-dir -r requirements-lock.txt && useradd --uid 10001 --create-home kelun
COPY backend ./backend
COPY web ./web
COPY scripts ./scripts
RUN mkdir /data && chown kelun:kelun /data
USER kelun
ENV DATA_DIR=/data HOST=0.0.0.0 PORT=8000
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"
CMD ["python", "-m", "backend.run"]

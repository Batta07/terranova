FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN addgroup --gid 1001 appgroup && \
    adduser --uid 1001 --ingroup appgroup --no-create-home appuser && \
    chown -R appuser:appgroup /app

COPY app.py db.py seed.py ./
COPY index.html styles.css app.js ./
COPY docs/ ./docs/

RUN chown -R appuser:appgroup /app

USER appuser

ENV HOME=/tmp

EXPOSE 8005

CMD ["gunicorn", "--bind", "0.0.0.0:8005", "--workers", "2", "--worker-tmp-dir", "/tmp", "app:app"]

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8005/')" || exit 1

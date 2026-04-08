FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN addgroup --gid 1001 appgroup && \
    adduser --uid 1001 --ingroup appgroup --no-create-home appuser && \
    chown -R appuser:appgroup /app

COPY app.py db.py seed.py ./
COPY index.html styles.css app.js ./

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/')" || exit 1

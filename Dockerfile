FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MF_DB_PATH=/data/finds.db \
    MF_MEDIA_DIR=/media \
    MF_BACKUP_DIR=/backups \
    TZ=Europe/Vienna

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --system --uid 1000 mf \
    && mkdir /data /media /backups && chown mf /data /media /backups
COPY app ./app
USER mf
VOLUME ["/data", "/media", "/backups"]
# Port-Reihe der Familie (D-001): counts 8080, finds 8090
EXPOSE 8090
CMD ["uvicorn", "--factory", "app.main:create_app", "--host", "0.0.0.0", "--port", "8090", "--proxy-headers"]

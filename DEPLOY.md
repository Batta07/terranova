# Deployment - Terranova Gestione Ferie

## 1. Variabili d'ambiente

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `SECRET_KEY` | Chiave segreta per le sessioni Flask | `terranova-dev-secret-2026` (cambiare in produzione) |

Creare un file `.env` nella directory del progetto:
```
SECRET_KEY=<genera con: openssl rand -hex 32>
```

## 2. Variabili da modificare nel codice

| File | Valore | Descrizione |
|------|--------|-------------|
| `app.py` | `terranova-dev-secret-2026` | Sostituire con `SECRET_KEY` da `.env` in produzione |

## 3. Configurazione Caddy (VPS)

Sul VPS, aggiornare il `docker-compose.yml` per usare `proxy_net` esterna invece di `terranova_net`:

```yaml
networks:
  proxy_net:
    external: true
```

Aggiungere questo blocco al Caddyfile:

```
ferie.tuodominio.it {
    reverse_proxy terranova:5000
}
```

## 4. Primo avvio (VPS)

```bash
cd /opt/docker/apps/terranova
docker network create proxy_net 2>/dev/null || true
docker compose up -d --build
docker compose ps
```

## 5. Aggiornamento dopo modifiche al codice

```bash
cd /opt/docker/apps/terranova
git pull
docker compose up -d --build --force-recreate
```

# Deployment - Terranova Gestione Ferie

## 1. Variabili d'ambiente

Nessuna variabile richiesta. Il progetto e un sito statico senza backend.

## 2. Variabili da modificare nel codice

| File | Valore | Descrizione |
|------|--------|-------------|
| Nessuno | — | Il sito e puramente statico, nessun valore hardcoded da cambiare |

## 3. Configurazione Caddy

Aggiungere questo blocco al Caddyfile:

```
ferie.tuodominio.it {
    reverse_proxy terranova:8005
}
```

Sostituire `ferie.tuodominio.it` con il dominio effettivo.

## 4. Primo avvio

```bash
# Clonare il repo nella directory delle app
cd /opt/docker/apps/terranova

# Creare l'immagine e avviare
docker compose up -d --build

# Verificare che il container sia attivo
docker compose ps
```

## 5. Aggiornamento dopo modifiche al codice

```bash
cd /opt/docker/apps/terranova
git pull
docker compose up -d --build --force-recreate
```

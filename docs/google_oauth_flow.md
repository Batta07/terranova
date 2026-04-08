# Google OAuth 2.0 — Authorization Code Flow

> **Regola d'oro:** Google OAuth serve solo per verificare l'identità dell'utente. Dopo il login, i token Google vengono scartati — il browser usa solo il session cookie del tuo server.

---

## Panoramica dei token

| Token | Chi lo usa | Per fare cosa | Dopo il login |
|---|---|---|---|
| `access_token` | Il **server** | Chiamare `/userinfo` di Google per ottenere email e nome | **Scartato** |
| `refresh_token` | Non serve | Non chiamiamo API Google dopo il login | **Non richiesto** |
| `id_token` | Il **server** | Decodificare per leggere email e nome (alternativa a `/userinfo`) | **Scartato** |
| `session cookie` | Il **browser** | Autenticarsi su tutte le chiamate al tuo server (`/api/ferie`, ecc.) | **Persiste** |

I token Google non vengono salvati nel DB. Non servono dopo il login.

---

## Il flusso completo — 10 passi

### Passo 1 — Utente clicca "Login con Google"
**Browser → Server**

Il server costruisce l'URL di autorizzazione Google e risponde con un redirect HTTP 302.

```
https://accounts.google.com/o/oauth2/v2/auth
  ?client_id=123456789-abc.apps.googleusercontent.com
  &redirect_uri=https://tuaapp.com/auth/callback
  &response_type=code
  &scope=openid%20email%20profile
  &state=xK9mP2qR
  &access_type=online
```

| Parametro | Perché |
|---|---|
| `client_id` | identifica la tua app su Google |
| `redirect_uri` | dove Google rimanda dopo il login |
| `response_type=code` | vogliamo il codice di autorizzazione |
| `scope=openid email profile` | vogliamo solo email e nome |
| `state=xK9mP2qR` | stringa random anti-CSRF, salvata in sessione |
| `access_type=online` | non ci serve il refresh_token — non chiamiamo API Google |

---

### Passo 2 — Il browser viene reindirizzato a Google
**Browser → Google**

Il browser segue il redirect e atterra sulla pagina di login Google. Il server non è coinvolto.

---

### Passo 3 — Google mostra login e consent screen
**Google → Utente**

L'utente inserisce le credenziali Google e approva. Tutto avviene tra browser e Google.

---

### Passo 4 — Google reindirizza con il codice
**Google → Server** (tramite redirect del browser)

```
https://tuaapp.com/auth/callback
  ?code=4/0AY0e-g7…XkQmZ
  &state=xK9mP2qR
```

> ⚠️ **Prima cosa:** verificare che `state` ricevuto == `state` salvato. Se diverso, scarta tutto (attacco CSRF).

---

### Passo 5 — Server scambia il code con i token
**Server → Google** (chiamata server-to-server, mai dal browser)

```http
POST https://oauth2.googleapis.com/token
Content-Type: application/x-www-form-urlencoded

code=4/0AY0e-g7…XkQmZ
&client_id=123456789-abc.apps.googleusercontent.com
&client_secret=GOCSPX-…segreto…
&redirect_uri=https://tuaapp.com/auth/callback
&grant_type=authorization_code
```

> 🔒 Il `client_secret` non deve mai uscire dal server.

---

### Passo 6 — Google risponde con i token
**Google → Server**

```json
{
  "access_token": "ya29.a0AfH6SMB…",
  "expires_in": 3600,
  "token_type": "Bearer",
  "scope": "openid email profile",
  "id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9…"
}
```

Il server fa tre cose e poi **scarta tutto**:

**6a — Decodifica l'`id_token`** per leggere l'email dell'utente:
```json
{
  "sub": "110169484474386276334",
  "email": "manuel@azienda.it",
  "email_verified": true,
  "name": "Manuel Battaglia"
}
```

**6b — Verifica che l'email sia nel DB** (`SELECT * FROM Utenti WHERE email = ?`).
Se non è presente → accesso negato. Solo gli account aziendali pre-registrati possono entrare.

**6c — Scarta i token Google.** Non servono più. Non vengono salvati nel DB.

---

### Passo 7 — Server crea la sessione e risponde all'utente
**Server → Browser**

Il server crea una propria sessione e la manda al browser come cookie `HttpOnly`:

```http
HTTP/1.1 302 Found
Location: /dashboard
Set-Cookie: session=eyJfdXNlcl9pZCI6MX0...; HttpOnly; Secure; SameSite=Lax
```

In Flask: `session['user_id'] = utente.id` — fatto.

Il cookie è **firmato con la `SECRET_KEY`** del server. Flask lo verifica crittograficamente ad ogni richiesta. Non serve una tabella sessioni nel DB.

---

### Passo 8 — Browser chiama le API del tuo server
**Browser → Server**

Il browser usa solo il session cookie. Non sa nulla di Google, access_token, o id_token.

```http
GET /api/ferie HTTP/1.1
Cookie: session=eyJfdXNlcl9pZCI6MX0...
```

Flask:
1. Apre il cookie, verifica la firma con `SECRET_KEY`
2. Legge `user_id = 1`
3. Fa la query al DB
4. Restituisce la risposta JSON

---

### Passo 9 — Risposta JSON all'utente
**Server → Browser**

Il server restituisce i dati. Fine.

---

## Cosa cambia nel DB

**Niente.** Lo schema delle 6 tabelle rimane invariato. I token Google non vengono salvati.

---

## Differenza con il prototipo attuale

Nel prototipo Terranova abbiamo sostituito Google OAuth con un dropdown di selezione utente. La struttura post-login è identica: Flask crea la sessione con `user_id`, il browser usa il cookie per tutte le chiamate a `/api/*`.

Aggiungere Google OAuth reale significherebbe sostituire solo i passi 1-6 con il flusso descritto sopra. I passi 7-9 restano invariati.

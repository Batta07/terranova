# Google OAuth 2.0 — Authorization Code Flow

> **Regola d'oro:** `access_token` vive lato server e dura 1h — `refresh_token` vive nel tuo database e dura anni — `client_secret` non esce mai dal server — `state` va sempre verificato prima di accettare qualsiasi codice.

---

## Step 1 — User clicca "Login con Google"
**Browser → Google**

Il browser non fa ancora nulla di speciale. L'app costruisce un URL e ci reindirizza il browser con un semplice redirect HTTP 302.

URL costruito dall'app:
```
https://accounts.google.com/o/oauth2/v2/auth
  ?client_id=123456789-abc.apps.googleusercontent.com
  &redirect_uri=https://tuaapp.com/auth/callback
  &response_type=code
  &scope=openid%20email%20profile
  &state=xK9mP2qR
  &access_type=offline
  &prompt=consent
```

| Parametro | Valore esempio | Perché |
|---|---|---|
| `client_id` | `123456789-abc…` | identifica la tua app su Google |
| `redirect_uri` | `https://tuaapp.com/auth/callback` | dove Google rimanda dopo il login |
| `response_type` | `code` | vogliamo il codice, non il token direttamente |
| `scope` | `openid email profile` | cosa vogliamo leggere dell'utente |
| `state` | `xK9mP2qR` | stringa random, anti-CSRF |
| `access_type` | `offline` | per ottenere il `refresh_token` |
| `prompt` | `consent` | forza la schermata di consenso |

---

## Step 2 — Google mostra login e consent screen
**User → Google**

L'utente vede la pagina Google. Non c'è nessuna chiamata API da parte tua — il browser comunica direttamente con Google. L'utente inserisce email e password e approva i permessi.

---

## Step 3 — Google reindirizza con authorization code
**Google → App**

Google fa un redirect verso il tuo `redirect_uri` aggiungendo due parametri in query string:

```
https://tuaapp.com/auth/callback
  ?code=4/0AY0e-g7…XkQmZ
  &state=xK9mP2qR
```

| Parametro | Note |
|---|---|
| `code` | authorization code, valido ~10 minuti, monouso |
| `state` | deve corrispondere esattamente a quello che hai mandato — se è diverso, scarta tutto (attacco CSRF) |

> ⚠️ **Prima cosa da fare sul server:** verificare che `state` ricevuto == `state` salvato in sessione.

---

## Step 4 — App scambia il code con il token (server-to-server)
**App → Google**

> 🔒 Questa è l'unica chiamata che parte dal tuo **server**, mai dal browser. Il `client_secret` non deve mai uscire dal server.

```http
POST https://oauth2.googleapis.com/token
Content-Type: application/x-www-form-urlencoded

code=4/0AY0e-g7…XkQmZ
&client_id=123456789-abc.apps.googleusercontent.com
&client_secret=GOCSPX-…segreto…
&redirect_uri=https://tuaapp.com/auth/callback
&grant_type=authorization_code
```

| Parametro | Note |
|---|---|
| `code` | il codice ricevuto al step 3 |
| `client_id` | stesso di prima |
| `client_secret` | segreto assoluto, solo lato server |
| `redirect_uri` | deve essere identico a quello del step 1 (Google lo verifica) |
| `grant_type` | sempre `authorization_code` per questo flusso |

---

## Step 5 — Google risponde con i token
**Google → App**

```json
{
  "access_token": "ya29.a0AfH6SMB…",
  "expires_in": 3600,
  "token_type": "Bearer",
  "scope": "openid email profile https://www.googleapis.com/auth/userinfo.email",
  "refresh_token": "1//0gLd…",
  "id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9…"
}
```

| Campo | Valore | Note |
|---|---|---|
| `access_token` | `ya29.a0…` | token da usare nelle API, scade in 1 ora |
| `expires_in` | `3600` | secondi alla scadenza |
| `token_type` | `Bearer` | come usarlo nell'header |
| `refresh_token` | `1//0gLd…` | arriva solo se hai chiesto `access_type=offline`, non scade mai (finché non viene revocato) |
| `id_token` | JWT firmato | contiene i dati dell'utente codificati in base64 |

L'`id_token` è un JWT. Decodificando il payload (base64) ottieni:

```json
{
  "sub": "110169484474386276334",
  "email": "manuel@gmail.com",
  "email_verified": true,
  "name": "Manuel Battaglia",
  "picture": "https://lh3.googleusercontent.com/…",
  "given_name": "Manuel",
  "family_name": "Battaglia",
  "iat": 1711540800,
  "exp": 1711544400,
  "iss": "https://accounts.google.com",
  "aud": "123456789-abc.apps.googleusercontent.com"
}
```

---

## Step 6 — App risponde all'utente: accesso concesso
**App → Browser**

Il tuo server crea la sessione utente (cookie, JWT proprio, ecc.) e reindirizza il browser alla pagina protetta. I token Google vengono salvati nel database del tuo server, non nel browser.

---

## Step 7 — App chiama le Google API
**App → Google**

Ogni richiesta alle API Google include l'`access_token` nell'header:

```http
GET https://www.googleapis.com/oauth2/v3/userinfo
Authorization: Bearer ya29.a0AfH6SMB…
```

Response:

```json
{
  "sub": "110169484474386276334",
  "name": "Manuel Battaglia",
  "given_name": "Manuel",
  "family_name": "Battaglia",
  "picture": "https://lh3.googleusercontent.com/…",
  "email": "manuel@gmail.com",
  "email_verified": true,
  "locale": "it"
}
```

---

## Step 8 — Refresh del token (quando scade)
**App → Google**

Dopo 1 ora l'`access_token` non funziona più. Il tuo server usa il `refresh_token` per ottenerne uno nuovo, senza che l'utente faccia nulla.

```http
POST https://oauth2.googleapis.com/token
Content-Type: application/x-www-form-urlencoded

client_id=123456789-abc.apps.googleusercontent.com
&client_secret=GOCSPX-…segreto…
&refresh_token=1//0gLd…
&grant_type=refresh_token
```

Response:

```json
{
  "access_token": "ya29.a0AfH6SMC…nuovo…",
  "expires_in": 3600,
  "token_type": "Bearer",
  "scope": "openid email profile"
}
```

> Il `refresh_token` non viene rinnovato (rimane lo stesso), solo l'`access_token` cambia.

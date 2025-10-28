# Auth0 Authentication

This document walks through wiring Auth0-issued access tokens to the `versionminus` API. With this setup the FastAPI service validates bearer tokens for both the React SPA (via the TypeScript SDK) and direct CLI calls (e.g. `curl`).

## 1. Configure environment variables

Populate the following keys in `.env` (or deployment secrets):

- `AUTH_ENABLED`: set to `true` to require Auth0 tokens.
- `AUTH_DOMAIN`: your Auth0 tenant domain, e.g. `versionminus.eu.auth0.com`.
- `AUTH_API_AUDIENCE`: the API Identifier you configured under Auth0 → APIs (often looks like `https://api.versionminus.com/`).
- `AUTH_APPLICATION_CLIENT_ID`: client id of the confidential app that will request tokens (typically the machine-to-machine app).
- `AUTH_APPLICATION_CLIENT_SECRET`: corresponding client secret (omit for public SPAs).

Restart the API after editing the `.env` file so new settings are picked up.

For the React client, supply the matching Vite variables (either in `src/versionminus/client/web/.env`, Docker Compose overrides, or your hosting platform):

- `VITE_AUTH0_DOMAIN`
- `VITE_AUTH0_CLIENT_ID`
- `VITE_AUTH0_AUDIENCE`
- `VITE_AUTH0_SCOPE` (defaults to `openid profile email offline_access`)
- `VITE_API_BASE` (`/api` when you proxy through the same origin)

## 2. Prepare Auth0

1. Create an **API** in Auth0 (Dashboard → APIs → Create API). Copy its Identifier for `AUTH_API_AUDIENCE`.
2. Create applications that will call the API:
   - **Single Page App (React)** – enable Authorization Code with PKCE. In *Advanced Settings → Grant Types*, keep `Authorization Code` and `Refresh Token (Rotation)`, disable Implicit/Password/Client Credentials. Add your API under “Permissions”.
   - **Machine to Machine** – authorize it to call the API and note its client id/secret for CLI or automation.
   - *(Optional)* **Native / Device** application if you want users to obtain a token from the command line via the Device Authorization flow.
3. (Optional) Define custom scopes on the API if you plan to enforce fine-grained permissions later.

## 3. React SPA login flow

Wrap the SPA with `Auth0Provider` and request an access token via `@auth0/auth0-react`. The SDK now accepts a `token` option and pauses data fetching until a bearer token is available.

```tsx
// src/versionminus/client/web/src/main.tsx
<Auth0Provider
  domain={import.meta.env.VITE_AUTH0_DOMAIN}
  clientId={import.meta.env.VITE_AUTH0_CLIENT_ID}
  authorizationParams={{
    audience: import.meta.env.VITE_AUTH0_AUDIENCE,
    redirect_uri: window.location.origin,
    scope: import.meta.env.VITE_AUTH0_SCOPE || 'openid profile email offline_access',
  }}
  cacheLocation="localstorage"
  useRefreshTokens
>
  <App />
</Auth0Provider>
```

Inside the app, let the hook manage the SDK and bearer token:

```tsx
const apiBase = import.meta.env.VITE_API_BASE || '/api';
const { isAuthenticated, getAccessTokenSilently, loginWithRedirect } = useAuth0();
const [token, setToken] = useState<string>();
const versionminus = useversionminus({ baseUrl: apiBase, token });

useEffect(() => {
  if (!isAuthenticated) {
    void loginWithRedirect();
    return;
  }
  void (async () => {
    const t = await getAccessTokenSilently();
    setToken(t);
  })();
}, [getAccessTokenSilently, isAuthenticated, loginWithRedirect]);

if (!token || !versionminus.currentUser) return <div>Authenticating…</div>;
```

The hook exposes the authenticated user via `versionminus.currentUser`, backed by the new `GET /api/v1/users/me` endpoint. Missing users are auto-provisioned when an `email` claim is present.

## 4. Getting a token for `curl` or scripts

Use the machine-to-machine application credentials with the OAuth2 client credentials flow:

```bash
curl --request POST "https://YOUR_DOMAIN/oauth/token" \
  --header "content-type: application/x-www-form-urlencoded" \
  --data "grant_type=client_credentials" \
  --data "client_id=${AUTH_APPLICATION_CLIENT_ID}" \
  --data "client_secret=${AUTH_APPLICATION_CLIENT_SECRET}" \
  --data "audience=${AUTH_API_AUDIENCE}"
```

The response contains an `access_token`. Call the API with it:

```bash
TOKEN="paste-token-here"
curl http://localhost:8000/api/v1/notes/ \
  --header "Authorization: Bearer ${TOKEN}"
```

## 5. Health checks and docs

The liveness/readiness endpoints (`/api/v1/health/*`) stay unauthenticated so Kubernetes-style probes keep working. Swagger UI (`/docs`) and the OpenAPI schema (`/openapi.json`) remain publicly accessible for inspection; all other routes require a valid Auth0 bearer token.

## 6. Quick reference

- `GET /api/v1/users/me` returns the local user record associated with the Auth0 `sub`.
- Pass SPA environment variables (the `VITE_*` keys) through Docker Compose or your hosting platform so the frontend can reach Auth0.
- The SDK’s `useversionminus` hook accepts `{ token }` and refreshes requests whenever the token changes.

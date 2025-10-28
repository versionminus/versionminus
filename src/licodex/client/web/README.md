# Licodex Web

Retro-modern terminal-inspired React interface consuming the local TypeScript SDK (`@licodex/sdk`) exclusively—no direct REST calls in components.

## Features

* Chat panel styled as a terminal (user / assistant lines)
* Notes panel with create / edit / delete, auto-title from first line
* Ask questions about a selected note or all notes (`sdk.ask`)
* Responsive (notes panel collapses under 1100px width)
* GitHub Dark color palette + Source Code Pro font

## Configuration

The SDK supplies a default API base URL: `http://licodex-api:8000`. Override later by passing `baseUrl` to `useLicodex({ baseUrl: 'https://api.example.com' })` if needed. No `.env` required for local usage.

## Local Development

```bash
# Build the SDK (once or when you change it)
cd src/licodex/sdk/ts
npm install
npm run build

# Start the web client
cd ../../client/web
npm install
npm run dev
```

Visit <http://localhost:5173> and ensure the API is reachable at `http://licodex-api:8000` (started via compose).

## Docker

The `Dockerfile` builds the app and serves it with Nginx, proxying `/api/` to the internal api service.

```bash
docker compose build web
docker compose up -d web
```

Site: <http://localhost:5173>

## Production Build Without Docker

```bash
cd src/licodex/client/web
npm run build  # outputs dist/
```
Serve `dist/` statically (ensure SPA fallback to index.html).

## Structure

```text
src/
	components/
		ChatPanel.tsx
		NotesPanel.tsx
	pages/
		App.tsx
	theme.css
	main.tsx
```

## Future Enhancements

* Routing for note deep links
* Persist chat history (localStorage)
* Optimistic UI + toasts
* Note search / filter
* Keyboard shortcuts (Cmd/Ctrl+Enter to ask, Cmd/Ctrl+N new note)
* Tests (Vitest + RTL)
* Light theme toggle

## License

Refer to root project license.

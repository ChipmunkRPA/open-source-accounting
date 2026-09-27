# Optional Next.js host (not built or browser-tested in the authoring environment)
The tested UI is a dependency-light TypeScript SPA served by FastAPI. This adapter hosts
that same UI inside Next.js instead of duplicating its behavior. It is intentionally
client-rendered; SEO, server components and Next routing are not implemented.

With the backend at 127.0.0.1:8000:
```
cd frontend/next-host
npm install
BACKEND_ORIGIN=http://127.0.0.1:8000 npm run dev
```
Use `npm run build && npm start` after dependency/security review. Webpack is explicit
because extension aliases resolve the shared UI's browser-style `.js` imports. Next
and React installation/build could not be tested here because package downloads were
unavailable. Keep the default bundled UI until this optional adapter is validated.
Do not expose a private API through a public rewrite without retaining backend auth.

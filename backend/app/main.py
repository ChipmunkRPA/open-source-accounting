from contextlib import asynccontextmanager
from pathlib import Path
import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError, OperationalError
from .config import Settings
from .db import Database
from .errors import ProviderError
from .api import core, workspaces, chats, runs, memos, sources, billing, watches, library, sec_core, intake, counsel, source_scopes, output_amendments, model_usage, model_budgets


class BodySizeLimit:
    """ASGI receive limit catches chunked bodies before unbounded multipart buffering."""
    def __init__(self, app, limit):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        headers = dict(scope.get('headers', []))
        try:
            length = int(headers.get(b'content-length', b'0'))
        except ValueError:
            length = self.limit+1
        if length > self.limit:
            return await JSONResponse({'error': {'code': 'BODY_TOO_LARGE', 'message': 'Request exceeds upload limit.'}}, status_code=413)(scope, receive, send)
        count = 0
        async def bounded_receive():
            nonlocal count
            message = await receive()
            count += len(message.get('body', b''))
            if count > self.limit:
                raise HTTPException(413, detail={'code': 'BODY_TOO_LARGE', 'message': 'Request exceeds upload limit.'})
            return message
        await self.app(scope, bounded_receive, send)


def create_app(config: Settings | None = None):
    config = config or Settings()
    database = Database(config.database_url)
    @asynccontextmanager
    async def lifespan(app):
        if config.auto_create_schema:
            database.create_all()
        if config.auto_seed:
            from .seed import seed
            with database.Session() as db:
                seed(db)
        if config.app_env == 'production':
            roots = [Path(__file__).resolve().parents[1] / 'frontend_dist',
                     Path(__file__).resolve().parents[2] / 'frontend/dist']
            if not any((p / 'vendor/identity.js').is_file() for p in roots):
                raise RuntimeError('Production requires the compiled Identity Platform frontend bundle.')
        yield
        database.engine.dispose()

    app = FastAPI(title='Open Source Accounting API', version='0.7.0', lifespan=lifespan,
                  description='Free general chat and paid annual Agent workflows. All research outputs are drafts.')
    app.state.settings, app.state.db = config, database
    app.add_middleware(BodySizeLimit, limit=(config.max_upload_mb+1)*1024*1024)
    app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in config.allowed_origins.split(',')],
                       allow_credentials=False, allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
                       allow_headers=['Authorization', 'Content-Type', 'Idempotency-Key', 'X-Dev-User'])

    @app.middleware('http')
    async def security_headers(request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers['X-Request-ID'] = request.state.request_id
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        if request.url.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        if config.app_env == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        # CSS is static; UI avoids inline handlers and innerHTML of untrusted data.
        if request.url.path not in {'/docs', '/redoc'}:
            live_auth = config.auth_mode == 'firebase'
            script = "script-src 'self'" + (" https://www.google.com/recaptcha/ https://www.gstatic.com/recaptcha/" if live_auth else '')
            frames = "frame-src https://www.google.com/recaptcha/ https://recaptcha.google.com/recaptcha/" if live_auth else "frame-src 'none'"
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; " + script + "; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                "connect-src 'self' https://identitytoolkit.googleapis.com https://securetoken.googleapis.com"
                + (" https://www.google.com/recaptcha/" if live_auth else '') + "; " + frames + "; "
                "frame-ancestors 'none'; object-src 'none'; base-uri 'self'; form-action 'self'")

        return response

    @app.exception_handler(HTTPException)
    async def http_error(request, error):
        detail = error.detail if isinstance(error.detail, dict) else {'code': 'REQUEST_ERROR', 'message': str(error.detail)}
        return JSONResponse({'error': detail, 'request_id': getattr(request.state, 'request_id', '')}, status_code=error.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        return JSONResponse({'error': {'code': 'VALIDATION_ERROR', 'message': 'Check the highlighted fields.',
                            'fields': [{'field': '.'.join(map(str, e['loc'])), 'message': e['msg']} for e in error.errors()]}}, status_code=422)

    @app.exception_handler(ProviderError)
    async def provider_error(request, error):
        return JSONResponse({'error': {'code': str(error), 'message': 'The external service could not complete this request.'}}, status_code=502)

    @app.exception_handler(IntegrityError)
    async def integrity_error(request, error):
        return JSONResponse({'error': {'code': 'CONCURRENT_CHANGE', 'message': 'A concurrent request changed this record. Reload and retry.'}}, status_code=409)

    @app.exception_handler(OperationalError)
    async def database_error(request, error):
        return JSONResponse({'error': {'code': 'DATABASE_UNAVAILABLE', 'message': 'The database is busy or unavailable. Retry shortly.'}}, status_code=503)

    for module in (core, workspaces, chats, runs, memos, sources, billing, watches, library, sec_core, intake, counsel, source_scopes, output_amendments, model_usage, model_budgets):
        app.include_router(module.router, prefix='/api/v1')
    dist = Path(__file__).resolve().parents[1] / 'frontend_dist'
    # Development checkout path; Docker copies dist into backend/frontend_dist.
    if not dist.exists():
        dist = Path(__file__).resolve().parents[2] / 'frontend' / 'dist'
    if dist.exists():
        app.mount('/assets', StaticFiles(directory=dist), name='assets')
        @app.get('/{path:path}', include_in_schema=False)
        def frontend(path: str):
            if path.startswith('api/'):
                raise HTTPException(404, 'API endpoint not found.')
            return FileResponse(dist / 'index.html')
    return app


app = create_app()

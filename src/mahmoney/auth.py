import hashlib
import hmac
import secrets
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse

from mahmoney.config import get_settings

# Simple in-memory session store (single-user app, fine for this scale)
_sessions: dict[str, float] = {}

SESSION_COOKIE = "mahmoney_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days

# Paths that don't require auth
PUBLIC_PATHS = {"/login", "/api/v1/health"}


def _sign_token(session_id: str) -> str:
    settings = get_settings()
    sig = hmac.new(
        settings.session_secret.encode(), session_id.encode(), hashlib.sha256
    ).hexdigest()
    return f"{session_id}.{sig}"


def _verify_token(token: str) -> str | None:
    if "." not in token:
        return None
    session_id, _sig = token.rsplit(".", 1)
    expected = _sign_token(session_id)
    if hmac.compare_digest(token, expected):
        return session_id
    return None


def create_session(response: Response) -> None:
    session_id = secrets.token_urlsafe(32)
    _sessions[session_id] = time.time()
    token = _sign_token(session_id)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
    )


def destroy_session(request: Request, response: Response) -> None:
    token = request.cookies.get(SESSION_COOKIE, "")
    session_id = _verify_token(token)
    if session_id:
        _sessions.pop(session_id, None)
    response.delete_cookie(SESSION_COOKIE)


def is_authenticated(request: Request) -> bool:
    token = request.cookies.get(SESSION_COOKIE, "")
    session_id = _verify_token(token)
    if not session_id:
        return False
    created = _sessions.get(session_id)
    if not created:
        return False
    if time.time() - created > SESSION_MAX_AGE:
        _sessions.pop(session_id, None)
        return False
    return True


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Allow public paths and static files
        if path in PUBLIC_PATHS or path.startswith("/static"):
            return await call_next(request)

        # API routes use the same session auth
        if not is_authenticated(request):
            if path.startswith("/api/"):
                return Response(status_code=401, content="Unauthorized")
            return RedirectResponse(url="/login", status_code=302)

        return await call_next(request)

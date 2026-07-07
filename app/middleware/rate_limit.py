"""
Week 6 addition: rate limiting via slowapi (a FastAPI-friendly
wrapper around the `limits` library).

Wire into main.py:

    from slowapi.errors import RateLimitExceeded
    from slowapi import _rate_limit_exceeded_handler
    from app.middleware.rate_limit import limiter

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

Then decorate sensitive routes, e.g. in app/routers/auth.py:

    from app.middleware.rate_limit import limiter

    @router.post("/login")
    @limiter.limit("5/minute")
    def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
        ...

Note: slowapi requires the route function to accept a `request: Request`
parameter when using the @limiter.limit(...) decorator.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Default: 100 requests/minute per client IP across the whole API.
# Override per-route with @limiter.limit("N/minute") for stricter limits
# (e.g. login/register should be tighter than read-only GETs).
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

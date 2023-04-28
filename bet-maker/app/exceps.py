from starlette.responses import JSONResponse

from app.services.utils import (
    NotInDB,
    ContainsInDB,
    ConflictError,
)


def get_default_error_handler(status_code: int):
    def default_error_handler(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=status_code)

    return default_error_handler


def init(app):
    app.add_exception_handler(NotInDB, get_default_error_handler(status_code=404))
    app.add_exception_handler(ContainsInDB, get_default_error_handler(status_code=409))
    app.add_exception_handler(ConflictError, get_default_error_handler(status_code=409))

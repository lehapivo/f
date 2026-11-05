"""Ошибки бизнес-логики и их отображение в HTTP-ответы."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DomainError(Exception):
    status_code = 400

    def __init__(self, code: str, detail: str = ""):
        super().__init__(detail or code)
        self.code = code
        self.detail = detail or code


class NotFoundError(DomainError):
    status_code = 404


class ConflictError(DomainError):
    status_code = 409


class BusinessRuleError(DomainError):
    status_code = 400


class DependencyError(DomainError):
    """Другой сервис недоступен или ответил ошибкой."""
    status_code = 503


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, exc: DomainError):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.code, "detail": exc.detail})

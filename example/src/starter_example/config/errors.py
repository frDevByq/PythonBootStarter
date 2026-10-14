"""Map business errors, HTTP errors and validation failures into one response envelope."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from pythonboot_web import controller_advise, exception_handler
from starter_example.domain.common import BaseResult, UserNotFoundError


@controller_advise
class ErrorAdvice:
    @exception_handler(UserNotFoundError)
    def user_missing(self, request: Request, error: UserNotFoundError) -> JSONResponse:
        return self.failure(str(error), 404)

    @exception_handler(RequestValidationError)
    def invalid(self, request: Request, error: RequestValidationError) -> JSONResponse:
        return self.failure(str(error), 422)

    @exception_handler(HTTPException)
    def http_error(self, request: Request, error: HTTPException) -> JSONResponse:
        return self.failure(str(error.detail), error.status_code)

    @exception_handler(TimeoutError)
    def lock_timeout(self, request: Request, error: TimeoutError) -> JSONResponse:
        return self.failure(str(error), 409)

    @staticmethod
    def failure(message: str, status: int) -> JSONResponse:
        return JSONResponse(BaseResult.failure(message).model_dump(mode="json"), status_code=status)

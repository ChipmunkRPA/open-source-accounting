from fastapi import HTTPException


def fail(code: str, message: str, status: int = 400, **details):
    raise HTTPException(status_code=status, detail={'code': code, 'message': message, **details})


class ProviderError(RuntimeError):
    """Safe error category; never expose provider request bodies or secrets."""


class RunStopped(RuntimeError):
    pass

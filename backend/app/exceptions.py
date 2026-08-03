from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictError(HTTPException):
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class EbayAPIError(Exception):
    def __init__(self, message: str, error_id: str | None = None, is_transient: bool = False):
        self.message = message
        self.error_id = error_id
        self.is_transient = is_transient
        super().__init__(self.message)


class AliExpressAPIError(Exception):
    def __init__(self, message: str, is_transient: bool = False):
        self.message = message
        self.is_transient = is_transient
        super().__init__(self.message)

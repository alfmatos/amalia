class AmaliaError(Exception):
    """Base error for the Amália SDK."""


class AmaliaAuthError(AmaliaError):
    """Raised on 401/403 from the API."""


class AmaliaHTTPError(AmaliaError):
    def __init__(self, status_code: int, body: str):
        super().__init__(f"HTTP {status_code}: {body[:500]}")
        self.status_code = status_code
        self.body = body

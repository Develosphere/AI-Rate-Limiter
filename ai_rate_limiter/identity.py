from fastapi import Request
from typing import Optional, Callable

DEFAULT_API_KEY_HEADER = "X-API-Key"
DEFAULT_USER_ID_HEADER = "X-User-Id"

async def default_identity_resolver(request: Request, api_key_header: str, user_id_header: str) -> tuple[str, Optional[str]]:
    api_key = request.headers.get(api_key_header)
    user_id = request.headers.get(user_id_header)
    return api_key, user_id

# Identity resolver type: Callable[[Request, str, str], Awaitable[Tuple[str, Optional[str]]]]

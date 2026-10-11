from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.common.config import get_settings
from backend.common.models import AuthUser


settings = get_settings()
bearer = HTTPBearer(auto_error=False)


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations_text, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations_text),
        )
        return hmac.compare_digest(_b64encode(derived), expected)
    except (TypeError, ValueError):
        return False


def create_access_token(user: AuthUser) -> str:
    header = _b64encode(json.dumps(
        {"alg": "HS256", "typ": "JWT"}, separators=(",", ":")
    ).encode())
    payload_data = user.model_dump()
    payload_data.update({
        "sub": user.username,
        "iat": int(time.time()),
        "exp": int(time.time()) + settings.access_token_minutes * 60,
    })
    payload = _b64encode(json.dumps(
        payload_data, separators=(",", ":"), ensure_ascii=False
    ).encode())
    signing_input = f"{header}.{payload}".encode()
    signature = _b64encode(hmac.new(
        settings.auth_secret.encode(), signing_input, hashlib.sha256
    ).digest())
    return f"{header}.{payload}.{signature}"


def decode_access_token(token: str) -> AuthUser:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="登录状态无效或已过期。",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        header, payload, signature = token.split(".")
        signing_input = f"{header}.{payload}".encode()
        expected = _b64encode(hmac.new(
            settings.auth_secret.encode(), signing_input, hashlib.sha256
        ).digest())
        if not hmac.compare_digest(signature, expected):
            raise unauthorized
        data = json.loads(_b64decode(payload))
        if int(data["exp"]) < int(time.time()):
            raise unauthorized
        return AuthUser.model_validate(data)
    except HTTPException:
        raise
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise unauthorized from exc


async def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> AuthUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录。",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)


def require_roles(*allowed_roles: str):
    async def dependency(user: Annotated[AuthUser, Depends(current_user)]) -> AuthUser:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="当前账号没有访问此功能的权限。")
        return user
    return dependency


AuthenticatedUser = Annotated[AuthUser, Depends(current_user)]
AdminUser = Annotated[AuthUser, Depends(require_roles("ADMIN", "SITE_ADMIN"))]
GlobalAdminUser = Annotated[AuthUser, Depends(require_roles("ADMIN"))]
StudentUser = Annotated[AuthUser, Depends(require_roles("STUDENT"))]

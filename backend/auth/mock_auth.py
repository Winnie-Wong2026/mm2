from copy import deepcopy
from typing import Optional


TOKEN_PREFIX = "mock-token-"

_USERS = {
    "admin": {
        "user_id": "u_admin",
        "username": "admin",
        "display_name": "管理员",
        "role": "admin",
        "password": "admin123",
    },
    "researcher": {
        "user_id": "u_researcher",
        "username": "researcher",
        "display_name": "研究员",
        "role": "researcher",
        "password": "research123",
    },
    "viewer": {
        "user_id": "u_viewer",
        "username": "viewer",
        "display_name": "普通用户",
        "role": "viewer",
        "password": "viewer123",
    },
}


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = _USERS.get(username)
    if not user or user["password"] != password:
        return None
    return deepcopy(user)


def create_access_token(username: str) -> str:
    return f"{TOKEN_PREFIX}{username}"


def get_user_by_token(token: str) -> Optional[dict]:
    if not token.startswith(TOKEN_PREFIX):
        return None
    username = token.replace(TOKEN_PREFIX, "", 1)
    user = _USERS.get(username)
    return deepcopy(user) if user else None


def to_public_user(user: dict) -> dict:
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "display_name": user["display_name"],
        "role": user["role"],
    }


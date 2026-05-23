from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.models import LoginRequest
from backend.api.responses import success_response
from backend.auth.dependencies import get_current_user
from backend.auth.mock_auth import authenticate_user, create_access_token, to_public_user


router = APIRouter()


@router.post("/login")
def login(payload: LoginRequest) -> dict:
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_INVALID_CREDENTIALS",
                "message": "用户名或密码不正确",
                "details": {},
            },
        )

    return success_response(
        {
            "access_token": create_access_token(user["username"]),
            "token_type": "bearer",
            "user": to_public_user(user),
        }
    )


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)) -> dict:
    return success_response(to_public_user(current_user))


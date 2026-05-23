from fastapi import APIRouter, Depends

from backend.api.mock_service import list_strategies
from backend.api.responses import success_response
from backend.auth.dependencies import get_current_user


router = APIRouter()


@router.get("/strategies")
def get_strategies(_: dict = Depends(get_current_user)) -> dict:
    return success_response(list_strategies())

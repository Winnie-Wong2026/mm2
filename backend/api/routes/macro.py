from fastapi import APIRouter, Depends

from backend.api.mock_service import get_macro_regime
from backend.api.responses import success_response
from backend.auth.dependencies import get_current_user


router = APIRouter()


@router.get("/macro-regime")
def get_current_macro_regime(_: dict = Depends(get_current_user)) -> dict:
    return success_response(get_macro_regime())

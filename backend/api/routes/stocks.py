from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.mock_service import get_stock_detail
from backend.api.responses import success_response
from backend.auth.dependencies import get_current_user


router = APIRouter()


@router.get("/stocks/{symbol}")
def get_stock(symbol: str, _: dict = Depends(get_current_user)) -> dict:
    detail = get_stock_detail(symbol)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "RESOURCE_NOT_FOUND",
                "message": "股票不存在或 mock 数据未覆盖",
                "details": {"symbol": symbol},
            },
        )
    return success_response(detail)


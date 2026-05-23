from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.api.mock_service import add_watchlist_item, list_watchlist, remove_watchlist_item
from backend.api.models import Market, RiskLevel, WatchlistCreateRequest
from backend.api.responses import paginated_response, success_response
from backend.auth.dependencies import get_current_user


router = APIRouter()


@router.get("/watchlist")
def get_watchlist(
    market: Optional[Market] = Query(None),
    risk_level: Optional[RiskLevel] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
) -> dict:
    items, total = list_watchlist(
        username=current_user["username"],
        market=market,
        risk_level=risk_level,
        page=page,
        page_size=page_size,
    )
    return paginated_response(items, page=page, page_size=page_size, total=total)


@router.post("/watchlist")
def create_watchlist_item(
    payload: WatchlistCreateRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    item, error = add_watchlist_item(
        username=current_user["username"],
        symbol=payload.symbol,
        note=payload.note,
    )
    if error == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "RESOURCE_NOT_FOUND",
                "message": "股票不存在或 mock 数据未覆盖",
                "details": {"symbol": payload.symbol},
            },
        )
    if error == "exists":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "WATCHLIST_ALREADY_EXISTS",
                "message": "观察名单中已存在该股票",
                "details": {"symbol": payload.symbol},
            },
        )
    return success_response(item)


@router.delete("/watchlist/{symbol}")
def delete_watchlist_item(
    symbol: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    deleted = remove_watchlist_item(current_user["username"], symbol)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "RESOURCE_NOT_FOUND",
                "message": "观察名单中不存在该股票",
                "details": {"symbol": symbol},
            },
        )
    return success_response({"deleted": True, "symbol": symbol.upper()})


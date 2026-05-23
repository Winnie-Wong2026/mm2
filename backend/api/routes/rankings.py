from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.api.mock_service import DEFAULT_STRATEGY_ID, list_rankings
from backend.api.models import Frequency, Market
from backend.api.responses import paginated_response
from backend.auth.dependencies import get_current_user


router = APIRouter()


@router.get("/rankings")
def get_rankings(
    market: Market = Query("cn"),
    frequency: Frequency = Query("daily"),
    top_n: int = Query(20, ge=1),
    strategy_id: str = Query(DEFAULT_STRATEGY_ID),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: dict = Depends(get_current_user),
) -> dict:
    if top_n not in {20, 50}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "COMMON_BAD_REQUEST",
                "message": "top_n 仅支持 20 或 50",
                "details": {"top_n": top_n},
            },
        )

    items, total = list_rankings(
        market=market,
        frequency=frequency,
        top_n=top_n,
        strategy_id=strategy_id,
        page=page,
        page_size=page_size,
    )
    return paginated_response(items, page=page, page_size=page_size, total=total)


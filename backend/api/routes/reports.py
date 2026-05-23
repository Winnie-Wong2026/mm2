from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.api.mock_service import get_report_detail, list_reports
from backend.api.models import Frequency, Market
from backend.api.responses import paginated_response, success_response
from backend.auth.dependencies import get_current_user


router = APIRouter()


@router.get("/reports")
def get_reports(
    frequency: Optional[Frequency] = Query(None),
    market: Optional[Market] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: dict = Depends(get_current_user),
) -> dict:
    items, total = list_reports(
        frequency=frequency,
        market=market,
        page=page,
        page_size=page_size,
    )
    return paginated_response(items, page=page, page_size=page_size, total=total)


@router.get("/reports/{report_id}")
def get_report(report_id: str, _: dict = Depends(get_current_user)) -> dict:
    detail = get_report_detail(report_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "RESOURCE_NOT_FOUND",
                "message": "报告不存在或 mock 数据未覆盖",
                "details": {"report_id": report_id},
            },
        )
    return success_response(detail)


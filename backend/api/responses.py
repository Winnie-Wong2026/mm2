from typing import Any, Optional


def build_meta(**extra: Any) -> dict:
    meta = {
        "request_id": "mock-request",
        "mock": True,
    }
    meta.update(extra)
    return meta


def success_response(data: Any, **meta_extra: Any) -> dict:
    return {
        "data": data,
        "meta": build_meta(**meta_extra),
    }


def paginated_response(data: list, page: int, page_size: int, total: int) -> dict:
    return success_response(
        data,
        pagination={
            "page": page,
            "page_size": page_size,
            "total": total,
        },
    )


def error_response(code: str, message: str, details: Optional[dict] = None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
        "meta": build_meta(),
    }


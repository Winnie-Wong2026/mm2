from fastapi import APIRouter, Depends

from backend.api.responses import success_response
from backend.auth.dependencies import require_roles
from backend.tasks.mock_tasks import get_task_status


router = APIRouter()


@router.get("/tasks/status")
def get_status(_: dict = Depends(require_roles("admin", "researcher"))) -> dict:
    return success_response(get_task_status())


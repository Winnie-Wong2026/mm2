from copy import deepcopy


_TASK_STATUS = {
    "as_of": "2026-05-22T20:10:00+08:00",
    "latest_data_update_at": "2026-05-22T17:30:00+08:00",
    "latest_ranking_generated_at": "2026-05-22T18:30:00+08:00",
    "latest_report_generated_at": "2026-05-22T19:00:00+08:00",
    "tasks": [
        {
            "task_id": "data_update_daily",
            "task_name": "日频数据更新",
            "status": "success",
            "started_at": "2026-05-22T16:10:00+08:00",
            "finished_at": "2026-05-22T17:30:00+08:00",
            "message": "mock 数据更新完成",
        },
        {
            "task_id": "ranking_generate_daily",
            "task_name": "日频榜单生成",
            "status": "success",
            "started_at": "2026-05-22T18:00:00+08:00",
            "finished_at": "2026-05-22T18:30:00+08:00",
            "message": "mock 榜单生成完成",
        },
        {
            "task_id": "report_generate_daily",
            "task_name": "日报生成",
            "status": "success",
            "started_at": "2026-05-22T18:40:00+08:00",
            "finished_at": "2026-05-22T19:00:00+08:00",
            "message": "mock 报告生成完成",
        },
    ],
    "failed_tasks": [],
}


def get_task_status() -> dict:
    return deepcopy(_TASK_STATUS)

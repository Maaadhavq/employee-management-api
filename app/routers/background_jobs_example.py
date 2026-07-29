"""
Background jobs example.

FastAPI's built-in BackgroundTasks is the lightest way to run background
work without pulling in Celery/SQS — appropriate for a task like "export
employees to S3 without blocking the request." For heavier/queued workloads
later, Celery + Redis or SQS would be the natural next step.

This pattern integrates directly into the employee router.
"""

import csv
import io
import logging
from datetime import datetime

import boto3
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user

# adjust to your actual employee model/repository import
# from app.repositories import employee_repository

logger = logging.getLogger("employee_api")

router = APIRouter(prefix="/employees", tags=["Employees"])

EXPORT_BUCKET = "madhav-employee-exports-2026"


def _export_employees_to_s3(rows: list[dict]) -> None:
    """Runs after the response has already been sent to the client."""
    buffer = io.StringIO()
    if rows:
        writer = csv.DictWriter(buffer, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    key = f"exports/employees_{datetime.utcnow():%Y%m%dT%H%M%S}.csv"
    s3 = boto3.client("s3", region_name="ap-south-1")
    s3.put_object(Bucket=EXPORT_BUCKET, Key=key, Body=buffer.getvalue().encode("utf-8"))
    logger.info(f"Background export complete: s3://{EXPORT_BUCKET}/{key}")


@router.post("/export", dependencies=[Depends(get_current_user)])
def trigger_export(
    background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    """Kicks off an S3 export in the background and returns immediately."""
    # rows = [row.__dict__ for row in employee_repository.get_all(db)]
    rows: list[dict] = []  # replace with real employee query

    background_tasks.add_task(_export_employees_to_s3, rows)
    return {"message": "Export started", "status": "processing"}

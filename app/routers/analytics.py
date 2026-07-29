"""
Read-only analytics endpoints backed by the tables
the Sales ETL pipeline's PostgresDataSink writes into the shared
RDS `analytics` schema. This is the integration point between the
Employee Management API and the Sales ETL pipeline.

Table names below (daily_sales_summary, product_performance,
category_breakdown, regional_summary) are placeholders — rename to
match your actual four aggregation tables.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
    dependencies=[Depends(get_current_user)],  # every route below requires a valid JWT
)


@router.get("/daily-sales")
def get_daily_sales(db: Session = Depends(get_db), limit: int = 100):
    rows = db.execute(
        text(
            "SELECT * FROM analytics.daily_sales_summary "
            "ORDER BY sale_date DESC LIMIT :limit"
        ),
        {"limit": limit},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/product-performance")
def get_product_performance(db: Session = Depends(get_db), limit: int = 100):
    rows = db.execute(
        text(
            "SELECT * FROM analytics.product_performance "
            "ORDER BY total_revenue DESC LIMIT :limit"
        ),
        {"limit": limit},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/category-breakdown")
def get_category_breakdown(db: Session = Depends(get_db)):
    rows = db.execute(
        text("SELECT * FROM analytics.category_breakdown")
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/regional-summary")
def get_regional_summary(db: Session = Depends(get_db)):
    rows = db.execute(
        text("SELECT * FROM analytics.regional_summary")
    ).mappings().all()
    return [dict(r) for r in rows]

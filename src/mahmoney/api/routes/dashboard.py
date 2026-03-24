from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mahmoney.api.deps import get_db
from mahmoney.models.enums import ExpenseStatus
from mahmoney.models.expense import Expense
from mahmoney.schemas.expense import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_summary(
    year: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> DashboardSummary:
    base = select(Expense)
    if year:
        base = base.where(extract("year", Expense.date) == year)

    # Total count and amount
    totals_q = select(
        func.count(Expense.id),
        func.coalesce(func.sum(Expense.total_amount), Decimal(0)),
    )
    if year:
        totals_q = totals_q.where(extract("year", Expense.date) == year)
    totals = (await db.execute(totals_q)).one()
    total_expenses = totals[0]
    total_amount_eur = totals[1]

    # By category
    cat_q = (
        select(Expense.category, func.sum(Expense.total_amount))
        .group_by(Expense.category)
    )
    if year:
        cat_q = cat_q.where(extract("year", Expense.date) == year)
    cat_result = await db.execute(cat_q)
    by_category = {row[0]: row[1] or Decimal(0) for row in cat_result.all()}

    # By month
    month_q = (
        select(
            func.to_char(Expense.date, "YYYY-MM"),
            func.sum(Expense.total_amount),
        )
        .group_by(func.to_char(Expense.date, "YYYY-MM"))
        .order_by(func.to_char(Expense.date, "YYYY-MM"))
    )
    if year:
        month_q = month_q.where(extract("year", Expense.date) == year)
    month_result = await db.execute(month_q)
    by_month = {row[0]: row[1] or Decimal(0) for row in month_result.all()}

    # By status
    status_q = select(
        Expense.status,
        func.count(Expense.id),
    ).group_by(Expense.status)
    if year:
        status_q = status_q.where(extract("year", Expense.date) == year)
    status_result = await db.execute(status_q)
    by_status = {row[0]: row[1] for row in status_result.all()}

    # Pending review count
    pending_q = select(func.count(Expense.id)).where(
        Expense.status == ExpenseStatus.PENDING_REVIEW
    )
    if year:
        pending_q = pending_q.where(extract("year", Expense.date) == year)
    pending_count = (await db.execute(pending_q)).scalar_one()

    return DashboardSummary(
        total_expenses=total_expenses,
        total_amount_eur=total_amount_eur,
        by_category=by_category,
        by_month=by_month,
        by_status=by_status,
        pending_review_count=pending_count,
    )

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mahmoney.api.deps import get_db
from mahmoney.models.enums import ExpenseStatus
from mahmoney.models.expense import Expense

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

router = APIRouter(tags=["ui"])


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    # Summary stats
    total_q = select(func.count(Expense.id))
    total = (await db.execute(total_q)).scalar_one()

    pending_q = select(func.count(Expense.id)).where(
        Expense.status == ExpenseStatus.PENDING_REVIEW
    )
    pending = (await db.execute(pending_q)).scalar_one()

    sum_q = select(func.coalesce(func.sum(Expense.total_amount), 0))
    total_amount = (await db.execute(sum_q)).scalar_one()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "total_expenses": total,
            "pending_review": pending,
            "total_amount": total_amount,
        },
    )


@router.get("/expenses", response_class=HTMLResponse)
async def expenses_page(
    request: Request,
    status: str | None = None,
    category: str | None = None,
    page: int = 1,
    db: AsyncSession = Depends(get_db),
):
    query = select(Expense)
    if status:
        query = query.where(Expense.status == status)
    if category:
        query = query.where(Expense.category == category)

    per_page = 50
    offset = (page - 1) * per_page
    query = query.order_by(Expense.date.desc()).offset(offset).limit(per_page)

    result = await db.execute(query)
    expenses = result.scalars().all()

    count_q = select(func.count(Expense.id))
    if status:
        count_q = count_q.where(Expense.status == status)
    if category:
        count_q = count_q.where(Expense.category == category)
    total = (await db.execute(count_q)).scalar_one()

    return templates.TemplateResponse(
        "expenses.html",
        {
            "request": request,
            "expenses": expenses,
            "total": total,
            "page": page,
            "per_page": per_page,
            "status_filter": status or "",
            "category_filter": category or "",
        },
    )

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from mahmoney.api.deps import get_db
from mahmoney.models.expense import Expense
from mahmoney.schemas.expense import BulkImportResponse
from mahmoney.services.csv_parser import parse_csv

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/csv", response_model=BulkImportResponse)
async def import_csv(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
) -> BulkImportResponse:
    content = (await file.read()).decode("utf-8")
    filename = file.filename or "unknown.csv"

    expenses, errors = parse_csv(content, filename)

    for expense_data in expenses:
        expense = Expense(**expense_data.model_dump())
        db.add(expense)

    await db.commit()

    return BulkImportResponse(imported=len(expenses), errors=errors)

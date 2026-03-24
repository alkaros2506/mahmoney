import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mahmoney.api.deps import get_db
from mahmoney.models.enums import Category, ExpenseStatus, Source
from mahmoney.models.expense import Expense
from mahmoney.schemas.expense import (
    ExpenseCreate,
    ExpenseListResponse,
    ExpenseResponse,
    ExpenseUpdate,
)
from mahmoney.services.ocr import process_receipt
from mahmoney.services.storage import save_file

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("", response_model=ExpenseListResponse)
async def list_expenses(
    status: ExpenseStatus | None = None,
    category: Category | None = None,
    source: Source | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    per_page: int = 50,
    db: AsyncSession = Depends(get_db),
) -> ExpenseListResponse:
    query = select(Expense)
    count_query = select(func.count(Expense.id))

    if status:
        query = query.where(Expense.status == status)
        count_query = count_query.where(Expense.status == status)
    if category:
        query = query.where(Expense.category == category)
        count_query = count_query.where(Expense.category == category)
    if source:
        query = query.where(Expense.source == source)
        count_query = count_query.where(Expense.source == source)
    if date_from:
        query = query.where(Expense.date >= date_from)
        count_query = count_query.where(Expense.date >= date_from)
    if date_to:
        query = query.where(Expense.date <= date_to)
        count_query = count_query.where(Expense.date <= date_to)

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * per_page
    query = query.order_by(Expense.date.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    items = [ExpenseResponse.model_validate(row) for row in result.scalars().all()]

    return ExpenseListResponse(items=items, total=total, page=page, per_page=per_page)


@router.post("", response_model=ExpenseResponse, status_code=201)
async def create_expense(
    data: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
) -> ExpenseResponse:
    expense = Expense(**data.model_dump())
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return ExpenseResponse.model_validate(expense)


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ExpenseResponse:
    expense = await db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return ExpenseResponse.model_validate(expense)


@router.patch("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: uuid.UUID,
    data: ExpenseUpdate,
    db: AsyncSession = Depends(get_db),
) -> ExpenseResponse:
    expense = await db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(expense, field, value)

    await db.commit()
    await db.refresh(expense)
    return ExpenseResponse.model_validate(expense)


@router.delete("/{expense_id}", status_code=204)
async def delete_expense(
    expense_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    expense = await db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    await db.delete(expense)
    await db.commit()


@router.post("/{expense_id}/approve", response_model=ExpenseResponse)
async def approve_expense(
    expense_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ExpenseResponse:
    expense = await db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    expense.status = ExpenseStatus.APPROVED
    await db.commit()
    await db.refresh(expense)
    return ExpenseResponse.model_validate(expense)


@router.post("/{expense_id}/receipt", response_model=ExpenseResponse)
async def upload_receipt(
    expense_id: uuid.UUID,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
) -> ExpenseResponse:
    expense = await db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    contents = await file.read()
    file_path = await save_file(contents, file.filename or "receipt.jpg")
    expense.receipt_image_path = str(file_path)

    ocr_result = await process_receipt(contents)
    if ocr_result:
        expense.ocr_raw_response = ocr_result.model_dump()
        expense.ocr_confidence = ocr_result.confidence
        # Fill in missing fields from OCR
        if not expense.supplier_name and ocr_result.supplier_name:
            expense.supplier_name = ocr_result.supplier_name
        if not expense.supplier_afm and ocr_result.supplier_afm:
            expense.supplier_afm = ocr_result.supplier_afm
        if ocr_result.total_amount:
            expense.total_amount = ocr_result.total_amount
        if ocr_result.net_amount:
            expense.net_amount = ocr_result.net_amount
        if ocr_result.vat_amount:
            expense.vat_amount = ocr_result.vat_amount
        if ocr_result.mark_number:
            expense.mark_number = ocr_result.mark_number

    await db.commit()
    await db.refresh(expense)
    return ExpenseResponse.model_validate(expense)

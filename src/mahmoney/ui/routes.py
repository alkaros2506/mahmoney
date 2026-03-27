import contextlib
import json
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mahmoney.api.deps import get_db
from mahmoney.auth import create_session, destroy_session, is_authenticated
from mahmoney.config import get_settings
from mahmoney.models.enums import ExpenseStatus, Source
from mahmoney.models.expense import Expense
from mahmoney.services.ocr import process_receipt
from mahmoney.services.storage import save_file

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

router = APIRouter(tags=["ui"])


# --- Auth routes ---


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if is_authenticated(request):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request):
    form = await request.form()
    password = form.get("password", "")
    settings = get_settings()

    if password == settings.auth_password:
        response = RedirectResponse(url="/", status_code=302)
        create_session(response)
        return response

    return templates.TemplateResponse(
        "login.html", {"request": request, "error": "Invalid password"}, status_code=401
    )


@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=302)
    destroy_session(request, response)
    return response


# --- Dashboard ---


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    total_q = select(func.count(Expense.id))
    total = (await db.execute(total_q)).scalar_one()

    pending_q = select(func.count(Expense.id)).where(Expense.status == ExpenseStatus.PENDING_REVIEW)
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


# --- Expenses list ---


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


# --- Receipt image serving ---


@router.get("/receipts/{path:path}")
async def serve_receipt(path: str):
    settings = get_settings()
    file_path = settings.storage_path / path
    if not file_path.is_file():
        return JSONResponse({"detail": "Receipt not found"}, status_code=404)
    return FileResponse(file_path)


# --- Quick Scan (ad-hoc) ---


@router.get("/scan", response_class=HTMLResponse)
async def scan_page(request: Request):
    return templates.TemplateResponse("scan.html", {"request": request})


@router.post("/scan/analyze")
async def scan_analyze(file: UploadFile):
    contents = await file.read()

    # Save the file
    file_path = await save_file(contents, file.filename or "receipt.jpg")

    # Run OCR
    ocr_result = await process_receipt(contents)

    response: dict = {"receipt_path": str(file_path)}
    if ocr_result:
        response["ocr"] = ocr_result.model_dump(mode="json")
    else:
        response["ocr"] = None
        response["warning"] = "OCR not available or failed. Fill in fields manually."

    return JSONResponse(response)


@router.post("/scan/save")
async def scan_save(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.json()

    date_str = body.get("date")
    if date_str:
        try:
            parsed_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            parsed_date = datetime.now(tz=UTC)
    else:
        parsed_date = datetime.now(tz=UTC)

    expense = Expense(
        supplier_name=body.get("supplier_name", "Unknown"),
        supplier_afm=body.get("supplier_afm"),
        supplier_country=body.get("supplier_country", "GR"),
        invoice_number=body.get("invoice_number"),
        date=parsed_date,
        net_amount=body.get("net_amount"),
        vat_amount=body.get("vat_amount"),
        vat_rate=body.get("vat_rate"),
        total_amount=body.get("total_amount", 0),
        currency=body.get("currency", "EUR"),
        payment_method=body.get("payment_method", "card"),
        category=body.get("category", "other"),
        mark_number=body.get("mark_number"),
        source=Source.MANUAL,
        receipt_image_path=body.get("receipt_path"),
        notes=body.get("notes"),
        status=ExpenseStatus.PENDING_REVIEW,
    )

    ocr_raw = body.get("ocr_raw")
    if ocr_raw:
        with contextlib.suppress(json.JSONDecodeError, TypeError):
            expense.ocr_raw_response = json.loads(ocr_raw) if isinstance(ocr_raw, str) else ocr_raw

    ocr_conf = body.get("ocr_confidence")
    if ocr_conf is not None:
        expense.ocr_confidence = ocr_conf

    db.add(expense)
    await db.commit()
    await db.refresh(expense)

    return JSONResponse({"id": str(expense.id), "status": "saved"})

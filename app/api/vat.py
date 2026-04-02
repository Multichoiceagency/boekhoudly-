import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.vat_report import VATReport, VATStatus
from app.schemas.vat import VATCalculation, VATReportResponse
from app.services.vat_service import VATService
from app.utils.auth import get_current_user

router = APIRouter(prefix="/vat", tags=["BTW"])


@router.post("/calculate", response_model=VATCalculation)
async def calculate_vat(
    period: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bereken BTW voor een opgegeven periode (bijv. '2026-Q1')."""
    vat_service = VATService(db)
    calculation = await vat_service.calculate_vat(current_user.company_id, period)
    return calculation


@router.get("/reports", response_model=list[VATReportResponse])
async def list_vat_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Haal alle BTW aangiftes op."""
    result = await db.execute(
        select(VATReport)
        .where(VATReport.company_id == current_user.company_id)
        .order_by(VATReport.created_at.desc())
    )
    return result.scalars().all()


@router.get("/reports/{report_id}", response_model=VATReportResponse)
async def get_vat_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Haal een specifieke BTW aangifte op."""
    result = await db.execute(
        select(VATReport).where(
            VATReport.id == report_id,
            VATReport.company_id == current_user.company_id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="BTW aangifte niet gevonden")
    return report


@router.post("/reports/{report_id}/submit", response_model=VATReportResponse)
async def submit_vat_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dien een BTW aangifte in."""
    result = await db.execute(
        select(VATReport).where(
            VATReport.id == report_id,
            VATReport.company_id == current_user.company_id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="BTW aangifte niet gevonden")
    if report.status != VATStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Alleen concept-aangiftes kunnen worden ingediend")

    report.status = VATStatus.SUBMITTED
    await db.flush()
    return report

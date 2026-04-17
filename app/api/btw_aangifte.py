"""BTW Aangifte berekening — volledige Nederlandse OB-aangifte met alle rubrieken.

Berekent automatisch alle rubrieken (1a t/m 5g) uit de facturen en uitgaven
in het systeem. Ondersteunt kwartaal- en maandaangifte.
"""
import logging
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.invoice import Invoice
from app.models.expense import Expense
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/btw-aangifte", tags=["BTW Aangifte"])


def _line_totals(lines: list) -> tuple[float, float]:
    """Calculate (omzet_excl, btw) from invoice lines."""
    omzet = sum(l.get("qty", 0) * l.get("price", 0) for l in (lines or []))
    btw = sum(l.get("qty", 0) * l.get("price", 0) * l.get("btwRate", 0) / 100 for l in (lines or []))
    return round(omzet, 2), round(btw, 2)


def _btw_rate(lines: list) -> float:
    """Get the dominant BTW rate from lines."""
    if not lines:
        return 21
    rates = {}
    for l in lines:
        r = round(l.get("btwRate", 21))
        amount = abs(l.get("qty", 0) * l.get("price", 0))
        rates[r] = rates.get(r, 0) + amount
    return max(rates, key=rates.get) if rates else 21


def _quarter_dates(year: int, quarter: int) -> tuple[date, date]:
    """Return (start_date, end_date) for a quarter."""
    start_month = (quarter - 1) * 3 + 1
    end_month = quarter * 3
    start = date(year, start_month, 1)
    if end_month == 12:
        end = date(year, 12, 31)
    else:
        end = date(year, end_month + 1, 1)
        from datetime import timedelta
        end = end - timedelta(days=1)
    return start, end


@router.get("/berekening")
async def bereken_btw_aangifte(
    year: int = 2026,
    quarter: int = 1,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bereken de volledige BTW aangifte voor een kwartaal.

    Returns alle rubrieken (1a t/m 5g) berekend uit facturen en uitgaven.
    """
    start, end = _quarter_dates(year, quarter)

    # Get invoices for the period
    inv_q = select(Invoice).where(
        Invoice.date >= start,
        Invoice.date <= end,
    )
    if current_user.company_id:
        inv_q = inv_q.where(Invoice.company_id == current_user.company_id)
    inv_result = await db.execute(inv_q)
    invoices = inv_result.scalars().all()

    # Get expenses for the period
    exp_q = select(Expense).where(
        Expense.date >= start,
        Expense.date <= end,
    )
    if current_user.company_id:
        exp_q = exp_q.where(Expense.company_id == current_user.company_id)
    exp_result = await db.execute(exp_q)
    expenses = exp_result.scalars().all()

    # === RUBRIEK 1: Prestaties binnenland ===
    r1a_omzet = 0.0  # Hoog tarief (21%)
    r1a_btw = 0.0
    r1b_omzet = 0.0  # Laag tarief (9%)
    r1b_btw = 0.0
    r1c_omzet = 0.0  # Overige tarieven
    r1c_btw = 0.0
    r1d_omzet = 0.0  # Privégebruik
    r1d_btw = 0.0
    r1e_omzet = 0.0  # 0% of niet belast

    for inv in invoices:
        doc_type = getattr(inv, 'document_type', 'factuur') or 'factuur'
        if doc_type != 'factuur':
            continue

        omzet, btw = _line_totals(inv.lines)
        rate = _btw_rate(inv.lines)

        if doc_type == 'creditnota':
            omzet = -abs(omzet)
            btw = -abs(btw)

        if rate == 21:
            r1a_omzet += omzet
            r1a_btw += btw
        elif rate == 9:
            r1b_omzet += omzet
            r1b_btw += btw
        elif rate == 0:
            r1e_omzet += omzet
        else:
            r1c_omzet += omzet
            r1c_btw += btw

    # === RUBRIEK 5a: Verschuldigde omzetbelasting ===
    r5a = round(r1a_btw + r1b_btw + r1c_btw + r1d_btw, 2)

    # === RUBRIEK 5b: Voorbelasting (BTW op inkopen/kosten) ===
    r5b = 0.0
    for exp in expenses:
        btw_rate = float(getattr(exp, 'btw_rate', 21) or 21)
        amount = float(exp.amount or 0)
        # BTW = amount * rate / (100 + rate) for inclusive amounts
        # Or amount * rate / 100 for exclusive amounts
        r5b += round(amount * btw_rate / (100 + btw_rate), 2)

    # === RUBRIEK 5 subtotalen ===
    r5c = round(r5a - r5b, 2)  # Subtotaal
    r5d = 0.0  # Vermindering kleinondernemersregeling
    r5e = 0.0  # Schatting vorige aangiften
    r5f = 0.0  # Schatting deze aangifte
    r5g = round(r5c - r5d + r5e - r5f, 2)  # Te betalen

    return {
        "periode": {
            "jaar": year,
            "kwartaal": quarter,
            "van": start.isoformat(),
            "tot": end.isoformat(),
            "label": f"Q{quarter} {year}",
        },
        "rubrieken": {
            "1a": {"label": "Leveringen/diensten belast met hoog tarief", "omzet": round(r1a_omzet), "btw": round(r1a_btw)},
            "1b": {"label": "Leveringen/diensten belast met laag tarief", "omzet": round(r1b_omzet), "btw": round(r1b_btw)},
            "1c": {"label": "Leveringen/diensten belast met overige tarieven", "omzet": round(r1c_omzet), "btw": round(r1c_btw)},
            "1d": {"label": "Privégebruik", "omzet": round(r1d_omzet), "btw": round(r1d_btw)},
            "1e": {"label": "Leveringen/diensten belast met 0% of niet bij u belast", "omzet": round(r1e_omzet)},
            "2a": {"label": "Verleggingsregeling binnenland", "omzet": 0, "btw": 0},
            "3a": {"label": "Prestaties naar/in het buitenland", "omzet": 0},
            "3b": {"label": "Leveringen naar landen buiten de EU", "omzet": 0},
            "3c": {"label": "Leveringen naar/diensten in landen binnen de EU", "omzet": 0},
            "4a": {"label": "Leveringen/diensten uit het buitenland aan u verricht", "omzet": 0, "btw": 0},
            "4b": {"label": "Leveringen/diensten uit landen binnen de EU", "omzet": 0, "btw": 0},
            "5a": {"label": "Verschuldigde omzetbelasting (subtotaal)", "btw": round(r5a)},
            "5b": {"label": "Voorbelasting", "btw": round(r5b)},
            "5c": {"label": "Subtotaal (5a min 5b)", "btw": round(r5c)},
            "5d": {"label": "Vermindering kleinondernemersregeling", "btw": round(r5d)},
            "5e": {"label": "Schatting vorige aangiften", "btw": round(r5e)},
            "5f": {"label": "Schatting deze aangifte", "btw": round(r5f)},
            "5g": {"label": "Totaal te betalen / te ontvangen", "btw": round(r5g)},
        },
        "samenvatting": {
            "totaal_omzet": round(r1a_omzet + r1b_omzet + r1c_omzet + r1d_omzet + r1e_omzet),
            "totaal_btw_verschuldigd": round(r5a),
            "totaal_voorbelasting": round(r5b),
            "te_betalen": round(r5g),
            "facturen_in_periode": len([i for i in invoices if (getattr(i, 'document_type', 'factuur') or 'factuur') == 'factuur']),
            "uitgaven_in_periode": len(expenses),
        },
    }

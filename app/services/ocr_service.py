import re
import io
import logging
from typing import Any

logger = logging.getLogger(__name__)


class OCRService:
    """Service voor het extraheren van tekst uit documenten via OCR."""

    async def extract_text(self, file_content: bytes, file_type: str) -> str:
        """Extraheer tekst uit een bestand."""
        if file_type == "pdf":
            return await self.extract_from_pdf(file_content)
        elif file_type in ("jpg", "png"):
            return await self.extract_from_image(file_content)
        elif file_type == "csv":
            return file_content.decode("utf-8", errors="replace")
        return ""

    async def extract_from_pdf(self, content: bytes) -> str:
        """Extraheer tekst uit een PDF bestand."""
        try:
            import pytesseract
            from PIL import Image
            # For production: use pdf2image to convert PDF pages, then OCR each
            # For now, attempt basic text extraction
            logger.info("PDF OCR verwerking gestart")
            return "PDF tekst extractie placeholder - integreer pdf2image voor productie"
        except ImportError:
            logger.warning("pytesseract niet beschikbaar")
            return ""

    async def extract_from_image(self, content: bytes) -> str:
        """Extraheer tekst uit een afbeelding via OCR."""
        try:
            import pytesseract
            from PIL import Image

            image = Image.open(io.BytesIO(content))
            text = pytesseract.image_to_string(image, lang="nld")
            return text
        except ImportError:
            logger.warning("pytesseract niet beschikbaar")
            return ""

    def parse_invoice_data(self, text: str) -> dict[str, Any]:
        """Parse factuurgegevens uit geëxtraheerde tekst."""
        data: dict[str, Any] = {
            "date": None,
            "amount": None,
            "btw_amount": None,
            "vendor": None,
            "invoice_number": None,
        }

        # Datumpatronen: DD-MM-YYYY, DD/MM/YYYY
        date_pattern = r"(\d{2}[-/]\d{2}[-/]\d{4})"
        date_match = re.search(date_pattern, text)
        if date_match:
            data["date"] = date_match.group(1)

        # Bedragpatronen: €1.234,56 of EUR 1234.56
        amount_patterns = [
            r"[€]\s*([\d.,]+)",
            r"EUR\s*([\d.,]+)",
            r"totaal[:\s]*([\d.,]+)",
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(".", "").replace(",", ".")
                try:
                    data["amount"] = float(amount_str)
                except ValueError:
                    pass
                break

        # BTW bedrag
        btw_patterns = [r"BTW[:\s]*([\d.,]+)", r"btw[:\s]*[€]?\s*([\d.,]+)"]
        for pattern in btw_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                btw_str = match.group(1).replace(".", "").replace(",", ".")
                try:
                    data["btw_amount"] = float(btw_str)
                except ValueError:
                    pass
                break

        # Factuurnummer
        inv_patterns = [
            r"factuurnummer[:\s]*([A-Za-z0-9-]+)",
            r"factuur\s*nr[.:\s]*([A-Za-z0-9-]+)",
            r"invoice[:\s]*([A-Za-z0-9-]+)",
        ]
        for pattern in inv_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data["invoice_number"] = match.group(1).strip()
                break

        return data

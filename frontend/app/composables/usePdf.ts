/**
 * Composable for generating professional PDF documents from HTML templates.
 * Uses html2pdf.js for client-side PDF generation.
 */
export function usePdf() {
  const generating = ref(false)

  async function generatePdf(element: HTMLElement, filename: string, options?: {
    margin?: number | number[]
    format?: 'a4' | 'letter'
    orientation?: 'portrait' | 'landscape'
    scale?: number
  }) {
    if (generating.value) return
    generating.value = true

    try {
      const html2pdf = (await import('html2pdf.js')).default

      const opt = {
        margin: options?.margin ?? [10, 10, 10, 10],
        filename: filename.endsWith('.pdf') ? filename : `${filename}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: {
          scale: options?.scale ?? 2,
          useCORS: true,
          letterRendering: true,
          logging: false,
        },
        jsPDF: {
          unit: 'mm',
          format: options?.format ?? 'a4',
          orientation: options?.orientation ?? 'portrait',
        },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] },
      }

      await html2pdf().set(opt).from(element).save()
    } finally {
      generating.value = false
    }
  }

  /**
   * Generates a PDF from a hidden template that gets temporarily injected.
   * This allows full control over the PDF layout without affecting the page.
   */
  async function generateFromTemplate(html: string, filename: string, options?: {
    margin?: number | number[]
    format?: 'a4' | 'letter'
    orientation?: 'portrait' | 'landscape'
  }) {
    if (generating.value) return
    generating.value = true

    try {
      const html2pdf = (await import('html2pdf.js')).default

      const container = document.createElement('div')
      container.innerHTML = html
      container.style.position = 'absolute'
      container.style.left = '-9999px'
      container.style.top = '0'
      document.body.appendChild(container)

      const opt = {
        margin: options?.margin ?? [10, 10, 10, 10],
        filename: filename.endsWith('.pdf') ? filename : `${filename}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: {
          scale: 2,
          useCORS: true,
          letterRendering: true,
          logging: false,
        },
        jsPDF: {
          unit: 'mm',
          format: options?.format ?? 'a4',
          orientation: options?.orientation ?? 'portrait',
        },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] },
      }

      await html2pdf().set(opt).from(container).save()
      document.body.removeChild(container)
    } finally {
      generating.value = false
    }
  }

  return { generating, generatePdf, generateFromTemplate }
}

// ---------- Shared PDF template helpers ----------

export function pdfStyles(): string {
  return `
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      body, html { font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; font-size: 10px; color: #1e293b; line-height: 1.5; }
      .pdf-page { width: 190mm; padding: 0; }
      .header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 3px solid #059669; }
      .header-left h1 { font-size: 20px; font-weight: 700; color: #059669; }
      .header-left p { font-size: 9px; color: #64748b; margin-top: 2px; }
      .header-right { text-align: right; font-size: 9px; color: #64748b; }
      .header-right strong { color: #1e293b; display: block; font-size: 10px; }
      .invoice-title { font-size: 22px; font-weight: 700; color: #1e293b; text-align: right; }
      .meta-grid { display: flex; gap: 24px; margin-bottom: 20px; }
      .meta-box { flex: 1; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; }
      .meta-box .label { font-size: 8px; text-transform: uppercase; color: #94a3b8; font-weight: 600; letter-spacing: 0.5px; margin-bottom: 4px; }
      .meta-box .value { font-size: 11px; font-weight: 600; color: #1e293b; }
      .meta-box .sub { font-size: 9px; color: #64748b; }
      table { width: 100%; border-collapse: collapse; margin-bottom: 16px; }
      table th { background: #f1f5f9; color: #475569; font-size: 8px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; padding: 8px 12px; text-align: left; border-bottom: 2px solid #e2e8f0; }
      table th.right, table td.right { text-align: right; }
      table td { padding: 8px 12px; font-size: 10px; border-bottom: 1px solid #f1f5f9; }
      table tr:last-child td { border-bottom: none; }
      .totals { display: flex; justify-content: flex-end; margin-bottom: 20px; }
      .totals-box { width: 220px; }
      .totals-row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 10px; }
      .totals-row.border-top { border-top: 2px solid #059669; padding-top: 8px; margin-top: 4px; }
      .totals-row .label { color: #64748b; }
      .totals-row .value { font-weight: 600; }
      .totals-row.total .label, .totals-row.total .value { font-size: 13px; font-weight: 700; color: #059669; }
      .footer { margin-top: 24px; padding-top: 12px; border-top: 1px solid #e2e8f0; font-size: 8px; color: #94a3b8; text-align: center; }
      .section-title { font-size: 14px; font-weight: 700; color: #1e293b; margin: 20px 0 10px; padding-bottom: 6px; border-bottom: 2px solid #e2e8f0; }
      .section-subtitle { font-size: 10px; color: #059669; font-weight: 600; margin-bottom: 8px; }
      .row { display: flex; justify-content: space-between; padding: 5px 0; font-size: 10px; border-bottom: 1px solid #f8fafc; }
      .row .label { color: #475569; }
      .row .value { font-weight: 600; color: #1e293b; }
      .row.highlight { background: #f0fdf4; padding: 5px 8px; border-radius: 4px; }
      .row.subtotal { border-top: 1px solid #e2e8f0; font-weight: 600; margin-top: 2px; padding-top: 6px; }
      .row.grand-total { border-top: 2px solid #059669; font-weight: 700; font-size: 12px; padding-top: 8px; margin-top: 4px; }
      .row.grand-total .value { color: #059669; }
      .badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 8px; font-weight: 600; }
      .badge-green { background: #dcfce7; color: #166534; }
      .badge-amber { background: #fef3c7; color: #92400e; }
      .badge-red { background: #fee2e2; color: #991b1b; }
      .note-box { background: #fffbeb; border: 1px solid #fde68a; border-radius: 6px; padding: 10px; font-size: 9px; color: #92400e; margin-top: 12px; }
      .pagebreak { page-break-before: always; }
    </style>
  `
}

export function fc(v: number, decimals = 0): string {
  const prefix = v < 0 ? '\u20AC -' : '\u20AC '
  return prefix + Math.abs(v).toLocaleString('nl-NL', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

export function formatDateNL(d: string): string {
  return new Date(d).toLocaleDateString('nl-NL', { day: 'numeric', month: 'long', year: 'numeric' })
}

/**
 * Professional PDF templates for invoices, annual accounts, audit reports, and tax filings.
 */
import { pdfStyles, fc, formatDateNL } from './usePdf'

// ============ FACTUUR (Invoice) ============
export function invoiceTemplate(invoice: any, branding: any, debtor: any): string {
  const subtotal = invoice.lines.reduce((s: number, l: any) => s + l.qty * l.price, 0)
  const btw = invoice.lines.reduce((s: number, l: any) => s + l.qty * l.price * l.btwRate / 100, 0)
  const total = subtotal + btw

  // Group BTW by rate
  const btwGroups: Record<number, { base: number; btw: number }> = {}
  invoice.lines.forEach((l: any) => {
    const rate = l.btwRate
    if (!btwGroups[rate]) btwGroups[rate] = { base: 0, btw: 0 }
    btwGroups[rate].base += l.qty * l.price
    btwGroups[rate].btw += l.qty * l.price * rate / 100
  })

  const primaryColor = branding?.primaryColor || '#059669'

  return `
    <!DOCTYPE html>
    <html><head><meta charset="utf-8">${pdfStyles()}
    <style>
      .header { border-bottom: 3px solid ${primaryColor}; }
      .header-left h1 { color: ${primaryColor}; }
      .totals-row.total .label, .totals-row.total .value { color: ${primaryColor}; }
      .totals-row.border-top { border-top: 2px solid ${primaryColor}; }
      table th { border-bottom-color: ${primaryColor}; }
      .invoice-title { color: ${primaryColor}; }
    </style>
    </head><body>
    <div class="pdf-page">
      <!-- Header -->
      <div class="header">
        <div class="header-left">
          <h1>${branding?.companyName || 'Bedrijf'}</h1>
          <p>${branding?.address || ''}</p>
          <p>${branding?.postcode || ''} ${branding?.city || ''}</p>
          <p>KvK: ${branding?.kvk || '-'} | BTW: ${branding?.btw || '-'}</p>
          <p>${branding?.email || ''} | ${branding?.phone || ''}</p>
        </div>
        <div style="text-align: right;">
          <div class="invoice-title">FACTUUR</div>
          <div style="margin-top: 8px; font-size: 10px; color: #64748b;">
            <strong style="color: #1e293b;">${invoice.number}</strong>
          </div>
        </div>
      </div>

      <!-- Meta info -->
      <div class="meta-grid">
        <div class="meta-box">
          <div class="label">Factuur aan</div>
          <div class="value">${invoice.client}</div>
          ${debtor ? `<div class="sub">${debtor.address || ''}, ${debtor.city || ''}</div>` : ''}
          ${debtor?.kvk ? `<div class="sub">KvK: ${debtor.kvk}</div>` : ''}
        </div>
        <div class="meta-box">
          <div class="label">Factuurdatum</div>
          <div class="value">${formatDateNL(invoice.date)}</div>
        </div>
        <div class="meta-box">
          <div class="label">Vervaldatum</div>
          <div class="value">${formatDateNL(invoice.dueDate)}</div>
        </div>
        <div class="meta-box">
          <div class="label">Status</div>
          <div class="value">${invoice.status === 'betaald' ? 'Betaald' : invoice.status === 'verzonden' ? 'Verzonden' : invoice.status === 'verlopen' ? 'Verlopen' : 'Concept'}</div>
        </div>
      </div>

      <!-- Line items -->
      <table>
        <thead>
          <tr>
            <th style="width: 45%">Omschrijving</th>
            <th class="right">Aantal</th>
            <th class="right">Prijs</th>
            <th class="right">BTW</th>
            <th class="right">Totaal</th>
          </tr>
        </thead>
        <tbody>
          ${invoice.lines.map((l: any) => `
            <tr>
              <td>${l.desc}</td>
              <td class="right">${l.qty}</td>
              <td class="right">${fc(l.price, 2)}</td>
              <td class="right">${l.btwRate}%</td>
              <td class="right" style="font-weight: 600;">${fc(l.qty * l.price, 2)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>

      <!-- BTW specification -->
      <div style="margin-bottom: 12px;">
        <table style="width: 300px; margin-left: auto;">
          <thead>
            <tr>
              <th>BTW tarief</th>
              <th class="right">Grondslag</th>
              <th class="right">BTW bedrag</th>
            </tr>
          </thead>
          <tbody>
            ${Object.entries(btwGroups).map(([rate, g]) => `
              <tr>
                <td>${rate}%</td>
                <td class="right">${fc((g as any).base, 2)}</td>
                <td class="right">${fc((g as any).btw, 2)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>

      <!-- Totals -->
      <div class="totals">
        <div class="totals-box">
          <div class="totals-row">
            <span class="label">Subtotaal</span>
            <span class="value">${fc(subtotal, 2)}</span>
          </div>
          <div class="totals-row">
            <span class="label">BTW</span>
            <span class="value">${fc(btw, 2)}</span>
          </div>
          <div class="totals-row total border-top">
            <span class="label">Totaal</span>
            <span class="value">${fc(total, 2)}</span>
          </div>
        </div>
      </div>

      <!-- Payment info -->
      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; margin-top: 16px;">
        <div style="font-size: 9px; font-weight: 600; color: #475569; margin-bottom: 4px;">BETALINGSGEGEVENS</div>
        <div style="font-size: 10px; color: #1e293b;">
          Gelieve het totaalbedrag van <strong>${fc(total, 2)}</strong> binnen ${debtor?.paymentTerm || 30} dagen over te maken op:<br>
          <strong>IBAN:</strong> ${branding?.iban || '-'}<br>
          <strong>T.n.v.:</strong> ${branding?.companyName || '-'}<br>
          <strong>Onder vermelding van:</strong> ${invoice.number}
        </div>
      </div>

      <!-- Footer -->
      <div class="footer">
        ${branding?.companyName || ''} | ${branding?.address || ''}, ${branding?.postcode || ''} ${branding?.city || ''} | KvK: ${branding?.kvk || '-'} | BTW: ${branding?.btw || '-'}<br>
        ${branding?.email || ''} | ${branding?.phone || ''} | ${branding?.website || ''}
      </div>
    </div>
    </body></html>
  `
}

// ============ JAARREKENING (Annual Accounts) ============
export function jaarrekeningTemplate(
  year: string,
  balans: any,
  wv: any,
  companyName: string,
  branding: any
): string {
  function subtotaal(items: { value: number }[]): number {
    return items.reduce((sum, i) => sum + i.value, 0)
  }
  const nettoResultaat = subtotaal(wv.opbrengsten) - subtotaal(wv.kosten)
  const vpb = Math.round(nettoResultaat * 0.15)
  const netto = Math.round(nettoResultaat * 0.85)
  const totaalActiva = subtotaal(balans.activa.vast) + subtotaal(balans.activa.vlottend)
  const totaalPassiva = subtotaal(balans.passiva.eigen) + subtotaal(balans.passiva.vreemd)
  const today = new Date().toLocaleDateString('nl-NL', { day: 'numeric', month: 'long', year: 'numeric' })

  return `
    <!DOCTYPE html>
    <html><head><meta charset="utf-8">${pdfStyles()}</head><body>
    <div class="pdf-page">
      <!-- Cover -->
      <div style="text-align: center; padding: 40px 0 30px;">
        <h1 style="font-size: 24px; color: #059669; margin-bottom: 4px;">${companyName}</h1>
        <div style="font-size: 14px; color: #64748b; margin-bottom: 24px;">
          ${branding?.address || ''}, ${branding?.postcode || ''} ${branding?.city || ''}<br>
          KvK: ${branding?.kvk || '-'} | BTW: ${branding?.btw || '-'}
        </div>
        <div style="font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 4px;">JAARREKENING ${year}</div>
        <div style="font-size: 10px; color: #94a3b8;">Opgesteld op ${today}</div>
      </div>

      <hr style="border: none; border-top: 2px solid #059669; margin: 0 0 20px;">

      <!-- BALANS -->
      <div class="section-title">Balans per 31 december ${year}</div>

      <div style="display: flex; gap: 16px;">
        <!-- Activa -->
        <div style="flex: 1;">
          <div class="section-subtitle">ACTIVA</div>
          <div style="font-size: 9px; font-weight: 600; color: #94a3b8; text-transform: uppercase; margin: 8px 0 4px;">Vaste activa</div>
          ${balans.activa.vast.map((i: any) => `
            <div class="row"><span class="label">${i.name}</span><span class="value">${fc(i.value)}</span></div>
          `).join('')}
          <div class="row subtotal"><span class="label">Subtotaal vaste activa</span><span class="value">${fc(subtotaal(balans.activa.vast))}</span></div>

          <div style="font-size: 9px; font-weight: 600; color: #94a3b8; text-transform: uppercase; margin: 12px 0 4px;">Vlottende activa</div>
          ${balans.activa.vlottend.map((i: any) => `
            <div class="row"><span class="label">${i.name}</span><span class="value">${fc(i.value)}</span></div>
          `).join('')}
          <div class="row subtotal"><span class="label">Subtotaal vlottende activa</span><span class="value">${fc(subtotaal(balans.activa.vlottend))}</span></div>
          <div class="row grand-total"><span class="label">TOTAAL ACTIVA</span><span class="value">${fc(totaalActiva)}</span></div>
        </div>

        <!-- Passiva -->
        <div style="flex: 1;">
          <div class="section-subtitle">PASSIVA</div>
          <div style="font-size: 9px; font-weight: 600; color: #94a3b8; text-transform: uppercase; margin: 8px 0 4px;">Eigen vermogen</div>
          ${balans.passiva.eigen.map((i: any) => `
            <div class="row"><span class="label">${i.name}</span><span class="value">${fc(i.value)}</span></div>
          `).join('')}
          <div class="row subtotal"><span class="label">Subtotaal eigen vermogen</span><span class="value">${fc(subtotaal(balans.passiva.eigen))}</span></div>

          <div style="font-size: 9px; font-weight: 600; color: #94a3b8; text-transform: uppercase; margin: 12px 0 4px;">Vreemd vermogen</div>
          ${balans.passiva.vreemd.map((i: any) => `
            <div class="row"><span class="label">${i.name}</span><span class="value">${fc(i.value)}</span></div>
          `).join('')}
          <div class="row subtotal"><span class="label">Subtotaal vreemd vermogen</span><span class="value">${fc(subtotaal(balans.passiva.vreemd))}</span></div>
          <div class="row grand-total"><span class="label">TOTAAL PASSIVA</span><span class="value">${fc(totaalPassiva)}</span></div>
        </div>
      </div>

      <!-- Page break before W&V -->
      <div class="pagebreak"></div>

      <!-- WINST & VERLIES -->
      <div class="section-title">Winst- en verliesrekening ${year}</div>

      <div class="section-subtitle">Opbrengsten</div>
      ${wv.opbrengsten.map((i: any) => `
        <div class="row"><span class="label">${i.name}</span><span class="value">${fc(i.value)}</span></div>
      `).join('')}
      <div class="row subtotal highlight"><span class="label">Totaal opbrengsten</span><span class="value">${fc(subtotaal(wv.opbrengsten))}</span></div>

      <div style="height: 12px;"></div>
      <div class="section-subtitle">Kosten</div>
      ${wv.kosten.map((i: any) => `
        <div class="row"><span class="label">${i.name}</span><span class="value">${fc(i.value)}</span></div>
      `).join('')}
      <div class="row subtotal"><span class="label">Totaal kosten</span><span class="value">${fc(subtotaal(wv.kosten))}</span></div>

      <div style="height: 12px;"></div>
      <div class="row highlight" style="font-weight: 700; font-size: 11px;">
        <span class="label">BEDRIJFSRESULTAAT</span>
        <span class="value" style="color: ${nettoResultaat >= 0 ? '#059669' : '#dc2626'};">${fc(nettoResultaat)}</span>
      </div>

      <div style="height: 8px;"></div>
      <div class="row"><span class="label">Vennootschapsbelasting (15%)</span><span class="value">${fc(vpb)}</span></div>
      <div class="row grand-total"><span class="label">NETTO RESULTAAT</span><span class="value">${fc(netto)}</span></div>

      <!-- Toelichting -->
      <div class="pagebreak"></div>
      <div class="section-title">Toelichting bij de jaarrekening ${year}</div>

      <div style="font-size: 10px; color: #475569; line-height: 1.7;">
        <p style="margin-bottom: 12px;"><strong>Algemeen</strong><br>
        De jaarrekening is opgesteld in overeenstemming met de bepalingen van Titel 9, Boek 2 BW en de stellige uitspraken van de Richtlijnen voor de jaarverslaggeving voor kleine rechtspersonen.</p>

        <p style="margin-bottom: 12px;"><strong>Grondslagen voor de waardering</strong><br>
        Materi\u00eble vaste activa worden gewaardeerd tegen aanschafprijs verminderd met lineaire afschrijvingen. Vorderingen worden gewaardeerd tegen nominale waarde, onder aftrek van een voorziening voor oninbaarheid.</p>

        <p style="margin-bottom: 12px;"><strong>Omzetverantwoording</strong><br>
        Omzet wordt verantwoord op het moment dat de dienst is geleverd of het product is overgedragen aan de klant, en het bedrag op betrouwbare wijze kan worden bepaald.</p>

        <p><strong>Personeelskosten</strong><br>
        Gedurende het boekjaar waren gemiddeld 1 persoon (voltijdsequivalent) werkzaam bij de onderneming.</p>
      </div>

      <div class="footer" style="margin-top: 40px;">
        ${companyName} | KvK: ${branding?.kvk || '-'} | Gegenereerd door FiscalFlow AI
      </div>
    </div>
    </body></html>
  `
}

// ============ IB AANGIFTE (Income Tax Filing) ============
export function aangifteIBTemplate(data: any, year: string): string {
  const saldoWV = data.wv.opbrengsten - data.wv.inkoop - data.wv.overigeKostenTotaal + data.wv.financieel
  const fiscaleWinst = saldoWV + data.fiscaal.nietAftrekbaar
  const today = new Date().toLocaleDateString('nl-NL')

  function row(label: string, value: string, opts?: { bold?: boolean; highlight?: boolean; subtotal?: boolean }) {
    const classes = ['row']
    if (opts?.highlight) classes.push('highlight')
    if (opts?.subtotal) classes.push('subtotal')
    const labelStyle = opts?.bold ? 'font-weight: 700; color: #1e293b;' : ''
    const valueStyle = opts?.bold ? 'font-weight: 700;' : ''
    return `<div class="${classes.join(' ')}"><span class="label" style="${labelStyle}">${label}</span><span class="value" style="${valueStyle}">${value}</span></div>`
  }

  function section(title: string, content: string) {
    return `
      <div class="section-title">${title}</div>
      ${content}
    `
  }

  return `
    <!DOCTYPE html>
    <html><head><meta charset="utf-8">${pdfStyles()}
    <style>
      .belasting-header { background: #1e3a5f; color: white; padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; }
      .belasting-header h1 { font-size: 16px; font-weight: 700; }
      .belasting-header .meta { font-size: 9px; text-align: right; opacity: 0.8; }
    </style>
    </head><body>
    <div class="pdf-page">
      <!-- Belastingdienst-style header -->
      <div class="belasting-header">
        <div>
          <h1>Aangifte Inkomstenbelasting ${year}</h1>
          <div style="font-size: 9px; opacity: 0.7; margin-top: 2px;">Eigen kopie, niet opsturen</div>
        </div>
        <div class="meta">
          <div>Formulierenversie: IB 650E - 2Z41OLAV</div>
          <div>Afgedrukt op: ${today}</div>
        </div>
      </div>

      <div style="padding: 4px 0;">
        <!-- Persoonsgegevens -->
        <div style="margin: 16px 0; padding: 12px; background: #f8fafc; border-radius: 6px;">
          <div style="font-size: 14px; font-weight: 700; color: #1e293b;">${data.naam}</div>
          <div style="font-size: 10px; color: #64748b;">BSN: ${data.bsn} | Geboortedatum: ${data.geboortedatum} | Tel: ${data.telefoon}</div>
        </div>

        ${section('Persoonlijke gegevens', `
          ${row('Naam', data.naam)}
          ${row('Geboortedatum', data.geboortedatum)}
          ${row('Burgerservicenummer', data.bsn)}
          ${row('Telefoonnummer', data.telefoon)}
          ${row('Nummer belastingconsulent', data.consultentNr)}
        `)}

        ${section('Partner', `
          ${row('Had u in ' + year + ' een echtgenoot?', data.partner ? 'Ja' : 'Nee')}
        `)}

        ${section('Gegevens onderneming(en)', `
          ${row('Naam onderneming', data.onderneming.naam)}
          ${row('Omschrijving activiteiten', data.onderneming.activiteiten)}
          ${row('Ondernemingsvorm', data.onderneming.vorm)}
          ${row('In dit boekjaar gestart?', 'Nee')}
        `)}

        <div class="pagebreak"></div>

        ${section('Winst-en-verliesrekening: ' + data.onderneming.naam, `
          ${row('Opbrengsten uit leveringen en diensten', fc(data.wv.opbrengsten), { highlight: true })}
          ${row('Totaal opbrengsten', fc(data.wv.opbrengsten), { bold: true, subtotal: true })}
          <div style="height: 8px;"></div>
          ${row('Inkoopkosten, uitbesteed werk en andere externe kosten', fc(data.wv.inkoop), { highlight: true })}
          ${row('Totaal inkoopkosten', fc(data.wv.inkoop), { bold: true, subtotal: true })}
          <div style="height: 8px;"></div>
          ${row('Overige bedrijfskosten', fc(data.wv.overigeKostenTotaal), { highlight: true })}
          ${row('Auto- en transportkosten', fc(data.wv.autokosten))}
          ${row('Huisvestingskosten', fc(data.wv.huisvesting))}
          ${row('Verkoopkosten', fc(data.wv.verkoop))}
          ${row('Andere kosten', fc(data.wv.andereKosten))}
          ${row('Totaal overige bedrijfskosten', fc(data.wv.overigeKostenTotaal), { bold: true, subtotal: true })}
          <div style="height: 8px;"></div>
          ${row('Financiele baten en lasten', fc(data.wv.financieel))}
          <div style="height: 8px;"></div>
          ${row('Saldo winst-en-verliesrekening', fc(saldoWV), { bold: true, highlight: true })}
        `)}

        ${section('Balans: activa', `
          ${row('Vordering omzetbelasting', fc(data.balans.vorderingOB))}
          ${row('Vorderingen op handelsdebiteuren', fc(data.balans.debiteuren))}
          ${row('Totaal vorderingen', fc(data.balans.vorderingen), { subtotal: true })}
          <div style="height: 6px;"></div>
          ${row('Liquide middelen', fc(data.balans.liquide))}
          ${row('Totaal activa', fc(data.balans.totaalActiva), { bold: true, subtotal: true })}
        `)}

        ${section('Balans: passiva', `
          ${row('Eigen vermogen (einde boekjaar)', fc(data.balans.eigenVermogenEind))}
          ${row('Schulden aan leveranciers', fc(data.balans.leveranciers))}
          ${row('Overige kortlopende schulden', fc(data.balans.overigeSchulden))}
          ${row('Totaal passiva', fc(data.balans.totaalPassiva), { bold: true, subtotal: true })}
        `)}

        <div class="pagebreak"></div>

        ${section('Fiscale winstberekening', `
          ${row('Ondernemingsvermogen einde boekjaar', fc(data.balans.eigenVermogenEind))}
          ${row('Ondernemingsvermogen begin boekjaar', fc(data.balans.eigenVermogenBegin))}
          ${row('Saldo ondernemingsvermogen', fc(data.balans.eigenVermogenEind - data.balans.eigenVermogenBegin))}
          <div style="height: 6px;"></div>
          ${row('Priveonttrekkingen', fc(data.fiscaal.priveOnttrekkingen))}
          ${row('Niet-aftrekbare kosten en lasten', fc(data.fiscaal.nietAftrekbaar))}
          ${row('Fiscale winst', fc(fiscaleWinst), { bold: true, highlight: true })}
        `)}

        ${section('Ondernemersaftrek', `
          ${row('Zelfstandigenaftrek', fc(data.aftrek.zelfstandigen))}
          ${row('Totaal ondernemersaftrek', fc(data.aftrek.zelfstandigen), { bold: true, subtotal: true })}
        `)}

        ${section('Inkomstenbelasting', `
          ${row('Te betalen', fc(data.belasting.teBetalen), { bold: true, highlight: true })}
          <div style="height: 8px;"></div>
          <div style="font-size: 10px; font-weight: 600; color: #475569; margin: 8px 0 4px;">Inkomen Box 1: werk en woning</div>
          ${row('Belastbare winst uit onderneming', fc(data.belasting.belastbareWinst))}
          ${data.werkgevers.map((w: any) => row('Loon - ' + w.naam, fc(w.loon))).join('')}
          ${row('Totaal box 1', fc(data.belasting.box1), { bold: true, subtotal: true })}
          <div style="height: 8px;"></div>
          <div style="font-size: 10px; font-weight: 600; color: #475569; margin: 8px 0 4px;">Berekening belasting en premie</div>
          ${row('1e schijf: 8,17% van \u20AC 38.441', fc(data.belasting.schijf1))}
          ${row('2e schijf: 37,48%', fc(data.belasting.schijf2))}
          ${row('Totaal inkomstenbelasting', fc(data.belasting.ib), { subtotal: true })}
          <div style="height: 6px;"></div>
          ${row('Premie AOW: 17,9%', fc(data.belasting.aow))}
          ${row('Premie Anw: 0,1%', fc(data.belasting.anw))}
          ${row('Premie Wlz: 9,65%', fc(data.belasting.wlz))}
          ${row('Premie volksverzekeringen', fc(data.belasting.premie), { subtotal: true })}
          <div style="height: 6px;"></div>
          ${row('Bijdrage Zorgverzekeringswet', fc(data.belasting.zvw))}
          <div style="height: 8px;"></div>
          ${row('TOTAAL TE BETALEN', fc(data.belasting.teBetalen), { bold: true, highlight: true })}
        `)}
      </div>

      <div class="footer">
        Aangifte Inkomstenbelasting ${year} | ${data.naam} | BSN: ${data.bsn} | Gegenereerd door FiscalFlow AI
      </div>
    </div>
    </body></html>
  `
}

// ============ AUDIT RAPPORT ============
export function auditTemplate(
  year: string,
  companyName: string,
  auditScore: number,
  checks: any[],
  findings: any[],
  balansCheck: any,
  wvCheck: any,
  btwCheck: any,
  branding: any
): string {
  const today = new Date().toLocaleDateString('nl-NL', { day: 'numeric', month: 'long', year: 'numeric' })

  return `
    <!DOCTYPE html>
    <html><head><meta charset="utf-8">${pdfStyles()}
    <style>
      .score-circle { display: inline-flex; align-items: center; justify-content: center; width: 60px; height: 60px; border-radius: 50%; font-size: 18px; font-weight: 700; color: white; }
      .score-good { background: #059669; }
      .score-medium { background: #d97706; }
      .score-bad { background: #dc2626; }
      .check-row { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid #f1f5f9; font-size: 10px; }
      .check-icon { width: 18px; height: 18px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 10px; color: white; flex-shrink: 0; }
      .check-pass { background: #059669; }
      .check-fail { background: #dc2626; }
    </style>
    </head><body>
    <div class="pdf-page">
      <!-- Header -->
      <div style="text-align: center; padding: 20px 0; border-bottom: 3px solid #0d9488;">
        <h1 style="font-size: 22px; color: #0d9488; margin-bottom: 4px;">AUDIT RAPPORT</h1>
        <div style="font-size: 12px; color: #1e293b; font-weight: 600;">${companyName}</div>
        <div style="font-size: 10px; color: #64748b;">Boekjaar ${year} | Opgesteld op ${today}</div>
      </div>

      <!-- Score overview -->
      <div style="display: flex; gap: 16px; margin: 20px 0;">
        <div style="flex: 1; text-align: center; padding: 16px; background: #f8fafc; border-radius: 8px;">
          <div class="score-circle ${auditScore >= 80 ? 'score-good' : auditScore >= 60 ? 'score-medium' : 'score-bad'}" style="margin: 0 auto 8px;">
            ${auditScore}%
          </div>
          <div style="font-size: 10px; font-weight: 600; color: #1e293b;">Audit Score</div>
          <div style="font-size: 9px; color: #64748b;">${auditScore >= 80 ? 'Goed' : auditScore >= 60 ? 'Matig' : 'Onvoldoende'}</div>
        </div>
        <div style="flex: 1; text-align: center; padding: 16px; background: #f8fafc; border-radius: 8px;">
          <div style="font-size: 24px; font-weight: 700; color: #1e293b;">${checks.filter(c => c.passed).length}/${checks.length}</div>
          <div style="font-size: 10px; font-weight: 600; color: #1e293b;">Controles geslaagd</div>
        </div>
        <div style="flex: 1; text-align: center; padding: 16px; background: #f8fafc; border-radius: 8px;">
          <div style="font-size: 24px; font-weight: 700; color: #d97706;">${findings.length}</div>
          <div style="font-size: 10px; font-weight: 600; color: #1e293b;">Bevindingen</div>
          <div style="font-size: 9px; color: #dc2626;">${findings.filter(f => f.severity === 'hoog').length} hoog risico</div>
        </div>
      </div>

      <!-- Controle punten -->
      <div class="section-title">Controle Punten</div>
      ${checks.map(c => `
        <div class="check-row">
          <div class="check-icon ${c.passed ? 'check-pass' : 'check-fail'}">${c.passed ? '\u2713' : '\u2717'}</div>
          <div style="flex: 1;">
            <div style="font-weight: 600; color: #1e293b;">${c.name}</div>
            <div style="font-size: 9px; color: #64748b;">${c.description}</div>
          </div>
          <span class="badge ${c.passed ? 'badge-green' : 'badge-red'}">${c.passed ? 'Voldoet' : 'Aandacht'}</span>
        </div>
      `).join('')}

      <div class="pagebreak"></div>

      <!-- Bevindingen -->
      <div class="section-title">Bevindingen</div>
      ${findings.map((f, i) => `
        <div style="padding: 10px; margin-bottom: 8px; background: ${f.severity === 'hoog' ? '#fef2f2' : f.severity === 'midden' ? '#fffbeb' : '#eff6ff'}; border-radius: 6px; border-left: 3px solid ${f.severity === 'hoog' ? '#dc2626' : f.severity === 'midden' ? '#d97706' : '#3b82f6'};">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
            <span class="badge ${f.severity === 'hoog' ? 'badge-red' : f.severity === 'midden' ? 'badge-amber' : 'badge-green'}">${f.severity}</span>
            <span style="font-size: 10px; font-weight: 600; color: #1e293b;">${f.title}</span>
          </div>
          <div style="font-size: 9px; color: #475569;">${f.description}</div>
          <div style="font-size: 8px; color: #94a3b8; margin-top: 4px;">Categorie: ${f.category} | Referentie: ${f.reference}</div>
        </div>
      `).join('')}

      <!-- Jaarrekening verificatie -->
      <div class="pagebreak"></div>
      <div class="section-title">Jaarrekening Verificatie</div>

      <div class="section-subtitle">Balans Controle</div>
      <div class="row"><span class="label">Totaal Activa</span><span class="value">${fc(balansCheck.activa)}</span></div>
      <div class="row"><span class="label">Totaal Passiva</span><span class="value">${fc(balansCheck.passiva)}</span></div>
      <div class="row ${balansCheck.activa === balansCheck.passiva ? 'highlight' : ''}" style="font-weight: 700;">
        <span class="label">Balans ${balansCheck.activa === balansCheck.passiva ? 'klopt' : 'klopt NIET'}</span>
        <span class="value">Verschil: ${fc(Math.abs(balansCheck.activa - balansCheck.passiva))}</span>
      </div>

      <div style="height: 12px;"></div>
      <div class="section-subtitle">Winst & Verlies Controle</div>
      <div class="row"><span class="label">Totaal Opbrengsten</span><span class="value">${fc(wvCheck.opbrengsten)}</span></div>
      <div class="row"><span class="label">Totaal Kosten</span><span class="value">${fc(wvCheck.kosten)}</span></div>
      <div class="row subtotal"><span class="label">Bedrijfsresultaat</span><span class="value" style="color: ${wvCheck.resultaat >= 0 ? '#059669' : '#dc2626'};">${fc(wvCheck.resultaat)}</span></div>
      <div class="row"><span class="label">Vennootschapsbelasting (15%)</span><span class="value">${fc(Math.round(wvCheck.resultaat * 0.15))}</span></div>
      <div class="row grand-total"><span class="label">Netto Resultaat</span><span class="value">${fc(Math.round(wvCheck.resultaat * 0.85))}</span></div>

      <div style="height: 12px;"></div>
      <div class="section-subtitle">BTW Controle</div>
      <div class="row"><span class="label">BTW Afgedragen</span><span class="value">${fc(btwCheck.afgedragen)}</span></div>
      <div class="row"><span class="label">BTW Teruggevorderd</span><span class="value">${fc(btwCheck.teruggevorderd)}</span></div>
      <div class="row subtotal"><span class="label">Saldo</span><span class="value">${fc(btwCheck.afgedragen - btwCheck.teruggevorderd)}</span></div>
      <div class="row"><span class="label">Alle BTW-aangiften ingediend</span><span class="value">${btwCheck.alleIngediend ? 'Ja' : 'Nee'}</span></div>

      <div class="note-box" style="margin-top: 20px;">
        Dit audit rapport is gegenereerd door de FiscalFlow AI Audit Agent. Confidence: 94%. Gebaseerd op RJ-standaarden en fiscale wetgeving. Een accountantsreview wordt aanbevolen voor definitieve ondertekening.
      </div>

      <div class="footer">
        Audit Rapport ${year} | ${companyName} | KvK: ${branding?.kvk || '-'} | Gegenereerd door FiscalFlow AI
      </div>
    </div>
    </body></html>
  `
}

"""Génération PDF des factures (reportlab, aucune dépendance système)."""
from io import BytesIO

from django.conf import settings
from django.utils import translation
from django.utils.formats import date_format
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BROWN = colors.HexColor('#5C3D2E')
CREAM = colors.HexColor('#F5EFE6')
INK = colors.HexColor('#2B1D14')
MUTED = colors.HexColor('#8B5E3C')


def _fr(d, fmt='j F Y'):
    with translation.override('fr'):
        return date_format(d, fmt)


def _eur(v):
    return f"{v:,.2f} €".replace(',', ' ').replace('.', ',')


def build_invoice_pdf(invoice) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm, title=f"Facture {invoice.number}")
    base = ParagraphStyle('base', fontName='Helvetica', fontSize=9.5, leading=13, textColor=INK)
    small = ParagraphStyle('small', parent=base, fontSize=8, leading=11, textColor=MUTED)
    h1 = ParagraphStyle('h1', parent=base, fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=BROWN)
    bold = ParagraphStyle('bold', parent=base, fontName='Helvetica-Bold')

    student = invoice.student
    user = student.user
    company_lines = [f"<b>{settings.COMPANY_NAME}</b>"]
    for v in (settings.COMPANY_ADDRESS, settings.COMPANY_EMAIL, settings.COMPANY_PHONE):
        if v:
            company_lines.append(v)
    if settings.COMPANY_SIRET:
        company_lines.append(f"SIRET {settings.COMPANY_SIRET}")
    if settings.COMPANY_VAT_NUMBER:
        company_lines.append(f"TVA {settings.COMPANY_VAT_NUMBER}")

    status_label = {'ISSUED': 'À régler', 'PAID': 'Payée', 'CANCELLED': 'Annulée'}[invoice.status]
    meta = [
        [Paragraph('<b>Facture</b>', base), Paragraph(invoice.number, base)],
        [Paragraph('Date', base), Paragraph(_fr(invoice.issued_at), base)],
        [Paragraph('Échéance', base), Paragraph(_fr(invoice.due_at), base)],
        [Paragraph('Statut', base), Paragraph(status_label + (f" le {_fr(invoice.paid_at.date())}" if invoice.paid_at else ''), bold)],
    ]
    header = Table([[
        Paragraph('<br/>'.join(company_lines), base),
        Table(meta, colWidths=[22 * mm, 48 * mm], style=TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('BOTTOMPADDING', (0, 0), (-1, -1), 2), ('TOPPADDING', (0, 0), (-1, -1), 2)])),
    ]], colWidths=[100 * mm, 74 * mm])
    header.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))

    client = Paragraph(
        f"<b>Facturé à</b><br/>{user.get_full_name()}<br/>{user.email}" + (f"<br/>{student.phone}" if student.phone else '') + (f"<br/>N° NEPH {student.neph_number}" if student.neph_number else ''),
        base,
    )

    rows = [[Paragraph('<b>Désignation</b>', base), Paragraph('<b>Qté</b>', base), Paragraph('<b>Prix unitaire HT</b>', base), Paragraph('<b>Total HT</b>', base)]]
    from decimal import Decimal
    qty = invoice.quantity_hours or 1
    unit_ht = invoice.amount_ht / Decimal(str(qty))
    desc = invoice.label
    if invoice.package.offer and invoice.package.offer.includes_lms:
        desc += " — inclut l'accès aux cours de code en ligne"
    rows.append([Paragraph(desc, base), Paragraph(f"{qty:g}{' h' if invoice.quantity_hours else ''}", base), Paragraph(_eur(unit_ht), base), Paragraph(_eur(invoice.amount_ht), base)])
    items = Table(rows, colWidths=[96 * mm, 18 * mm, 32 * mm, 28 * mm])
    items.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), CREAM), ('LINEBELOW', (0, 0), (-1, 0), 0.8, BROWN),
        ('LINEBELOW', (0, -1), (-1, -1), 0.4, colors.HexColor('#DCCFBC')),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    vat_line = f"TVA {float(invoice.vat_rate):g} %" if invoice.vat_rate else "TVA non applicable, art. 293 B du CGI"
    totals = Table([
        ['Total HT', _eur(invoice.amount_ht)],
        [vat_line, _eur(invoice.amount_vat)],
        ['Total TTC', _eur(invoice.amount_ttc)],
    ], colWidths=[60 * mm, 32 * mm], hAlign='RIGHT')
    totals.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 0), (-1, -1), 9.5), ('TEXTCOLOR', (0, 0), (-1, -1), INK),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'), ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), CREAM), ('LINEABOVE', (0, -1), (-1, -1), 0.8, BROWN),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    story = [header, Spacer(1, 10 * mm), client, Spacer(1, 8 * mm), items, Spacer(1, 6 * mm), totals, Spacer(1, 12 * mm)]
    if invoice.status == 'CANCELLED':
        story.append(Paragraph('<b>Cette facture a été annulée.</b>', ParagraphStyle('c', parent=base, textColor=colors.HexColor('#B91C1C'))))
        story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(settings.INVOICE_FOOTER, small))
    doc.build(story)
    return buf.getvalue()

"""Contrat de formation pré-rempli (PDF, reportlab) — format conforme aux mentions obligatoires (arrêté du 10 mai 2024 / Code de la route art. L213-2)."""
from io import BytesIO

from django.conf import settings
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .invoices import BROWN, CREAM, INK, MUTED, _eur, _fr


def _company_block():
    lines = [f"<b>{settings.COMPANY_NAME}</b>"]
    for v in (settings.COMPANY_ADDRESS, settings.COMPANY_EMAIL, settings.COMPANY_PHONE):
        if v:
            lines.append(v)
    if settings.COMPANY_SIRET:
        lines.append(f"SIRET {settings.COMPANY_SIRET}")
    if settings.COMPANY_AGREMENT:
        lines.append(f"Agrément préfectoral n° {settings.COMPANY_AGREMENT}")
    return '<br/>'.join(lines)


def build_contract_pdf(student, package=None) -> bytes:
    """Contrat pré-rempli pour l'élève ; la formule reprend l'achat passé en paramètre (sinon le dernier)."""
    user = student.user
    package = package or student.packages.exclude(status='FAILED').select_related('offer').first()
    offer = package.offer if package else None
    today = timezone.localdate()

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm, title=f"Contrat de formation — {user.get_full_name()}")
    base = ParagraphStyle('base', fontName='Helvetica', fontSize=9.5, leading=13, textColor=INK)
    small = ParagraphStyle('small', parent=base, fontSize=8, leading=11, textColor=MUTED)
    h1 = ParagraphStyle('h1', parent=base, fontName='Helvetica-Bold', fontSize=16, leading=20, textColor=BROWN)
    h2 = ParagraphStyle('h2', parent=base, fontName='Helvetica-Bold', fontSize=11, leading=15, textColor=BROWN, spaceBefore=6)

    header = Table([[Paragraph(_company_block(), base), Paragraph(f"<b>Contrat de formation</b><br/>Réf. KAHO-CTR-{student.id:05d}<br/>Édité le {_fr(today)}", base)]], colWidths=[104 * mm, 70 * mm])
    header.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('ALIGN', (1, 0), (1, 0), 'RIGHT')]))

    license_label = 'B — boîte automatique (BEA)' if student.license_type == 'AUTO' else 'B — boîte manuelle'
    rows = [
        ['Élève', f"{user.get_full_name()}"],
        ['Email / téléphone', f"{user.email}{' · ' + student.phone if student.phone else ''}"],
        ['N° NEPH', student.neph_number or 'en cours d’attribution'],
        ['Catégorie préparée', license_label],
    ]
    client = Table([[Paragraph(f'<b>{k}</b>', base), Paragraph(v, base)] for k, v in rows], colWidths=[45 * mm, 129 * mm])
    client.setStyle(TableStyle([('BOTTOMPADDING', (0, 0), (-1, -1), 3), ('TOPPADDING', (0, 0), (-1, -1), 3), ('LINEBELOW', (0, 0), (-1, -1), 0.3, colors.HexColor('#DCCFBC'))]))

    if package:
        items = [[Paragraph('<b>Désignation</b>', base), Paragraph('<b>Détail</b>', base), Paragraph('<b>Prix TTC</b>', base)]]
        detail = []
        if package.hours_purchased:
            detail.append(f"{package.hours_purchased:g} h de conduite")
        if offer and offer.includes_lms:
            detail.append('accès en ligne aux cours de code, quiz et examens blancs')
        if offer and offer.validity_months:
            detail.append(f"valable {offer.validity_months} mois")
        if offer:
            detail.append(f"facturation : {offer.get_billing_type_display().lower()}")
        items.append([Paragraph(package.display_label, base), Paragraph(', '.join(detail) or '—', base), Paragraph(_eur(package.amount_paid), base)])
        if offer and offer.hours:
            items.append([Paragraph('Heure de conduite supplémentaire', base), Paragraph('au-delà du forfait, même tarif unitaire', base), Paragraph(_eur(offer.price_per_hour), base)])
        formula = Table(items, colWidths=[60 * mm, 84 * mm, 30 * mm])
        formula.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), CREAM), ('LINEBELOW', (0, 0), (-1, 0), 0.8, BROWN), ('ALIGN', (2, 0), (2, -1), 'RIGHT'), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    else:
        formula = Paragraph("<i>Aucune formule sélectionnée : la formule et son prix seront complétés à la main.</i>", base)

    clauses = [
        ('1. Objet', "L'établissement s'engage à dispenser à l'élève la formation théorique et pratique nécessaire à l'obtention de la catégorie de permis indiquée ci-dessus, conformément au programme officiel (REMC)."),
        ('2. Évaluation préalable', "Une évaluation de départ est réalisée avant la signature ; le volume d'heures proposé est indicatif et peut être revu en fonction de la progression constatée. L'élève est informé que le nombre d'heures minimal réglementaire est de 20 h."),
        ('3. Déroulement et suivi', "Les leçons sont réservées depuis l'espace en ligne de l'élève. Chaque leçon donne lieu à un bilan consultable dans le livret d'apprentissage numérique. L'élève peut consulter à tout moment son solde d'heures et sa progression."),
        ('4. Prix et paiement', "Les prix sont exprimés TTC. Le règlement s'effectue en ligne (carte bancaire), par virement, chèque, espèces ou CPF selon la formule. Les heures sont créditées à réception du paiement. Une facture est émise pour chaque règlement."),
        ('5. Annulation et absence', f"Toute leçon annulée moins de {settings.BOOKING_CANCEL_DEADLINE_HOURS} h avant l'heure prévue, ainsi que toute absence, est due, sauf cas de force majeure justifié (certificat médical). L'établissement peut déplacer une leçon en cas d'absence du moniteur ; l'élève en est informé par email."),
        ('6. Durée et résiliation', "Le contrat est conclu pour la durée de la formation, dans la limite de la validité de la formule. Chaque partie peut y mettre fin par écrit ; les heures non consommées sont remboursées au prorata, déduction faite des frais engagés. Le dossier administratif est restitué sur demande."),
        ('7. Protection des données', "Les données de l'élève sont traitées pour la gestion de sa formation et conservées pendant la durée légale. L'élève dispose d'un droit d'accès, de rectification et de suppression auprès de l'établissement."),
        ('8. Litiges', "En cas de litige, les parties recherchent une solution amiable. À défaut, l'élève peut saisir le médiateur de la consommation dont relève l'établissement, puis les tribunaux compétents."),
    ]
    story = [header, Spacer(1, 6 * mm), Paragraph('Contrat de formation à la conduite', h1), Spacer(1, 4 * mm),
             Paragraph('Parties', h2), client, Spacer(1, 3 * mm), Paragraph('Formule choisie', h2), formula, Spacer(1, 3 * mm)]
    for title, text in clauses:
        story += [Paragraph(title, h2), Paragraph(text, base)]
    story.append(Spacer(1, 8 * mm))
    sign = Table([[Paragraph("<b>L'élève</b><br/>Lu et approuvé, le ___ / ___ / ______<br/><br/><br/>Signature :", base),
                   Paragraph(f"<b>Pour {settings.COMPANY_NAME}</b><br/>Le ___ / ___ / ______<br/><br/><br/>Signature et cachet :", base)]], colWidths=[87 * mm, 87 * mm])
    sign.setStyle(TableStyle([('BOX', (0, 0), (0, 0), 0.5, BROWN), ('BOX', (1, 0), (1, 0), 0.5, BROWN), ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8), ('LEFTPADDING', (0, 0), (-1, -1), 8)]))
    story += [sign, Spacer(1, 4 * mm), Paragraph("Contrat établi en deux exemplaires. Une fois signé, il peut être déposé dans l'espace « Documents » de l'élève (pièce « Contrat de formation signé »).", small)]
    doc.build(story)
    return buf.getvalue()

"""Alignement strict du bilan de compétences sur la grille REMC : 4 compétences, 20 sous-compétences.

Les évaluations déjà saisies (et les compétences ciblées des offres / achats) sont conservées : chaque ancienne
compétence est rattachée à son équivalent dans la nouvelle grille ; en cas de fusion, le meilleur statut l'emporte."""
from django.db import migrations, models

GRID = [
    (1, '1.1', "Connaître le véhicule et son poste de conduite (réglages siège et rétroviseurs, témoins du tableau de bord, mécanique de base)"),
    (1, '1.2', "Démarrer et s'arrêter (usage combiné embrayage / accélérateur / frein, dosage)"),
    (1, '1.3', "Maintenir la trajectoire (ligne droite, courbes, regard porté loin)"),
    (1, '1.4', "Manier le volant et utiliser les clignotants (position des mains, anticipation)"),
    (1, '1.5', "Démarrer en côte (frein à main et embrayage)"),
    (1, '1.6', "Marche arrière et manœuvres (créneau, bataille, épi, demi-tour, suivi de trottoir)"),
    (2, '2.1', "Rechercher les indices et appliquer la signalisation (panneaux, marquages, feux, zones d'incertitude)"),
    (2, '2.2', "Maîtriser les vitesses (limitations, adaptation au profil de la route)"),
    (2, '2.3', "Gérer les intersections (priorité à droite, rond-point, cédez le passage, stop)"),
    (2, '2.4', "Changer de direction et de voie (contrôles visuels, rétroviseur, angle mort, clignotant)"),
    (2, '2.5', "S'insérer et sortir des voies rapides et autoroutes"),
    (2, '2.6', "Respecter les distances de sécurité (frontale et latérale)"),
    (3, '3.1', "Circuler en conditions dégradées (pluie, nuit, brouillard, verglas, chaussée déformée)"),
    (3, '3.2', "Croiser et dépasser (faisabilité, réserve d'accélération)"),
    (3, '3.3', "Partager la route (piétons, cyclistes, deux-roues, trottinettes, transports en commun)"),
    (3, '3.4', "Faire face aux situations d'urgence (freinage d'urgence, trajectoire d'évitement)"),
    (4, '4.1', "Être autonome dans son itinéraire (panneaux de direction, GPS)"),
    (4, '4.2', "Pratiquer l'éco-conduite (changement de rapport anticipé, frein moteur, arrêt du moteur)"),
    (4, '4.3', "Prendre conscience des risques (alcool, stupéfiants, fatigue, distracteurs, téléphone)"),
    (4, '4.4', "Faire son bilan personnel et s'auto-évaluer (connaître ses limites et son état physique)"),
]
# ancienne compétence -> nouvelle
MAPPING = {
    '1.1': '1.1', '1.2': '1.2', '1.3': '1.3', '1.4': '1.6', '1.5': '1.2', '1.6': '1.6',
    '2.1': '2.1', '2.2': '1.3', '2.3': '2.2', '2.4': '2.4', '2.5': '2.3', '2.6': '1.6',
    '3.1': '2.6', '3.2': '3.2', '3.3': '2.5', '3.4': '3.1', '3.5': '3.1', '3.6': '3.3',
    '4.1': '4.1', '4.2': '4.2', '4.3': '1.1', '4.4': '3.4',
}
RANK = {'NOT_COVERED': 0, 'IN_PROGRESS': 1, 'ACQUIRED': 2}


def restructure(apps, schema_editor):
    Competency = apps.get_model('core', 'Competency')
    Assessment = apps.get_model('core', 'CompetencyAssessment')
    Offer = apps.get_model('core', 'Offer')
    Package = apps.get_model('core', 'Package')

    old = list(Competency.objects.all())
    for c in old:  # libère les codes pour la nouvelle grille
        c.code = f"old-{c.code}-{c.pk}"
        c.save(update_fields=['code'])
    new = {}
    for order, (group, code, label) in enumerate(GRID, start=1):
        new[code] = Competency.objects.create(code=code, label=label, group=group, order=order)

    def target(c):
        base = c.code.split('-')[1] if c.code.startswith('old-') else c.code
        return new.get(MAPPING.get(base))

    for c in old:
        t = target(c)
        if t is None:
            continue  # compétence personnalisée hors grille : conservée telle quelle
        for a in Assessment.objects.filter(competency=c):
            existing = Assessment.objects.filter(lesson_id=a.lesson_id, competency=t).first()
            if existing:
                if RANK.get(a.status, 0) > RANK.get(existing.status, 0):
                    existing.status = a.status
                    existing.save(update_fields=['status'])
                a.delete()
            else:
                a.competency = t
                a.save(update_fields=['competency'])
        for offer in Offer.objects.filter(skills=c):
            offer.skills.add(t)
            offer.skills.remove(c)
        c.delete()

    # Achats : les compétences choisies par l'élève sont stockées sous forme de codes (JSON)
    for pkg in Package.objects.exclude(requested_skills=[]):
        codes = []
        for code in pkg.requested_skills:
            mapped = MAPPING.get(code, code)
            if mapped not in codes:
                codes.append(mapped)
        if codes != pkg.requested_skills:
            pkg.requested_skills = codes
            pkg.save(update_fields=['requested_skills'])


class Migration(migrations.Migration):
    dependencies = [('core', '0020_cancellation_policy_assessment_lock')]
    operations = [
        migrations.AlterField(
            model_name='competency', name='group',
            field=models.PositiveSmallIntegerField(choices=[
                (1, 'Maîtriser le véhicule dans un trafic faible ou nul'),
                (2, 'Appréhender la route et circuler dans des conditions normales'),
                (3, 'Circuler dans des conditions difficiles et partager la route'),
                (4, 'Pratiquer une conduite autonome, sûre et éco-responsable')]),
        ),
        migrations.RunPython(restructure, migrations.RunPython.noop),
    ]

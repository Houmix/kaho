from django.db import migrations

# Grille REMC (Référentiel pour l'Éducation à une Mobilité Citoyenne) — 4 compétences générales
COMPETENCIES = [
    (1, '1.1', "S'installer au poste de conduite et connaître les commandes"),
    (1, '1.2', "Démarrer et s'arrêter"),
    (1, '1.3', "Diriger la voiture en marche avant (trajectoire, allure)"),
    (1, '1.4', "Diriger la voiture en marche arrière"),
    (1, '1.5', "Utiliser la boîte de vitesses / l'embrayage"),
    (1, '1.6', "Réaliser les manœuvres : créneau, bataille, épi, demi-tour"),
    (2, '2.1', "Rechercher et appliquer la signalisation"),
    (2, '2.2', "Positionner le véhicule sur la chaussée"),
    (2, '2.3', "Adapter l'allure aux situations"),
    (2, '2.4', "Tourner à droite et à gauche en agglomération"),
    (2, '2.5', "Franchir les intersections et les ronds-points"),
    (2, '2.6', "S'arrêter et stationner en agglomération"),
    (3, '3.1', "Évaluer et maintenir les distances de sécurité"),
    (3, '3.2', "Croiser, dépasser, être dépassé"),
    (3, '3.3', "S'insérer et circuler sur voie rapide / autoroute"),
    (3, '3.4', "Conduire de nuit"),
    (3, '3.5', "Conduire par intempéries (pluie, brouillard, neige)"),
    (3, '3.6', "Partager la route avec les usagers vulnérables (piétons, cyclistes, deux-roues)"),
    (4, '4.1', "Suivre un itinéraire de manière autonome"),
    (4, '4.2', "Pratiquer l'éco-conduite"),
    (4, '4.3', "Effectuer les vérifications courantes du véhicule"),
    (4, '4.4', "Adopter le bon comportement en cas d'accident / situation d'urgence"),
]


def seed(apps, schema_editor):
    Competency = apps.get_model('core', 'Competency')
    for order, (group, code, label) in enumerate(COMPETENCIES, start=1):
        Competency.objects.get_or_create(code=code, defaults={'label': label, 'group': group, 'order': order})


def unseed(apps, schema_editor):
    apps.get_model('core', 'Competency').objects.filter(code__in=[c[1] for c in COMPETENCIES]).delete()


class Migration(migrations.Migration):
    dependencies = [('core', '0004_competency_alter_lesson_options_and_more')]
    operations = [migrations.RunPython(seed, unseed)]

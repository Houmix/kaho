"""Programme intégral : les 10 thèmes officiels de l'ETG deviennent les sections du cours « Code de la route ».
Les sections de démonstration existantes (priorités, signalisation, vitesse) sont fusionnées dans le thème L."""
from django.db import migrations

THEMES = [
    ('L', 'La circulation routière', 'Signalisation, panneaux, règles de priorité, intersections, vitesses'),
    ('C', 'Le conducteur', 'Vigilance, fatigue, alcool, drogues, médicaments, vision, temps de réaction'),
    ('R', 'La route', 'Conduite nocturne, intempéries, adhérence, chaussée dégradée, autoroute'),
    ('U', 'Les autres usagers', 'Partage de la route, piétons, cyclistes, deux-roues, véhicules lourds'),
    ('D', 'Réglementation générale', 'Papiers du véhicule, permis à points, infractions, contrôle technique, équipements'),
    ('P', 'Prendre et quitter son véhicule', 'Installation au poste de conduite, passagers, sécurité des enfants'),
    ('M', 'Éléments mécaniques et de sécurité', 'Commandes, voyants du tableau de bord, pneumatiques, entretien'),
    ('S', 'Équipements de sécurité des véhicules', 'Ceinture, airbags, aides à la conduite, ABS, ESP'),
    ('E', "L'environnement", 'Éco-conduite, pollution, consommations, choix du véhicule'),
    ('A', 'Premiers secours', 'Protéger, Alerter, Secourir (PAS), comportement en cas d’accident'),
]
DISTRIBUTION = {'L': 10, 'C': 7, 'R': 4, 'U': 3, 'D': 3, 'P': 2, 'M': 3, 'S': 3, 'E': 3, 'A': 2}

INTRO = {
    'C': """## Le conducteur

Conduire demande une **vigilance constante**. Le temps de réaction moyen est d'**une seconde** : à 90 km/h, ce sont 25 m parcourus avant même de freiner.

### Ce qui dégrade la conduite
- **Fatigue** : après 2 h de route, pause de 15 min ; les signes (bâillements, paupières lourdes, écarts de trajectoire) ne trompent pas.
- **Alcool** : limite de 0,5 g/l de sang (0,2 g/l en permis probatoire). Un verre standard ≈ 0,2 à 0,25 g/l.
- **Drogues et médicaments** : pictogrammes de niveau 1 à 3 sur les boîtes ; niveau 3 = ne pas conduire.
- **Vision** : acuité minimale 5/10 pour les deux yeux ensemble ; lunettes obligatoires si mentionnées sur le permis.
""",
    'R': """## La route

### Conditions difficiles
- **Nuit** : feux de croisement en agglomération, feux de route hors agglomération si personne en face.
- **Pluie** : distance d'arrêt doublée, vitesse limitée à 110 km/h sur autoroute, 100 km/h sur voie rapide, 80 km/h sur route.
- **Brouillard** (visibilité < 50 m) : 50 km/h partout, feux de brouillard avant autorisés, arrière uniquement si visibilité réduite.
- **Verglas, gravillons, chaussée déformée** : anticiper, freiner en ligne droite, ne pas tourner le volant brusquement.

### Autoroute
Vitesse minimale 80 km/h sur la voie de gauche ; voie d'insertion ; bande d'arrêt d'urgence réservée aux pannes.
""",
    'U': """## Les autres usagers

La route se partage. Les **usagers vulnérables** (piétons, cyclistes, trottinettes, deux-roues motorisés) ont priorité de protection.

- Piéton engagé ou manifestant l'intention de traverser : **je m'arrête**.
- Dépassement d'un cycliste : **1 m en ville, 1,5 m hors agglomération**.
- Angle mort des poids lourds et bus : ne pas rester à leur droite ni juste derrière.
- Véhicules prioritaires (gyrophare + sirène) : je facilite le passage.
""",
    'D': """## Réglementation générale

### Documents obligatoires à bord
Permis de conduire, certificat d'immatriculation (carte grise), attestation d'assurance.

### Permis à points
12 points (6 en probatoire, +2 par an sans infraction, 3 ans ou 2 ans avec conduite accompagnée). Retrait selon l'infraction (ex. téléphone au volant : 3 points, 135 €).

### Contrôle technique
Avant les 4 ans du véhicule, puis tous les 2 ans. Équipements obligatoires : gilet haute visibilité et triangle de présignalisation.
""",
    'P': """## Prendre et quitter son véhicule

### Installation au poste de conduite
1. Siège : jambe légèrement fléchie pédale enfoncée.
2. Dossier et appui-tête : haut de l'appui-tête au niveau du sommet du crâne.
3. Rétroviseurs : intérieur centré sur la lunette arrière, extérieurs effleurant la carrosserie.
4. Ceinture : plaquée sur l'épaule et le bassin, jamais sous le bras.

### Passagers et enfants
Siège adapté obligatoire jusqu'à **10 ans** (ou 1,35 m) ; dos à la route tant que possible ; jamais d'enfant devant avec airbag actif en dos à la route.
""",
    'M': """## Éléments mécaniques et de sécurité

### Voyants du tableau de bord
- **Rouge** : arrêt immédiat (huile, température, freins, batterie).
- **Orange** : anomalie à vérifier rapidement (moteur, ABS, pression pneus).
- **Vert / bleu** : simple information (feux, clignotants).

### Pneumatiques
Profondeur de sculpture minimale **1,6 mm** ; pression à vérifier à froid tous les mois ; usure anormale = parallélisme ou pression.
""",
    'S': """## Équipements de sécurité des véhicules

- **Ceinture** : réduit de moitié le risque de décès ; obligatoire à toutes les places.
- **Airbags** : complètent la ceinture, ne la remplacent pas.
- **ABS** : empêche le blocage des roues, permet de garder la direction en freinage d'urgence.
- **ESP** : corrige la trajectoire en cas de perte d'adhérence.
- **AFU** : aide au freinage d'urgence ; **régulateur / limiteur** : gestion de la vitesse ; **détecteur d'angle mort**, **freinage automatique**.
""",
    'E': """## L'environnement

### Éco-conduite
- Passer les rapports tôt (≈ 2 000 tr/min essence, 1 500 diesel), anticiper pour éviter les freinages.
- Couper le moteur dès 20 s d'arrêt ; pas de préchauffage.
- Pneus bien gonflés, coffre de toit retiré, climatisation raisonnée : jusqu'à −10 % de consommation.

### Pollution
Vignette **Crit'Air** pour les zones à faibles émissions ; véhicules électriques et hybrides ; covoiturage et transports alternatifs.
""",
    'A': """## Premiers secours

### P.A.S. — Protéger, Alerter, Secourir
1. **Protéger** : feux de détresse, gilet, triangle à 30 m (sauf autoroute : se mettre derrière la glissière), couper le contact.
2. **Alerter** : **112** (urgences européen), 15 (SAMU), 18 (pompiers), 17 (police). Indiquer lieu, nombre de victimes, état.
3. **Secourir** : ne pas déplacer un blessé (sauf danger immédiat), couvrir, parler, ne rien donner à boire ; victime inconsciente qui respire → position latérale de sécurité.
""",
}


def forwards(apps, schema_editor):
    Course = apps.get_model('lms', 'Course')
    Section = apps.get_model('lms', 'Section')
    Lesson = apps.get_model('lms', 'Lesson')
    Quiz = apps.get_model('lms', 'Quiz')
    Question = apps.get_model('lms', 'Question')
    Exam = apps.get_model('lms', 'Exam')
    course = Course.objects.filter(slug='code-de-la-route').first() or Course.objects.order_by('id').first()
    if course is None:
        course = Course.objects.create(title='Code de la route', slug='code-de-la-route', order=1, is_published=True,
                                       description="Le programme complet de l'examen théorique général (ETG) : 10 thèmes officiels, quiz et examens blancs.")
    old_sections = list(Section.objects.filter(course=course, code=''))
    created = {}
    for i, (code, title, desc) in enumerate(THEMES, start=1):
        s = Section.objects.filter(course=course, code=code).first()
        if not s:
            s = Section.objects.create(course=course, code=code, title=f"{code} — {title}", order=i, unlock_threshold=0, is_free_preview=(code == 'L'))
        created[code] = s
        if not Quiz.objects.filter(section=s).exists():
            Quiz.objects.create(section=s, title=f"Quiz — {title}", pass_score=80)
        if code in INTRO and not Lesson.objects.filter(section=s).exists():
            Lesson.objects.create(section=s, title=title, slug=f"theme-{code.lower()}", order=1, estimated_minutes=10, content_md=INTRO[code], is_published=True)
    # Fusion des anciennes sections de démo dans le thème L (leçons, questions de quiz, tentatives)
    L = created['L']
    quiz_L = Quiz.objects.get(section=L)
    n = Lesson.objects.filter(section=L).count()
    for old in old_sections:
        for l in Lesson.objects.filter(section=old).order_by('order', 'id'):
            n += 1
            l.section, l.order = L, n
            l.save()
        old_quiz = Quiz.objects.filter(section=old).first()
        if old_quiz:
            Question.objects.filter(quiz=old_quiz).update(quiz=quiz_L)
            # les tentatives référencent l'ancien quiz : on les rattache au nouveau
            QuizAttempt = apps.get_model('lms', 'QuizAttempt')
            QuizAttempt.objects.filter(quiz=old_quiz).update(quiz=quiz_L)
            old_quiz.delete()
        old.delete()
    Question.objects.filter(topic__in=['Priorités', 'Signalisation', 'Vitesse', 'Sécurité']).update(topic='L')
    # Examens : format officiel 40 questions, 20 s par question, répartition nationale
    for e in Exam.objects.filter(is_demo=False):
        e.question_count, e.seconds_per_question, e.pass_score, e.distribution = 40, 20, 88, DISTRIBUTION
        e.description = "Conditions réelles de l'ETG : 40 questions, 20 secondes par question, 35 bonnes réponses requises."
        e.save()
    Exam.objects.filter(is_demo=True).update(seconds_per_question=20)


class Migration(migrations.Migration):
    dependencies = [('lms', '0003_themes_distribution_studytime')]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]

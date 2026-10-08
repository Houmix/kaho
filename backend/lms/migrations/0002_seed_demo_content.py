from django.db import migrations

PRIORITES_1 = """## La règle de base : priorité à droite

En l'absence de signalisation, **le conducteur doit céder le passage au véhicule venant de sa droite**. C'est la règle par défaut à toute intersection (art. R415-5 du Code de la route).

### Quand s'applique-t-elle ?
- Aucun panneau ni marquage à l'intersection
- Les deux voies ont le même statut (pas de route prioritaire)
- Dans les zones de rencontre et les lotissements, très souvent

### Les trois questions à se poser
1. Y a-t-il un **panneau** (stop, cédez-le-passage, route prioritaire) ?
2. Y a-t-il un **marquage** au sol (ligne continue, triangles) ?
3. Sinon : **qui vient de ma droite ?**

> Astuce : regardez *tôt* sur la droite en approchant, pas au dernier moment.

### Exemple : lire une intersection
```text
          |   |
   ───────┘   └───────
     ←  moi      B →
   ───────┐   ┌───────
          | A |
          | ↑ |
```
Je roule vers la droite. `A` arrive de ma droite : **je cède**. `B` arrive de ma gauche : il me cède.
"""

PRIORITES_2 = """## Les ronds-points et carrefours à sens giratoire

Deux cas très différents qui portent le même nom dans le langage courant :

| | Carrefour à sens giratoire | Rond-point (vrai) |
|---|---|---|
| Panneau | « Cédez le passage » à l'entrée | Aucun |
| Qui a la priorité ? | **Ceux qui sont déjà dans l'anneau** | **Ceux qui entrent** (priorité à droite) |
| Fréquence | 99 % des cas | Rare (ex. place de l'Étoile à Paris) |

### Clignotants dans un giratoire
- **Entrée** : pas de clignotant si vous allez tout droit ou à gauche
- **Sortie** : clignotant **droit** avant la sortie que vous prenez
- **Tourner à gauche / demi-tour** : clignotant gauche en entrant, puis droit avant de sortir

### Placement
- Première sortie ou tout droit : voie de droite
- Au-delà de la moitié du giratoire : voie de gauche, puis se rabattre avant la sortie
"""

SIGNALISATION_1 = """## Formes et couleurs des panneaux

| Forme | Couleur | Signification |
|---|---|---|
| Rond | Fond blanc, bord rouge | **Interdiction** |
| Rond | Fond bleu | **Obligation** |
| Triangle | Bord rouge | **Danger** |
| Carré | Fond bleu | **Indication** |
| Octogone | Rouge | **STOP** |

### Les panneaux à connaître absolument
- Triangle pointe en bas : *cédez le passage*
- Losange jaune : *route à caractère prioritaire*
- Rond blanc bord rouge vide : *circulation interdite dans les deux sens*
"""

SIGNALISATION_2 = """## Marquage au sol

- **Ligne continue** : interdiction de la chevaucher ou de la franchir
- **Ligne discontinue** : franchissement autorisé si la manœuvre est sans danger
- **Ligne mixte** : on ne franchit que si la ligne discontinue est de *son* côté
- **Zébras** : zone interdite à la circulation
- **Flèches de rabattement** : annoncent une ligne continue, rabattez-vous

### Couleurs
- Blanc : marquage permanent
- Jaune : marquage **temporaire** (travaux) — il prime sur le blanc
"""

BANK = [
    ('Priorités', 'SINGLE', "À une intersection sans aucune signalisation, qui a la priorité ?", [("Le véhicule venant de droite", True), ("Le véhicule venant de gauche", False), ("Le véhicule le plus rapide", False), ("Celui qui arrive en premier", False)], "Règle de la priorité à droite (R415-5)."),
    ('Priorités', 'TRUE_FALSE', "Dans un carrefour à sens giratoire, les véhicules déjà engagés dans l'anneau sont prioritaires.", [("Vrai", True), ("Faux", False)], "Le panneau « cédez le passage » à l'entrée donne la priorité à l'anneau."),
    ('Priorités', 'SINGLE', "Dans un sens giratoire, quand doit-on mettre le clignotant droit ?", [("Avant la sortie que l'on prend", True), ("En entrant dans le giratoire", False), ("Jamais", False), ("Pendant tout le tour", False)], "On signale sa sortie, pas son entrée (sauf pour tourner à gauche : clignotant gauche en entrant)."),
    ('Priorités', 'MULTI', "Quelles situations imposent de céder le passage ? (plusieurs réponses)", [("Panneau STOP", True), ("Panneau cédez le passage", True), ("Losange jaune devant moi", False), ("Véhicule venant de droite sans signalisation", True)], "Le losange jaune indique que VOUS êtes prioritaire."),
    ('Priorités', 'TRUE_FALSE', "Un tramway est prioritaire dans la plupart des situations.", [("Vrai", True), ("Faux", False)], "Le tramway est prioritaire sauf signalisation contraire."),
    ('Signalisation', 'SINGLE', "Un panneau rond à fond bleu indique :", [("Une obligation", True), ("Une interdiction", False), ("Un danger", False), ("Une indication", False)], "Rond bleu = obligation ; rond blanc bord rouge = interdiction."),
    ('Signalisation', 'SINGLE', "Un panneau triangulaire à bord rouge signale :", [("Un danger", True), ("Une interdiction", False), ("Une priorité", False), ("Une fin d'interdiction", False)], "Triangle = danger."),
    ('Signalisation', 'TRUE_FALSE', "Le marquage au sol jaune (temporaire) prime sur le marquage blanc.", [("Vrai", True), ("Faux", False)], "Le jaune signale des travaux et l'emporte sur le marquage permanent."),
    ('Signalisation', 'SINGLE', "Une ligne mixte : on peut la franchir si…", [("La ligne discontinue est de mon côté", True), ("La ligne continue est de mon côté", False), ("Jamais", False), ("Toujours", False)], "On ne franchit une ligne mixte que depuis le côté discontinu."),
    ('Signalisation', 'SHORT', "Quelle forme a le panneau STOP ? (un mot)", None, "Octogone — la seule forme à 8 côtés, reconnaissable même recouvert de neige.", "octogone|octogonale|un octogone"),
    ('Vitesse', 'SINGLE', "Vitesse maximale en agglomération, sauf indication contraire :", [("50 km/h", True), ("30 km/h", False), ("70 km/h", False), ("90 km/h", False)], "50 km/h par défaut ; 30 km/h en zone 30."),
    ('Vitesse', 'SINGLE', "Sur autoroute par temps de pluie, la vitesse maximale est :", [("110 km/h", True), ("130 km/h", False), ("90 km/h", False), ("100 km/h", False)], "130 → 110 par temps de pluie (R413-2)."),
    ('Vitesse', 'TRUE_FALSE', "Un jeune conducteur (permis probatoire) est limité à 110 km/h sur autoroute.", [("Vrai", True), ("Faux", False)], "Pendant la période probatoire : 110 au lieu de 130, 100 au lieu de 110, 80 au lieu de 90."),
    ('Sécurité', 'SINGLE', "La distance de sécurité minimale correspond à :", [("2 secondes", True), ("1 seconde", False), ("5 secondes", False), ("10 mètres", False)], "Repère fixe : comptez 2 secondes après le passage du véhicule qui précède."),
    ('Sécurité', 'MULTI', "Quels éléments augmentent la distance d'arrêt ? (plusieurs réponses)", [("La vitesse", True), ("La fatigue", True), ("Une route sèche", False), ("Des pneus usés", True)], "Distance d'arrêt = distance de réaction + distance de freinage."),
    ('Sécurité', 'SINGLE', "Le taux d'alcool maximal autorisé pour un conducteur en permis probatoire est :", [("0,2 g/L de sang", True), ("0,5 g/L", False), ("0,8 g/L", False), ("0 g/L", False)], "0,2 g/L en probatoire (soit zéro verre en pratique), 0,5 g/L ensuite."),
]


def seed(apps, schema_editor):
    Course = apps.get_model('lms', 'Course')
    Section = apps.get_model('lms', 'Section')
    Lesson = apps.get_model('lms', 'Lesson')
    Quiz = apps.get_model('lms', 'Quiz')
    Question = apps.get_model('lms', 'Question')
    Choice = apps.get_model('lms', 'Choice')
    Exam = apps.get_model('lms', 'Exam')
    if Course.objects.exists():
        return

    course = Course.objects.create(title='Code de la route', slug='code-de-la-route', order=1, is_published=True,
                                   description="Le programme complet de l'examen théorique général (ETG) : priorités, signalisation, vitesse, sécurité, avec quiz et examens blancs.")
    s1 = Section.objects.create(course=course, title='Les priorités', order=1, is_free_preview=True, unlock_threshold=80)
    Lesson.objects.create(section=s1, title='La priorité à droite', slug='priorite-a-droite', order=1, content_md=PRIORITES_1, estimated_minutes=8)
    Lesson.objects.create(section=s1, title='Ronds-points et giratoires', slug='giratoires', order=2, content_md=PRIORITES_2, estimated_minutes=10,
                          video_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ')
    s2 = Section.objects.create(course=course, title='La signalisation', order=2, unlock_threshold=80)
    Lesson.objects.create(section=s2, title='Formes et couleurs des panneaux', slug='panneaux', order=1, content_md=SIGNALISATION_1, estimated_minutes=12)
    Lesson.objects.create(section=s2, title='Le marquage au sol', slug='marquage', order=2, content_md=SIGNALISATION_2, estimated_minutes=8)
    s3 = Section.objects.create(course=course, title='Vitesse et distances de sécurité', order=3, unlock_threshold=0)
    Lesson.objects.create(section=s3, title='Les limitations de vitesse', slug='vitesse', order=1, estimated_minutes=10,
                          content_md="## Limitations par défaut\n\n- Agglomération : **50 km/h**\n- Route : **80 km/h** (90 sur certaines routes à 2×2 voies ou décidé par le département)\n- Voie rapide : **110 km/h**\n- Autoroute : **130 km/h** (110 sous la pluie, 50 si visibilité < 50 m)\n\nPermis probatoire : 110 / 100 / 80.")

    quizzes = {s1: Quiz.objects.create(section=s1, title='Quiz — Les priorités', pass_score=80),
               s2: Quiz.objects.create(section=s2, title='Quiz — La signalisation', pass_score=80),
               s3: Quiz.objects.create(section=s3, title='Quiz — Vitesse et sécurité', pass_score=70)}
    topic_to_section = {'Priorités': s1, 'Signalisation': s2, 'Vitesse': s3, 'Sécurité': s3}
    counters = {}
    for topic, kind, text, choices, explanation, *rest in BANK:
        sec = topic_to_section[topic]
        counters[sec.id] = counters.get(sec.id, 0) + 1
        q = Question.objects.create(quiz=quizzes[sec], kind=kind, text_md=text, explanation_md=explanation, order=counters[sec.id],
                                    topic=topic, in_exam_bank=True, expected_answer=(rest[0] if rest else ''))
        for i, (label, ok) in enumerate(choices or []):
            Choice.objects.create(question=q, text=label, is_correct=ok, order=i + 1)

    Exam.objects.create(title="Série d'essai gratuite", description="10 questions tirées au hasard pour vous tester, sans compte.", duration_minutes=10, question_count=10, pass_score=80, is_demo=True, order=0)
    Exam.objects.create(title='Examen blanc ETG', description="Conditions réelles : 40 questions, 30 minutes, 35 bonnes réponses requises.", duration_minutes=30, question_count=40, pass_score=88, order=1)


def unseed(apps, schema_editor):
    apps.get_model('lms', 'Course').objects.filter(slug='code-de-la-route').delete()
    apps.get_model('lms', 'Exam').objects.filter(title__in=["Série d'essai gratuite", 'Examen blanc ETG']).delete()


class Migration(migrations.Migration):
    dependencies = [('lms', '0001_initial')]
    operations = [migrations.RunPython(seed, unseed)]

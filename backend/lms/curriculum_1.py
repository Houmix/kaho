"""Programme ETG — contenus rédigés pour les thèmes L, C, R, U, D.

Structure : THEME -> {'lessons': [(slug, titre, minutes, markdown)], 'questions': [(énoncé, [propositions], [indices corrects], explication)]}
Les règles citées sont celles du Code de la route en vigueur ; elles sont modifiables depuis le back-office (Contenus LMS)."""

DATA = {}

# ---------------------------------------------------------------------------------------------------------------------
DATA['L'] = {
    'lessons': [
        ('la-hierarchie-des-regles', "La hiérarchie des règles et signaux", 8, """## Qui décide à un carrefour ?

Quand plusieurs indications se contredisent, on applique toujours le **même ordre** :

1. **Les ordres d'un agent** (policier, gendarme, agent de circulation, pompier ou signaleur de chantier) ;
2. **Les feux de signalisation** ;
3. **Les panneaux** (stop, cédez le passage, route prioritaire, interdictions…) ;
4. **Les règles générales** (priorité à droite, etc.).

> Exemple : un feu est vert, mais un agent vous fait signe de vous arrêter → **vous vous arrêtez**.

### Les feux tricolores
- **Rouge** : arrêt derrière la ligne d'effet des feux.
- **Orange fixe** : arrêt obligatoire, sauf si l'on est trop près pour s'arrêter dans de bonnes conditions de sécurité.
- **Vert** : passage autorisé, mais on reste vigilant (piétons encore engagés, véhicules retardataires).
- **Orange clignotant** : le feu ne règle plus la circulation ; ce sont les **panneaux** (ou la priorité à droite) qui s'appliquent.

### Feu rouge clignotant
Il signale un passage à niveau, un pont mobile ou la sortie d'un véhicule d'urgence : **arrêt obligatoire** jusqu'à l'extinction.
"""),
        ('stop-et-cedez-le-passage', "Stop, cédez le passage et routes prioritaires", 8, """## Les panneaux de priorité

| Panneau | Obligation |
|---|---|
| **Stop** (octogone rouge) | Arrêt **complet** à la ligne continue, puis céder le passage. Le stop s'impose même si la route semble libre. |
| **Cédez le passage** (triangle pointe en bas) | Ralentir, et s'arrêter si nécessaire pour laisser passer. |
| **Route à caractère prioritaire** (losange jaune) | Vous avez la priorité aux intersections jusqu'à la fin de cette priorité. |
| **Fin de route à caractère prioritaire** | Retour à la règle de la priorité à droite. |
| **Intersection où la priorité est ponctuelle** | Le panneau précise où la priorité s'applique. |

### Où s'arrêter ?
- À un **stop**, derrière la **ligne d'arrêt** continue ; si elle est mal placée, on avance prudemment jusqu'au point d'où l'on voit.
- À un **cédez le passage**, derrière la ligne discontinue (triangles) ou, à défaut, au niveau du panneau.

### Passages à niveau
Feux rouges clignotants, signal sonore ou demi-barrières qui s'abaissent : **arrêt**. Il est interdit de contourner ou de franchir la barrière, et de s'engager si l'on n'est pas sûr de pouvoir dégager la voie ferrée.
"""),
        ('depasser-et-croiser', "Croiser et dépasser", 9, """## Croiser

On croise **à droite**. Sur une route étroite, celui qui a un obstacle de son côté s'arrête et laisse passer. En **côte**, en cas d'impossibilité, le véhicule qui descend cède.

## Dépasser
On dépasse **par la gauche**, après avoir vérifié :
1. que la voie est **libre sur une distance suffisante** ;
2. qu'aucun véhicule ne me dépasse déjà (rétroviseur, angle mort) ;
3. que j'ai la **vitesse** et la **place** pour me rabattre sans gêner.

### Dépassement interdit
- avant un **sommet de côte** ou dans un **virage** sans visibilité ;
- en franchissant une **ligne continue** ;
- à l'approche d'un **passage piéton** (on ne dépasse pas un véhicule arrêté devant lui : un piéton peut être masqué) ;
- quand un panneau l'interdit ;
- à l'approche d'un passage à niveau.

### Distances latérales
Pour dépasser un cycliste, un piéton ou un engin de déplacement personnel : **1 m en agglomération, 1,5 m hors agglomération**.

### Être dépassé
Je **ne dois pas accélérer** et je serre à droite si nécessaire. Le dépassement d'un véhicule qui tourne à gauche se fait par la droite.
"""),
        ('arret-et-stationnement', "Arrêt et stationnement", 8, """## Arrêt et stationnement : quelle différence ?

- **Arrêt** : immobilisation momentanée, **conducteur présent** et prêt à repartir (prise ou dépose de passagers).
- **Stationnement** : immobilisation prolongée, le conducteur peut s'éloigner.

### Stationnement très gênant (135 €, enlèvement possible)
- sur un **trottoir**, un passage piéton, une piste cyclable ;
- sur une place **réservée aux personnes handicapées** (GIC / GIG) ;
- sur un **arrêt de bus** ou une voie réservée aux bus.

### Interdit ou dangereux
- à moins de **5 m en amont d'un passage piéton** ;
- dans un virage, avant un sommet de côte, sur un pont ;
- devant une sortie de garage ou un accès de pompiers ;
- en **stationnement unilatéral alterné semi-mensuel** : du 1ᵉʳ au 15 du mois, côté des numéros **impairs** ; du 16 à la fin du mois, côté des numéros **pairs**.

### Quitter son véhicule
Couper le contact, serrer le frein à main, laisser une vitesse engagée, regarder dans le rétroviseur et **ouvrir la portière de la main éloignée** (cela oblige à tourner la tête et à voir arriver cyclistes et deux-roues).
"""),
        ('feux-eclairage', "Éclairage et signalisation lumineuse du véhicule", 8, """## Quels feux, quand ?

| Situation | Feux à utiliser |
|---|---|
| Jour, bonne visibilité | Feux de jour (ou croisement) |
| Nuit en agglomération | **Feux de croisement** |
| Nuit hors agglomération | **Feux de route**, remplacés par les croisement dès qu'on croise ou suit un véhicule |
| Brouillard / chute de neige dense | Croisement + antibrouillard avant ; antibrouillard arrière **seulement si la visibilité est inférieure à 50 m** |
| Véhicule arrêté ou en panne | **Feux de détresse** |

### Ne pas éblouir
On passe en feux de croisement **dès qu'un véhicule arrive en face** ou lorsqu'on suit un véhicule à courte distance.

### Les antibrouillards
Le feu **arrière** antibrouillard ne s'utilise que si la visibilité est **inférieure à 50 m** (brouillard, neige) : il éblouit en cas de simple pluie.

### Les clignotants
Ils s'enclenchent **avant** la manœuvre (changement de file, dépassement, sortie) et s'éteignent **après**. Un clignotant n'est pas une autorisation de passage : il annonce.

### Les feux de détresse
Danger, panne, ralentissement brutal sur autoroute : on les actionne pour **prévenir** les usagers derrière.
"""),
        ('vitesses-et-distances', "Vitesses maximales et distances de sécurité", 10, """## Les limites de base (conducteur confirmé)

| Réseau | Temps sec | Pluie / chaussée mouillée |
|---|---|---|
| Agglomération | 50 km/h | 50 km/h |
| Route à double sens, sans séparateur central | 80 km/h | 80 km/h |
| Route à chaussées séparées (2×2 voies) | 110 km/h | 100 km/h |
| Autoroute | 130 km/h | 110 km/h |

> Un panneau local ou temporaire **prime toujours** sur la limite générale. Les conducteurs en permis probatoire ont des limites réduites (ex. 110 km/h sur autoroute).

### Distance d'arrêt = réaction + freinage
- **Temps de réaction** moyen : environ **1 seconde**. À 50 km/h : ≈ 14 m ; à 90 km/h : ≈ 25 m ; à 130 km/h : ≈ 36 m.
- **Freinage** (route sèche) : environ (vitesse / 10)² mètres → 25 m à 50 km/h, 81 m à 90 km/h.
- **Sur sol mouillé** la distance de freinage est **multipliée par 1,5 à 2**.

### Distance de sécurité
Gardez au moins **2 secondes** derrière le véhicule qui vous précède (3 secondes par temps de pluie) : on passe devant un repère, on compte, et on ne doit pas atteindre ce repère avant 2 s.

### Pourquoi ralentir de 10 km/h ?
L'énergie d'un choc augmente avec le **carré** de la vitesse : à 50 km/h, un choc équivaut à une chute de 10 m ; à 90 km/h, à une chute de 30 m. Le risque de décès d'un piéton est multiplié plusieurs fois entre 30 et 50 km/h.
"""),
    ],
    'questions': [
        ("Un agent de la circulation vous fait signe de vous arrêter alors que le feu est vert. Que faites-vous ?",
         ["Je m'arrête", "Je passe car le feu est vert", "Je passe si personne ne vient", "Je ralentis seulement"], [0],
         "Les ordres d'un agent l'emportent sur les feux, les panneaux et les règles générales."),
        ("Le feu tricolore clignote à l'orange. Qu'est-ce qui règle la priorité ?",
         ["Les panneaux de l'intersection", "Le feu, qui est prioritaire", "Je dois toujours m'arrêter", "Le véhicule le plus gros"], [0],
         "Le feu orange clignotant ne règle plus la circulation : on applique les panneaux, ou à défaut la priorité à droite."),
        ("Devant un panneau STOP, je dois :",
         ["M'arrêter complètement derrière la ligne, puis céder le passage", "Ralentir et passer si la voie est libre", "M'arrêter uniquement si un véhicule arrive", "Klaxonner et passer"], [0],
         "L'arrêt est obligatoire, même si la route paraît libre."),
        ("À un cédez le passage, je dois :",
         ["Ralentir et m'arrêter si nécessaire pour laisser passer", "M'arrêter toujours complètement", "Passer en priorité si je roule vite", "Mettre mes feux de détresse"], [0],
         "Le cédez le passage impose de ralentir, et de s'arrêter seulement si la situation l'exige."),
        ("Quelle est la limite de vitesse par temps de pluie sur autoroute pour un conducteur confirmé ?",
         ["110 km/h", "130 km/h", "100 km/h", "90 km/h"], [0],
         "Sur autoroute : 130 km/h par temps sec, 110 km/h par temps de pluie."),
        ("Sur une route à double sens sans séparateur central, la vitesse maximale est en principe de :",
         ["80 km/h", "90 km/h", "100 km/h", "70 km/h"], [0],
         "Hors agglomération, sans séparateur central : 80 km/h, sauf signalisation contraire."),
        ("En agglomération, sauf indication contraire, la vitesse est limitée à :",
         ["50 km/h", "30 km/h", "60 km/h", "70 km/h"], [0],
         "La limite générale en agglomération est de 50 km/h."),
        ("Quelle distance latérale minimale dois-je laisser pour dépasser un cycliste hors agglomération ?",
         ["1,5 m", "1 m", "0,5 m", "2 m"], [0],
         "1 m en agglomération, 1,5 m hors agglomération."),
        ("Le dépassement est interdit :",
         ["Avant un sommet de côte sans visibilité", "Sur une route à trois voies, en dehors des agglomérations", "Derrière un véhicule lent sur une ligne discontinue", "De jour par temps sec"], [0],
         "On ne dépasse pas lorsqu'on ne voit pas suffisamment loin devant soi."),
        ("Vous êtes dépassé par un autre véhicule. Que devez-vous faire ?",
         ["Ne pas accélérer et serrer à droite si nécessaire", "Accélérer pour ne pas être doublé", "Mettre vos feux de route", "Klaxonner"], [0],
         "Un conducteur dépassé ne doit pas augmenter son allure."),
        ("À partir de quelle visibilité peut-on utiliser le feu antibrouillard arrière ?",
         ["Moins de 50 m", "Moins de 100 m", "Moins de 200 m", "Dès qu'il pleut"], [0],
         "Le feu antibrouillard arrière n'est autorisé que lorsque la visibilité est inférieure à 50 mètres."),
        ("Quand dois-je passer des feux de route aux feux de croisement ?",
         ["Dès que je croise un véhicule ou que j'en suis un de près", "Seulement en agglomération", "Jamais, c'est facultatif", "Uniquement quand il pleut"], [0],
         "Pour ne pas éblouir les autres usagers, on passe en feux de croisement dès qu'on croise ou suit un véhicule."),
        ("Stationner sur un trottoir est :",
         ["Très gênant et sanctionné par une amende de 135 €", "Autorisé s'il reste 1 m de passage", "Toléré en agglomération", "Autorisé pour moins de 10 minutes"], [0],
         "Le stationnement sur trottoir est très gênant (135 €), avec mise en fourrière possible."),
        ("À quelle distance minimale d'un passage piéton ai-je le droit de stationner (en amont) ?",
         ["5 m", "1 m", "10 m", "20 m"], [0],
         "Le stationnement est interdit à moins de 5 m en amont d'un passage piéton, pour que le piéton soit visible."),
        ("Le 12 du mois, dans une rue en stationnement unilatéral alterné semi-mensuel, je me gare :",
         ["Du côté des numéros impairs", "Du côté des numéros pairs", "Là où je veux", "Sur le trottoir"], [0],
         "Du 1ᵉʳ au 15 : côté impair ; du 16 à la fin du mois : côté pair."),
        ("Des feux rouges clignotent à un passage à niveau. Je :",
         ["M'arrête et attends l'extinction des feux", "Passe rapidement si je vois qu'aucun train n'arrive", "Contourne les demi-barrières", "Klaxonne"], [0],
         "Il est strictement interdit de franchir un passage à niveau dont les feux clignotent ou les barrières sont baissées."),
        ("Quel est approximativement le temps de réaction d'un conducteur attentif ?",
         ["1 seconde", "0,1 seconde", "3 secondes", "5 secondes"], [0],
         "Le temps de réaction moyen est d'environ une seconde, durant lesquelles le véhicule continue de rouler."),
        ("Sur sol mouillé, la distance de freinage est environ :",
         ["Multipliée par 1,5 à 2", "Identique", "Réduite de moitié", "Multipliée par 10"], [0],
         "L'adhérence diminue : il faut compter une distance de freinage nettement plus longue."),
        ("Quels éléments forment la distance d'arrêt ?",
         ["La distance de réaction", "La distance de freinage", "La distance de sécurité", "La longueur du véhicule"], [0, 1],
         "Distance d'arrêt = distance parcourue pendant le temps de réaction + distance de freinage."),
        ("À partir de quelle vitesse, sur route sèche, la distance de réaction d'un conducteur attentif dépasse-t-elle 25 m ?",
         ["Au-delà de 90 km/h", "À partir de 50 km/h", "À partir de 30 km/h", "Jamais"], [0],
         "Environ 25 m sont parcourus pendant 1 seconde à 90 km/h."),
        ("Que signifie une ligne continue au milieu de la chaussée ?",
         ["Il est interdit de la franchir ou de la chevaucher", "Je peux la franchir pour dépasser", "Elle indique une zone de danger seulement", "Elle est facultative"], [0],
         "La ligne continue interdit de la franchir et de la chevaucher."),
        ("Je m'engage dans un giratoire signalé par un cédez le passage. Qui est prioritaire ?",
         ["Les véhicules qui circulent déjà sur l'anneau", "Ceux qui entrent", "Les plus rapides", "Les véhicules utilitaires"], [0],
         "Les véhicules déjà engagés sur l'anneau sont prioritaires."),
        ("Je veux tourner à gauche en agglomération. Que dois-je faire en priorité ?",
         ["Mettre mon clignotant, me placer à gauche et céder aux véhicules en face", "Tourner sans signaler", "Tourner en serrant à droite", "Accélérer avant d'être gêné"], [0],
         "On signale, on se positionne, et on cède le passage aux véhicules de face."),
        ("Quel panneau signale un octogone rouge ?",
         ["STOP", "Cédez le passage", "Interdiction de circuler", "Danger"], [0],
         "Le panneau STOP est le seul à avoir une forme octogonale."),
        ("Les feux de détresse peuvent être utilisés :",
         ["En cas de panne ou de danger imminent à signaler", "Pour se garer rapidement en double file", "Pour remercier un usager", "Toujours sous la pluie"], [0],
         "Ils servent à signaler un danger, une panne ou un ralentissement brutal."),
        ("Un panneau carré à fond bleu signale :",
         ["Une indication", "Une interdiction", "Un danger", "Une obligation"], [0],
         "Le fond bleu carré ou rectangulaire donne une indication ; rond bleu : obligation."),
        ("Dans quel ordre s'imposent les indications ?",
         ["Agent, feux, panneaux, règles générales", "Panneaux, feux, agent, règles", "Règles générales, panneaux, feux, agent", "Feux, agent, règles, panneaux"], [0],
         "Les ordres d'un agent priment sur les feux, qui priment sur les panneaux, puis les règles générales."),
        ("Un conducteur qui roule à 110 km/h au lieu de 90 km/h sur une route à 90 km/h commet :",
         ["Un excès de vitesse de 20 km/h", "Une simple tolérance", "Une infraction sans conséquences", "Aucune infraction si le temps est sec"], [0],
         "Tout dépassement de la vitesse maximale autorisée est une infraction, même de quelques km/h."),
        ("Pour mesurer la distance de sécurité par temps sec, on recommande de laisser au moins :",
         ["2 secondes", "0,5 seconde", "10 secondes", "Un mètre"], [0],
         "La règle des 2 secondes permet de garder une marge suffisante derrière le véhicule précédent."),
        ("Quand puis-je franchir une ligne discontinue pour dépasser ?",
         ["Lorsque j'ai constaté que la voie est libre et que la manœuvre est sûre", "Toujours", "Jamais", "Seulement le week-end"], [0],
         "La ligne discontinue autorise le franchissement, sous réserve de sécurité."),
    ],
}

# ---------------------------------------------------------------------------------------------------------------------
DATA['C'] = {
    'lessons': [
        ('vision-et-perception', "Vision, attention et temps de réaction", 8, """## Voir et percevoir

Le conducteur reçoit **plus de 90 % de ses informations par la vue**. Mais on ne voit pas de la même façon à toutes les vitesses :

- le **champ visuel se rétrécit** quand la vitesse augmente (à 100 km/h, on ne perçoit nettement qu'un cône très étroit devant soi) ;
- l'œil met du temps à s'adapter à l'obscurité ou à l'éblouissement ;
- la vision **périphérique** détecte le mouvement, la vision **centrale** les détails.

### Bien regarder
Portez le regard **loin devant** (12 à 15 secondes) et balayez : route, rétroviseurs, tableau de bord. Un regard fixé sur le capot réduit l'anticipation.

### Acuité et correction
Si le permis mentionne le port de **lunettes ou de lentilles**, elles sont obligatoires à chaque trajet. L'acuité exigée est d'au moins 5/10 aux deux yeux ensemble.

### Le temps de réaction
Il comprend la **perception**, la **décision** et l'**action**. Il est d'environ **1 seconde** pour un conducteur reposé, et il s'allonge avec la fatigue, l'alcool, certains médicaments et les distractions.
"""),
        ('alcool-et-stupefiants', "Alcool, stupéfiants et médicaments", 10, """## Alcool

- **Limite légale** : 0,5 g d'alcool par litre de sang (0,25 mg par litre d'air expiré).
- **0,2 g/l** pour les conducteurs en **permis probatoire**, les conducteurs accompagnés et les transports en commun.
- **Un verre standard** (25 cl de bière, 12,5 cl de vin, 3 cl de whisky) = environ **0,20 à 0,25 g/l**.
- L'organisme élimine environ **0,10 à 0,15 g/l par heure** : ni café, ni douche, ni air frais ne dégrisent plus vite.

### Effets
Euphorie et surestimation de ses capacités, **vision rétrécie**, **temps de réaction allongé**, difficulté à évaluer distances et vitesses.

### Sanctions
- de 0,5 à 0,8 g/l : contravention (135 €) et retrait de **6 points** ;
- à partir de 0,8 g/l : **délit** (jusqu'à 2 ans de prison, 4 500 € d'amende), suspension ou annulation du permis.

## Stupéfiants
Conduire après usage de stupéfiants est un **délit** (2 ans d'emprisonnement, 4 500 € d'amende, retrait de 6 points), quelle que soit la quantité. Les effets durent bien plus longtemps que la sensation.

## Médicaments
Les boîtes affichent un **pictogramme** :
- **niveau 1** (jaune) : soyez prudent ;
- **niveau 2** (orange) : soyez très prudent, demandez conseil ;
- **niveau 3** (rouge) : **ne conduisez pas** sans l'avis d'un médecin.
"""),
        ('fatigue-et-distracteurs', "Fatigue, distracteurs et téléphone", 8, """## La fatigue

Les signes : bâillements, paupières lourdes, picotements des yeux, douleurs dans la nuque, trajectoire qui dérive, perte de mémoire des derniers kilomètres.

### Agir avant le sommeil
- **Pause de 15 minutes toutes les 2 heures** (ou 200 km), même sans fatigue apparente ;
- pas de départ après une nuit trop courte ou un repas lourd ;
- une courte sieste de **15 à 20 minutes** est efficace ; ouvrir la fenêtre ou monter la radio ne le sont pas.

La fatigue est un **facteur majeur** d'accidents mortels, notamment sur autoroute la nuit et en début d'après-midi.

## Les distracteurs
Téléphone, GPS, passagers bruyants, radio, objets qui roulent, repas… Une attention détournée **2 secondes à 90 km/h** = 50 m parcourus en aveugle.

### Téléphone et écouteurs
- **Tenir** un téléphone en main en conduisant est interdit : **3 points** et **135 €** ; l'usage d'**écouteurs ou casque** également ;
- le **kit mains libres** est toléré mais reste dangereux : la conversation détourne l'attention ;
- la **lecture de SMS** multiplie fortement le risque d'accident.
"""),
        ('comportement-et-etat-physique', "Comportement, stress et état physique", 7, """## Le conducteur et son état

Le comportement dépend de la **condition physique** et **psychologique** : stress, colère, précipitation, euphorie, anxiété.

- **Agressivité** : la conduite agressive (appels de phares, queue de poisson, dépassements dangereux) augmente le risque d'accident pour tous.
- **Retard** : on part plus tôt plutôt que d'accélérer en route.
- **Excès de confiance** : surtout chez les jeunes conducteurs ou sur un trajet connu.
- **Âge** : les conducteurs âgés compensent par la prudence, mais leur temps de réaction et leur vision nocturne diminuent.

### Les bonnes habitudes
1. Vérifier son **état** avant de partir (sommeil, médicaments, émotions).
2. Anticiper : plus on voit loin, moins on freine fort.
3. Rester **courtois** : céder, remercier, ne pas répondre à l'agressivité.
4. Savoir **s'arrêter** quand l'on n'est pas en état de conduire.

### Les facteurs aggravants
Alcool + fatigue + vitesse, ou stupéfiants + alcool : les effets **s'additionnent** et se multiplient.
"""),
    ],
    'questions': [
        ("Quel est le taux maximal d'alcool dans le sang autorisé pour un conducteur confirmé ?",
         ["0,5 g/l", "0,8 g/l", "0,2 g/l", "1 g/l"], [0], "La limite générale est de 0,5 g/l de sang, soit 0,25 mg/l d'air expiré."),
        ("Quel est le taux maximal d'alcool pour un conducteur en permis probatoire ?",
         ["0,2 g/l", "0,5 g/l", "0,3 g/l", "0,0 g/l"], [0], "En permis probatoire, la limite est abaissée à 0,2 g/l."),
        ("Que faire pour éliminer plus vite l'alcool ?",
         ["Attendre : l'organisme l'élimine à son rythme", "Boire du café", "Prendre une douche froide", "Manger beaucoup"], [0],
         "Seul le temps permet d'éliminer l'alcool : environ 0,10 à 0,15 g/l par heure."),
        ("Un verre standard d'alcool représente environ :",
         ["0,20 à 0,25 g/l d'alcool dans le sang", "0,5 g/l", "0,05 g/l", "1 g/l"], [0], "Les verres servis dans les bars sont en général équivalents entre eux."),
        ("Quels sont les effets de l'alcool sur la conduite ?",
         ["Vision rétrécie", "Temps de réaction allongé", "Meilleure concentration", "Attention renforcée"], [0, 1],
         "L'alcool altère la vision, la perception des distances et rallonge le temps de réaction."),
        ("Après la prise de stupéfiants, conduire est :",
         ["Un délit, quelle que soit la quantité", "Autorisé si l'on se sent bien", "Toléré en petite quantité", "Interdit seulement la nuit"], [0],
         "La conduite après usage de stupéfiants constitue un délit."),
        ("Un médicament affiché avec un pictogramme rouge (niveau 3) signifie :",
         ["Ne pas conduire sans l'avis d'un médecin", "Être prudent", "Pas d'effet sur la conduite", "Conduire seulement de jour"], [0],
         "Le niveau 3 correspond à un médicament qui rend la conduite dangereuse."),
        ("Quelle pause est recommandée lors d'un long trajet ?",
         ["Environ 15 minutes toutes les 2 heures", "5 minutes toutes les 4 heures", "Aucune si on n'est pas fatigué", "1 heure par 100 km"], [0],
         "Faire une pause régulière retarde l'apparition de la fatigue."),
        ("Quels sont des signes de fatigue au volant ?",
         ["Bâillements", "Paupières lourdes", "Trajectoire qui dérive", "Envie de chanter"], [0, 1, 2], "Il faut s'arrêter dès l'apparition de ces signes."),
        ("Pour combattre la somnolence, le plus efficace est :",
         ["De faire une courte sieste", "D'ouvrir la fenêtre", "De mettre la radio fort", "De boire du café et de continuer"], [0],
         "Seul le sommeil permet de récupérer la vigilance."),
        ("Tenir un téléphone en main en conduisant est puni de :",
         ["3 points et 135 € d'amende", "Aucune sanction", "1 point", "6 points"], [0],
         "Le téléphone tenu en main est interdit, tout comme l'usage d'écouteurs ou casque."),
        ("Le champ visuel du conducteur, quand la vitesse augmente :",
         ["Se rétrécit", "S'élargit", "Reste identique", "Devient plus précis"], [0], "Plus on roule vite, plus on voit un cône étroit devant soi."),
        ("Que signifie un temps de réaction allongé ?",
         ["La distance parcourue avant de freiner est plus longue", "Le véhicule freine mieux", "L'adhérence augmente", "Le freinage ABS s'active"], [0],
         "Un temps de réaction plus long augmente la distance d'arrêt."),
        ("Quels conducteurs doivent respecter 0,2 g/l ?",
         ["Titulaires du permis probatoire", "Conducteurs de transport en commun", "Conducteurs de plus de 70 ans", "Tous les conducteurs"], [0, 1],
         "0,2 g/l s'applique aux permis probatoires, à la conduite accompagnée et aux transports en commun."),
        ("Je dois conduire après une nuit blanche. Que dois-je faire ?",
         ["Éviter de conduire ou prévoir de dormir avant", "Prendre un café et partir", "Rouler plus vite pour arriver tôt", "Mettre la climatisation"], [0],
         "La fatigue est comparable à l'effet d'une alcoolémie importante."),
        ("Le port de lunettes mentionné sur le permis est :",
         ["Obligatoire à chaque conduite", "Facultatif de jour", "Facultatif en agglomération", "Obligatoire seulement la nuit"], [0],
         "La mention des verres correcteurs sur le permis s'impose à tous les trajets."),
        ("Quelle est la distance parcourue en 2 secondes d'inattention à 90 km/h ?",
         ["Environ 50 m", "Environ 5 m", "Environ 10 m", "Environ 100 m"], [0], "À 90 km/h, on parcourt 25 m par seconde."),
        ("Un conducteur énervé peut :",
         ["Adopter une conduite à risque", "Mieux anticiper", "Réduire ses distances de sécurité", "Améliorer sa vigilance"], [0, 2],
         "La colère altère le jugement ; il vaut mieux s'arrêter et se calmer."),
        ("Vous avez pris un médicament somnifère le soir précédent. Vous devez :",
         ["Vous assurer de l'avoir éliminé avant de conduire", "Conduire normalement", "Rouler en feux de croisement", "Mettre la radio"], [0],
         "Certains médicaments gardent leurs effets plusieurs heures après la prise."),
    ],
}

# ---------------------------------------------------------------------------------------------------------------------
DATA['R'] = {
    'lessons': [
        ('conduite-de-nuit', "Conduire de nuit", 7, """## La nuit : moins de visibilité, plus de risques

- Le **champ de vision** et la perception des couleurs se réduisent ; les distances sont mal appréciées.
- L'**éblouissement** par les phares d'en face est dangereux : on regarde le **bord droit de la chaussée** (ligne de rive) pour rester en trajectoire.

### Équipements et réglages
1. Feux de **croisement** en agglomération, **route** en rase campagne quand personne n'est en face.
2. Phares **propres et réglés** (la hauteur dépend de la charge).
3. **Pare-brise** propre : la buée et les traces augmentent l'éblouissement.
4. Réduire la vitesse : **la distance d'arrêt reste identique** mais on voit moins loin que sa distance d'arrêt.

### Les obstacles imprévus
Animaux sauvages (zones forestières), piétons peu visibles, cyclistes sans éclairage : la **vitesse adaptée** est la meilleure protection.

### La fatigue
Entre 2 h et 5 h du matin la vigilance est au plus bas ; planifiez des pauses ou dormez.
"""),
        ('pluie-brouillard-neige', "Pluie, brouillard, neige et verglas", 9, """## Pluie
- La distance de freinage est **multipliée par 1,5 à 2**.
- **Aquaplaning** : une pellicule d'eau sépare les pneus du sol. Réaction : **lever le pied de l'accélérateur**, ne pas freiner brutalement, tenir le volant fermement.
- Limite : **110 km/h** sur autoroute, **100 km/h** sur voie à chaussées séparées, **80 km/h** sur route normale (sauf plus bas).

## Brouillard
- **Visibilité inférieure à 50 m** : **50 km/h** maximum, feux de croisement, antibrouillards autorisés.
- Ne pas rouler à la lueur des feux du véhicule précédent ; garder une distance suffisante.

## Neige et verglas
- Chaînes ou **pneus hiver** selon les panneaux ; départ en douceur, **2ᵉ vitesse**.
- Freiner en **ligne droite**, **par petites touches** (si pas d'ABS), anticiper les ralentissements.
- Les **ponts et ombres** givrent d'abord. En cas de **verglas**, ne pas freiner dans un virage.

## Vent latéral
Sortie d'un tunnel, viaduc, trouée : tenir le volant des **deux mains**, ralentir, attention aux camions et caravanes.
"""),
        ('autoroute-et-voie-rapide', "Autoroute et voie rapide", 9, """## Entrer sur l'autoroute
- Sur la **voie d'accélération**, on atteint la vitesse du trafic **avant** de s'insérer : **le véhicule déjà sur l'autoroute est prioritaire**.
- Clignotant à gauche, regard dans le rétroviseur, **angle mort**.

## Rouler
- **Voie de droite** par défaut ; on se rabat dès que possible après un dépassement.
- **Vitesse minimale** : 80 km/h sur la voie de gauche (hors conditions particulières).
- **Distance de sécurité** : 2 secondes, 3 s par pluie ; les **chevrons** au sol indiquent une distance correcte.
- **Interdits** : demi-tour, marche arrière, arrêt ou stationnement sur la chaussée et sur la **bande d'arrêt d'urgence** (hors urgence).

## Panne ou accident
1. Allumer les **feux de détresse** et rejoindre la **bande d'arrêt d'urgence** ;
2. enfiler le **gilet**, sortir du côté droit, se mettre **derrière la glissière** ;
3. **alerter** via la borne d'appel orange ou le 112 ;
4. ne pas poser le triangle si c'est dangereux.

## Sortir
Se placer à droite **à l'avance**, clignotant, **décélérer sur la voie de sortie** (pas sur l'autoroute).
"""),
        ('adherence-et-obstacles', "Adhérence, chaussée et obstacles", 7, """## L'adhérence
Elle dépend de l'état des **pneus** (pression, profondeur de sculpture ≥ 1,6 mm), de la **chaussée** (sèche, mouillée, enneigée, gravillonnée), de la **vitesse** et des **sollicitations** (freinage, virage).

### Les situations délicates
| Situation | Conduite adaptée |
|---|---|
| Gravillons | Réduire, éviter les à-coups, augmenter les distances |
| Feuilles mortes, boue | Freiner doucement, éviter les trajectoires serrées |
| Flaques / eau | Ralentir ; **tester les freins** après passage dans l'eau |
| Chaussée déformée | Réduire, tenir fermement le volant |
| Virages | Freiner **avant** le virage, accélérer légèrement en sortie |

### Passage à gué, inondation
Ne jamais s'engager sans connaître la profondeur ; en cas de doute, **faire demi-tour**.

### Chute d'objets / animaux
On évite si c'est possible **sans** changer brutalement de file ; sinon on freine fort en ligne droite plutôt que de risquer un écart.
"""),
    ],
    'questions': [
        ("Par temps de brouillard (visibilité < 50 m), la vitesse maximale est de :",
         ["50 km/h", "70 km/h", "30 km/h", "80 km/h"], [0], "Lorsque la visibilité est inférieure à 50 m, on est limité à 50 km/h sur tous les réseaux."),
        ("En cas d'aquaplaning, je dois :",
         ["Lever le pied de l'accélérateur et tenir le volant", "Freiner à fond", "Braquer brusquement", "Accélérer"], [0],
         "Freiner ou braquer brutalement fait perdre le contrôle ; il faut laisser le véhicule ralentir."),
        ("Par temps de pluie, la vitesse maximale sur autoroute est de :",
         ["110 km/h", "130 km/h", "100 km/h", "90 km/h"], [0], "Sur autoroute : 110 km/h par temps de pluie."),
        ("Sur une route à deux voies, avec des chaussées séparées, sous la pluie, la vitesse maximale est de :",
         ["100 km/h", "110 km/h", "80 km/h", "90 km/h"], [0], "Les voies à chaussées séparées sont limitées à 100 km/h par temps de pluie."),
        ("La nuit, quand un véhicule vous éblouit, vous devez :",
         ["Regarder le bord droit de la chaussée", "Fermer les yeux", "Passer en feux de route", "Freiner brutalement"], [0],
         "On évite l'éblouissement en portant le regard vers la ligne de rive."),
        ("Sur autoroute, je suis en panne. Que dois-je faire ?",
         ["Rejoindre la bande d'arrêt d'urgence, mettre le gilet, me placer derrière la glissière", "Rester dans le véhicule", "Poser le triangle sur la voie", "Traverser l'autoroute"], [0],
         "Les occupants se protègent derrière la glissière et alertent par la borne ou le 112."),
        ("Sur voie d'accélération, c'est :",
         ["Le véhicule déjà sur l'autoroute qui est prioritaire", "Le véhicule qui s'insère qui est prioritaire", "Le plus rapide qui est prioritaire", "Le plus lourd qui est prioritaire"], [0],
         "L'insertion se fait en cédant le passage aux véhicules qui circulent déjà sur l'autoroute."),
        ("Quelle est la vitesse minimale sur la voie de gauche d'une autoroute ?",
         ["80 km/h", "50 km/h", "100 km/h", "60 km/h"], [0], "La voie de gauche ne doit pas être occupée par un véhicule trop lent."),
        ("Il est interdit sur autoroute de :",
         ["Faire demi-tour", "Rouler sur la voie de droite", "Dépasser par la gauche", "Utiliser la voie d'insertion"], [0],
         "Demi-tour et marche arrière sont strictement interdits sur autoroute."),
        ("Par temps de pluie, la distance de sécurité conseillée est d'au moins :",
         ["3 secondes", "1 seconde", "0,5 seconde", "10 secondes"], [0], "On double presque la distance par rapport au temps sec."),
        ("Sur une route verglacée, je dois :",
         ["Réduire ma vitesse et freiner en ligne droite avec douceur", "Freiner dans le virage", "Rouler vite pour garder la trajectoire", "Rétrograder brusquement"], [0],
         "Aucune manœuvre brusque : volant, frein et accélérateur doivent être maniés très doucement."),
        ("Après la traversée d'une flaque profonde, je dois :",
         ["Tester mes freins en roulant doucement", "Accélérer", "Ne rien faire", "Rouler en feux de détresse"], [0],
         "L'eau diminue l'efficacité des freins : on les sèche en les sollicitant légèrement."),
        ("Quelle est la profondeur minimale de la sculpture des pneus ?",
         ["1,6 mm", "1 mm", "3 mm", "0,5 mm"], [0], "En dessous de 1,6 mm, les pneus sont hors la loi et dangereux sous la pluie."),
        ("La nuit, hors agglomération, sans véhicule en face, j'utilise :",
         ["Les feux de route", "Les feux de brouillard", "Les feux de détresse", "Les feux de position seuls"], [0],
         "Les feux de route offrent une meilleure visibilité, à condition de ne pas éblouir."),
        ("Que signifie la présence de chevrons sur l'autoroute ?",
         ["Ils permettent d'apprécier la distance de sécurité", "Une zone de travaux", "Un passage piéton", "Un radar"], [0],
         "Deux chevrons visibles entre vous et le véhicule précédent indiquent une distance de 2 secondes."),
        ("Le vent latéral est le plus dangereux :",
         ["À la sortie d'un tunnel ou sur un viaduc", "En ville", "En forêt", "Sur chaussée sèche uniquement"], [0],
         "Un souffle latéral soudain peut dévier le véhicule : on tient le volant fermement."),
    ],
}

# ---------------------------------------------------------------------------------------------------------------------
DATA['U'] = {
    'lessons': [
        ('pietons-et-passages', "Piétons et passages protégés", 7, """## Les piétons : des usagers vulnérables

Un piéton est prioritaire sur un **passage protégé** et quand il manifeste clairement l'intention de traverser ou est déjà engagé : le conducteur **ralentit et s'arrête**.

- **Passage piéton** : s'arrêter dès qu'un piéton s'engage ou **manifeste l'intention** de s'engager.
- **Tourner** dans une rue : céder aux piétons qui traversent la voie où l'on s'engage.
- **Zone de rencontre** (20 km/h) : le piéton est prioritaire et peut marcher sur la chaussée.
- **Zone 30** : vitesse limitée, double sens cyclable fréquent.

### Les piétons à risque
- **Enfants** : imprévisibles, petits donc peu visibles ; ralentir aux abords des écoles.
- **Personnes âgées ou handicapées** : traversée lente, ne pas klaxonner.
- Piéton avec **canne blanche** ou chien-guide : arrêt absolu.

### Sanction
Ne pas céder au piéton engagé : **4 points** et **135 €**.
"""),
        ('cyclistes-et-deux-roues', "Cyclistes, deux-roues motorisés et EDPM", 9, """## Les deux-roues

### Cyclistes
- Ils peuvent rouler **à deux de front** et en double sens dans certaines zones.
- **Sas vélo** : zone devant les feux, réservée aux cyclistes ; les voitures s'arrêtent derrière.
- **Dépassement** : 1 m en agglomération, 1,5 m hors agglomération ; on ne se rabat pas sans visibilité.
- **Angle mort** : avant de tourner à droite, vérifier le rétroviseur et l'angle mort pour ne pas « couper » un cycliste.
- **Ouverture de portière** : de la main éloignée.

### Motos et scooters
- Ils **se faufilent** (circulation inter-files autorisée dans certaines conditions) : regarder les rétroviseurs avant de changer de voie.
- Un deux-roues paraît plus loin et plus lent qu'il n'est : **attention à la sortie d'intersection**.
- Au freinage, la distance d'arrêt est comparable à celle d'une voiture.

### Engins de déplacement personnel (trottinettes…)
Ils circulent sur les pistes cyclables ou la chaussée en agglomération (pas sur le trottoir), limités à **25 km/h**. Mêmes précautions que pour les cyclistes.
"""),
        ('poids-lourds-et-transports', "Poids lourds, bus, tramways et véhicules prioritaires", 8, """## Les véhicules lourds

- **Angles morts** : le long du poids lourd, à droite et derrière ; si je ne vois pas son conducteur dans son rétroviseur, il ne me voit pas.
- **Distance d'arrêt** : bien plus longue qu'une voiture ; ne jamais se rabattre juste devant.
- **Virages** : un camion peut déborder sur la voie voisine ; laisser de l'espace.

## Bus et cars
- **Bus qui quitte son arrêt** en agglomération : **priorité** au bus, qui signale par son clignotant.
- Une **navette scolaire** à l'arrêt : prudence aux piétons, notamment des enfants qui traversent.

## Tramways
Ils sont **prioritaires** sur les voies partagées. La voie du tramway est interdite aux véhicules, sauf à l'approche d'un carrefour pour tourner.

## Véhicules prioritaires
Gyrophare bleu et sirène (police, pompiers, SAMU, ambulance) : je **facilite leur passage** en serrant à droite et en m'arrêtant si nécessaire. Je ne passe **jamais** un feu rouge pour les laisser passer sans m'assurer d'être en sécurité.
"""),
        ('partager-la-route', "Partager la route : comportement et courtoisie", 6, """## Une route, plusieurs usagers

Les règles du Code protègent d'abord les **plus vulnérables** : piétons, cyclistes, deux-roues motorisés, personnes à mobilité réduite, enfants et seniors.

### Principes
- **Anticiper** le comportement des autres : hésitation d'un piéton, ballon qui roule, portière qui s'ouvre.
- **Ne pas klaxonner** pour presser un usager lent ; l'avertisseur sert à prévenir d'un danger.
- **Céder** le passage quand la règle l'exige, mais aussi quand la situation le recommande.
- **Rester calme** face à un comportement incorrect : la sécurité l'emporte sur le droit.

### Situations particulières
- **Troupeaux et cavaliers** : ralentir, ne pas klaxonner, laisser un grand espace.
- **Chantiers** : respecter les panneaux et les ordres du signaleur.
- **Véhicules agricoles / lents** : ne dépasser qu'après vérification de la visibilité.
- **Personne handicapée** : ne jamais stationner sur ses places réservées.
"""),
    ],
    'questions': [
        ("Un piéton manifeste l'intention de traverser sur un passage protégé. Je dois :",
         ["Ralentir et m'arrêter pour le laisser passer", "Passer en klaxonnant", "Accélérer", "Passer s'il est loin"], [0],
         "Le conducteur doit céder le passage au piéton engagé ou manifestant l'intention de traverser."),
        ("Ne pas céder le passage à un piéton régulièrement engagé est sanctionné par :",
         ["4 points et 135 €", "Aucune sanction", "1 point", "6 points"], [0], "L'infraction est lourdement sanctionnée pour protéger les piétons."),
        ("Quelle distance latérale minimale pour dépasser un cycliste en agglomération ?",
         ["1 m", "1,5 m", "0,5 m", "2 m"], [0], "1 m en agglomération, 1,5 m hors agglomération."),
        ("Un sas vélo est :",
         ["Une zone devant les feux réservée aux cyclistes", "Un parking", "Une piste de bus", "Un trottoir"], [0],
         "Les automobilistes s'arrêtent derrière la zone du sas vélo."),
        ("Quelle est la vitesse maximale dans une zone de rencontre ?",
         ["20 km/h", "30 km/h", "50 km/h", "10 km/h"], [0], "En zone de rencontre, les piétons sont prioritaires et la vitesse limitée à 20 km/h."),
        ("En agglomération, je vois un autobus qui signale son départ de l'arrêt. Je dois :",
         ["Le laisser repartir", "Accélérer pour le doubler", "Klaxonner", "Le suivre de très près"], [0],
         "En agglomération, le bus qui quitte son arrêt est prioritaire s'il signale son intention."),
        ("À proximité d'un poids lourd, quel est le principal danger ?",
         ["Les angles morts", "Le bruit", "Les vibrations", "L'éblouissement"], [0], "Un poids lourd ne voit pas ce qui est à droite et derrière lui."),
        ("Un véhicule d'urgence (gyrophare et sirène) approche. Je dois :",
         ["Faciliter son passage en me garant si besoin", "Accélérer pour le devancer", "Ne rien faire", "Passer au feu rouge sans vérifier"], [0],
         "Les véhicules prioritaires sont à laisser passer, en sécurité."),
        ("Quelle vitesse maximale pour une trottinette électrique ?",
         ["25 km/h", "40 km/h", "50 km/h", "15 km/h"], [0], "La vitesse des EDPM est limitée à 25 km/h."),
        ("Pour ne pas « couper » un cycliste avant de tourner à droite, je dois :",
         ["Vérifier le rétroviseur droit et l'angle mort", "Klaxonner", "Accélérer", "Allumer mes feux de détresse"], [0],
         "Les cyclistes et deux-roues se glissent souvent dans l'angle mort."),
        ("Les deux-roues motorisés paraissent souvent :",
         ["Plus loin et plus lents qu'ils ne sont", "Plus proches", "À vitesse réelle", "Plus gros"], [0],
         "Ils sont étroits : on sous-estime leur vitesse et on s'engage trop tôt."),
        ("Une personne avec une canne blanche s'apprête à traverser. Je dois :",
         ["M'arrêter et attendre", "Klaxonner", "L'éviter à vive allure", "Passer doucement derrière elle"], [0],
         "Elle est prioritaire et son handicap la rend particulièrement vulnérable."),
        ("Comment ouvrir la portière sur le côté de la circulation ?",
         ["De la main éloignée, après avoir regardé dans le rétroviseur", "Brusquement", "De la main proche", "Sans regarder"], [0],
         "La main éloignée oblige à tourner le buste et à voir arriver les deux-roues."),
        ("Un tramway et moi arrivons à un carrefour sans feux. Qui est prioritaire ?",
         ["Le tramway", "Moi", "Le plus rapide", "Le plus lourd"], [0], "Le tramway est prioritaire sur les voies sur lesquelles il circule."),
        ("Que faire à l'approche d'un car scolaire à l'arrêt, enfants descendant ?",
         ["Ralentir fortement et rester très vigilant", "Accélérer pour dépasser", "Klaxonner", "Passer à pleine vitesse"], [0],
         "Les enfants peuvent traverser à tout moment sans regarder."),
    ],
}

# ---------------------------------------------------------------------------------------------------------------------
DATA['D'] = {
    'lessons': [
        ('documents-et-assurance', "Les documents et l'assurance", 7, """## Documents à présenter

À chaque contrôle, le conducteur doit pouvoir présenter :
- le **permis de conduire** correspondant à la catégorie du véhicule ;
- le **certificat d'immatriculation** (carte grise) ;
- le **justificatif d'assurance** du véhicule.

### Le certificat d'immatriculation
Au nom du propriétaire. Toute **modification d'adresse** ou de propriétaire doit être déclarée sous **1 mois**.

### L'assurance
Elle est **obligatoire** pour tout véhicule terrestre à moteur, même à l'arrêt sur la voie publique. La **responsabilité civile** couvre les dommages causés aux tiers ; les garanties complémentaires (tous risques, bris de glace, vol) sont facultatives.

### En cas d'accident
Remplir le **constat amiable** (dans les **5 jours ouvrés**, à déclarer à l'assureur). Le **bonus-malus** (coefficient de réduction-majoration) augmente avec les sinistres où l'on est responsable.

### Contrôle technique
Pour les véhicules particuliers : **avant les 4 ans** du véhicule, puis **tous les 2 ans**.
"""),
        ('permis-a-points', "Le permis à points", 9, """## Le capital de points

| Permis | Capital |
|---|---|
| Permis **probatoire** (3 ans, 2 ans avec conduite accompagnée) | **6 points** |
| Permis définitif | **12 points** |

En permis probatoire, le capital augmente de **+2 points par an** sans infraction (**+3** après une conduite accompagnée) jusqu'à 12 points au bout de 3 ans (2 ans si conduite accompagnée).

### Retraits fréquents
| Infraction | Points | Amende |
|---|---|---|
| Téléphone tenu en main | **3** | 135 € |
| Non-port de la ceinture | **3** | 135 € |
| Excès de vitesse ≥ 50 km/h | **6** | délit |
| Excès de vitesse < 20 km/h | **1** | 68 € (135 € si la limite est ≤ 50 km/h) |
| Alcool entre 0,5 et 0,8 g/l | **6** | 135 € |
| Feu rouge grillé | **4** | 135 € |

### Récupérer des points
- **6 mois** sans infraction : récupération d'**1 point** pour un retrait d'1 point ;
- **2 ans** sans infraction : récupération totale ;
- **3 ans** pour les retraits liés à des délits ou contraventions de 4ᵉ/5ᵉ classe ;
- **Stage de sensibilisation** à la sécurité routière : jusqu'à **4 points** récupérés, une fois par an.

### 0 point
Le permis est **invalidé** : remise du permis à la préfecture dans les 10 jours, nouveau passage de l'examen après un délai.
"""),
        ('infractions-et-sanctions', "Infractions et sanctions", 8, """## Les trois catégories

- **Contravention** (classes 1 à 5) : amende, éventuellement retrait de points, suspension ;
- **Délit** : tribunal correctionnel, jusqu'à plusieurs années de prison, retrait de points, suspension ou annulation ;
- **Crime** : cour d'assises (rare en matière routière).

### Exemples de délits
- alcool ≥ 0,8 g/l, stupéfiants, **refus d'obtempérer**, **délit de fuite** après un accident ;
- **conduite sans permis** ou **sans assurance** ;
- **grand excès de vitesse** (≥ 50 km/h au-dessus de la limite).

### Sanctions complémentaires
Suspension ou **annulation** du permis, **immobilisation** ou **confiscation** du véhicule, stage obligatoire, travaux d'intérêt général.

### Responsabilité
Le **titulaire de la carte grise** est redevable pécuniairement de certaines amendes (excès de vitesse, feu rouge, stationnement) s'il ne désigne pas le conducteur.
"""),
        ('equipements-obligatoires', "Équipements et contrôle du véhicule", 6, """## Équipements obligatoires à bord

- **Gilet de haute visibilité** : accessible depuis l'habitacle (pas dans le coffre) ;
- **Triangle de présignalisation** : à poser à **30 m minimum** en amont d'un danger (sauf sur autoroute, où l'on évite de s'exposer) ;
- **Éthylotest** : plus de sanction mais recommandé ;
- **Plaque d'immatriculation** lisible, avant et arrière ;
- **Feux, clignotants, essuie-glaces, pneus** en bon état.

### Interdits
- **Détecteurs de radars** ;
- Vitres teintées sur les surfaces vitrées avant (transparence minimale requise) ;
- **Pneus lisses** ou à la sculpture < 1,6 mm.

### Entretien et sécurité
Un véhicule en mauvais état (freins, éclairage, pneus) engage la **responsabilité du conducteur** et peut entraîner une amende, voire l'immobilisation.
"""),
    ],
    'questions': [
        ("Quels documents dois-je présenter lors d'un contrôle ?",
         ["Le permis de conduire", "Le certificat d'immatriculation", "Le justificatif d'assurance", "Le carnet d'entretien"], [0, 1, 2],
         "Permis, carte grise et justificatif d'assurance."),
        ("Combien de points compte le permis probatoire au départ ?",
         ["6", "12", "8", "10"], [0], "Le permis probatoire démarre avec 6 points, puis +2 par an sans infraction."),
        ("Quelle est la sanction pour téléphone tenu en main au volant ?",
         ["3 points et 135 €", "1 point et 35 €", "6 points et 750 €", "Aucune"], [0], "L'usage du téléphone tenu en main au volant est sanctionné par 3 points et 135 €."),
        ("Après combien de temps sans infraction récupère-t-on la totalité de ses points ?",
         ["2 ans", "6 mois", "1 an", "5 ans"], [0], "Au bout de 2 ans sans infraction, le capital est reconstitué (3 ans pour certaines infractions plus graves)."),
        ("Quelle est la durée maximale de récupération de points grâce à un stage ?",
         ["4 points", "2 points", "6 points", "12 points"], [0], "Un stage permet de récupérer jusqu'à 4 points, une fois par an."),
        ("Combien d'années peut durer le permis probatoire ?",
         ["3 ans (2 ans avec conduite accompagnée)", "1 an", "5 ans", "6 mois"], [0], "La durée du probatoire est réduite à 2 ans si l'on a suivi la conduite accompagnée."),
        ("L'assurance responsabilité civile couvre :",
         ["Les dommages causés aux tiers", "Les dommages causés à mon véhicule", "Les dommages causés à moi-même", "Rien"], [0],
         "C'est la garantie minimale obligatoire : les dommages aux autres."),
        ("Le contrôle technique d'un véhicule particulier est obligatoire :",
         ["Avant 4 ans, puis tous les 2 ans", "Tous les ans", "Tous les 5 ans", "Après 10 ans"], [0], "Premier contrôle avant les 4 ans, puis tous les 2 ans."),
        ("Un excès de vitesse de 50 km/h ou plus est :",
         ["Un délit", "Une simple contravention", "Toléré sur autoroute", "Sans retrait de points"], [0], "Il peut conduire à une peine de prison, une suspension, voire une confiscation du véhicule."),
        ("Après un accident, le constat amiable doit être transmis à l'assureur dans les :",
         ["5 jours ouvrés", "48 heures", "1 mois", "6 mois"], [0], "La déclaration du sinistre doit être faite dans les 5 jours ouvrés."),
        ("Le triangle de présignalisation doit être placé à :",
         ["30 mètres au moins en amont du danger", "10 mètres", "100 mètres", "Contre le véhicule"], [0], "Pour laisser le temps aux autres usagers de réagir."),
        ("Le gilet de haute visibilité doit être :",
         ["Accessible depuis l'habitacle", "Dans le coffre", "Sous la banquette", "Dans le sac à dos"], [0], "Le conducteur doit pouvoir l'enfiler avant de sortir du véhicule."),
        ("La conduite sans assurance est :",
         ["Un délit", "Une simple contravention", "Tolérée si le véhicule est à l'arrêt", "Interdite seulement la nuit"], [0], "Le défaut d'assurance est un délit sévèrement puni."),
        ("Le propriétaire du véhicule doit déclarer son changement d'adresse sur la carte grise sous :",
         ["1 mois", "6 mois", "1 an", "1 semaine"], [0], "La déclaration est à faire dans le mois suivant le déménagement."),
    ],
}

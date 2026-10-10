"""Programme ETG — contenus rédigés pour les thèmes P, M, S, E, A (même structure que curriculum_1)."""

DATA = {}

# ---------------------------------------------------------------------------------------------------------------------
DATA['P'] = {
    'lessons': [
        ('verifications-avant-depart', "Vérifications avant le départ", 7, """## Avant de démarrer

Un tour du véhicule de **30 secondes** évite bien des surprises.

1. **Pneus** : état apparent, pression (à froid), absence de hernie ou de corps étranger.
2. **Éclairage** : feux de position, croisement, stop, clignotants (se faire aider ou utiliser un reflet).
3. **Vitres, rétroviseurs et plaques** propres et dégagées.
4. **Chargement** : arrimé, sans masquer vitres ni éclairage ; ne dépasse pas le **poids total autorisé (PTAC)**.
5. **Autour du véhicule** : enfants, animaux, obstacles.

### Chargement et galerie
Les objets lourds au **plus bas** et au **plus près du centre** ; on ne conduit jamais avec un objet sur la plage arrière susceptible de devenir un projectile en cas de freinage brutal.

### Le contrôle de niveaux
Huile, liquide de refroidissement, lave-glace : à vérifier **régulièrement** et avant un long trajet, moteur froid sur terrain plat.
"""),
        ('poste-de-conduite', "Le poste de conduite et la position", 8, """## S'installer

L'ordre à respecter :
1. **Siège** : distance aux pédales — jambe légèrement fléchie quand la pédale d'embrayage est enfoncée à fond ;
2. **Dossier** : incliné d'environ 110°, bien plaqué ; épaules en contact avec le dossier ;
3. **Volant** : hauteur et profondeur — les bras légèrement fléchis, **poignets** au-dessus du volant à bout de bras ;
4. **Appuis-tête** : sommet de la tête à la hauteur du haut de l'appui-tête, au plus près de la nuque (limite le **coup du lapin**) ;
5. **Rétroviseurs** : intérieur centré sur la lunette arrière, extérieurs en effleurant à peine la carrosserie ;
6. **Ceinture** : sangle plaquée **sur l'épaule** et **sur le bassin**, jamais sous le bras ni lâche.

### Position des mains
**« 9 h 15 »** ou **« 10 h 10 »** sur le volant. Les pouces à l'extérieur, jamais à l'intérieur des branches.

### Les commandes
Connaître l'emplacement de : feux, clignotants, essuie-glaces, désembuage, feux de détresse, avertisseur sonore.
"""),
        ('passagers-et-enfants', "Passagers, enfants et animaux", 7, """## Les passagers

- **Ceinture obligatoire** à toutes les places, y compris à l'arrière. Le conducteur est responsable des mineurs.
- Non-port de la ceinture : **3 points et 135 €**.
- Les objets lourds ne doivent **pas** être posés sur les genoux ou la plage arrière.

## Les enfants
- **Jusqu'à 10 ans** : dispositif de retenue **homologué** adapté à la taille et au poids (siège coque, rehausseur).
- Un enfant de **moins de 10 ans** voyage en principe à l'**arrière** ; devant seulement si c'est la seule place disponible et que l'airbag passager est **désactivé** pour un siège « dos à la route ».
- Le siège **dos à la route** est conseillé le plus longtemps possible (au moins jusqu'à 15 mois).
- Ne **jamais laisser un enfant seul** dans un véhicule (chaleur, verrouillage, démarrage accidentel).

## Les animaux
Ils doivent être **transportés de manière à ne pas gêner** la conduite (cage, filet, ceinture adaptée). Un animal non retenu devient un projectile en cas de choc.
"""),
    ],
    'questions': [
        ("Jusqu'à quel âge un dispositif de retenue adapté est-il obligatoire pour les enfants ?",
         ["10 ans", "6 ans", "12 ans", "3 ans"], [0], "Jusqu'à 10 ans, l'enfant doit être retenu par un dispositif adapté à sa morphologie."),
        ("La ceinture de sécurité est obligatoire :",
         ["À toutes les places, avant et arrière", "Uniquement à l'avant", "Uniquement sur autoroute", "Uniquement hors agglomération"], [0], "Chaque occupant doit être attaché."),
        ("L'appui-tête doit être réglé de façon que :",
         ["Le haut de l'appui-tête soit à hauteur du sommet de la tête", "Il soit au plus bas", "Il soit au niveau des épaules", "Il soit retiré"], [0],
         "Il limite le risque de blessures cervicales (« coup du lapin »)."),
        ("La ceinture doit passer :",
         ["Sur l'épaule et sur le bassin", "Sous le bras", "Sur le ventre", "Derrière le dos"], [0], "Elle doit être plaquée sur le corps pour répartir les forces."),
        ("Pour un enfant en siège dos à la route placé à l'avant, il faut :",
         ["Désactiver l'airbag passager", "Laisser l'airbag actif", "Mettre un coussin", "Reculer le siège"], [0],
         "L'airbag, en se déployant, pourrait blesser gravement l'enfant."),
        ("Les bras doivent être légèrement fléchis quand on tient le volant :",
         ["Vrai", "Faux"], [0], "Une position trop éloignée réduit la précision et la réactivité."),
        ("Quelle position de mains sur le volant est recommandée ?",
         ["9 h 15 ou 10 h 10", "Une main à 6 h", "Sur la jante inférieure", "À l'intérieur des branches"], [0], "Elle garantit un contrôle optimal et évite de se blesser avec l'airbag."),
        ("Le conducteur est responsable de la ceinture :",
         ["Des passagers mineurs", "De tous les passagers majeurs", "Aucun passager", "Des enfants uniquement à l'arrière"], [0],
         "Il doit s'assurer que les mineurs sont correctement retenus."),
        ("Avant de partir, je vérifie :",
         ["L'état des pneus et les feux", "La couleur de la carrosserie", "Le niveau du réservoir d'essence uniquement", "Rien"], [0, 1],
         "Les vérifications simples évitent pannes et accidents."),
        ("Où réglez-vous le rétroviseur intérieur ?",
         ["Pour voir toute la lunette arrière", "Pour voir la banquette", "Vers le haut", "Vers la portière"], [0], "Il doit permettre de voir la route derrière le véhicule sans bouger la tête."),
        ("Un enfant seul dans un véhicule à l'arrêt :",
         ["Ne doit jamais y être laissé", "Peut y rester 10 minutes", "Peut y rester s'il dort", "Peut y rester avec la fenêtre ouverte"], [0],
         "Chaleur, risque d'enfermement et de démarrage accidentel : il ne faut jamais laisser un enfant seul."),
        ("Un objet lourd non arrimé dans l'habitacle :",
         ["Devient un projectile en cas de freinage brusque", "N'a aucun effet", "Améliore la stabilité", "Doit être posé sur la plage arrière"], [0],
         "À 50 km/h, un objet de 1 kg équivaut à plusieurs dizaines de kilos lors d'un choc."),
    ],
}

# ---------------------------------------------------------------------------------------------------------------------
DATA['M'] = {
    'lessons': [
        ('voyants-et-tableau-de-bord', "Les voyants du tableau de bord", 8, """## Lire son tableau de bord

| Couleur | Signification | Que faire ? |
|---|---|---|
| **Rouge** | Danger immédiat | **Arrêtez-vous** dès que possible, en sécurité |
| **Orange** | Anomalie à contrôler | Faites vérifier **rapidement** |
| **Vert / bleu** | Information (feux, régulateur) | Rien à faire |

### Les voyants rouges à connaître
- **Pression d'huile** : arrêt immédiat, moteur coupé.
- **Température du liquide de refroidissement** : arrêt, laisser refroidir, **ne pas ouvrir le bouchon** moteur chaud.
- **Freins** : niveau trop bas ou frein à main serré.
- **Batterie / charge** : alternateur ou courroie défaillant.
- **Ceinture non bouclée** et **airbag** défaillant.

### Les voyants orange
- **Moteur** / dépollution, **ABS**, **ESP**, **pression des pneus** (TPMS), **FAP** (filtre à particules), **préchauffage** (diesel).

> Un voyant qui s'allume au contact doit s'éteindre au démarrage : sinon, anomalie.
"""),
        ('pneumatiques-et-liaison-au-sol', "Pneumatiques, freins et liaison au sol", 9, """## Les pneus : seul contact avec la route

Quatre surfaces de la taille d'une carte postale assurent **toute** l'adhérence.

- **Profondeur de sculpture** : **1,6 mm minimum** (indicateurs d'usure TWI) ; sur la pluie, privilégier 3 mm.
- **Pression** : à contrôler à **froid** tous les mois, y compris la roue de secours.
  - **Sous-gonflé** : usure des épaules, surconsommation, risque d'éclatement.
  - **Sur-gonflé** : usure centrale, adhérence moindre.
- **Âge** : au-delà de 6 à 10 ans, le caoutchouc durcit même s'il n'est pas usé.
- **Équilibrage** et **parallélisme** : vibrations au volant ou usure irrégulière.

## Les freins
- **Plaquettes** : usure indiquée par un bruit métallique ou un voyant.
- **Disques**, **liquide de frein** : à remplacer régulièrement (hygroscopique).
- **Pédale molle** ou qui s'enfonce : danger, arrêt.

## Les amortisseurs
Usés, ils allongent la **distance de freinage** et affectent le **contact** pneu/sol : à contrôler tous les 80 000 km.
"""),
        ('entretien-et-niveaux', "Entretien courant et niveaux", 7, """## Les niveaux à surveiller

| Niveau | Fréquence | Remarque |
|---|---|---|
| **Huile moteur** | Mensuelle | Entre les repères mini et maxi, moteur froid ou coupé depuis 5 min |
| **Liquide de refroidissement** | Mensuelle | **Jamais** à chaud |
| **Liquide de frein** | Tous les 2 ans à changer | Niveau lié à l'usure des plaquettes |
| **Lave-glace** | Fréquente | Antigel en hiver |
| **Batterie** | Annuelle | Bornes propres, fixation |

### Les organes d'usure
Essuie-glaces (tous les ans), ampoules, **courroie de distribution** (selon préconisation constructeur), **filtres** à air, huile, habitacle.

### Quand consulter ?
Bruit anormal, fumées, odeur de brûlé, voyant allumé, tenue de route modifiée, vibrations, consommation soudainement plus élevée.

### Entretien et sécurité
L'entretien régulier **limite** pannes et accidents mais ne remplace pas le **contrôle technique**.
"""),
        ('commandes-et-boite', "Commandes, boîte de vitesses et conduite à froid", 7, """## Les commandes de base

- **Embrayage** (pied gauche, boîte manuelle) : relier ou séparer le moteur des roues.
- **Frein** (pied droit) ; **accélérateur** (pied droit).
- **Frein à main / de stationnement** : immobilise le véhicule à l'arrêt ; on garde une vitesse engagée en pente.
- **Boîte automatique** : P (parking), R (marche arrière), N (point mort), D (avant).

## Démarrer et conduire
- Dans les premières minutes, le moteur **n'est pas à température** : évitez les régimes élevés.
- Le **rétrogradage** (passer à un rapport inférieur) aide à ralentir sans chauffer les freins (**frein moteur**) dans les descentes longues.
- **Ne jamais** rouler au **point mort** ni moteur coupé : direction et freinage assistés ne fonctionnent plus normalement.

## Position de l'accélérateur
Appuyer **progressivement** : un coup d'accélérateur brutal augmente la consommation, l'usure et la perte d'adhérence.
"""),
    ],
    'questions': [
        ("Un voyant rouge s'allume en roulant. Que dois-je faire ?",
         ["M'arrêter dès que possible en sécurité", "Continuer jusqu'à destination", "Ignorer", "Accélérer"], [0], "Un voyant rouge signale un danger immédiat."),
        ("Un voyant orange s'allume. Cela signifie :",
         ["Qu'il faut faire vérifier rapidement le véhicule", "Qu'il faut s'arrêter immédiatement", "Qu'il n'y a pas de danger", "Que tout va bien"], [0], "Le voyant orange signale une anomalie à contrôler."),
        ("La profondeur minimale de la sculpture des pneus est de :",
         ["1,6 mm", "1 mm", "3 mm", "0,5 mm"], [0], "Au-dessous, les pneus ne sont plus conformes."),
        ("La pression des pneus doit être vérifiée :",
         ["À froid, tous les mois", "À chaud, tous les ans", "Après avoir roulé 100 km", "Uniquement avant un long trajet"], [0],
         "Rouler fait monter la pression : la mesure à froid est la seule fiable."),
        ("Un pneu sous-gonflé entraîne :",
         ["Une surconsommation et un risque d'éclatement", "Une meilleure adhérence", "Une baisse du bruit", "Une usure plus lente"], [0], "Il chauffe davantage et se déforme."),
        ("Le voyant de pression d'huile s'allume en rouge. Que faire ?",
         ["Couper le moteur et s'arrêter immédiatement", "Continuer lentement", "Remettre du liquide lave-glace", "Rouler plus vite"], [0],
         "Rouler sans pression d'huile détruit le moteur en quelques minutes."),
        ("Le liquide de refroidissement se vérifie :",
         ["Moteur froid", "Moteur chaud", "En roulant", "Jamais"], [0], "Ouvrir le bouchon à chaud expose à des projections brûlantes."),
        ("Quel est le rôle des amortisseurs ?",
         ["Maintenir le contact des pneus avec la route", "Réduire la consommation", "Refroidir les freins", "Augmenter la vitesse"], [0], "Des amortisseurs usés allongent la distance de freinage."),
        ("Le voyant ABS orange allumé indique :",
         ["Que le système ABS est défaillant mais que le freinage normal fonctionne", "Un blocage des roues", "Un excès de vitesse", "Un niveau d'huile bas"], [0], "Le freinage reste possible sans l'assistance antiblocage."),
        ("Rouler au point mort en descente est :",
         ["Dangereux", "Recommandé pour économiser", "Obligatoire en montagne", "Sans conséquence"], [0], "On perd le frein moteur et l'assistance."),
        ("Une pédale de frein molle ou qui s'enfonce :",
         ["Est un signe de défaillance du circuit de freinage", "Est normale par temps froid", "Signale des plaquettes neuves", "N'a aucune importance"], [0], "Arrêt immédiat et dépannage."),
        ("Le frein moteur permet :",
         ["De ralentir sans solliciter les freins", "D'augmenter la vitesse", "De refroidir le moteur", "De consommer plus"], [0], "En rétrogradant, on utilise la résistance du moteur."),
        ("Les bruits métalliques lors du freinage sont souvent le signe :",
         ["De plaquettes usées", "De pneus trop gonflés", "D'un lave-glace vide", "D'une batterie faible"], [0], "Il faut les changer sans attendre."),
        ("Le niveau d'huile moteur doit être entre :",
         ["Les repères mini et maxi", "Le maxi et au-dessus", "Le mini et en dessous", "Peu importe"], [0], "Trop ou trop peu d'huile abîme le moteur."),
    ],
}

# ---------------------------------------------------------------------------------------------------------------------
DATA['S'] = {
    'lessons': [
        ('ceinture-et-retenue', "Ceinture, airbags et retenue", 8, """## La ceinture de sécurité

**Premier équipement de sécurité** : elle divise par plusieurs fois le risque de décès en cas de choc. Elle est obligatoire à **toutes les places** équipées.

- Elle doit être **ajustée** : sangle sur le bassin et l'épaule, **sans** mou ni vêtement épais.
- À **50 km/h**, un occupant non attaché est projeté avec une force équivalente à celle d'une chute de **10 m**.
- Les **prétensionneurs** serrent la ceinture à l'instant du choc ; les **limiteurs d'effort** relâchent progressivement la sangle.

## L'airbag
Il **complète** la ceinture, il ne la remplace pas. Il se déploie en une fraction de seconde.
- Garder au moins **25 cm** entre le thorax et le volant.
- **Interdit** d'installer un siège enfant dos à la route sur un siège protégé par un airbag actif.
- **Ne rien fixer** sur la zone de déploiement.

## Les appuis-tête
Réglés au niveau du sommet du crâne, ils réduisent le « coup du lapin » en cas de choc arrière.
"""),
        ('aides-a-la-conduite', "ABS, ESP, AFU et aides électroniques", 9, """## Les aides

| Équipement | Rôle | Réflexe |
|---|---|---|
| **ABS** | Empêche le blocage des roues au freinage | Appuyer **fort** et **maintenir** ; ne pas pomper ; on peut éviter |
| **AFU** (aide au freinage d'urgence) | Amplifie le freinage en cas de freinage brusque | Appuyer fort |
| **ESP** (contrôle de stabilité) | Corrige la trajectoire en cas de survirage / sous-virage | Rester sur les freins, ne pas lutter |
| **ASR** (antipatinage) | Évite le patinage à l'accélération | Moduler l'accélérateur |
| **Régulateur / limiteur** | Maintient / plafonne la vitesse | Toujours rester **vigilant** |
| **Freinage automatique d'urgence (AEB)** | Freine si une collision est imminente | Ne pas s'y fier seul |
| **Détecteur d'angle mort / alerte de franchissement de ligne** | Informe le conducteur | Aide, non substitut |

### Limites
Ces aides **ne suppriment pas** les lois de la physique : une vitesse inadaptée reste dangereuse. Elles peuvent donner un **faux sentiment de sécurité**.

### eCall
Dispositif intégré de **appel d'urgence automatique** (112) en cas de choc grave.
"""),
        ('equipements-et-securite-passive', "Sécurité active et passive, ISOFIX", 7, """## Active ou passive ?

- **Sécurité active** : agit **avant** l'accident pour l'éviter (freins, pneus, direction, éclairage, ABS, ESP).
- **Sécurité passive** : limite les **conséquences** d'un accident (ceinture, airbags, structure déformable, habitacle rigide, appuis-tête).

## La structure du véhicule
- **Zones de déformation programmée** à l'avant et à l'arrière : elles absorbent l'énergie.
- **Cellule de survie** rigide autour des occupants.
- **Pare-brise feuilleté** : ne vole pas en éclats.

## Fixation des sièges enfants
- **ISOFIX** : fixation rigide aux points d'ancrage du véhicule, évite les erreurs de montage ;
- **Ceinture** : possible si le siège est homologué pour une fixation par ceinture.

## Le chargement
Un chargement mal arrimé annule l'efficacité des protections : objets lourds dans le coffre, **séparés** de l'habitacle.
"""),
    ],
    'questions': [
        ("La ceinture de sécurité :",
         ["Est obligatoire à toutes les places", "Est facultative à l'arrière", "N'est utile qu'à grande vitesse", "N'est obligatoire qu'en ville"], [0], "Elle réduit le risque de décès en cas de choc."),
        ("L'airbag :",
         ["Complète la ceinture", "Remplace la ceinture", "Est inutile avec la ceinture", "Se déploie à tous les chocs"], [0], "Il est conçu pour fonctionner avec la ceinture."),
        ("En cas de freinage d'urgence avec ABS, je dois :",
         ["Appuyer fortement sur la pédale et maintenir l'appui", "Pomper sur la pédale", "Relâcher la pédale", "Braquer d'abord"], [0], "L'ABS gère le blocage : un appui franc suffit."),
        ("L'ESP sert à :",
         ["Corriger la trajectoire en cas de perte d'adhérence", "Augmenter la vitesse", "Économiser du carburant", "Réduire le bruit"], [0], "Il agit sur les freins roue par roue."),
        ("L'ABS permet :",
         ["De garder la maîtrise de la direction en freinant", "De freiner plus court sur toutes surfaces", "De rouler plus vite", "D'économiser de l'énergie"], [0], "Les roues ne se bloquent pas ; on peut donc éviter l'obstacle."),
        ("Un régulateur de vitesse :",
         ["Ne dispense pas de rester vigilant", "Permet de lâcher le volant", "Évite tous les accidents", "Doit être utilisé sous la pluie"], [0], "Le conducteur reste responsable."),
        ("Les prétensionneurs :",
         ["Serrent la ceinture au moment du choc", "Gonflent l'airbag", "Détendent la ceinture en permanence", "Ne servent à rien"], [0], "Ils plaquent l'occupant contre le siège."),
        ("La sécurité passive regroupe :",
         ["La ceinture", "Les airbags", "L'ABS", "La structure déformable"], [0, 1, 3], "Elle limite les conséquences d'un accident ; l'ABS est un équipement de sécurité active."),
        ("L'ISOFIX est :",
         ["Un système de fixation de sièges enfants aux points d'ancrage du véhicule", "Un type de pneu", "Un airbag", "Un voyant"], [0], "Il réduit le risque de mauvaise installation."),
        ("Une alerte de franchissement de ligne :",
         ["Prévient le conducteur mais ne conduit pas à sa place", "Remplace le conducteur", "Corrige toujours la trajectoire", "Désactive le clignotant"], [0], "Ces aides ne remplacent pas l'attention."),
        ("Distance minimale conseillée entre votre thorax et le volant :",
         ["25 cm", "5 cm", "10 cm", "40 cm"], [0], "Elle permet à l'airbag de se déployer sans blesser."),
        ("Quel dispositif appelle automatiquement les secours en cas de choc grave ?",
         ["L'eCall", "L'ABS", "L'ESP", "Le limiteur de vitesse"], [0], "L'eCall compose le 112 et transmet la position du véhicule."),
    ],
}

# ---------------------------------------------------------------------------------------------------------------------
DATA['E'] = {
    'lessons': [
        ('eco-conduite', "L'éco-conduite", 8, """## Conduire souple pour consommer moins

L'éco-conduite permet d'économiser jusqu'à **10 à 15 % de carburant** et de réduire les émissions.

### Les gestes
1. **Démarrer en douceur** et monter les rapports tôt (≈ 2 000 tr/min en essence, 1 500 en diesel).
2. **Anticiper** : regarder loin pour **relâcher l'accélérateur** plutôt que freiner.
3. **Utiliser le frein moteur** lorsque l'on s'arrête (rapport engagé, pied levé : l'injection est coupée).
4. **Couper le moteur** pour un arrêt de plus de **20 secondes** (le redémarrage consomme moins).
5. **Garder une vitesse stable** ; le régulateur est utile sur autoroute.
6. **Limiter la vitesse** : consommation +20 % entre 110 et 130 km/h.

### Équipements
- **Pneus** bien gonflés (−0,5 bar = +2 à 4 % de consommation) ;
- Pas de **coffre de toit** ni de charge inutile ;
- **Climatisation** à bon escient : jusqu'à +20 % de consommation en ville.
"""),
        ('pollution-et-nuisances', "Pollution, nuisances et réglementation", 8, """## Les polluants

| Polluant | Origine | Effet |
|---|---|---|
| **CO₂** | Combustion | Réchauffement climatique |
| **NOx** | Combustion à haute température (diesel) | Pollution de l'air, maladies respiratoires |
| **Particules fines** | Combustion, freins, pneus | Santé (poumons, cœur) |
| **CO** | Combustion incomplète | Toxique (intoxication) |

### Les équipements
- **Catalyseur** : transforme les gaz polluants ;
- **Filtre à particules (FAP)** : retient les suies du diesel ;
- **AdBlue** : réduit les NOx.

### Réglementation
- **Crit'Air** : vignette (de 0 à 5) qui classe les véhicules pour les **Zones à Faibles Émissions (ZFE)** ;
- **Contrôle technique** : mesure des émissions ;
- **Nuisances sonores** : klaxon, pots non conformes, moteur emballé ;
- **Déchets** : huile, batteries, pneus, déposés en déchèterie ou chez un professionnel.

## Choisir ses déplacements
Transports en commun, **covoiturage**, vélo, marche : un trajet de moins de 2 km en voiture démarre à froid et pollue davantage.
"""),
        ('choisir-et-entretenir', "Choisir, entretenir et partager son véhicule", 6, """## Choisir un véhicule

- La **puissance** et la **masse** déterminent la consommation : un véhicule plus léger consomme moins.
- **Motorisations** : essence, diesel, hybride, hybride rechargeable, **100 % électrique**, GPL, hydrogène : chaque choix dépend des usages.
- **Étiquette énergie / bonus-malus** : indicateurs des émissions de CO₂.

## Entretenir
Moteur **réglé**, filtres propres, pneus gonflés, huile adaptée : entretien régulier = émissions et consommations réduites.

## Partager
Le **covoiturage** réduit le nombre de véhicules (et le coût du trajet) ; l'**autopartage** limite la possession d'un second véhicule.

## Bruit
Respecter le voisinage : pas de moteur tournant à l'arrêt, **limiter les à-coups**, silencieux d'échappement conformes.
"""),
    ],
    'questions': [
        ("L'éco-conduite permet :",
         ["De consommer moins de carburant", "D'augmenter la vitesse", "De rouler plus près du véhicule précédent", "De freiner moins efficacement"], [0], "Une conduite souple et anticipée réduit la consommation."),
        ("À partir de quelle durée d'arrêt est-il conseillé de couper le moteur ?",
         ["20 secondes environ", "5 minutes", "1 heure", "Jamais"], [0], "Le redémarrage consomme moins que le ralenti prolongé."),
        ("Pour économiser du carburant, je dois :",
         ["Monter les rapports tôt", "Rester longtemps en 1ʳᵉ", "Accélérer à fond", "Freiner souvent"], [0], "Un régime moteur faible limite la consommation."),
        ("Un pneu sous-gonflé :",
         ["Augmente la consommation de carburant", "Diminue la consommation", "N'a aucune influence", "Améliore la tenue de route"], [0], "La résistance au roulement augmente."),
        ("Quel gaz est principalement responsable du réchauffement climatique ?",
         ["Le CO₂", "L'oxygène", "L'azote", "L'argon"], [0], "La combustion des carburants émet du dioxyde de carbone."),
        ("La vignette Crit'Air sert à :",
         ["Identifier la classe d'émission du véhicule pour circuler en zone à faibles émissions", "Payer le péage", "Justifier l'assurance", "Remplacer le contrôle technique"], [0], "Elle va de 0 (électrique) à 5."),
        ("Le filtre à particules (FAP) :",
         ["Retient les particules fines des moteurs diesel", "Refroidit le moteur", "Augmente la puissance", "Remplace le pot d'échappement"], [0], "Il limite l'émission de suies."),
        ("Une surcharge ou un coffre de toit inutile :",
         ["Augmente la consommation", "Diminue la consommation", "N'a aucun effet", "Améliore l'aérodynamisme"], [0], "Poids et traînée supplémentaires augmentent la consommation."),
        ("Les huiles de vidange doivent être :",
         ["Déposées en déchèterie ou chez un professionnel", "Versées dans les égouts", "Jetées à la poubelle", "Brûlées"], [0], "Elles polluent durablement l'eau et les sols."),
        ("Le covoiturage permet :",
         ["De réduire le nombre de véhicules en circulation", "D'augmenter les embouteillages", "De rouler plus vite", "De supprimer la pollution"], [0], "Plusieurs personnes partagent un seul trajet."),
        ("Le meilleur moyen de limiter la consommation sur autoroute :",
         ["Rouler à vitesse stable et plus modérée", "Accélérer et ralentir souvent", "Rouler très près des camions", "Couper le moteur en roulant"], [0], "La consommation augmente fortement avec la vitesse."),
        ("Qu'est-ce qu'un trajet très court en voiture, pour l'environnement ?",
         ["Plus polluant, car le moteur n'est pas à température", "Sans effet", "Plus économique", "Idéal pour l'entretien"], [0], "Un moteur froid consomme et pollue davantage."),
    ],
}

# ---------------------------------------------------------------------------------------------------------------------
DATA['A'] = {
    'lessons': [
        ('proteger-et-alerter', "Protéger et alerter", 8, """## Sur les lieux d'un accident

### Protéger (P)
1. **Se garer** en sécurité, **feux de détresse**, couper le contact.
2. **Enfiler le gilet** de haute visibilité avant de sortir.
3. **Baliser** : triangle de présignalisation à **30 m minimum** (sauf autoroute) ; en agglomération, adapter la distance.
4. **Faire évacuer** les personnes valides derrière la glissière ou hors de la voie.
5. **Ne pas fumer**, ne pas allumer de flammes en présence de carburant.

### Alerter (A)
- **112** : numéro d'urgence européen, unique, gratuit, depuis un mobile même sans carte SIM.
- **15** SAMU / **18** pompiers / **17** police / **114** par SMS pour les personnes sourdes ou malentendantes.
- **Message** : lieu précis (route, point kilométrique), nombre de victimes, état apparent, nature de l'accident (feu, produits dangereux…), **ne pas raccrocher** avant d'y être invité.

### Où est le danger ?
Le principal danger est le **suraccident** : protéger avant de secourir, c'est se protéger **soi-même** et les autres.
"""),
        ('secourir', "Secourir : les gestes de base", 10, """## Secourir (S)

### Hémorragie
Pression **directe** avec la main (protégée par un gant ou un tissu) sur la plaie, **sans interruption**, et allonger la victime. Alerter les secours.

### Victime inconsciente qui respire
**Position latérale de sécurité (PLS)** : sur le côté, voies aériennes dégagées. On surveille la respiration jusqu'aux secours.

### Victime inconsciente qui ne respire pas
- **Alerter** (112) et **demander un défibrillateur** (DAE) ;
- **Massage cardiaque** : mains superposées au centre de la poitrine, **100 à 120 compressions par minute**, 5 à 6 cm de profondeur ;
- Continuer jusqu'à l'arrivée des secours, ou jusqu'à la reprise de la respiration.

### Étouffement (obstruction totale)
**5 claques** vigoureuses dans le dos, puis, si besoin, **5 compressions abdominales** (manœuvre de Heimlich), en alternant.

### Brûlure
Arroser abondamment à l'eau tempérée (**10 minutes minimum**) ; ne rien appliquer d'autre ; ne pas retirer un vêtement collé.

### Casque
Ne pas retirer le casque d'un motard, sauf s'il est nécessaire de **dégager les voies aériennes**, et alors à plusieurs.
"""),
        ('situations-particulieres', "Situations particulières : feu, produits dangereux, passage à niveau", 8, """## Feu de véhicule
Éloigner les personnes, s'abriter, alerter (**18**). Ne pas ouvrir le capot : l'apport d'air attise le feu. Utiliser l'extincteur si l'on peut le faire sans risque.

## Transport de matières dangereuses
Panneaux orange et pictogrammes : **s'éloigner** (de préférence face au vent), **alerter** en précisant le numéro de danger et de matière, ne pas toucher aux fuites.

## Passage à niveau
- **Panne** ou **véhicule bloqué** : évacuer immédiatement les occupants, **s'éloigner de la voie et du véhicule**, puis alerter ;
- **Ne jamais tenter de dégager** le véhicule si un train approche.

## Tunnel
Éteindre le moteur, **laisser la clé sur le contact**, évacuer par les issues de secours, alerter via la borne.

## Autoroute
Rester derrière la glissière, **jamais au milieu** de la chaussée ; ne pas traverser.
"""),
        ('prevention-et-premiers-reflexes', "Prévention et réflexes pour les secours", 6, """## Se préparer

- Disposer d'une **trousse de secours** et d'un **extincteur** adaptés.
- **Savoir** où se trouve le **défibrillateur** (applications, cartes) le plus proche.
- **Apprendre** les gestes : formation **PSC1** (Prévention et secours civiques de niveau 1), très accessible.

## Ce qu'il ne faut pas faire
- **Ne pas déplacer** une victime (sauf danger immédiat : feu, noyade) : risque de lésions de la colonne vertébrale.
- **Ne pas faire boire** ni manger une victime.
- **Ne pas retirer** un objet planté : on le **stabilise**.
- **Ne pas laisser** la victime seule.

## Après l'accident
Remplir le **constat amiable**, **déclarer le sinistre** sous 5 jours ouvrés, faire examiner même les blessures légères. Un **soutien psychologique** peut être nécessaire.
"""),
    ],
    'questions': [
        ("Quel numéro permet d'appeler les secours dans toute l'Europe ?",
         ["112", "17", "15", "110"], [0], "Le 112 est le numéro d'urgence européen, gratuit."),
        ("Que signifie « PAS » ?",
         ["Protéger, Alerter, Secourir", "Prévenir, Attendre, Sécuriser", "Parler, Aider, Signaler", "Protéger, Arrêter, Sauver"], [0], "Ce sont les trois étapes de la conduite à tenir face à un accident."),
        ("Que faire en premier sur les lieux d'un accident ?",
         ["Protéger les lieux et les victimes", "Déplacer les victimes", "Donner à boire", "Photographier"], [0], "Il faut éviter un « suraccident »."),
        ("Une victime est inconsciente mais respire. Que faire ?",
         ["La placer en position latérale de sécurité", "La laisser sur le dos", "La faire asseoir", "La faire boire"], [0], "La PLS dégage les voies aériennes."),
        ("En cas d'hémorragie, que faire ?",
         ["Comprimer directement la plaie", "Mettre un garrot sur le cou", "Retirer l'objet planté", "Laver la plaie à l'eau"], [0], "La compression directe, continue, arrête le saignement."),
        ("À quelle fréquence réaliser un massage cardiaque chez l'adulte ?",
         ["100 à 120 compressions par minute", "30 par minute", "60 par minute", "200 par minute"], [0], "Le rythme est rapide et régulier."),
        ("Pour appeler les secours par SMS (personnes sourdes ou malentendantes), on utilise le :",
         ["114", "112 uniquement", "15", "18"], [0], "Le 114 est le numéro d'urgence par SMS."),
        ("Vous êtes témoin d'un accident sur l'autoroute. Où vous placez-vous ?",
         ["Derrière la glissière de sécurité", "Sur la voie de gauche", "Au milieu des voies", "Devant les véhicules"], [0], "Vous êtes à l'abri des véhicules qui continuent de circuler."),
        ("Quelle est la distance minimale du triangle de présignalisation ?",
         ["30 mètres", "5 mètres", "10 mètres", "100 mètres"], [0], "Il doit être visible de loin pour avertir les autres conducteurs."),
        ("Une victime s'étouffe. Que faire ?",
         ["Donner 5 claques dans le dos", "Lui donner de l'eau", "L'allonger", "Attendre"], [0], "On alterne claques dans le dos et compressions abdominales."),
        ("Un véhicule est en feu :",
         ["Éloigner les personnes et alerter le 18", "Ouvrir le capot", "Rester près du véhicule", "Jeter de l'eau sur le moteur"], [0], "L'air attise le feu : on ne soulève pas le capot."),
        ("Que faire si votre véhicule est bloqué sur un passage à niveau ?",
         ["Évacuer immédiatement les occupants et s'éloigner de la voie", "Rester à l'intérieur", "Essayer de redémarrer", "Appeler un ami"], [0], "Un train ne peut pas s'arrêter à temps."),
        ("Dans quel cas déplace-t-on une victime ?",
         ["En cas de danger immédiat (feu, noyade)", "Toujours", "Jamais", "Pour la faire asseoir"], [0], "Sinon, on risque d'aggraver les lésions de la colonne vertébrale."),
        ("En présence d'une brûlure, il faut :",
         ["L'arroser à l'eau tempérée pendant 10 minutes", "Appliquer du beurre", "Percer les cloques", "Retirer le vêtement collé"], [0], "L'eau refroidit la brûlure et limite l'aggravation."),
        ("Qu'est-ce que le DAE ?",
         ["Un défibrillateur automatisé externe", "Un détecteur d'airbag", "Un voyant du tableau de bord", "Un type d'extincteur"], [0], "Il aide à rétablir un rythme cardiaque normal."),
    ],
}

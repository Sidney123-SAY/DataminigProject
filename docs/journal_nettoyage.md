# Journal de nettoyage — Maison Delorme

Script : `src/01_nettoyage.py` (lancer avec `python src/01_nettoyage.py` depuis la racine).
Les fichiers bruts de `data/raw/` ne sont jamais modifiés ; tout est réécrit dans `data/clean/`.

**Bilan : 64 → 59 boutiques, 768 → 708 lignes de ventes (59 boutiques × 12 mois).**

| # | Problème constaté | Décision | Justification en une phrase |
|---|---|---|---|
| 1 | Le sujet annonce des ventes « sur deux ans », le fichier ne couvre que **12 mois (2024-01 à 2024-12)**. | **Signalé.** | On ne peut pas mesurer de tendance d'une année sur l'autre ; toute analyse temporelle se limite à la saisonnalité 2024. |
| 2 | `boutiques.csv` : **B121 et B152 apparaissent deux fois**, avec des lignes strictement identiques. | **Copie supprimée** (64 → 62 lignes). | Deux lignes identiques ne portent qu'une seule information, et la garder compterait la boutique deux fois. |
| 3 | `ventes_mensuelles.csv` : la série de **B121 est recopiée à l'identique** (12 lignes). | **Copie supprimée.** | Même raison qu'au point 2. |
| 4 | `ventes_mensuelles.csv` : **B152 a deux séries de 12 mois différentes** (moyennes 18 052 € et 17 182 €). | **On garde la série 1**, la plus proche du CA de la fiche (17 827 €, écart de 1,3 % contre 3,6 %). | La fiche boutique est une source indépendante qui permet de départager les deux séries. L'enjeu est faible : les deux séries ne diffèrent que de 5 %. |
| 5 | **B101, B105 et B121** : CA = −1 dans la fiche, 1 € et 0 ticket tous les mois dans les ventes. | **Écartées des deux fichiers** (62 → 59 boutiques). | Un CA négatif ou constant à 1 € avec zéro client est un code de remplissage (boutique fermée ou non saisie). Le garder fausserait toutes les moyennes et corrélations. |
| 5 bis | Ces trois boutiques ont 36 à 136 mois d'ancienneté. | **Signalé** à l'équipe de la Q1. | Ce ne sont donc pas les « trois nouvelles boutiques qui ne décollent pas » du sujet : il ne faut pas les confondre. |
| 6 | **Surface = 0 m²** pour B129, B113 et B159. | **Remplacée par la médiane du même type d'emplacement** (94 m² en quartier résidentiel, 78 m² en centre commercial). Colonne drapeau `surface_imputee`. | Une boulangerie de 0 m² n'existe pas. La médiane du même type d'emplacement est l'estimation la plus prudente, et le drapeau permet d'exclure ces lignes si une analyse y est sensible. |
| 7 | **3 valeurs manquantes dans `part_emporter`** (B129, B132, B116) et **3 dans `habitants_1km`** (B130, B136, B135). | **Remplacées par la médiane de la colonne** (0,59 et 15 152). Colonnes drapeaux `part_emporter_imputee` et `habitants_1km_imputee`. | Supprimer ces lignes ferait perdre 6 boutiques sur 59 (10 %), c'est trop. La médiane ne déplace pas le centre de la distribution. |
| 8 | **B120 et B154 : CA de la fiche = 9 000 € tout rond.** | Vérifié : la moyenne des ventes 2024 vaut 8 964 € et 9 255 € (écarts de 0,4 % et −2,8 %). **Signalé** (drapeau `ca_fiche_arrondi`). | C'est un arrondi de saisie, pas une erreur grossière, mais il montre que la fiche est moins précise que le fichier des ventes. |
| 9 | Comparaison, pour les 59 boutiques, du CA de la fiche et de la moyenne des ventes 2024. | **Aucun écart > 10 %** (écarts de −4,6 % à +4,0 %, médiane 0 %). Détail dans `outputs/tables/ecarts_ca.csv`. | Les deux sources concordent. |
| 9 bis | Choix de la variable de CA à analyser. | **Nouvelle colonne `ca_moyen_2024`**, la moyenne des 12 mois de ventes. **C'est la cible à utiliser dans toutes les questions.** La colonne d'origine `ca_mensuel_eur` est conservée. | Elle est calculée de la même manière pour toutes les boutiques, sans arrondi saisi à la main. |
| 10 | Le sujet parle de **18 boutiques ouvertes depuis moins de deux ans**, alors que le fichier n'en compte que **3** avec une ancienneté < 24 mois (B139 : 10, B123 : 19, B149 : 21). | **Signalé, non corrigé.** | Aucun changement d'unité simple ne retombe sur 18 (il faudrait un seuil vers 44 mois). On ignore aussi la date de référence de l'ancienneté. L'équipe de la Q1 doit en tenir compte. |
| 11 | B139 a 10 mois d'ancienneté, mais un CA normal dès janvier 2024. | **Signalé.** | C'est cohérent seulement si l'ancienneté a été mesurée vers novembre 2024. Cela confirme que sa date de référence est inconnue. |

## Section 9 — Plausibilité des unités

Valeurs calculées sur les 59 boutiques après nettoyage :

| Colonne | min / médiane / max | Unité annoncée plausible ? |
|---|---|---|
| `surface_m2` | 35 / 81 / 130 | **Oui**, une surface de boulangerie parisienne classique. |
| `loyer_mensuel_eur` | 2 142 / 5 236 / 9 710 | **Douteux** (voir ci-dessous). Rapporté à la surface, cela fait environ 830 €/m²/an : cher mais possible à Paris. Rapporté au CA, ça ne tient pas. |
| `passage_pietons_jour` | 659 / 3 559 / 18 788 | **Oui**, des passages par jour. Les gares sont en tête (12 000 à 19 000), ce qui est cohérent. |
| `habitants_1km` | 2 427 / 15 152 / 25 927 | **Plutôt bas** pour Paris (environ 20 000 hab./km², soit environ 60 000 dans un disque de 1 km de rayon), mais cohérent entre boutiques. On garde la colonne comme indicateur relatif. |
| `concurrents_300m` | 0 / 2 / 7 | **Oui**, un nombre entier. |
| `effectif` | 2 / 4 / 6 | **Oui**, des personnes (ou des ETP). |
| `amplitude_horaire_h` | 8,1 / 12,6 / 15,3 | **Oui**, des heures d'ouverture par jour (par exemple 6 h-19 h). |
| `anciennete_mois` | 10 / 63 / 178 | **Oui en mois** (de moins d'un an à environ 15 ans), mais voir le point 10. |
| `part_emporter` | 0,34 / 0,59 / 0,95 | **C'est une proportion entre 0 et 1, pas un pourcentage.** À ne pas lire « 0,59 % ». |
| `ca_moyen_2024` | 8 964 / 16 459 / 36 020 | **Douteux** (voir ci-dessous). |
| `tickets_moyen_2024` | 1 423 / 2 654 / 5 751 | **Douteux** : environ 88 tickets par jour sur 30 jours, c'est peu pour une boulangerie. |

**Incohérence loyer / CA.** Le loyer représente en médiane **31 % du CA mensuel** (de 12 % à 78 %). Dans la boulangerie, il tourne d'habitude autour de 10 %. De même, 88 tickets par jour, c'est faible. Le panier moyen (6,22 € par ticket) est en revanche réaliste. Deux lectures sont possibles :

- le CA et les tickets sont **hebdomadaires** malgré leur nom (×4,3 donne environ 380 tickets par jour et un loyer à environ 7 % du CA, des valeurs de boulangerie typiques) ;
- ou le loyer n'est pas mensuel (par exemple il inclut les charges, ou il couvre une autre période).

**Décision : signalé, non corrigé.** Rien dans les fichiers ne permet de trancher. Les corrélations, la classification, le clustering sur variables standardisées et les classements entre boutiques ne changent pas si on multiplie une colonne par une constante. En revanche, **tout montant en euros annoncé à la direction (Q3, synthèse) doit être présenté « dans l'unité du fichier »**, avec cette réserve.

## Fichiers produits

- `data/clean/boutiques_clean.csv` : 59 lignes. Il contient les colonnes d'origine plus `ca_moyen_2024`, `tickets_moyen_2024` et les drapeaux `surface_imputee`, `part_emporter_imputee`, `habitants_1km_imputee` et `ca_fiche_arrondi`.
- `data/clean/ventes_clean.csv` : 708 lignes, soit 59 boutiques × 12 mois, sans doublon (boutique, mois).
- `outputs/tables/qualite_donnees.csv` : profil avant / après de chaque colonne (lignes, manquants, zéros, négatifs, min, médiane, max).
- `outputs/tables/ecarts_ca.csv` : CA de la fiche vs moyenne des ventes 2024, par boutique.

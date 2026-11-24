# Journal de nettoyage

Les fichiers d'origine (dans `data/raw/`) ne sont jamais modifiés. Les versions nettoyées sont dans `data/clean/`.

Au final on passe de 64 à 59 boutiques, et de 768 à 708 lignes de ventes (59 boutiques × 12 mois).

## Les problèmes trouvés et ce qu'on a décidé

| # | Problème | Ce qu'on a fait | Pourquoi |
|---|---|---|---|
| 1 | Le sujet parle de ventes sur deux ans, mais le fichier ne couvre que 12 mois (janvier à décembre 2024). | Signalé. | On ne peut pas comparer deux années, seulement regarder les variations dans l'année 2024. |
| 2 | B121 et B152 apparaissent deux fois dans le fichier des boutiques, avec exactement les mêmes informations. | On a supprimé la copie (64 → 62). | Sinon ces boutiques compteraient double dans toutes les moyennes. |
| 3 | Les ventes de B121 sont recopiées deux fois à l'identique. | On a supprimé la copie. | Même raison. |
| 4 | B152 a deux séries de ventes différentes pour les mêmes mois (moyennes de 18 052 € et 17 182 €). | On garde la première, la plus proche du CA indiqué dans la fiche boutique (17 827 €). | La fiche permet de départager. De toute façon les deux séries ne diffèrent que d'environ 5 %. |
| 5 | B101, B105 et B121 ont un CA de -1 € dans la fiche et 1 € avec 0 client tous les mois dans les ventes. | On les a retirées des deux fichiers (62 → 59). | Ce ne sont pas de vraies ventes mais des cases remplies faute de données. Les garder fausserait tous les calculs. |
| 6 | Ces trois boutiques ont entre 36 et 136 mois d'ancienneté. | Signalé à l'équipe de la Q1. | Ce ne sont donc pas les trois nouvelles boutiques en difficulté dont parle le sujet. |
| 7 | B129, B113 et B159 ont une surface de 0 m². | Remplacée par la surface médiane des boutiques du même type d'emplacement (94 m² en quartier résidentiel, 78 m² en centre commercial). On a ajouté une colonne `surface_imputee` pour les repérer. | Une boulangerie de 0 m² n'existe pas. La médiane est moins influencée par les très grands locaux que la moyenne. |
| 8 | Il manque 3 valeurs dans `part_emporter` et 3 dans `habitants_1km`. | Remplacées par la médiane de la colonne, avec une colonne pour les repérer. | Supprimer ces boutiques en ferait perdre 6 sur 59, ce qui est beaucoup. |
| 9 | B120 et B154 ont un CA de 9 000 € tout rond dans la fiche. | Vérifié avec les ventes : 8 964 € et 9 255 €. Signalé. | C'est un simple arrondi, mais ça montre que la fiche est moins précise que les ventes. |
| 10 | On a comparé, pour chaque boutique, le CA de la fiche et la moyenne des 12 mois de ventes. | Aucun écart de plus de 10 % (entre -4,6 % et +4,0 %). | Les deux sources sont cohérentes. |
| 11 | Il fallait choisir quel CA utiliser. | On a créé la colonne `ca_moyen_2024`, la moyenne des 12 mois de ventes. C'est celle que tout le groupe utilise. | Elle est calculée pareil pour toutes les boutiques, sans arrondi saisi à la main. |
| 12 | Le sujet parle de 18 boutiques ouvertes depuis moins de deux ans, mais le fichier n'en contient que 3 (B139, B123, B149). | Signalé, pas corrigé. | On ne trouve pas d'explication simple, et on ne connaît pas la date à partir de laquelle l'ancienneté est comptée. |
| 13 | B139 a 10 mois d'ancienneté mais vend normalement dès janvier 2024. | Signalé. | Ça confirme qu'on ne sait pas à quelle date l'ancienneté a été mesurée. |
| 14 | Les boîtes à moustaches montrent des valeurs très élevées, surtout pour les 5 gares (beaucoup de passage, CA au-dessus de 30 000 €). | Gardées. | Ce sont de vraies boutiques, pas des erreurs. On vérifie simplement nos résultats avec et sans elles. |

## Les unités sont-elles cohérentes ?

On a regardé le minimum, la médiane et le maximum de chaque colonne pour voir si les valeurs avaient du sens.

| Colonne | min / médiane / max | Avis |
|---|---|---|
| surface_m2 | 35 / 81 / 130 | Normal pour une boulangerie. |
| loyer_mensuel_eur | 2 142 / 5 236 / 9 710 | Possible pour Paris, mais incohérent avec le CA (voir plus bas). |
| passage_pietons_jour | 659 / 3 559 / 18 788 | Cohérent, les gares sont en tête. |
| habitants_1km | 2 427 / 15 152 / 25 927 | Un peu bas pour Paris, mais utilisable pour comparer les boutiques entre elles. |
| concurrents_300m | 0 / 2 / 7 | Normal. |
| effectif | 2 / 4 / 6 | Normal. |
| amplitude_horaire_h | 8,1 / 12,6 / 15,3 | Normal (heures d'ouverture par jour). |
| anciennete_mois | 10 / 63 / 178 | Normal en mois, mais voir les points 12 et 13. |
| part_emporter | 0,34 / 0,59 / 0,95 | C'est une proportion : 0,59 veut dire 59 %. |
| ca_moyen_2024 | 8 964 / 16 459 / 36 020 | Douteux, voir plus bas. |
| tickets_moyen_2024 | 1 423 / 2 654 / 5 751 | Douteux : environ 88 clients par jour, c'est peu pour une boulangerie. |

Le problème principal : le loyer représente en moyenne 31 % du CA, alors que dans une boulangerie c'est plutôt autour de 10 %. Et 88 clients par jour, c'est peu. Par contre le panier moyen (environ 6 € par client) est réaliste.

Deux explications possibles :
- le CA et les tickets sont en fait par semaine et pas par mois (en multipliant par 4,3, on retombe sur des chiffres normaux) ;
- ou le loyer n'est pas vraiment mensuel.

On ne peut pas trancher avec les fichiers, donc on n'a rien corrigé. Ça ne change rien aux corrélations, aux régressions ni aux comparaisons entre boutiques. Mais tous les montants en euros présentés à la direction doivent être donnés « dans l'unité du fichier ».

## Fichiers produits

- `data/clean/boutiques_clean.csv` : les 59 boutiques, avec `ca_moyen_2024`, `tickets_moyen_2024` et les colonnes qui signalent les valeurs remplacées.
- `data/clean/ventes_clean.csv` : 708 lignes, une par boutique et par mois.
- `outputs/tables/qualite_donnees.csv` : le résumé de chaque colonne avant et après nettoyage.
- `outputs/tables/ecarts_ca.csv` : la comparaison entre le CA de la fiche et celui des ventes.
- `outputs/figures/nettoyage_boxplots.png` : les boîtes à moustaches après nettoyage.
# Question 2 : le loyer est-il un bon indicateur du potentiel ?

Script : `src/q2_loyer_potentiel.py` (lancer avec `python src/q2_loyer_potentiel.py` depuis la racine).
Données : les 59 boutiques après nettoyage. Cible : `ca_moyen_2024`, le CA moyen des 12 mois de ventes.
Les montants sont donnés **dans l'unité du fichier** (voir la réserve sur les unités dans `journal_nettoyage.md`).

## La question

L'idée de la direction : un loyer cher veut dire une bonne adresse, donc beaucoup de clients, donc un gros CA. Si c'est vrai, on pourrait se servir du loyer pour juger un emplacement avant d'ouvrir.

## Ce que j'ai compris

Un loyer élevé peut avoir deux causes : un **grand local** ou une **adresse passante**. Si le loyer suit le CA seulement parce que les grands locaux paient plus et vendent plus, alors il ne dit rien sur l'emplacement. Il faut donc comparer le loyer à d'autres variables, et regarder ce qui reste de son effet quand on les ajoute.

## Méthode retenue et pourquoi

| Étape | Ce que je fais | Pourquoi (cours) |
|---|---|---|
| 1 | Médiane du loyer, du passage et du CA par type d'emplacement | La médiane n'est pas tirée par les gares. *Cours Analyse exploratoire : comparer les médianes selon un groupe.* |
| 2 | Matrice de corrélation de Pearson entre loyer, loyer au m², surface, passage, concurrents et CA | Elle donne d'un coup d'œil la force du lien linéaire entre chaque paire. *Cours Analyse exploratoire.* |
| 3 | CA médian par tranche de loyer et par tranche de passage (4 tranches coupées aux quartiles) | C'est une lecture simple, sans modèle : est-ce que le CA monte d'une tranche à l'autre ? *Cours Analyse exploratoire : valeur médiane par tranche.* |
| 4 | Régressions linéaires (sklearn `LinearRegression`) : loyer seul, surface seule, passage seul, loyer + surface, loyer + passage | Le coefficient se lit en euros : « +1 000 € de loyer = +X € de CA ». Et avec plusieurs variables, on voit si celui du loyer fond. *Cours Régression linéaire : un coefficient n'a de sens qu'en présence des autres variables.* |
| 5 | R² et RMSE sur les 59 boutiques, comparés au « modèle moyenne » | Un modèle n'est utile que s'il se trompe moins que « prédire toujours le CA moyen ». *Cours Régression linéaire.* Ici on décrit le lien ; l'évaluation sur des boutiques non vues (`train_test_split`) est faite en Q4, où on cherche à prédire. |
| 6 | Nuage des résidus du modèle « loyer seul » | Si les erreurs sont rangées par type d'emplacement, le loyer rate une information. *Cours Régression linéaire : résidus.* |

## Ce que j'ai vérifié

- **Sans les 5 gares** (54 boutiques), parce qu'elles ont un passage et un CA hors norme. Le passage reste meilleur que le loyer : R² de 0,38 contre 0,13.
- **Sans les 3 surfaces remplacées** par une médiane au nettoyage (56 boutiques). Rien ne bouge : R² de 0,18 pour le loyer et 0,68 pour le passage.
- **Les résidus du modèle loyer seul** ne sont pas au hasard. Le loyer sous-estime les gares d'environ 10 900 € (résidu médian) et surestime les rues passantes et les quartiers résidentiels d'environ 1 400 à 1 600 €. Le loyer ne voit pas ce qui fait la différence entre les emplacements.

## Résultats chiffrés

**Corrélations avec le CA (Pearson)** : passage 0,82, loyer 0,43, surface 0,35, loyer au m² 0,24, concurrents −0,22.
Le loyer est d'abord lié à la surface (0,68), bien plus qu'au passage (0,39).

**CA médian par tranche :**

| Tranche | par loyer | par passage |
|---|---|---|
| Q1 (bas) | 13 262 € | 13 948 € |
| Q2 | 17 105 € | 15 120 € |
| Q3 | 16 964 € | 16 376 € |
| Q4 (haut) | 19 268 € | 23 225 € |

Par tranche de passage, le CA monte à chaque marche, et nettement en haut (+67 % de Q1 à Q4). Par tranche de loyer, il monte moins (+45 %) et pas de façon régulière : Q3 fait moins que Q2.

**Régressions :**

| Modèle | R² | RMSE | RMSE modèle moyenne | Lecture |
|---|---|---|---|---|
| loyer seul | 0,18 | 5 317 € | 5 880 € | +1 000 € de loyer = +1 308 € de CA |
| surface seule | 0,12 | 5 503 € | 5 880 € | +10 m² = +927 € de CA |
| passage seul | 0,67 | 3 390 € | 5 880 € | +1 000 passants/jour = +1 253 € de CA |
| loyer + surface | 0,19 | 5 294 € | 5 880 € | le loyer tombe à +1 067 € |
| loyer + passage | 0,68 | 3 319 € | 5 880 € | le loyer tombe à **+391 €** |

Le loyer seul fait à peine mieux que le modèle moyenne (5 317 € d'erreur contre 5 880 €, soit 10 % de moins). Le passage seul réduit l'erreur de 42 % (3 390 €). Quand on ajoute le passage, l'effet du loyer est divisé par plus de trois (de 1 308 € à 391 €) et le R² ne gagne qu'un point (0,67 → 0,68). Ce que le loyer semblait dire sur le CA, c'était en fait surtout le passage.

## Recommandation

- **Le chiffre :** le loyer explique 18 % des écarts de CA entre boutiques, le passage piéton 67 %.
- **La décision :** pour juger un emplacement, compter le passage piéton devant la porte. Le loyer est un coût à négocier, pas une preuve de potentiel.
- **Ce que ça rapporte :** les boutiques du quart le plus passant font un CA médian supérieur de 9 277 € (+67 %) à celles du quart le moins passant. Un loyer élevé, lui, ne garantit pas ce supplément.

**Limites :** 59 boutiques seulement, et les RMSE sont mesurées sur les boutiques qui ont servi à ajuster le modèle : elles décrivent le lien, elles ne garantissent pas la qualité d'une prédiction sur une nouvelle boutique (c'est l'objet de la Q4). Le passage piéton est fortement tiré par les 5 gares, mais il reste le meilleur indicateur sans elles.

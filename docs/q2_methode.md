# Question 2 : le loyer est-il un bon indicateur du potentiel ?

## La question

Le directeur immobilier pense qu'un loyer cher veut dire une bonne adresse, et donc un bon chiffre d'affaires.
Si c'était vrai, on pourrait regarder le loyer d'un local pour savoir s'il va marcher.

Le problème, c'est qu'un loyer peut être cher pour deux raisons : le local est grand, ou il est dans un endroit passant.
On a donc voulu savoir ce qui reste du lien entre loyer et CA quand on tient compte de la surface et du passage.

On travaille sur les 59 boutiques gardées après le nettoyage, avec le CA moyen de 2024. Les montants sont donnés dans l'unité du fichier.

## Ce qu'on a fait

On a d'abord regardé les médianes par type d'emplacement et la matrice de corrélation.
Le passage piéton est la variable la plus liée au CA (r = 0,82). Le loyer l'est beaucoup moins (r = 0,43), et il est surtout lié à la surface (r = 0,68).

On a ensuite coupé les boutiques en 4 tranches de loyer et 4 tranches de passage, et regardé le CA médian de chaque tranche.
Quand le passage augmente, le CA monte à chaque tranche (+67 % entre la plus basse et la plus haute).
Avec le loyer, il monte moins (+45 %) et pas de façon régulière : la 3e tranche vend moins que la 2e.

Enfin, on a fait plusieurs régressions linéaires :

| Modèle | R² | Erreur moyenne (RMSE) | Ce que dit le coefficient |
|---|---|---|---|
| Aucun modèle (on prédit la moyenne) | 0 | 5 880 € | - |
| Loyer seul | 0,18 | 5 317 € | +1 000 € de loyer ≈ +1 300 € de CA |
| Surface seule | 0,12 | 5 503 € | +10 m² ≈ +930 € de CA |
| Passage seul | 0,67 | 3 390 € | +1 000 passants/jour ≈ +1 250 € de CA |
| Loyer + surface | 0,19 | 5 294 € | le loyer tombe à +1 070 € |
| Loyer + passage | 0,68 | 3 319 € | le loyer tombe à +390 € |

Le loyer seul fait à peine mieux que prédire la moyenne.
Le point important, c'est la dernière ligne : quand on met le loyer et le passage ensemble, l'effet du loyer est divisé par trois, et le R² ne bouge presque pas.
Ce que le loyer semblait expliquer venait en fait surtout du passage.

## Ce qu'on a vérifié

- Sans les 5 gares, qui ont beaucoup de passage et un gros CA : le passage reste meilleur que le loyer (R² de 0,38 contre 0,13).
- Sans les 3 boutiques dont on avait remplacé la surface au nettoyage : les résultats ne changent pas.
- Les erreurs du modèle « loyer seul » ne sont pas réparties au hasard : il sous-estime les gares d'environ 10 900 €. Il passe donc à côté de ce qui fait vraiment la différence entre les emplacements.

## Conclusion et recommandation

Le loyer explique environ 18 % des différences de CA entre boutiques, contre 67 % pour le passage piéton.
Pour juger un emplacement, il faut donc compter le passage devant la porte, et voir le loyer comme un coût à négocier plutôt que comme une preuve que le local va marcher.
Les boutiques les plus passantes font un CA médian supérieur d'environ 9 300 € (+67 %) aux moins passantes, alors qu'un loyer élevé ne garantit pas ça.

Limites : on n'a que 59 boutiques, et les erreurs sont calculées sur les boutiques qui ont servi à faire la régression. Elles décrivent le lien mais ne disent pas à quel point on se tromperait sur une nouvelle boutique : c'est le rôle de la Q4.
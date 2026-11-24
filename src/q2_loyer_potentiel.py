"""
Question 2 : le loyer est-il un bon indicateur de l'emplacement, donc du potentiel (CA) ?

Lancer depuis la racine du projet : python src/q2_loyer_potentiel.py
Entrée : data/clean/boutiques_clean.csv (produit par src/01_nettoyage.py)
Sorties : outputs/tables/q2_*.csv et outputs/figures/q2_*.png
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # pas de fenêtre, on écrit directement les PNG
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

RACINE = Path(__file__).resolve().parent.parent
FIGURES = RACINE / "outputs" / "figures"
TABLES = RACINE / "outputs" / "tables"
FIGURES.mkdir(parents=True, exist_ok=True)
TABLES.mkdir(parents=True, exist_ok=True)

# Cible choisie au nettoyage : le CA moyen 2024 recalculé depuis les ventes.
CIBLE = "ca_moyen_2024"
LOYER = "loyer_mensuel_eur"
PASSAGE = "passage_pietons_jour"
SURFACE = "surface_m2"

# Une couleur par type d'emplacement, la même sur toutes les figures.
COULEURS = {
    "gare": "#d62728",
    "centre commercial": "#1f77b4",
    "rue passante": "#2ca02c",
    "quartier résidentiel": "#ff7f0e",
}


def titre(texte):
    print("\n" + "=" * 70 + "\n" + texte + "\n" + "=" * 70)


def euros(x, signe=False):
    """Écrit un montant à la française : 1308.4 -> '1 308', avec '+' si signe=True."""
    texte = f"{x:+,.0f}" if signe else f"{x:,.0f}"
    return texte.replace(",", " ")


b = pd.read_csv(RACINE / "data" / "clean" / "boutiques_clean.csv", encoding="utf-8")
# Le loyer au m² enlève l'effet taille : c'est le prix de l'adresse.
b["loyer_m2"] = b[LOYER] / b[SURFACE]
print(f"{len(b)} boutiques, cible = {CIBLE} (montants dans l'unité du fichier)")


# a) Analyse exploratoire
titre("a) Médianes par type d'emplacement et matrice de corrélation")

# Médiane plutôt que moyenne : elle n'est pas tirée par les gares (cours Analyse exploratoire).
medianes = (b.groupby("emplacement")[[LOYER, "loyer_m2", PASSAGE, CIBLE]]
            .median().round(0).sort_values(CIBLE, ascending=False))
medianes["n_boutiques"] = b["emplacement"].value_counts()
print(medianes.to_string())
medianes.to_csv(TABLES / "q2_medianes_emplacement.csv", encoding="utf-8")

# Matrice de Pearson : force du lien linéaire entre chaque paire de colonnes.
colonnes = [LOYER, "loyer_m2", SURFACE, PASSAGE, "concurrents_300m", CIBLE]
matrice = b[colonnes].corr(method="pearson").round(2)
print("\n" + matrice.to_string())
matrice.to_csv(TABLES / "q2_matrice_correlation.csv", encoding="utf-8")

fig, ax = plt.subplots(figsize=(7.5, 6))
image = ax.imshow(matrice, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(colonnes)), colonnes, rotation=40, ha="right")
ax.set_yticks(range(len(colonnes)), colonnes)
for i in range(len(colonnes)):
    for j in range(len(colonnes)):
        ax.text(j, i, f"{matrice.iloc[i, j]:.2f}", ha="center", va="center", fontsize=9)
fig.colorbar(image, ax=ax, label="r de Pearson")
ax.set_title("Matrice de corrélation (Pearson)")
fig.tight_layout()
fig.savefig(FIGURES / "q2_matrice_correlation.png", dpi=150)
plt.close(fig)


# b) CA médian par tranche
titre("b) CA médian par tranche de loyer et par tranche de passage")

# 4 tranches de même effectif, coupées aux quartiles (cours Analyse exploratoire).
noms = ["Q1 (bas)", "Q2", "Q3", "Q4 (haut)"]
b["tranche_loyer"] = pd.qcut(b[LOYER], q=4, labels=noms)
b["tranche_passage"] = pd.qcut(b[PASSAGE], q=4, labels=noms)

tranches = pd.DataFrame({
    "ca_median_par_tranche_loyer": b.groupby("tranche_loyer", observed=True)[CIBLE].median(),
    "ca_median_par_tranche_passage": b.groupby("tranche_passage", observed=True)[CIBLE].median(),
}).round(0)
print(tranches.to_string())
tranches.to_csv(TABLES / "q2_ca_par_tranche.csv", encoding="utf-8")

# Écart entre la tranche haute et la tranche basse : c'est ce qu'on compare.
hausse_loyer = tranches.iloc[-1, 0] / tranches.iloc[0, 0] - 1
hausse_passage = tranches.iloc[-1, 1] / tranches.iloc[0, 1] - 1
print(f"\nDe Q1 à Q4 : CA médian +{hausse_loyer:.0%} par tranche de loyer, "
      f"+{hausse_passage:.0%} par tranche de passage.")

fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
for ax, col, nom, couleur in zip(axes, tranches.columns, ["loyer", "passage piéton"],
                                 ["#7f7f7f", "#2ca02c"]):
    ax.bar(tranches.index.astype(str), tranches[col], color=couleur)
    for k, v in enumerate(tranches[col]):
        ax.text(k, v, euros(v), ha="center", va="bottom", fontsize=9)
    ax.set_title(f"CA médian par tranche de {nom}")
    ax.set_xlabel(f"Quartile de {nom}")
axes[0].set_ylabel("CA moyen 2024 médian (€, unité du fichier)")
fig.tight_layout()
fig.savefig(FIGURES / "q2_ca_par_tranche.png", dpi=150)
plt.close(fig)


# c) Régressions linéaires
titre("c) Régressions linéaires")


def regression(df, variables, nom):
    """Ajuste CA = a1*x1 + a2*x2 + ... + b et renvoie les mesures du cours."""
    X = df[variables]
    y = df[CIBLE]

    # Modèle sur toutes les boutiques : sert à lire les coefficients, le R² et la RMSE.
    modele = LinearRegression().fit(X, y)
    prediction = modele.predict(X)

    # Le "modèle moyenne" prédit toujours le CA moyen : la régression doit se tromper moins que lui.
    # Ici on décrit le lien sur les 59 boutiques ; l'évaluation sur des boutiques
    # non vues (train_test_split) est faite en Q4, où on cherche vraiment à prédire.
    rmse_moyenne = np.sqrt(mean_squared_error(y, np.full(len(y), y.mean())))

    ligne = {"modele": nom, "n": len(df),
             "R2": r2_score(y, prediction),
             "RMSE": np.sqrt(mean_squared_error(y, prediction)),
             "RMSE_modele_moyenne": rmse_moyenne}
    for var, coef in zip(variables, modele.coef_):
        ligne[f"coef_{var}"] = coef
    return ligne, modele


def phrase(ligne):
    """Traduit les coefficients en langage métier."""
    morceaux = []
    if f"coef_{LOYER}" in ligne and not pd.isna(ligne[f"coef_{LOYER}"]):
        morceaux.append(f"+1 000 € de loyer = {euros(ligne[f'coef_{LOYER}'] * 1000, True)} € de CA")
    if f"coef_{SURFACE}" in ligne and not pd.isna(ligne[f"coef_{SURFACE}"]):
        morceaux.append(f"+10 m² = {euros(ligne[f'coef_{SURFACE}'] * 10, True)} € de CA")
    if f"coef_{PASSAGE}" in ligne and not pd.isna(ligne[f"coef_{PASSAGE}"]):
        morceaux.append(f"+1 000 passants/jour = {euros(ligne[f'coef_{PASSAGE}'] * 1000, True)} € de CA")
    return " ; ".join(morceaux)


modeles = [
    ([LOYER], "loyer seul"),
    ([SURFACE], "surface seule"),
    ([PASSAGE], "passage seul"),
    ([LOYER, SURFACE], "loyer + surface"),
    ([LOYER, PASSAGE], "loyer + passage"),
]
lignes = []
for variables, nom in modeles:
    ligne, modele = regression(b, variables, nom)
    lignes.append(ligne)
    if nom == "loyer seul":
        modele_loyer = modele  # gardé pour le nuage des résidus
    print(f"{nom:<16} R² = {ligne['R2']:.2f} | RMSE = {euros(ligne['RMSE'])} € "
          f"vs modèle moyenne {euros(ligne['RMSE_modele_moyenne'])} €")
    print(f"{'':<16} {phrase(ligne)}")

# Cours Régression linéaire : un coefficient n'a de sens qu'en présence des autres variables.
# Si celui du loyer fond quand on ajoute la surface ou le passage, c'est que le loyer
# ne faisait que refléter la taille du local ou le passage devant la porte.
regressions = pd.DataFrame(lignes)
coef_seul = regressions.loc[regressions["modele"] == "loyer seul", f"coef_{LOYER}"].iloc[0]
coef_avec_surface = regressions.loc[regressions["modele"] == "loyer + surface", f"coef_{LOYER}"].iloc[0]
coef_avec_passage = regressions.loc[regressions["modele"] == "loyer + passage", f"coef_{LOYER}"].iloc[0]
print(f"\nEffet de 1 000 € de loyer : {euros(coef_seul * 1000)} € seul, "
      f"{euros(coef_avec_surface * 1000)} € avec la surface, "
      f"{euros(coef_avec_passage * 1000)} € avec le passage.")


# d) Vérifications avant de faire confiance au résultat
titre("d) Vérifications")

# Les 5 gares ont un passage et un CA hors norme : le résultat tient-il sans elles ?
# Et sans les 3 surfaces remplacées par une médiane au nettoyage ?
echantillons = {
    "sans gares": b[b["emplacement"] != "gare"],
    "sans surfaces imputées": b[~b["surface_imputee"]],
}
for nom_ech, df in echantillons.items():
    for variables, nom in [([LOYER], "loyer seul"), ([PASSAGE], "passage seul")]:
        ligne, _ = regression(df, variables, f"{nom} ({nom_ech})")
        lignes.append(ligne)
        print(f"{ligne['modele']:<38} n = {ligne['n']} | R² = {ligne['R2']:.2f} | {phrase(ligne)}")

regressions = pd.DataFrame(lignes)
regressions.round(4).to_csv(TABLES / "q2_regressions.csv", index=False, encoding="utf-8")

# Nuage des résidus du modèle loyer seul : s'ils sont rangés par emplacement
# au lieu d'être répartis au hasard autour de 0, le loyer rate une information.
b["prediction_loyer"] = modele_loyer.predict(b[[LOYER]])
b["residu_loyer"] = b[CIBLE] - b["prediction_loyer"]
print("\nRésidu médian du modèle loyer seul par emplacement :")
print(b.groupby("emplacement")["residu_loyer"].median().round(0).to_string())

fig, ax = plt.subplots(figsize=(8, 5))
for emplacement, couleur in COULEURS.items():
    sous = b[b["emplacement"] == emplacement]
    ax.scatter(sous["prediction_loyer"], sous["residu_loyer"], color=couleur, s=55,
               alpha=0.8, edgecolor="white", label=emplacement)
ax.axhline(0, color="grey", linestyle="--", linewidth=1)
ax.set_title("Résidus du modèle « loyer seul »\n(CA réel - CA prédit par le loyer)")
ax.set_xlabel("CA prédit par le loyer (€)")
ax.set_ylabel("Résidu (€)")
ax.legend(title="Emplacement")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIGURES / "q2_residus_loyer.png", dpi=150)
plt.close(fig)


# e) Nuages de points avec r de Pearson dans le titre
titre("e) Nuages de points")


def nuage(x, label_x, nom_fichier, titre_fig):
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for emplacement, couleur in COULEURS.items():
        sous = b[b["emplacement"] == emplacement]
        ax.scatter(sous[x], sous[CIBLE], color=couleur, s=55, alpha=0.8,
                   edgecolor="white", label=f"{emplacement} ({len(sous)})")
    # Droite de la régression linéaire simple x -> CA.
    droite = LinearRegression().fit(b[[x]], b[CIBLE])
    xs = pd.DataFrame({x: [b[x].min(), b[x].max()]})
    ax.plot(xs[x], droite.predict(xs), color="grey", linestyle="--", linewidth=1)
    r = b[x].corr(b[CIBLE])
    ax.set_title(f"{titre_fig}\nPearson r = {r:.2f} | n = {len(b)}")
    ax.set_xlabel(label_x)
    ax.set_ylabel("CA moyen 2024 (€, unité du fichier)")
    ax.legend(title="Emplacement")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES / nom_fichier, dpi=150)
    plt.close(fig)
    print(f"outputs/figures/{nom_fichier} (r = {r:.2f})")


nuage(LOYER, "Loyer mensuel (€)", "q2_loyer_vs_ca.png", "Loyer vs chiffre d'affaires")
nuage("loyer_m2", "Loyer au m² (€ / m² / mois)", "q2_loyer_m2_vs_ca.png", "Loyer au m² vs chiffre d'affaires")
nuage(PASSAGE, "Passage piéton (personnes / jour)", "q2_passage_vs_ca.png", "Passage piéton vs chiffre d'affaires")


# g) Conclusion : un chiffre, une décision, ce qu'elle rapporte
titre("g) Conclusion")


def r2(nom):
    return regressions.loc[regressions["modele"] == nom, "R2"].iloc[0]


ecart_passage = tranches.iloc[-1, 1] - tranches.iloc[0, 1]
print(f"CHIFFRE : le loyer explique {r2('loyer seul'):.0%} des écarts de CA entre boutiques, "
      f"le passage piéton {r2('passage seul'):.0%}. Une fois le passage connu, 1 000 € de loyer "
      f"en plus ne valent plus que {euros(coef_avec_passage * 1000)} € de CA (contre "
      f"{euros(coef_seul * 1000)} € seul).")
print("DÉCISION : pour juger un emplacement, compter le passage piéton devant la porte ; "
      "traiter le loyer comme un coût à négocier, pas comme une preuve de potentiel.")
print(f"CE QUE ÇA RAPPORTE : les boutiques du quart le plus passant font un CA médian supérieur de "
      f"{euros(ecart_passage)} € (unité du fichier) à celles du quart le moins passant, "
      f"soit +{hausse_passage:.0%}, contre +{hausse_loyer:.0%} entre loyers hauts et bas.")

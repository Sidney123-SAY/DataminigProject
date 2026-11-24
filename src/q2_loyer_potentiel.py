"""
Question 2 — Le loyer est-il un bon indicateur de l'emplacement, donc du potentiel (CA) ?

Lancer depuis la racine du projet :
    python src/q2_loyer_potentiel.py

Entrée :
    data/clean/boutiques_clean.csv   (produit par src/01_nettoyage.py)
Sorties :
    outputs/figures/q2_loyer_vs_ca.png
    outputs/figures/q2_loyer_m2_vs_ca.png
    outputs/figures/q2_passage_vs_ca.png
    outputs/tables/q2_correlations.csv

Idée générale : si le loyer « résume » la qualité d'un emplacement, alors les
boutiques qui paient cher doivent vendre plus. On mesure la force de ce lien,
on vérifie qu'il ne vient pas simplement de la taille du local, puis on le
compare à un indicateur concurrent : le passage piéton.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # pas de fenêtre graphique : on écrit directement des PNG
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

# ---------------------------------------------------------------------------
# 0. Chemins et constantes
# ---------------------------------------------------------------------------
RACINE = Path(__file__).resolve().parent.parent
FIGURES = RACINE / "outputs" / "figures"
TABLES = RACINE / "outputs" / "tables"
FIGURES.mkdir(parents=True, exist_ok=True)
TABLES.mkdir(parents=True, exist_ok=True)

# Cible : le CA moyen 2024 recalculé depuis les ventes (décision 9 bis du
# journal de nettoyage), plus fiable que le CA saisi dans la fiche.
CIBLE = "ca_moyen_2024"

# Une couleur fixe par type d'emplacement, la même sur toutes les figures.
COULEURS = {
    "gare": "#d62728",
    "centre commercial": "#1f77b4",
    "rue passante": "#2ca02c",
    "quartier résidentiel": "#ff7f0e",
}


def titre(texte):
    """Affiche un titre de section lisible dans la console."""
    print("\n" + "=" * 70 + "\n" + texte + "\n" + "=" * 70)


# ---------------------------------------------------------------------------
# 1. Lecture et variable dérivée
# Le loyer au m² retire l'effet "grand local = gros loyer" : c'est le prix
# que le marché donne à l'ADRESSE, indépendamment de la taille.
# ---------------------------------------------------------------------------
b = pd.read_csv(RACINE / "data" / "clean" / "boutiques_clean.csv", encoding="utf-8")
b["loyer_m2"] = b["loyer_mensuel_eur"] / b["surface_m2"]

titre("1. Données")
print(f"{len(b)} boutiques ; cible = {CIBLE}")
print(b.groupby("emplacement")[["loyer_mensuel_eur", "loyer_m2", "passage_pietons_jour", CIBLE]]
      .median().round(0).to_string())


# ---------------------------------------------------------------------------
# 2. Fonctions de mesure
# ---------------------------------------------------------------------------
def correlations(df, x, echantillon, controle=""):
    """Pearson ET Spearman entre la colonne x et le CA, avec leurs p-valeurs.

    Pourquoi les deux ?
      - Pearson mesure un lien LINÉAIRE et il est sensible aux valeurs extrêmes
        (ici les 5 gares, très au-dessus du reste) ;
      - Spearman travaille sur les RANGS : il mesure si « plus de x » va avec
        « plus de CA », même si la relation est courbe, et quelques points
        extrêmes ne le tirent pas.
    Si les deux sont proches, le résultat est solide. S'ils divergent, c'est
    que quelques boutiques atypiques font une partie du résultat.

    La p-valeur est la probabilité d'observer une corrélation aussi forte par
    pur hasard s'il n'y avait aucun lien. En dessous de 0,05 on parle de lien
    significatif.
    """
    r, p_r = stats.pearsonr(df[x], df[CIBLE])
    rho, p_rho = stats.spearmanr(df[x], df[CIBLE])
    return {"echantillon": echantillon, "indicateur": x, "controle": controle,
            "n": len(df), "pearson_r": r, "pearson_p": p_r,
            "spearman_rho": rho, "spearman_p": p_rho}


def residus(y, z):
    """Ce qui reste de y une fois retirée la partie expliquée par z.
    On ajuste la droite y = a*z + b (np.polyfit, degré 1) puis on soustrait."""
    a, b0 = np.polyfit(z, y, 1)
    return y - (a * z + b0)


def correlation_partielle(x, y, z):
    """Corrélation entre x et y « à z égal ».

    Méthode des résidus : on retire de x ce que z explique, on retire de y ce
    que z explique, et on corrèle ce qui reste. Si la corrélation tombe à zéro,
    c'est que le lien x–y passait entièrement par z.
    La p-valeur vient d'un test de Student à n - 3 degrés de liberté
    (un de moins que la corrélation simple, car on a estimé l'effet de z).
    """
    r = np.corrcoef(residus(x, z), residus(y, z))[0, 1]
    ddl = len(x) - 3
    t = r * np.sqrt(ddl / (1 - r ** 2))
    p = 2 * stats.t.sf(abs(t), ddl)
    return r, p


def ligne_partielle(df, x, z, echantillon="toutes"):
    """Corrélation partielle x–CA en contrôlant z, version Pearson (valeurs)
    et version Spearman (on applique la même formule aux rangs)."""
    r, p_r = correlation_partielle(df[x], df[CIBLE], df[z])
    rho, p_rho = correlation_partielle(df[x].rank(), df[CIBLE].rank(), df[z].rank())
    return {"echantillon": echantillon, "indicateur": x, "controle": z,
            "n": len(df), "pearson_r": r, "pearson_p": p_r,
            "spearman_rho": rho, "spearman_p": p_rho}


def nuage(x, label_x, nom_fichier, titre_fig):
    """Nuage de points x vs CA, une couleur par type d'emplacement, avec la
    droite de régression et les deux corrélations dans le titre."""
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for emplacement, couleur in COULEURS.items():
        sous = b[b["emplacement"] == emplacement]
        ax.scatter(sous[x], sous[CIBLE], color=couleur, s=55, alpha=0.8,
                   edgecolor="white", label=f"{emplacement} ({len(sous)})")
    # Droite de régression sur l'ensemble des boutiques (repère visuel).
    a, b0 = np.polyfit(b[x], b[CIBLE], 1)
    xs = np.array([b[x].min(), b[x].max()])
    ax.plot(xs, a * xs + b0, color="grey", linestyle="--", linewidth=1)
    c = correlations(b, x, "toutes")
    ax.set_title(f"{titre_fig}\nPearson r = {c['pearson_r']:.2f} | "
                 f"Spearman rho = {c['spearman_rho']:.2f} | n = {c['n']}")
    ax.set_xlabel(label_x)
    ax.set_ylabel("CA moyen 2024 (€, unité du fichier)")
    ax.legend(title="Emplacement")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES / nom_fichier, dpi=150)
    plt.close(fig)
    print(f"Figure écrite : outputs/figures/{nom_fichier}")


# ---------------------------------------------------------------------------
# 3. Loyer vs CA : corrélation brute
# ---------------------------------------------------------------------------
titre("3. Loyer vs CA")
lignes = []  # on accumule ici toutes les lignes du tableau final
lignes.append(correlations(b, "loyer_mensuel_eur", "toutes"))
nuage("loyer_mensuel_eur", "Loyer mensuel (€)", "q2_loyer_vs_ca.png",
      "Loyer vs chiffre d'affaires")

# ---------------------------------------------------------------------------
# 4. Le loyer n'est-il qu'un effet de la taille du local ?
# Un grand local coûte plus cher ET permet de vendre plus. Deux contrôles :
#   a) le loyer au m² (prix de l'adresse, sans la taille) ;
#   b) la corrélation partielle loyer–CA à surface égale.
# ---------------------------------------------------------------------------
titre("4. Effet de la taille")
r_ls, _ = stats.pearsonr(b["loyer_mensuel_eur"], b["surface_m2"])
print(f"Corrélation loyer–surface : {r_ls:.2f} -> le loyer reflète d'abord la taille.")
lignes.append(correlations(b, "surface_m2", "toutes"))
lignes.append(correlations(b, "loyer_m2", "toutes"))
lignes.append(ligne_partielle(b, "loyer_mensuel_eur", "surface_m2"))
nuage("loyer_m2", "Loyer au m² (€ / m² / mois)", "q2_loyer_m2_vs_ca.png",
      "Loyer au m² vs chiffre d'affaires")

# Vérification : 3 surfaces ont été imputées au nettoyage (médiane du type).
# On refait le calcul sans elles pour voir si le loyer au m² en dépend.
sans_imput = b[~b["surface_imputee"]]
lignes.append(correlations(sans_imput, "loyer_m2", "sans surfaces imputées"))

# ---------------------------------------------------------------------------
# 5. Indicateur concurrent : le passage piéton
# On le soumet aux mêmes mesures, puis on fait le test croisé :
#   - que reste-t-il du loyer une fois le passage connu ?
#   - que reste-t-il du passage une fois le loyer connu ?
# ---------------------------------------------------------------------------
titre("5. Passage piéton")
lignes.append(correlations(b, "passage_pietons_jour", "toutes"))
lignes.append(ligne_partielle(b, "loyer_mensuel_eur", "passage_pietons_jour"))
lignes.append(ligne_partielle(b, "passage_pietons_jour", "loyer_mensuel_eur"))
nuage("passage_pietons_jour", "Passage piéton (personnes / jour)", "q2_passage_vs_ca.png",
      "Passage piéton vs chiffre d'affaires")

# Vérification : les 5 gares ont un passage et un CA hors norme. On retire
# les gares pour voir si le passage reste meilleur que le loyer sans elles.
sans_gares = b[b["emplacement"] != "gare"]
lignes.append(correlations(sans_gares, "loyer_mensuel_eur", "sans gares"))
lignes.append(correlations(sans_gares, "passage_pietons_jour", "sans gares"))

# Vérification : le lien tient-il À L'INTÉRIEUR de chaque type d'emplacement ?
# (Une corrélation globale peut n'être qu'une différence entre groupes.)
for emplacement in COULEURS:
    sous = b[b["emplacement"] == emplacement]
    lignes.append(correlations(sous, "loyer_mensuel_eur", emplacement))
    lignes.append(correlations(sous, "passage_pietons_jour", emplacement))

# ---------------------------------------------------------------------------
# 6. Tableau final
# ---------------------------------------------------------------------------
titre("6. Tableau des corrélations")
tableau = pd.DataFrame(lignes)
# r² = part de la variance du CA « expliquée » par l'indicateur seul.
tableau["r2"] = tableau["pearson_r"] ** 2
tableau.round(4).to_csv(TABLES / "q2_correlations.csv", index=False, encoding="utf-8")
print(tableau.round(3).to_string(index=False))
print("\nTableau écrit : outputs/tables/q2_correlations.csv")

# ---------------------------------------------------------------------------
# 7. Conclusion chiffrée
# On relit les valeurs dans le tableau pour que la phrase suive toujours
# les données (rien n'est recopié à la main).
# ---------------------------------------------------------------------------
titre("7. Conclusion")


def valeur(indicateur, controle="", echantillon="toutes"):
    """Retrouve une ligne du tableau."""
    m = ((tableau["indicateur"] == indicateur) & (tableau["controle"] == controle)
         & (tableau["echantillon"] == echantillon))
    return tableau[m].iloc[0]


loyer = valeur("loyer_mensuel_eur")
loyer_m2 = valeur("loyer_m2")
passage = valeur("passage_pietons_jour")
loyer_a_surface = valeur("loyer_mensuel_eur", "surface_m2")
loyer_a_passage = valeur("loyer_mensuel_eur", "passage_pietons_jour")
passage_a_loyer = valeur("passage_pietons_jour", "loyer_mensuel_eur")

print(f"- Loyer seul       : r = {loyer['pearson_r']:.2f}, rho = {loyer['spearman_rho']:.2f} "
      f"-> explique {loyer['r2']:.0%} de la variance du CA.")
print(f"- Loyer au m²      : r = {loyer_m2['pearson_r']:.2f} (p = {loyer_m2['pearson_p']:.2f}), "
      f"rho = {loyer_m2['spearman_rho']:.2f} (p = {loyer_m2['spearman_p']:.2f}).")
print(f"- Loyer à surface égale : r = {loyer_a_surface['pearson_r']:.2f} "
      f"(p = {loyer_a_surface['pearson_p']:.3f}), rho = {loyer_a_surface['spearman_rho']:.2f} "
      f"(p = {loyer_a_surface['spearman_p']:.3f}).")
print(f"- Passage piéton   : r = {passage['pearson_r']:.2f}, rho = {passage['spearman_rho']:.2f} "
      f"-> explique {passage['r2']:.0%} de la variance du CA.")
print(f"- Loyer à passage égal  : r = {loyer_a_passage['pearson_r']:.2f} "
      f"(p = {loyer_a_passage['pearson_p']:.3f}).")
print(f"- Passage à loyer égal  : r = {passage_a_loyer['pearson_r']:.2f} "
      f"(p = {passage_a_loyer['pearson_p']:.1e}).")

# Recommandation pour la direction (le chiffre clé + la décision).
print(f"\nRECOMMANDATION : le loyer n'explique que {loyer['r2']:.0%} des écarts de CA entre "
      f"boutiques, contre {passage['r2']:.0%} pour le passage piéton ; une fois le passage "
      f"connu, le loyer n'apporte presque plus rien (r = {loyer_a_passage['pearson_r']:.2f}). "
      "Pour juger une ouverture, se fier au comptage du passage piéton et traiter le loyer "
      "comme un coût à négocier, pas comme une preuve de la qualité de l'emplacement.")

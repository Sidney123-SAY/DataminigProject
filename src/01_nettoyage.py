"""
Étape 1 — Nettoyage des données Maison Delorme.

Lancer depuis la racine du projet :
    python src/01_nettoyage.py

Entrées (jamais modifiées) :
    data/raw/Delorme_boutiques.csv
    data/raw/Delorme_ventes_mensuelles.csv
Sorties :
    data/clean/boutiques_clean.csv
    data/clean/ventes_clean.csv
    outputs/tables/qualite_donnees.csv   (profil avant / après, par colonne)
    outputs/tables/ecarts_ca.csv         (CA de la fiche vs moyenne des ventes 2024)

Chaque décision prise ici est écrite en une phrase dans docs/journal_nettoyage.md.
"""

from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 0. Chemins
# On part de l'emplacement du script pour que les chemins marchent
# quel que soit le dossier d'où on lance la commande.
# ---------------------------------------------------------------------------
RACINE = Path(__file__).resolve().parent.parent
RAW = RACINE / "data" / "raw"
CLEAN = RACINE / "data" / "clean"
TABLES = RACINE / "outputs" / "tables"
CLEAN.mkdir(parents=True, exist_ok=True)
TABLES.mkdir(parents=True, exist_ok=True)

# Boutiques dont tout le CA vaut -1 (fiche) et 1 € / 0 ticket (ventes) :
# ce sont des valeurs de remplissage, pas des ventes réelles.
BOUTIQUES_FANTOMES = ["B101", "B105", "B121"]

# Seuil au-delà duquel on signale un écart entre le CA de la fiche boutique
# et la moyenne des ventes mensuelles 2024.
SEUIL_ECART_CA = 0.10


def titre(texte):
    """Affiche un titre de section lisible dans la console."""
    print("\n" + "=" * 70 + "\n" + texte + "\n" + "=" * 70)


def profil(df, etape):
    """Résume chaque colonne : nb de lignes, manquants, zéros, min, médiane, max.
    On l'appelle avant et après nettoyage pour montrer l'effet des décisions."""
    lignes = []
    for col in df.columns:
        s = df[col]
        info = {"etape": etape, "colonne": col, "n_lignes": len(s),
                "n_manquants": int(s.isna().sum())}
        if pd.api.types.is_numeric_dtype(s):
            info.update({"n_zeros": int((s == 0).sum()),
                         "n_negatifs": int((s < 0).sum()),
                         "min": s.min(), "mediane": s.median(), "max": s.max()})
        else:
            info["n_valeurs_distinctes"] = s.nunique()
        lignes.append(info)
    return pd.DataFrame(lignes)


# ---------------------------------------------------------------------------
# 1. Lecture
# Les fichiers sont en UTF-8 ("résidentiel" est bien codé). On le précise
# pour ne pas dépendre de l'encodage par défaut de Windows.
# ---------------------------------------------------------------------------
boutiques_brut = pd.read_csv(RAW / "Delorme_boutiques.csv", encoding="utf-8")
ventes_brut = pd.read_csv(RAW / "Delorme_ventes_mensuelles.csv", encoding="utf-8")

titre("1. Lecture des fichiers bruts")
print(f"boutiques : {boutiques_brut.shape[0]} lignes, "
      f"{boutiques_brut['boutique_id'].nunique()} identifiants distincts")
print(f"ventes    : {ventes_brut.shape[0]} lignes, "
      f"{ventes_brut['boutique_id'].nunique()} identifiants distincts")

# On travaille sur des copies : les DataFrames bruts restent intacts
# pour le profil "avant".
boutiques = boutiques_brut.copy()
ventes = ventes_brut.copy()

# ---------------------------------------------------------------------------
# 2. Couverture temporelle des ventes
# Le sujet annonce "deux ans" de ventes : on vérifie ce qu'il y a vraiment.
# ---------------------------------------------------------------------------
titre("2. Période couverte par les ventes")
mois = sorted(ventes["mois"].unique())
print(f"{len(mois)} mois distincts, de {mois[0]} à {mois[-1]}")
print("-> Le fichier ne couvre que 12 mois (2024), pas deux ans comme annoncé.")

# ---------------------------------------------------------------------------
# 3. Doublons dans boutiques.csv
# On regarde d'abord les identifiants répétés, puis si les lignes sont
# strictement identiques. Si oui, supprimer la copie ne perd aucune info.
# ---------------------------------------------------------------------------
titre("3. Doublons dans boutiques.csv")
ids_doubles = boutiques.loc[boutiques["boutique_id"].duplicated(), "boutique_id"].tolist()
print("Identifiants en double :", ids_doubles)
n_exacts = boutiques.duplicated().sum()
print(f"Lignes strictement identiques à une autre : {n_exacts}")
boutiques = boutiques.drop_duplicates().reset_index(drop=True)
# Contrôle : après suppression, chaque identifiant doit être unique.
assert boutiques["boutique_id"].is_unique, "Il reste des doublons non identiques !"
print(f"-> {n_exacts} lignes supprimées, {len(boutiques)} boutiques restantes.")

# ---------------------------------------------------------------------------
# 4. Doublons dans ventes_mensuelles.csv
# Deux cas différents :
#   - B121 : sa série de 12 mois est recopiée à l'identique -> on supprime ;
#   - B152 : deux séries de 12 mois DIFFÉRENTES pour les mêmes mois.
# Pour B152 on ne peut pas garder les deux (24 mois "2024" n'ont pas de sens).
# Règle choisie : garder la série dont la moyenne est la plus proche du CA
# de la fiche boutique, qui sert de référence indépendante.
# ---------------------------------------------------------------------------
titre("4. Doublons dans ventes_mensuelles.csv")
n_exacts_v = ventes.duplicated().sum()
print(f"Lignes strictement identiques : {n_exacts_v} "
      f"(boutiques : {ventes.loc[ventes.duplicated(), 'boutique_id'].unique().tolist()})")
ventes = ventes.drop_duplicates().reset_index(drop=True)

# Il reste des couples (boutique, mois) en double avec des valeurs différentes.
cle = ["boutique_id", "mois"]
conflits = ventes[ventes.duplicated(cle, keep=False)]
print("Boutiques avec deux séries différentes :", conflits["boutique_id"].unique().tolist())

# cumcount numérote les occurrences de chaque (boutique, mois) à partir de 0 ;
# avec +1 on obtient : 1 = 1re série, 2 = 2e série (ordre d'apparition dans le fichier).
ventes["serie"] = ventes.groupby(cle).cumcount() + 1

for bid in conflits["boutique_id"].unique():
    sous = ventes[ventes["boutique_id"] == bid]
    tableau = sous.pivot(index="mois", columns="serie", values=["ca_mensuel_eur", "tickets"])
    print(f"\nLes deux séries de {bid} :")
    print(tableau.to_string())

    ca_fiche = boutiques.loc[boutiques["boutique_id"] == bid, "ca_mensuel_eur"].iloc[0]
    moyennes = sous.groupby("serie")["ca_mensuel_eur"].mean()
    ecarts = (moyennes - ca_fiche).abs() / ca_fiche
    serie_gardee = ecarts.idxmin()
    print(f"CA fiche = {ca_fiche:.0f} € ; moyennes par série = "
          + ", ".join(f"série {k} : {m:.0f} € (écart {ecarts[k]:.1%})" for k, m in moyennes.items()))
    print(f"-> On garde la série {serie_gardee}.")
    ventes = ventes[~((ventes["boutique_id"] == bid) & (ventes["serie"] != serie_gardee))]

ventes = ventes.drop(columns="serie").reset_index(drop=True)
assert not ventes.duplicated(cle).any()
print(f"\n-> {len(ventes)} lignes de ventes restantes.")

# ---------------------------------------------------------------------------
# 5. Boutiques "fantômes" : B101, B105, B121
# CA = -1 dans la fiche (impossible) et 1 € / 0 ticket tous les mois dans les
# ventes : c'est un code de remplissage, pas une activité. Les garder fausserait
# toutes les moyennes et corrélations -> on les écarte des deux fichiers.
# ---------------------------------------------------------------------------
titre("5. Boutiques sans activité réelle")
print(boutiques.loc[boutiques["ca_mensuel_eur"] < 0, ["boutique_id", "ca_mensuel_eur", "anciennete_mois"]].to_string(index=False))
resume_v = (ventes[ventes["boutique_id"].isin(BOUTIQUES_FANTOMES)]
            .groupby("boutique_id")[["ca_mensuel_eur", "tickets"]].agg(["min", "max"]))
print(resume_v.to_string())
# Contrôle : on vérifie qu'on n'oublie aucune autre boutique dans ce cas.
autres = boutiques.loc[(boutiques["ca_mensuel_eur"] <= 0)
                       & ~boutiques["boutique_id"].isin(BOUTIQUES_FANTOMES), "boutique_id"]
assert autres.empty, f"Autres boutiques à CA <= 0 : {autres.tolist()}"
boutiques = boutiques[~boutiques["boutique_id"].isin(BOUTIQUES_FANTOMES)].reset_index(drop=True)
ventes = ventes[~ventes["boutique_id"].isin(BOUTIQUES_FANTOMES)].reset_index(drop=True)
print(f"-> Écartées. Il reste {len(boutiques)} boutiques et {len(ventes)} lignes de ventes.")
print("   Leur ancienneté (36 à 136 mois) montre que ce ne sont PAS les 3 nouvelles "
      "boutiques en difficulté de la question 1.")

# ---------------------------------------------------------------------------
# 6. Surface = 0 m² (B129, B113, B159)
# Une boulangerie de 0 m² n'existe pas : c'est une valeur manquante déguisée.
# On la remplace par la médiane des boutiques du MÊME type d'emplacement
# (un local de centre commercial n'a pas la taille d'un local de quartier).
# La médiane plutôt que la moyenne : elle n'est pas tirée par les grands locaux.
# Une colonne drapeau garde la trace pour pouvoir exclure ces lignes si besoin.
# ---------------------------------------------------------------------------
titre("6. Surfaces impossibles (0 m²)")
masque = boutiques["surface_m2"] <= 0
print(boutiques.loc[masque, ["boutique_id", "emplacement", "surface_m2", "loyer_mensuel_eur", "effectif"]].to_string(index=False))
boutiques["surface_imputee"] = masque
boutiques.loc[masque, "surface_m2"] = np.nan
mediane_par_type = boutiques.groupby("emplacement")["surface_m2"].transform("median")
boutiques["surface_m2"] = boutiques["surface_m2"].fillna(mediane_par_type)
print("Après remplacement par la médiane du type d'emplacement :")
print(boutiques.loc[masque, ["boutique_id", "emplacement", "surface_m2"]].to_string(index=False))

# ---------------------------------------------------------------------------
# 7. Valeurs manquantes : part_emporter et habitants_1km
# 3 manquants sur 59 dans chaque colonne. Supprimer ces lignes ferait perdre
# 6 boutiques sur 59 (10 %), c'est trop pour un si petit échantillon.
# On remplace par la médiane de la colonne et on garde un drapeau.
# ---------------------------------------------------------------------------
titre("7. Valeurs manquantes")
for col in ["part_emporter", "habitants_1km"]:
    manquants = boutiques[col].isna()
    med = boutiques[col].median()
    print(f"{col} : {manquants.sum()} manquants ({boutiques.loc[manquants, 'boutique_id'].tolist()}) "
          f"-> remplacés par la médiane {med:g}")
    boutiques[f"{col}_imputee"] = manquants
    boutiques[col] = boutiques[col].fillna(med)
# Contrôle : plus aucune valeur manquante dans le fichier boutiques.
assert boutiques.isna().sum().sum() == 0

# ---------------------------------------------------------------------------
# 8. CA de la fiche vs moyenne réelle des ventes 2024
# La fiche boutique donne un CA mensuel ; le fichier de ventes permet de le
# recalculer. On compare les deux pour toutes les boutiques.
# ---------------------------------------------------------------------------
titre("8. Cohérence du CA : fiche boutique vs ventes 2024")
agg = (ventes.groupby("boutique_id")
       .agg(ca_moyen_2024=("ca_mensuel_eur", "mean"),
            tickets_moyen_2024=("tickets", "mean"),
            nb_mois=("mois", "nunique"))
       .reset_index())
assert (agg["nb_mois"] == 12).all(), "Une boutique n'a pas ses 12 mois"
comparaison = boutiques[["boutique_id", "ca_mensuel_eur"]].merge(agg, on="boutique_id")
comparaison["ecart_relatif"] = (comparaison["ca_mensuel_eur"] - comparaison["ca_moyen_2024"]) / comparaison["ca_moyen_2024"]
comparaison["ecart_sup_10pct"] = comparaison["ecart_relatif"].abs() > SEUIL_ECART_CA
print(comparaison["ecart_relatif"].describe().to_string())
print(f"Boutiques avec un écart > {SEUIL_ECART_CA:.0%} : {comparaison['ecart_sup_10pct'].sum()}")

# B120 et B154 : CA fiche = 9000 tout rond, suspect.
print("\nCas B120 et B154 (CA fiche = 9 000 € tout rond) :")
print(comparaison[comparaison["boutique_id"].isin(["B120", "B154"])].round(3).to_string(index=False))
print("-> Écart < 4 % : c'est un arrondi, pas une erreur grossière. Mais il montre que "
      "la fiche est moins fiable que les ventes.")

# Décision : on ajoute le CA moyen 2024 calculé depuis les ventes.
# C'est la cible à utiliser dans les analyses : calculée de la même façon pour
# toutes les boutiques, sans arrondi saisi à la main. On garde la colonne
# d'origine pour la transparence.
boutiques = boutiques.merge(agg[["boutique_id", "ca_moyen_2024", "tickets_moyen_2024"]], on="boutique_id")
boutiques["ca_fiche_arrondi"] = boutiques["boutique_id"].isin(["B120", "B154"])
comparaison.round(4).to_csv(TABLES / "ecarts_ca.csv", index=False)

# ---------------------------------------------------------------------------
# 9. Plausibilité des unités
# On affiche min / médiane / max et on calcule quelques ratios métier
# pour juger si chaque colonne est dans l'unité annoncée par son nom.
# ---------------------------------------------------------------------------
titre("9. Plausibilité des unités")
num = boutiques.select_dtypes("number").drop(columns=["longitude", "latitude"])
print(num.describe().T[["min", "50%", "max"]].round(2).to_string())

loyer_sur_ca = boutiques["loyer_mensuel_eur"] / boutiques["ca_moyen_2024"]
loyer_m2_an = boutiques["loyer_mensuel_eur"] * 12 / boutiques["surface_m2"]
panier = ventes["ca_mensuel_eur"] / ventes["tickets"]
tickets_jour = boutiques["tickets_moyen_2024"] / 30
print(f"\nLoyer / CA mensuel      : médiane {loyer_sur_ca.median():.0%} (min {loyer_sur_ca.min():.0%}, max {loyer_sur_ca.max():.0%})")
print(f"Loyer au m² et par an   : médiane {loyer_m2_an.median():.0f} €")
print(f"Panier moyen (CA/ticket): médiane {panier.median():.2f} €")
print(f"Tickets par jour        : médiane {tickets_jour.median():.0f}")
print(f"Boutiques ouvertes depuis < 24 mois : {(boutiques['anciennete_mois'] < 24).sum()} "
      "(le sujet en annonce 18)")
print("Commentaires dans docs/journal_nettoyage.md, section 9.")

# Contrôle des coordonnées : toutes les boutiques doivent être dans Paris
# (environ 2,22-2,47 E et 48,81-48,91 N).
assert boutiques["longitude"].between(2.22, 2.47).all()
assert boutiques["latitude"].between(48.81, 48.91).all()

# ---------------------------------------------------------------------------
# 10. Sauvegarde et tableau qualité avant / après
# ---------------------------------------------------------------------------
titre("10. Sauvegarde")
boutiques.to_csv(CLEAN / "boutiques_clean.csv", index=False, encoding="utf-8")
ventes.to_csv(CLEAN / "ventes_clean.csv", index=False, encoding="utf-8")

qualite = pd.concat([
    profil(boutiques_brut, "avant").assign(fichier="boutiques"),
    profil(boutiques, "apres").assign(fichier="boutiques"),
    profil(ventes_brut, "avant").assign(fichier="ventes"),
    profil(ventes, "apres").assign(fichier="ventes"),
], ignore_index=True)
# On met fichier / colonne / étape en premier et on trie pour lire avant et après côte à côte.
colonnes = ["fichier", "colonne", "etape"] + [c for c in qualite.columns if c not in ("fichier", "colonne", "etape")]
qualite = qualite[colonnes].sort_values(["fichier", "colonne", "etape"], ascending=[True, True, False])
qualite.round(3).to_csv(TABLES / "qualite_donnees.csv", index=False)

print(f"boutiques_clean.csv : {boutiques.shape}")
print(f"ventes_clean.csv    : {ventes.shape}")
print("qualite_donnees.csv et ecarts_ca.csv écrits dans outputs/tables/")

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# Configuration de la page
st.set_page_config(page_title="Gestion de Stock & Ventes", page_icon="📦", layout="wide")

STOCK_FILE = "data_stock.csv"
VENTES_FILE = "data_ventes.csv"

# Chargement / Sauvegarde
def charger_donnees():
    if os.path.exists(STOCK_FILE):
        stock = pd.read_csv(STOCK_FILE)
    else:
        stock = pd.DataFrame(columns=["Produit", "Quantité", "Prix Unitaire (€)"])

    if os.path.exists(VENTES_FILE):
        ventes = pd.read_csv(VENTES_FILE)
    else:
        ventes = pd.DataFrame(columns=["Date", "Produit", "Quantité Vendue", "Total (€)"])

    return stock, ventes

def sauvegarder_donnees():
    st.session_state.stock.to_csv(STOCK_FILE, index=False)
    st.session_state.ventes.to_csv(VENTES_FILE, index=False)

if "stock" not in st.session_state or "ventes" not in st.session_state:
    st.session_state.stock, st.session_state.ventes = charger_donnees()

if "authentifie" not in st.session_state:
    st.session_state.authentifie = False
    st.session_state.role = None

# Connexion
if not st.session_state.authentifie:
    st.title("🔒 Connexion")
    pwd = st.text_input("Mot de passe Admin (ou cliquez sur Lecteur)", type="password")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Connexion Admin"):
            if pwd == "99":
                st.session_state.authentifie = True
                st.session_state.role = "Admin"
                st.rerun()
            else:
                st.error("Code Admin incorrect.")
    with col2:
        if st.button("Connexion Lecteur"):
            st.session_state.authentifie = True
            st.session_state.role = "Lecteur"
            st.rerun()

else:
    st.sidebar.title(f"👤 Mode : {st.session_state.role}")
    if st.sidebar.button("Déconnexion"):
        st.session_state.authentifie = False
        st.session_state.role = None
        st.rerun()

    st.title("📦 Application de Stock & Ventes")

    if st.session_state.role == "Admin":
        menu = st.sidebar.radio("Navigation", ["Tableau de Bord", "Saisir une Vente", "Gérer / Modifier le Stock"])
    else:
        menu = st.sidebar.radio("Navigation", ["Tableau de Bord"])

    # 1. TABLEAU DE BORD (CONSULTATION)
    if menu == "Tableau de Bord":
        st.header("📊 Stock & Ventes")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📦 Stock en Temps Réel")
            st.dataframe(st.session_state.stock, use_container_width=True)

        with col2:
            st.subheader("🛒 Historique des Ventes")
            st.dataframe(st.session_state.ventes, use_container_width=True)

        st.divider()
        st.subheader("📈 Courbe des Ventes")
        if not st.session_state.ventes.empty:
            ventes_cumul = st.session_state.ventes.copy()
            ventes_cumul["Vente N°"] = range(1, len(ventes_cumul) + 1)
            fig_courbe = px.line(
                ventes_cumul, 
                x="Vente N°", 
                y="Total (€)", 
                markers=True, 
                line_shape="spline"
            )
            st.plotly_chart(fig_courbe, use_container_width=True)

    # 2. SAISIR UNE VENTE
    elif menu == "Saisir une Vente":
        st.header("🛒 Enregistrer une Vente")
        if st.session_state.stock.empty:
            st.warning("Aucun produit disponible. Ajoutez des produits en mode Admin.")
        else:
            produits = st.session_state.stock["Produit"].tolist()
            prod_choisi = st.selectbox("Produit vendu :", produits)
            quantite = st.number_input("Quantité vendue :", min_value=1, step=1, value=1)

            if st.button("Valider la vente"):
                idx = st.session_state.stock[st.session_state.stock["Produit"] == prod_choisi].index[0]
                stock_actuel = st.session_state.stock.at[idx, "Quantité"]
                prix_unitaire = st.session_state.stock.at[idx, "Prix Unitaire (€)"]

                if quantite > stock_actuel:
                    st.error(f"Stock insuffisant ({stock_actuel} restant).")
                else:
                    st.session_state.stock.at[idx, "Quantité"] -= quantite
                    total = quantite * prix_unitaire
                    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    nouvelle_vente = pd.DataFrame([{
                        "Date": date_str,
                        "Produit": prod_choisi, 
                        "Quantité Vendue": quantite, 
                        "Total (€)": total
                    }])
                    st.session_state.ventes = pd.concat([st.session_state.ventes, nouvelle_vente], ignore_index=True)
                    sauvegarder_donnees()
                    st.success(f"Vente validée ! Total : {total:.2f} €")
                    st.rerun()

    # 3. GÉRER ET MODIFIER LE STOCK (ADMIN INTERACTIF)
    elif menu == "Gérer / Modifier le Stock":
        st.header("⚙️ Espace Administration (Création & Modification)")

        st.subheader("➕ 1. Créer un produit")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            nom_saisi = st.text_input("Nom du Produit :", key="nouveau_nom")
        with col_b:
            qte_saisie = st.number_input("Quantité :", min_value=0, step=1, value=0, key="nouvelle_qte")
        with col_c:
            prix_saisi = st.number_input("Prix Unitaire (€) :", min_value=0.0, step=0.5, value=0.0, key="nouveau_prix")

        if st.button("➕ Ajouter au Stock"):
            if nom_saisi.strip() == "":
                st.error("Veuillez entrer un nom de produit.")
            elif nom_saisi in st.session_state.stock["Produit"].values:
                st.error("Ce produit existe déjà.")
            else:
                nouveau_produit = pd.DataFrame([{"Produit": nom_saisi, "Quantité": qte_saisie, "Prix Unitaire (€)": prix_saisi}])
                st.session_state.stock = pd.concat([st.session_state.stock, nouveau_produit], ignore_index=True)
                sauvegarder_donnees()
                st.success(f"Produit '{nom_saisi}' créé avec succès !")
                st.rerun()

        st.divider()

        # Modification interactive des produits déjà créés
        if not st.session_state.stock.empty:
            st.subheader("✏️ 2. Modifier un produit existant")
            prod_slectionne = st.selectbox("Choisir le produit à modifier :", st.session_state.stock["Produit"].tolist())
            idx_p = st.session_state.stock[st.session_state.stock["Produit"] == prod_slectionne].index[0]

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                qte_mod = st.number_input("Changer la Quantité :", min_value=0, step=1, value=int(st.session_state.stock.at[idx_p, "Quantité"]))
            with col_m2:
                prix_mod = st.number_input("Changer le Prix (€) :", min_value=0.0, step=0.5, value=float(st.session_state.stock.at[idx_p, "Prix Unitaire (€)"]))

            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("💾 Enregistrer les modifications"):
                    st.session_state.stock.at[idx_p, "Quantité"] = qte_mod
                    st.session_state.stock.at[idx_p, "Prix Unitaire (€)"] = prix_mod
                    sauvegarder_donnees()
                    st.success("Produit mis à jour !")
                    st.rerun()
            with col_b2:
                if st.button("🗑️ Supprimer ce produit"):
                    st.session_state.stock = st.session_state.stock.drop(idx_p).reset_index(drop=True)
                    sauvegarder_donnees()
                    st.success("Produit supprimé !")
                    st.rerun()
                

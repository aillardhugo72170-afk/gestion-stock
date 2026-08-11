import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# Configuration de la page
st.set_page_config(page_title="Gestion de Stock & Ventes", page_icon="📦", layout="wide")

# Noms des fichiers de sauvegarde permanente
STOCK_FILE = "data_stock.csv"
VENTES_FILE = "data_ventes.csv"

# Fonctions pour charger et sauvegarder automatiquement les données
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

# Chargement initial des données
if "stock" not in st.session_state or "ventes" not in st.session_state:
    st.session_state.stock, st.session_state.ventes = charger_donnees()

# Authentification simple
if "authentifie" not in st.session_state:
    st.session_state.authentifie = False
    st.session_state.role = None

def connexion():
    st.title("🔒 Connexion à l'Application")
    pwd = st.text_input("Entrez le mot de passe Admin (ou cliquez directement sur Lecteur)", type="password")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Connexion Admin"):
            if pwd == "99":
                st.session_state.authentifie = True
                st.session_state.role = "Admin"
                st.rerun()
            else:
                st.error("Mot de passe Admin incorrect.")
    with col2:
        if st.button("Connexion Lecteur"):
            st.session_state.authentifie = True
            st.session_state.role = "Lecteur"
            st.rerun()

if not st.session_state.authentifie:
    connexion()
else:
    st.sidebar.title(f"👤 Mode : {st.session_state.role}")
    if st.sidebar.button("Déconnexion"):
        st.session_state.authentifie = False
        st.session_state.role = None
        st.rerun()

    st.title("📦 Gestion de Stock & Suivi des Ventes")

    # Restriction du menu selon le rôle
    if st.session_state.role == "Admin":
        menu = st.sidebar.radio("Navigation", ["Tableau de Bord", "Saisir une Vente", "Gérer le Stock (Admin)"])
    else:
        menu = st.sidebar.radio("Navigation", ["Tableau de Bord"])

    # 1. TABLEAU DE BORD
    if menu == "Tableau de Bord":
        st.header("📊 Tableau de Bord & Historique")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📦 Stock Actuel")
            if st.session_state.stock.empty:
                st.info("Aucun article en stock pour le moment.")
            else:
                st.dataframe(st.session_state.stock, use_container_width=True)

        with col2:
            st.subheader("🛒 Historique des Ventes")
            if st.session_state.ventes.empty:
                st.info("Aucune vente enregistrée pour le moment.")
            else:
                st.dataframe(st.session_state.ventes, use_container_width=True)

        st.divider()
        st.subheader("📈 Évolution des Ventes (Graphique en Courbe)")
        if st.session_state.ventes.empty:
            st.warning("Le graphique en courbe s'affichera dès qu'une première vente sera enregistrée.")
        else:
            ventes_cumul = st.session_state.ventes.copy()
            ventes_cumul["Vente N°"] = range(1, len(ventes_cumul) + 1)
            fig_courbe = px.line(
                ventes_cumul, 
                x="Vente N°", 
                y="Total (€)", 
                markers=True, 
                line_shape="spline",
                title="Évolution du Chiffre d'Affaires (€)"
            )
            fig_courbe.update_traces(line_color="#1f77b4", line_width=3)
            st.plotly_chart(fig_courbe, use_container_width=True)

    # 2. SAISIR UNE VENTE
    elif menu == "Saisir une Vente":
        st.header("🛒 Enregistrer une Nouvelle Vente")
        if st.session_state.stock.empty:
            st.warning("Le stock est vide. Veuillez d'abord ajouter des produits.")
        else:
            produits = st.session_state.stock["Produit"].tolist()
            prod_choisi = st.selectbox("Sélectionnez le produit", produits)
            quantite = st.number_input("Quantité vendue", min_value=1, step=1)

            if st.button("Valider la vente"):
                idx = st.session_state.stock[st.session_state.stock["Produit"] == prod_choisi].index[0]
                stock_actuel = st.session_state.stock.at[idx, "Quantité"]
                prix_unitaire = st.session_state.stock.at[idx, "Prix Unitaire (€)"]

                if quantite > stock_actuel:
                    st.error(f"Stock insuffisant ! Il ne reste que {stock_actuel} unités.")
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
                    sauvegarder_donnees()  # SAUVEGARDE AUTOMATIQUE
                    st.success(f"Vente enregistrée avec succès ! Total : {total:.2f} €")
                    st.rerun()

    # 3. GÉRER LE STOCK (ADMIN)
    elif menu == "Gérer le Stock (Admin)":
        if st.session_state.role != "Admin":
            st.error("Accès restreint : Seul un Administrateur peut modifier le stock.")
        else:
            st.header("⚙️ Administration du Stock")

            st.subheader("➕ Ajouter un nouveau produit")
            with st.form("ajout_produit"):
                nom_prod = st.text_input("Nom du produit")
                qte_prod = st.number_input("Quantité initiale", min_value=0, step=1, value=0)
                prix_prod = st.number_input("Prix unitaire (€)", min_value=0.0, step=0.5, value=0.0)
                valider_ajout = st.form_submit_button("Ajouter au stock")

                if valider_ajout:
                    if nom_prod.strip() == "":
                        st.error("Veuillez indiquer un nom de produit.")
                    elif nom_prod in st.session_state.stock["Produit"].values:
                        st.error("Ce produit existe déjà dans le stock.")
                    else:
                        nouveau_prod = pd.DataFrame([{"Produit": nom_prod, "Quantité": qte_prod, "Prix Unitaire (€)": prix_prod}])
                        st.session_state.stock = pd.concat([st.session_state.stock, nouveau_prod], ignore_index=True)
                        sauvegarder_donnees()  # SAUVEGARDE AUTOMATIQUE
                        st.success(f"Produit '{nom_prod}' ajouté au stock !")
                        st.rerun()

            st.divider()

            if not st.session_state.stock.empty:
                st.subheader("✏️ Modifier / Supprimer des produits existants")
                
                prod_a_modifier = st.selectbox("Sélectionnez le produit à éditer", st.session_state.stock["Produit"].tolist())
                idx_mod = st.session_state.stock[st.session_state.stock["Produit"] == prod_a_modifier].index[0]
                
                qte_actuelle = int(st.session_state.stock.at[idx_mod, "Quantité"])
                prix_actuel = float(st.session_state.stock.at[idx_mod, "Prix Unitaire (€)"])

                col_mod1, col_mod2 = st.columns(2)
                with col_mod1:
                    nouvelle_qte = st.number_input("Nouvelle quantité", min_value=0, step=1, value=qte_actuelle)
                with col_mod2:
                    nouveau_prix = st.number_input("Nouveau prix (€)", min_value=0.0, step=0.5, value=prix_actuel)

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("💾 Mettre à jour"):
                        st.session_state.stock.at[idx_mod, "Quantité"] = nouvelle_qte
                        st.session_state.stock.at[idx_mod, "Prix Unitaire (€)"] = nouveau_prix
                        sauvegarder_donnees()  # SAUVEGARDE AUTOMATIQUE
                        st.success("Mise à jour effectuée et sauvegardée !")
                        st.rerun()
                with col_btn2:
                    if st.button("🗑️ Supprimer le produit"):
                        st.session_state.stock = st.session_state.stock.drop(idx_mod).reset_index(drop=True)
                        sauvegarder_donnees()  # SAUVEGARDE AUTOMATIQUE
                        st.success("Produit supprimé !")
                        st.rerun()
                        

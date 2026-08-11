import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# Configuration de la page
st.set_page_config(page_title="Gestion de Stock & Ventes", page_icon="📦", layout="wide")

STOCK_FILE = "data_stock.csv"
VENTES_FILE = "data_ventes.csv"

# Chargement / Sauvegarde des fichiers
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

# 🔒 ÉCRAN DE CONNEXION
if not st.session_state.authentifie:
    st.title("🔒 Connexion à l'Application")
    pwd = st.text_input("Entrez le mot de passe Admin (ou laissez vide pour Lecteur)", type="password")
    
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

else:
    # BARRE LATÉRALE
    st.sidebar.title(f"👤 Mode : {st.session_state.role}")
    if st.sidebar.button("Déconnexion"):
        st.session_state.authentifie = False
        st.session_state.role = None
        st.rerun()

    st.title("📦 Application de Stock & Ventes")

    # RESTRICTION : Seul l'Admin voit les menus de modification
    if st.session_state.role == "Admin":
        menu = st.sidebar.radio("Navigation", ["Tableau de Bord", "Saisir une Vente", "Gérer / Modifier le Stock"])
    else:
        menu = st.sidebar.radio("Navigation", ["Tableau de Bord"])

    # 1. TABLEAU DE BORD (Accessible par tous)
    if menu == "Tableau de Bord":
        st.header("📊 Stock & Ventes")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📦 Stock Actuel")
            if st.session_state.stock.empty:
                st.info("Le stock est vide.")
            else:
                st.dataframe(st.session_state.stock, use_container_width=True)

        with col2:
            st.subheader("🛒 Historique des Ventes")
            if st.session_state.ventes.empty:
                st.info("Aucune vente enregistrée.")
            else:
                st.dataframe(st.session_state.ventes, use_container_width=True)

        st.divider()
        st.subheader("📈 Évolution des Ventes (Graphique en Courbe)")
        if st.session_state.ventes.empty:
            st.warning("Le graphique apparaîtra dès la première vente.")
        else:
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

    # 2. SAISIR UNE VENTE (ADMIN SEULEMENT)
    elif menu == "Saisir une Vente":
        st.header("🛒 Enregistrer une Vente")
        if st.session_state.stock.empty:
            st.warning("Le stock est vide. Ajoutez d'abord des produits.")
        else:
            with st.form("form_vente"):
                produits = st.session_state.stock["Produit"].tolist()
                prod_choisi = st.selectbox("Produit vendu :", produits)
                quantite = st.number_input("Quantité vendue :", min_value=1, step=1, value=1)
                valider_v = st.form_submit_button("🛒 Valider la vente")

                if valider_v:
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
                        sauvegarder_donnees()
                        st.success(f"Vente enregistrée ! Total : {total:.2f} €")
                        st.rerun()

    # 3. GÉRER LE STOCK (ADMIN SEULEMENT - FORMULAIRES TOTALEMENT ÉDITABLES)
    elif menu == "Gérer / Modifier le Stock":
        st.header("⚙️ Espace Admin : Création & Modification")

        # FORMULAIRE 1 : CRÉATION D'UN PRODUIT
        st.subheader("➕ 1. Créer un nouveau produit")
        with st.form("form_ajout_produit"):
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                nom_saisi = st.text_input("Nom du Produit")
            with col_b:
                qte_saisie = st.number_input("Quantité", min_value=0, step=1, value=0)
            with col_c:
                prix_saisi = st.number_input("Prix Unitaire (€)", min_value=0.0, step=0.5, value=0.0)
            
            bouton_ajouter = st.form_submit_button("➕ Ajouter au Stock")

            if bouton_ajouter:
                if nom_saisi.strip() == "":
                    st.error("Veuillez saisir un nom de produit.")
                elif nom_saisi in st.session_state.stock["Produit"].values:
                    st.error("Ce produit existe déjà.")
                else:
                    nouveau_produit = pd.DataFrame([{"Produit": nom_saisi, "Quantité": qte_saisie, "Prix Unitaire (€)": prix_saisi}])
                    st.session_state.stock = pd.concat([st.session_state.stock, nouveau_produit], ignore_index=True)
                    sauvegarder_donnees()
                    st.success(f"Produit '{nom_saisi}' ajouté avec succès !")
                    st.rerun()

        st.divider()

        # FORMULAIRE 2 : MODIFICATION / SUPPRESSION D'UN PRODUIT EXISTANT
        if not st.session_state.stock.empty:
            st.subheader("✏️ 2. Modifier ou Supprimer un produit existant")
            
            prod_selectionne = st.selectbox("Choisir le produit à modifier :", st.session_state.stock["Produit"].tolist())
            idx_p = st.session_state.stock[st.session_state.stock["Produit"] == prod_selectionne].index[0]

            qte_actuelle = int(st.session_state.stock.at[idx_p, "Quantité"])
            prix_actuel = float(st.session_state.stock.at[idx_p, "Prix Unitaire (€)"])

            with st.form("form_modif_produit"):
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    nouvelle_qte = st.number_input("Nouvelle Quantité", min_value=0, step=1, value=qte_actuelle)
                with col_m2:
                    nouveau_prix = st.number_input("Nouveau Prix (€)", min_value=0.0, step=0.5, value=prix_actuel)

                btn_sauver = st.form_submit_button("💾 Enregistrer les modifications")

                if btn_sauver:
                    st.session_state.stock.at[idx_p, "Quantité"] = nouvelle_qte
                    st.session_state.stock.at[idx_p, "Prix Unitaire (€)"] = nouveau_prix
                    sauvegarder_donnees()
                    st.success("Produit mis à jour !")
                    st.rerun()

            # Bouton de suppression séparé
            if st.button("🗑️ Supprimer définitivement ce produit"):
                st.session_state.stock = st.session_state.stock.drop(idx_p).reset_index(drop=True)
                sauvegarder_donnees()
                st.success("Produit supprimé !")
                st.rerun()
                

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# Configuration de la page
st.set_page_config(page_title="Gestion de Stock & Ventes", page_icon="📦", layout="wide")

STOCK_FILE = "data_stock.csv"
VENTES_FILE = "data_ventes.csv"

# Chargement des données
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
    st.title("🔒 Connexion à l'Application")
    pwd = st.text_input("Entrez le mot de passe Admin (ou cliquez sur Lecteur)", type="password")
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
    st.sidebar.title(f"👤 Mode : {st.session_state.role}")
    if st.sidebar.button("Déconnexion"):
        st.session_state.authentifie = False
        st.session_state.role = None
        st.rerun()

    st.title("📦 Gestion de Stock & Suivi des Ventes")

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
                st.info("Aucun article en stock.")
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
            st.warning("Le graphique s'affichera dès la première vente.")
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
        st.header("🛒 Enregistrer une Vente")
        if st.session_state.stock.empty:
            st.warning("Le stock est vide.")
        else:
            produits = st.session_state.stock["Produit"].tolist()
            prod_choisi = st.selectbox("Sélectionnez le produit", produits)
            quantite = st.number_input("Quantité vendue", min_value=1, step=1)

            if st.button("Valider la vente"):
                idx = st.session_state.stock[st.session_state.stock["Produit"] == prod_choisi].index[0]
                stock_actuel = st.session_state.stock.at[idx, "Quantité"]
                prix_unitaire = st.session_state.stock.at[idx, "Prix Unitaire (€)"]

                if quantite > stock_actuel:
                    st.error(f"Stock insuffisant ! Seulement {stock_actuel} en stock.")
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

    # 3. GÉRER LE STOCK (ADMIN INTERACTIF)
    elif menu == "Gérer le Stock (Admin)":
        st.header("⚙️ Modification du Stock en Temps Réel")

        # Formulaire rapide pour ajouter un produit
        st.subheader("➕ Ajouter un nouveau produit")
        with st.form("ajout_rapide"):
            c1, c2, c3 = st.columns(3)
            with c1:
                nouveau_nom = st.text_input("Nom du produit")
            with c2:
                nouvelle_qte = st.number_input("Quantité", min_value=0, step=1, value=0)
            with c3:
                nouveau_prix = st.number_input("Prix (€)", min_value=0.0, step=0.5, value=0.0)
            
            if st.form_submit_button("Ajouter le produit"):
                if nouveau_nom.strip() != "":
                    nouvel_article = pd.DataFrame([{"Produit": nouveau_nom, "Quantité": nouvelle_qte, "Prix Unitaire (€)": nouveau_prix}])
                    st.session_state.stock = pd.concat([st.session_state.stock, nouvel_article], ignore_index=True)
                    sauvegarder_donnees()
                    st.success(f"Produit '{nouveau_nom}' ajouté !")
                    st.rerun()
                else:
                    st.error("Mettez un nom de produit.")

        st.divider()

        # Édition directe du tableau
        st.subheader("✏️ Modifier directement dans le tableau")
        st.info("Astuce : Clique directement sur les cases du tableau ci-dessous pour changer la quantité ou le prix, puis clique sur le bouton de sauvegarde.")

        df_edite = st.data_editor(
            st.session_state.stock,
            num_rows="dynamic",
            use_container_width=True,
            key="editeur_stock"
        )

        if st.button("💾 Sauvegarder les modifications du tableau"):
            st.session_state.stock = df_edite
            sauvegarder_donnees()
            st.success("Modifications enregistrées avec succès !")
            st.rerun()
            

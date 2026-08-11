import streamlit as st
import pandas as pd
import plotly.express as px

# Configuration de la page
st.set_page_config(page_title="Gestion de Stock & Ventes", page_icon="📦", layout="wide")

# Initialisation des données dans la session
if "stock" not in st.session_state:
    st.session_state.stock = pd.DataFrame([
        {"Produit": "Article A", "Quantité": 50, "Prix Unitaire (€)": 15.0},
        {"Produit": "Article B", "Quantité": 20, "Prix Unitaire (€)": 25.0},
    ])

if "ventes" not in st.session_state:
    st.session_state.ventes = pd.DataFrame(columns=["Produit", "Quantité Vendue", "Total (€)"])

# Authentification simple
if "authentifie" not in st.session_state:
    st.session_state.authentifie = False
    st.session_state.role = None

def connexion():
    st.title("🔒 Connexion à l'Application")
    pwd = st.text_input("Entrez le mot de passe", type="password")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Connexion Admin"):
            if pwd == "admin99":
                st.session_state.authentifie = True
                st.session_state.role = "Admin"
                st.rerun()
            else:
                st.error("Mot de passe Admin incorrect.")
    with col2:
        if st.button("Connexion Lecteur"):
            if pwd == "1234":
                st.session_state.authentifie = True
                st.session_state.role = "Lecteur"
                st.rerun()
            else:
                st.error("Mot de passe Lecteur incorrect.")

if not st.session_state.authentifie:
    connexion()
else:
    st.sidebar.title(f"👤 Mode : {st.session_state.role}")
    if st.sidebar.button("Déconnexion"):
        st.session_state.authentifie = False
        st.session_state.role = None
        st.rerun()

    st.title("📦 Application de Gestion de Stock & Ventes")

    menu = st.sidebar.radio("Navigation", ["Aperçu & Graphiques", "Saisir une Vente", "Gérer le Stock (Admin)"])

    if menu == "Aperçu & Graphiques":
        st.header("📊 Tableau de Bord")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Stock Actuel")
            st.dataframe(st.session_state.stock, use_container_width=True)
            if not st.session_state.stock.empty:
                fig_stock = px.bar(st.session_state.stock, x="Produit", y="Quantité", title="Quantités en Stock", color="Produit")
                st.plotly_chart(fig_stock, use_container_width=True)

        with col2:
            st.subheader("Historique des Ventes")
            st.dataframe(st.session_state.ventes, use_container_width=True)
            if not st.session_state.ventes.empty:
                fig_ventes = px.pie(st.session_state.ventes, names="Produit", values="Total (€)", title="Répartition du Chiffre d'Affaires")
                st.plotly_chart(fig_ventes, use_container_width=True)

    elif menu == "Saisir une Vente":
        st.header("🛒 Enregistrer une Vente")
        if st.session_state.stock.empty:
            st.warning("Aucun produit disponible en stock.")
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
                    nouvelle_vente = pd.DataFrame([{"Produit": prod_choisi, "Quantité Vendue": quantite, "Total (€)": total}])
                    st.session_state.ventes = pd.concat([st.session_state.ventes, nouvelle_vente], ignore_index=True)
                    st.success(f"Vente enregistrée ! Total : {total:.2f} €")
                    st.rerun()

    elif menu == "Gérer le Stock (Admin)":
        if st.session_state.role != "Admin":
            st.error("Seul un Administrateur peut modifier le stock.")
        else:
            st.header("🛠️ Ajouter un Produit")
            nom_prod = st.text_input("Nom du produit")
            qte_prod = st.number_input("Quantité initiale", min_value=0, step=1)
            prix_prod = st.number_input("Prix unitaire (€)", min_value=0.0, step=0.5)

            if st.button("Ajouter au stock"):
                if nom_prod.strip() == "":
                    st.error("Le nom du produit ne peut pas être vide.")
                else:
                    nouveau_prod = pd.DataFrame([{"Produit": nom_prod, "Quantité": qte_prod, "Prix Unitaire (€)": prix_prod}])
                    st.session_state.stock = pd.concat([st.session_state.stock, nouveau_prod], ignore_index=True)
                    st.success(f"Produit '{nom_prod}' ajouté avec succès !")
                    st.rerun()
                  

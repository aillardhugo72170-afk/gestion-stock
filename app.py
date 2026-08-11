import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# 1. Configuration de la page
st.set_page_config(
    page_title="Gestion de Stock & Ventes", 
    page_icon="📦", 
    layout="wide"
)

# Design CSS Moderne & Pro
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        border-radius: 8px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: bold;
        color: #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)

STOCK_FILE = "data_stock.csv"
VENTES_FILE = "data_ventes.csv"

# 2. Chargement & Sauvegarde Permanente des Fichiers
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

# 🔒 3. ÉCRAN DE CONNEXION
if not st.session_state.authentifie:
    st.title("🔒 App de Gestion de Stock")
    st.caption("Veuillez vous connecter pour accéder à votre espace.")

    with st.form("form_connexion"):
        pwd = st.text_input("Mot de passe Admin", type="password", help="Code '99' pour le mode Administrateur")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            btn_admin = st.form_submit_button("🔑 Connexion Admin", use_container_width=True)
        with col_c2:
            btn_lecteur = st.form_submit_button("👁️ Connexion Lecteur", use_container_width=True)

        if btn_admin:
            if pwd == "99":
                st.session_state.authentifie = True
                st.session_state.role = "Admin"
                st.rerun()
            else:
                st.error("Code Admin incorrect.")

        if btn_lecteur:
            st.session_state.authentifie = True
            st.session_state.role = "Lecteur"
            st.rerun()

else:
    # BARRE LATÉRALE
    st.sidebar.markdown(f"### 👤 Mode : **{st.session_state.role}**")
    if st.sidebar.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.authentifie = False
        st.session_state.role = None
        st.rerun()

    st.sidebar.divider()

    # RESTRICTION STRICTE DES MENUS SELON LE RÔLE
    if st.session_state.role == "Admin":
        menu = st.sidebar.radio("Navigation", ["📊 Tableau de Bord", "🛒 Saisir une Vente", "⚙️ Gérer le Stock"])
    else:
        menu = st.sidebar.radio("Navigation", ["📊 Tableau de Bord"])
        st.sidebar.info("🔒 Vous êtes en mode Lecteur. La modification des données est réservée à l'Admin.")

    # ----------------------------------------------------
    # 1. TABLEAU DE BORD (Accessible à tous)
    # ----------------------------------------------------
    if menu == "📊 Tableau de Bord":
        st.title("📊 Tableau de Bord & Statistiques")

        # Métriques clés en haut
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            total_articles = int(st.session_state.stock["Quantité"].sum()) if not st.session_state.stock.empty else 0
            st.metric("Total Articles en Stock", total_articles)
        with col_m2:
            nb_ventes = len(st.session_state.ventes) if not st.session_state.ventes.empty else 0
            st.metric("Nombre de Ventes", nb_ventes)
        with col_m3:
            ca_total = st.session_state.ventes["Total (€)"].sum() if not st.session_state.ventes.empty else 0.0
            st.metric("Chiffre d'Affaires", f"{ca_total:.2f} €")

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📦 Stock en Temps Réel")
            if st.session_state.stock.empty:
                st.info("Le stock est actuellement vide.")
            else:
                st.dataframe(st.session_state.stock, use_container_width=True)

        with col2:
            st.subheader("🛒 Historique des Ventes")
            if st.session_state.ventes.empty:
                st.info("Aucune vente enregistrée.")
            else:
                st.dataframe(st.session_state.ventes, use_container_width=True)

        st.divider()
        st.subheader("📈 Évolution du Chiffre d'Affaires")
        if st.session_state.ventes.empty:
            st.warning("Le graphique en courbe s'affichera dès la première vente.")
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

    # ----------------------------------------------------
    # 2. SAISIR UNE VENTE (Admin Uniquement)
    # ----------------------------------------------------
    elif menu == "🛒 Saisir une Vente":
        st.title("🛒 Saisie d'une Nouvelle Vente")
        
        if st.session_state.stock.empty:
            st.warning("Le stock est vide. Veuillez ajouter des produits dans l'espace Administration.")
        else:
            with st.form("form_saisie_vente"):
                produits = st.session_state.stock["Produit"].tolist()
                prod_choisi = st.selectbox("Sélectionner le Produit :", produits)
                quantite = st.number_input("Quantité Vendue :", min_value=1, step=1, value=1)
                
                btn_valider_vente = st.form_submit_button("🛒 Valider la Vente", use_container_width=True)

                if btn_valider_vente:
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
                        st.success(f"Vente validée avec succès ! Total : {total:.2f} €")
                        st.rerun()

    # ----------------------------------------------------
    # 3. GÉRER LE STOCK (Admin Uniquement)
    # ----------------------------------------------------
    elif menu == "⚙️ Gérer le Stock":
        st.title("⚙️ Administration du Stock")

        # 1. CRÉATION
        st.subheader("➕ 1. Créer un nouveau produit")
        with st.form("form_creer_produit"):
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                nom_saisi = st.text_input("Nom du Produit")
            with col_b:
                qte_saisie = st.number_input("Quantité Initiale", min_value=0, step=1, value=0)
            with col_c:
                prix_saisi = st.number_input("Prix Unitaire (€)", min_value=0.0, step=0.5, value=0.0)
            
            btn_creer = st.form_submit_button("➕ Ajouter au Stock", use_container_width=True)

            if btn_creer:
                if nom_saisi.strip() == "":
                    st.error("Veuillez renseigner un nom de produit.")
                elif nom_saisi in st.session_state.stock["Produit"].values:
                    st.error("Ce produit existe déjà dans le stock.")
                else:
                    nouveau_produit = pd.DataFrame([{"Produit": nom_saisi, "Quantité": qte_saisie, "Prix Unitaire (€)": prix_saisi}])
                    st.session_state.stock = pd.concat([st.session_state.stock, nouveau_produit], ignore_index=True)
                    sauvegarder_donnees()
                    st.success(f"Produit '{nom_saisi}' ajouté avec succès !")
                    st.rerun()

        st.divider()

        # 2. MODIFICATION & SUPPRESSION
        if not st.session_state.stock.empty:
            st.subheader("✏️ 2. Modifier ou Supprimer un produit existant")
            
            prod_selectionne = st.selectbox("Choisir le produit à modifier :", st.session_state.stock["Produit"].tolist())
            idx_p = st.session_state.stock[st.session_state.stock["Produit"] == prod_selectionne].index[0]

            qte_actuelle = int(st.session_state.stock.at[idx_p, "Quantité"])
            prix_actuel = float(st.session_state.stock.at[idx_p, "Prix Unitaire (€)"])

            with st.form("form_modifier_produit"):
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    nouvelle_qte = st.number_input("Changer la Quantité", min_value=0, step=1, value=qte_actuelle)
                with col_m2:
                    nouveau_prix = st.number_input("Changer le Prix (€)", min_value=0.0, step=0.5, value=prix_actuel)

                btn_sauver_modif = st.form_submit_button("💾 Sauvegarder les modifications", use_container_width=True)

                if btn_sauver_modif:
                    st.session_state.stock.at[idx_p, "Quantité"] = nouvelle_qte
                    st.session_state.stock.at[idx_p, "Prix Unitaire (€)"] = nouveau_prix
                    sauvegarder_donnees()
                    st.success("Modifications enregistrées !")
                    st.rerun()

            st.write("")
            if st.button("🗑️ Supprimer définitivement ce produit", type="secondary"):
                st.session_state.stock = st.session_state.stock.drop(idx_p).reset_index(drop=True)
                sauvegarder_donnees()
                st.success("Produit supprimé !")
                st.rerun()

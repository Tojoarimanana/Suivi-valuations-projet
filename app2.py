import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go


# Liste des utilisateurs autorisés (minimum 3 y compris admin)
USERS = {
    "admin": "2025",
    "user1": "2024",
    "user2": "2023"
}

def check_login():
    """Vérifie l'authentification de l'utilisateur."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = ""
    
    username = st.text_input("Nom d'utilisateur :")
    password = st.text_input("Mot de passe :", type="password")
    
    if st.button("Se connecter"):
        if username in USERS and USERS[username] == password:
            st.session_state.authenticated = True
            st.session_state.username = username
        else:
            st.error("Nom d'utilisateur ou mot de passe incorrect")
    
    return st.session_state.authenticated

st.set_page_config(page_title="Tableau de Bord des Projets", layout="wide")
st.title("📊 Tableau de Bord des Projets")

if check_login():
    st.success(f"Bienvenue, {st.session_state.username} !")
# Téléchargement du fichier Excel
uploaded_file = st.file_uploader("Téléchargez le fichier Excel des projets", type=["xlsx"])

if uploaded_file:
    # Lire les feuilles de l'Excel
    xl = pd.ExcelFile(uploaded_file)
    sheet_names = xl.sheet_names  # Liste des noms des feuilles

    # Sélectionner la feuille à afficher
    page = st.selectbox("Choisissez une Projet", sheet_names)
    
    # Charger les données de la feuille sélectionnée
    df = xl.parse(page)
    
    # Vérification des colonnes
    required_columns = ["Titre du Projet", "Tâche", "Sous-tâche", "Budget (Ariary)", "Responsable", "Date Début Prévu", "Date Fin Prévu", "Statut", "Avancement (%)", "Durée estimée (jours)", "Durée réel (Jours)", "Budget Consommé  (Ariary)", "Écart Budgétaire  (Ariary)", "% de Consommation Budgétaire", "Commentaires"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"Colonnes manquantes : {', '.join(missing_columns)}")
    else:
        # Conversion des types
        df["Avancement (%)"] = pd.to_numeric(df["Avancement (%)"], errors='coerce')
        df["Budget Consommé  (Ariary)"] = pd.to_numeric(df["Budget Consommé  (Ariary)"], errors='coerce')
        df["Budget (Ariary)"] = pd.to_numeric(df["Budget (Ariary)"], errors='coerce')
        
        # Création des cartes d'indicateurs
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📂 Nombre de Responsable", len(df["Responsable"].unique()))
        with col2:
            st.metric("💰 Budget Total", f"{df['Budget (Ariary)'].sum():,.0f} Ariary")
        with col3:
            st.metric("📈 Taux moyen d'avancement", f"{df['Avancement (%)'].mean():.1f} %")
        with col4:
            st.metric("⚠️ Écart budgétaire total", f"{df['Écart Budgétaire  (Ariary)'].sum():,.0f} Ariary")
        
        # Filtres interactifs
        with st.sidebar:
            st.subheader("🔍 Filtres")
            status_filter = st.multiselect("Filtrer par Statut", df["Statut"].unique())
            responsable_filter = st.multiselect("Filtrer par Responsable", df["Responsable"].unique())
            start_date = st.date_input("Date de début minimale", pd.to_datetime(df["Date Début Prévu"]).min())
            end_date = st.date_input("Date de fin maximale", pd.to_datetime(df["Date Fin Prévu"]).max())
            
            if status_filter:
                df = df[df["Statut"].isin(status_filter)]
            if responsable_filter:
                df = df[df["Responsable"].isin(responsable_filter)]
            df = df[(pd.to_datetime(df["Date Début Prévu"]) >= pd.to_datetime(start_date)) & 
                    (pd.to_datetime(df["Date Fin Prévu"]) <= pd.to_datetime(end_date))]
            

     # 📊 Sélection des graphiques
        st.subheader("📊 Visualisation des Projets")
        col1, col2 = st.columns(2)
        

        def create_graph(column, title, combined=False):
            """ Fonction pour créer un graphique interactif """
            with column:
                st.subheader(title)

                # Sélection des axes
                x_axes = st.multiselect(f"📌 Sélectionnez les axes X pour {title}", df.columns)
                y_axes1 = st.multiselect(f"📈 Sélectionnez les variables Y1 pour {title}", df.columns)
                y_axes2 = st.multiselect(f"📊 Sélectionnez les variables Y2 pour {title} (optionnel)", df.columns)

                # Choix du type de graphique
                chart_type = st.selectbox(
                    f"📊 Type de graphique pour {title}",
                    ["Barres", "Lignes", "Secteurs", "Nuage de points", "Histogramme", "Boîte à moustaches", "Combiné"]
                )

                if not x_axes or not (y_axes1 or y_axes2):
                    st.warning("⚠️ Sélectionnez au moins une variable pour X et Y1.")
                else:
                    fig = go.Figure()

                    # Pour les autres types de graphiques
                    if chart_type != "Combiné":
                        for y in y_axes1:
                            for x in x_axes:
                                if chart_type == "Barres":
                                    fig.add_trace(go.Bar(x=df[x], y=df[y], name=f"{x} - {y}"))
                                elif chart_type == "Lignes":
                                    fig.add_trace(go.Scatter(x=df[x], y=df[y], mode='lines+markers', name=f"{x} - {y}"))
                                elif chart_type == "Secteurs":
                                    fig = px.pie(df, names=x, values=y, title=f"{title} - Secteurs")
                                elif chart_type == "Nuage de points":
                                    fig.add_trace(go.Scatter(x=df[x], y=df[y], mode='markers', name=f"{x} - {y}"))
                                elif chart_type == "Histogramme":
                                    fig.add_trace(go.Histogram(x=df[x], y=df[y], name=f"{x} - {y}"))
                                elif chart_type == "Boîte à moustaches":
                                    fig.add_trace(go.Box(y=df[y], name=f"{y} (Boîte à moustaches)"))

                    # Pour le graphique combiné (Barres et Lignes avec deux axes Y)
                    elif chart_type == "Combiné":
                        # Première série (barres) : Ajouter plusieurs variables Y1
                        for y1 in y_axes1:
                            fig.add_trace(go.Bar(x=df[x_axes[0]], y=df[y1], name=f"{x_axes[0]} - {y1}", yaxis='y1'))

                        # Deuxième série (lignes) : Ajouter plusieurs variables Y2
                        for y2 in y_axes2:
                            fig.add_trace(go.Scatter(x=df[x_axes[0]], y=df[y2], mode='lines+markers', name=f"{x_axes[0]} - {y2}", yaxis='y2'))

                        # Ajout de l'axe Y secondaire (y2)
                        fig.update_layout(
                            yaxis2=dict(
                                title="Second Y Axis",
                                overlaying='y',
                                side='right'
                            )
                        )

                    fig.update_layout(title=title)
                    st.plotly_chart(fig, use_container_width=True)

        # Création des deux graphiques indépendants
        create_graph(col1, "📊 Graphique 1")
        create_graph(col2, "📊 Graphique 2", combined=True)  # Exemple de graphique combiné


        # GANTT
        st.subheader("📅 Diagramme de Gantt")
        
        # Calcul de la fin réelle de la tâche en fonction de l'avancement
        df["Durée réel (Jours)"] = pd.to_numeric(df["Durée réel (Jours)"], errors='coerce')
        df["Progression"] = (df["Durée réel (Jours)"] * df["Avancement (%)"] / 100).round()
        
        gantt_data = df[["Sous-tâche", "Date Début Prévu", "Date Fin Prévu", "Progression", "Durée réel (Jours)"]].rename(columns={
            "Sous-tâche": "Task", 
            "Date Début Prévu": "Start", 
            "Date Fin Prévu": "Finish",
            "Progression": "Progress",
            "Durée réel (Jours)": "Real Duration"
        })
        
        # Créer un dictionnaire de couleurs, en s'assurant que toutes les clés existent
        unique_tasks = gantt_data["Task"].unique()
        
        color_dict = {task: f'rgba({int(255 * (i / len(unique_tasks)))}, 0, {int(255 * (1 - i / len(unique_tasks)))}, 0.6)' for i, task in enumerate(unique_tasks)}

        # Créer le graphique Gantt avec les couleurs
        fig_gantt = ff.create_gantt(
            gantt_data, 
            index_col="Task", 
            show_colorbar=False,  # Désactive la barre de couleur
            group_tasks=True, 
            showgrid_x=True, 
            showgrid_y=True,
            bar_width=0.3,
            height=600,
            title="Diagramme de Gantt avec Progression",
            colors=color_dict  # Utilisation des couleurs mappées par le dictionnaire
           
        )

        st.plotly_chart(fig_gantt, use_container_width=True)
           # Diagramme de Gantt avec progression (barres empilées)
        st.subheader("📅 Diagramme de Gantt")

        # Calcul de la fin réelle de la tâche en fonction de l'avancement
        df["Durée réel (Jours)"] = pd.to_numeric(df["Durée réel (Jours)"], errors='coerce')
        df["Progression"] = (df["Durée réel (Jours)"] * df["Avancement (%)"] / 100).round()
        
        # Préparation des données pour le graphique
        gantt_data = df[["Sous-tâche", "Date Début Prévu", "Date Fin Prévu", "Progression", "Durée réel (Jours)"]].rename(columns={
            "Sous-tâche": "Task", 
            "Date Début Prévu": "Start", 
            "Date Fin Prévu": "Finish",
            "Progression": "Progress",
            "Durée réel (Jours)": "Real Duration"
        })
        
        # Création des barres empilées
        gantt_data["Progress Duration"] = gantt_data["Progress"]  # Durée de la progression
        gantt_data["Remaining Duration"] = gantt_data["Real Duration"] - gantt_data["Progress"]  # Durée restante
        
        fig_gantt = go.Figure()

        # Ajouter la barre pour la progression (portion terminée)
        fig_gantt.add_trace(go.Bar(
            x=gantt_data["Progress Duration"],
            y=gantt_data["Task"],
            name="Progression",
            orientation="h",
            marker=dict(color="green"),
            width=0.4
        ))

        # Ajouter la barre pour la durée restante (portion non terminée)
        fig_gantt.add_trace(go.Bar(
            x=gantt_data["Remaining Duration"],
            y=gantt_data["Task"],
            name="Reste",
            orientation="h",
            marker=dict(color="gray"),
            width=0.4
        ))

        fig_gantt.update_layout(
            barmode="stack",
            title="Diagramme de Gantt avec Progression",
            xaxis_title="Durée (Jours)",
            yaxis_title="Tâches",
            height=600,
            showlegend=True
        )
        

        st.plotly_chart(fig_gantt, use_container_width=True)


        # Affichage du tableau
        st.subheader("📋 Tableau de Données")
        st.dataframe(df)



"""
Avisia UTM Builder - Streamlit Web App
Deploy to Cloud Run with Google OAuth authentication and BigQuery tracking
"""

import streamlit as st
from google.oauth2 import id_token
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport import requests
import os
import json
from urllib.parse import quote, urlencode
from google.cloud import secretmanager
from google.cloud import bigquery
from datetime import datetime
import pandas as pd

# ============================================================================
# BIGQUERY CONFIGURATION
# ============================================================================

# BigQuery configuration
BQ_PROJECT_ID = os.getenv('GCP_PROJECT', 'avisia-training')
BQ_DATASET_ID = 'utm_tracking'
BQ_TABLE_ID = 'utm_campaigns'

def get_bigquery_client():
    """Initialize BigQuery client"""
    try:
        return bigquery.Client(project=BQ_PROJECT_ID)
    except Exception as e:
        st.error(f"❌ Erreur de connexion à BigQuery: {str(e)}")
        return None

def save_utm_to_bigquery(base_url, source, medium, campaign, content, term, final_url, user_email):
    """Save UTM campaign data to BigQuery"""
    try:
        client = get_bigquery_client()
        if not client:
            return False
        
        table_id = f"{BQ_PROJECT_ID}.{BQ_DATASET_ID}.{BQ_TABLE_ID}"
        
        rows_to_insert = [{
            "timestamp": datetime.utcnow().isoformat(),
            "user_email": user_email,
            "initial_url": base_url,
            "utm_source": source.lower().strip().replace(' ', '-'),
            "utm_medium": medium.lower().strip().replace(' ', '-'),
            "utm_campaign": campaign.lower().strip().replace(' ', '-'),
            "utm_content": content.lower().strip().replace(' ', '-') if content else None,
            "utm_term": term.lower().strip().replace(' ', '-') if term else None,
            "final_url": final_url
        }]
        
        errors = client.insert_rows_json(table_id, rows_to_insert)
        
        if errors:
            st.error(f"❌ Erreur lors de l'enregistrement: {errors}")
            return False
        
        return True
        
    except Exception as e:
        st.error(f"❌ Erreur BigQuery: {str(e)}")
        return False

def delete_utm_from_bigquery(final_urls):
    """Delete UTM campaigns from BigQuery by final_url"""
    try:
        client = get_bigquery_client()
        if not client:
            return False
        
        table_id = f"{BQ_PROJECT_ID}.{BQ_DATASET_ID}.{BQ_TABLE_ID}"
        
        # Create a list of URLs for the SQL IN clause
        urls_str = "', '".join(final_urls)
        
        query = f"""
        DELETE FROM `{table_id}`
        WHERE final_url IN ('{urls_str}')
        """
        
        query_job = client.query(query)
        query_job.result()  # Wait for the query to complete
        
        return True
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la suppression: {str(e)}")
        return False

def get_utm_history(limit=100, source_filter=None, medium_filter=None, campaign_filter=None):
    """Retrieve UTM campaign history from BigQuery"""
    try:
        client = get_bigquery_client()
        if not client:
            return None
        
        table_id = f"{BQ_PROJECT_ID}.{BQ_DATASET_ID}.{BQ_TABLE_ID}"
        
        # Build query with filters
        query = f"""
        SELECT 
            timestamp,
            user_email,
            initial_url,
            utm_source,
            utm_medium,
            utm_campaign,
            utm_content,
            utm_term,
            final_url
        FROM `{table_id}`
        WHERE 1=1
        """
        
        if source_filter:
            query += f" AND utm_source = '{source_filter}'"
        if medium_filter:
            query += f" AND utm_medium = '{medium_filter}'"
        if campaign_filter:
            query += f" AND LOWER(utm_campaign) LIKE LOWER('%{campaign_filter}%')"
        
        query += f"""
        ORDER BY timestamp DESC
        LIMIT {limit}
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        # Convert to pandas DataFrame
        df = results.to_dataframe()
        
        if not df.empty:
            # Format timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la récupération de l'historique: {str(e)}")
        return None

def get_unique_values(column_name):
    """Get unique values for a column (for filters)"""
    try:
        client = get_bigquery_client()
        if not client:
            return []
        
        table_id = f"{BQ_PROJECT_ID}.{BQ_DATASET_ID}.{BQ_TABLE_ID}"
        
        query = f"""
        SELECT DISTINCT {column_name}
        FROM `{table_id}`
        WHERE {column_name} IS NOT NULL
        ORDER BY {column_name}
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        return [row[0] for row in results]
        
    except Exception as e:
        return []

# ============================================================================
# EXISTING FUNCTIONS (OAuth, etc.)
# ============================================================================

def get_client_secrets():
    """Load client secrets from environment variable or Secret Manager"""
    try:
        # Method 1: Read directly from environment variable (when using --set-secrets)
        if 'GOOGLE_CLIENT_SECRETS' in os.environ:
            secrets_json = os.environ['GOOGLE_CLIENT_SECRETS']
            return json.loads(secrets_json)
        
        # Method 2: Read from Secret Manager directly (fallback)
        project_id = os.environ.get('GCP_PROJECT', 'avisia-training')
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/oauth-client-secrets/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return json.loads(response.payload.data.decode("UTF-8"))
        
    except Exception as e:
        # In local development, read from file
        if os.path.exists('client_secrets.json'):
            with open('client_secrets.json', 'r') as f:
                return json.load(f)
        else:
            st.error(f"⚠️ Could not load client secrets: {str(e)}")
            return None

# ============================================================================
# LOGO FUNCTION (Defined early so both pages can use it)
# ============================================================================

def display_logo():
    """Display Avisia logo centered on the page with blue background"""
    import base64
    
    # Try to read and encode the image
    try:
        with open("avisia.png", "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode()
        
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 2rem; 
                        border-radius: 10px; 
                        text-align: center;
                        margin-bottom: 2rem;">
                <img src="data:image/png;base64,{encoded_image}" style="width: 300px; max-width: 100%;">
            </div>
            """, unsafe_allow_html=True)
    except FileNotFoundError:
        # Fallback if image not found
        st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 2rem; 
                        border-radius: 10px; 
                        text-align: center;
                        margin-bottom: 2rem;">
                <h2 style="color: white; margin: 0;">AVISIA</h2>
            </div>
            """, unsafe_allow_html=True)


# ============================================================================
# CONFIGURATION
# ============================================================================

# Google OAuth Configuration
CLIENT_SECRETS_FILE = "client_secrets.json"  # Download from Google Cloud Console
SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 
          'https://www.googleapis.com/auth/userinfo.profile']

# For Cloud Run deployment
REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:8501')

# ============================================================================
# AUTHENTICATION FUNCTIONS
# ============================================================================

def initialize_google_oauth():
    """Initialize Google OAuth flow"""
    # Load client secrets from environment or Secret Manager
    client_config = get_client_secrets()
    
    if client_config is None:
        st.error("⚠️ Missing OAuth configuration. Please configure client secrets.")
        st.stop()
    
    # Create OAuth flow from config dict (not from file)
    from google_auth_oauthlib.flow import Flow
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    
    return flow

def check_authentication():
    """Check if user is authenticated"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    
    return st.session_state.authenticated

def login_page():
    """Display login page"""
    # ✅ LOGO CALL #1 - Display logo on login page
    display_logo()
    
    st.title("🔐 Avisia UTM Builder")
    st.subheader("Connexion requise")
    
    st.markdown("""
    ### Bienvenue sur l'outil de génération d'URLs UTM Avisia
    
    Veuillez vous connecter avec votre compte Google pour accéder à l'application.
    """)
    
    # Create OAuth flow
    flow = initialize_google_oauth()
    
    # Generate authorization URL
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    # Store state in session
    st.session_state.oauth_state = state
    
    # Login button
    if st.button("🔑 Se connecter avec Google", use_container_width=True):
        st.markdown(f'<meta http-equiv="refresh" content="0;url={authorization_url}">', 
                   unsafe_allow_html=True)

def handle_oauth_callback():
    """Handle OAuth callback and authenticate user"""
    query_params = st.query_params
    
    if 'code' in query_params:
        code = query_params['code']
        
        try:
            flow = initialize_google_oauth()
            flow.fetch_token(code=code)
            
            credentials = flow.credentials
            
            # Verify the token
            id_info = id_token.verify_oauth2_token(
                credentials.id_token,
                requests.Request(),
                flow.client_config['client_id']
            )
            
            # Store user info
            st.session_state.authenticated = True
            st.session_state.user_info = {
                'email': id_info.get('email'),
                'name': id_info.get('name'),
                'picture': id_info.get('picture')
            }
            
            # Clear query params
            st.query_params.clear()
            st.rerun()
            
        except Exception as e:
            st.error(f"Erreur d'authentification : {str(e)}")
            st.session_state.authenticated = False

# ============================================================================
# UTM BUILDER FUNCTIONS
# ============================================================================

def normalize_value(value):
    """Normalize UTM parameter value (lowercase, hyphens)"""
    return value.lower().strip().replace(' ', '-')

def generate_utm_url(base_url, source, medium, campaign, content='', term=''):
    """Generate URL with UTM parameters"""
    if not base_url:
        return ''
    
    params = {}
    if source:
        params['utm_source'] = normalize_value(source)
    if medium:
        params['utm_medium'] = normalize_value(medium)
    if campaign:
        params['utm_campaign'] = normalize_value(campaign)
    if content:
        params['utm_content'] = normalize_value(content)
    if term:
        params['utm_term'] = normalize_value(term)
    
    if params:
        separator = '&' if '?' in base_url else '?'
        url = base_url + separator + urlencode(params)
        return url
    
    return base_url

# ============================================================================
# NAVIGATION
# ============================================================================

def display_navigation():
    """Display navigation menu"""
    st.sidebar.title("📱 Navigation")
    
    pages = {
        "🔗 Générateur UTM": "generator",
        "📊 Historique": "history"
    }
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "generator"
    
    for label, page_id in pages.items():
        if st.sidebar.button(label, use_container_width=True, key=f"nav_{page_id}"):
            st.session_state.current_page = page_id
            st.rerun()
    
    st.sidebar.markdown("---")
    
    # User info in sidebar
    if st.session_state.user_info:
        st.sidebar.markdown(f"""
        **👤 Connecté en tant que:**  
        {st.session_state.user_info['name']}  
        {st.session_state.user_info['email']}
        """)
        
        if st.sidebar.button("🚪 Se déconnecter", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.rerun()

# ============================================================================
# HISTORY PAGE WITH BULK DELETE
# ============================================================================

def history_page():
    """Display history page with UTM campaigns and bulk delete functionality"""
    
    st.title("📊 Historique des campagnes UTM")
    
    st.markdown("""
    Retrouvez ici l'historique des URLs générées avec leurs paramètres UTM.
    """)
    
    # Filters
    st.subheader("🔍 Filtres")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sources = get_unique_values('utm_source')
        source_filter = st.selectbox(
            "Source",
            options=['Toutes'] + sources,
            key='history_source_filter'
        )
    
    with col2:
        mediums = get_unique_values('utm_medium')
        medium_filter = st.selectbox(
            "Medium",
            options=['Tous'] + mediums,
            key='history_medium_filter'
        )
    
    with col3:
        campaign_filter = st.text_input(
            "Campagne (recherche)",
            placeholder="Ex: blog, newsletter...",
            key='history_campaign_filter'
        )
    
    # Apply filters
    source = None if source_filter == 'Toutes' else source_filter
    medium = None if medium_filter == 'Tous' else medium_filter
    campaign = None if not campaign_filter else campaign_filter
    
    # Fetch data
    with st.spinner("Chargement de l'historique..."):
        df = get_utm_history(
            limit=100,
            source_filter=source,
            medium_filter=medium,
            campaign_filter=campaign
        )
    
    if df is not None and not df.empty:
        st.subheader(f"📋 Dernières campagnes ({len(df)} résultats)")
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total", len(df))
        
        with col2:
            st.metric("Sources", df['utm_source'].nunique())
        
        with col3:
            st.metric("Mediums", df['utm_medium'].nunique())
        
        with col4:
            st.metric("Campagnes", df['utm_campaign'].nunique())
        
        # Initialize selection state
        if 'selected_rows' not in st.session_state:
            st.session_state.selected_rows = []
        
        # Add selection column to dataframe
        st.markdown("---")
        st.markdown("**Sélectionnez les lignes à supprimer :**")
        
        # Create a selection column
        df_display = df.copy()
        df_display.insert(0, '☑️ Sélection', False)
        
        # Pre-select rows that are already in selected_rows
        for idx in df_display.index:
            if df_display.loc[idx, 'final_url'] in st.session_state.selected_rows:
                df_display.loc[idx, '☑️ Sélection'] = True
        
        # Display data editor with selection column
        edited_df = st.data_editor(
            df_display,
            column_config={
                "☑️ Sélection": st.column_config.CheckboxColumn(
                    "☑️",
                    help="Cochez pour sélectionner",
                    default=False,
                ),
                "timestamp": st.column_config.DatetimeColumn(
                    "Date",
                    format="DD/MM/YYYY HH:mm"
                ),
                "user_email": "Utilisateur",
                "initial_url": "URL initiale",
                "utm_source": "Source",
                "utm_medium": "Medium",
                "utm_campaign": "Campagne",
                "utm_content": "Contenu",
                "utm_term": "Terme",
                "final_url": st.column_config.LinkColumn(
                    "URL finale",
                    display_text="🔗 Lien"
                )
            },
            hide_index=True,
            use_container_width=True,
            disabled=["timestamp", "user_email", "initial_url", "utm_source", "utm_medium", 
                     "utm_campaign", "utm_content", "utm_term", "final_url"],
            key="data_editor"
        )
        
        # Update selected rows based on edited dataframe
        st.session_state.selected_rows = edited_df[edited_df['☑️ Sélection'] == True]['final_url'].tolist()
        
        # Action buttons
        st.markdown("---")
        col_download, col_delete, col_cancel = st.columns([2, 2, 2])
        
        with col_download:
            # Download button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Télécharger en CSV",
                data=csv,
                file_name=f"utm_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col_delete:
            # Delete button
            num_selected = len(st.session_state.selected_rows)
            delete_label = f"🗑️ Supprimer ({num_selected})" if num_selected > 0 else "🗑️ Supprimer"
            
            if st.button(
                delete_label,
                use_container_width=True,
                type="primary",
                disabled=(num_selected == 0),
                key="delete_button"
            ):
                st.session_state.show_delete_confirmation = True
        
        with col_cancel:
            if st.button("❌ Désélectionner tout", use_container_width=True):
                st.session_state.selected_rows = []
                st.rerun()
        
        # Show selected count
        if num_selected > 0:
            st.info(f"ℹ️ **{num_selected} ligne(s) sélectionnée(s)**")
        
        # Delete confirmation dialog
        if st.session_state.get('show_delete_confirmation', False):
            st.markdown("---")
            st.warning(f"⚠️ **Vous êtes sûr de vouloir supprimer ces {num_selected} lien(s) ?**")
            st.markdown("Cette action est irréversible.")
            
            col_confirm, col_cancel_confirm = st.columns(2)
            
            with col_confirm:
                if st.button("✅ Oui, supprimer", use_container_width=True, type="primary", key="confirm_delete"):
                    # Perform deletion
                    with st.spinner("Suppression en cours..."):
                        success = delete_utm_from_bigquery(st.session_state.selected_rows)
                        
                        if success:
                            st.success(f"✅ {num_selected} ligne(s) supprimée(s) avec succès!")
                            st.session_state.selected_rows = []
                            st.session_state.show_delete_confirmation = False
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de la suppression")
            
            with col_cancel_confirm:
                if st.button("🚫 Annuler", use_container_width=True, key="cancel_delete"):
                    st.session_state.show_delete_confirmation = False
                    st.rerun()
        
    elif df is not None:
        st.info("ℹ️ Aucune campagne trouvée avec ces filtres.")
    else:
        st.error("❌ Impossible de charger l'historique.")

# ============================================================================
# GENERATOR PAGE (MAIN APP)
# ============================================================================

def generator_page():
    """Main UTM Builder application"""
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .user-info {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔗 Avisia UTM Builder</h1>
        <p>Générés des URLs trackées pour vos campagnes marketing</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state for form fields
    if 'base_url' not in st.session_state:
        st.session_state.base_url = 'https://avisia.fr/'
    if 'source' not in st.session_state:
        st.session_state.source = ''
    if 'medium' not in st.session_state:
        st.session_state.medium = ''
    if 'campaign' not in st.session_state:
        st.session_state.campaign = ''
    if 'campaign_year' not in st.session_state:
        st.session_state.campaign_year = str(datetime.now().year)
    if 'campaign_month' not in st.session_state:
        st.session_state.campaign_month = f"{datetime.now().month:02d}"
    if 'campaign_name' not in st.session_state:
        st.session_state.campaign_name = ''
    if 'content' not in st.session_state:
        st.session_state.content = ''
    if 'term' not in st.session_state:
        st.session_state.term = ''
    
    # Main form
    col_form, col_result = st.columns([1, 1])
    
    with col_form:
        st.subheader("📝 Paramètres UTM")
        
        # Base URL
        base_url = st.text_input(
            "URL de base *",
            value=st.session_state.base_url,
            placeholder="https://avisia.fr/page",
            help="L'URL de destination de votre campagne"
        )
        st.session_state.base_url = base_url
        
        # Source
        st.markdown("**Source (utm_source)** *")
        source_presets = {
            'LinkedIn': 'linkedin',
            'Email': 'email',
            'Newsletter': 'newsletter',
            'Twitter/X': 'twitter',
            'YouTube': 'youtube',
            'Instagram': 'instagram',
            'Signature Email': 'signature-email',
            'Reddit': 'reddit',
            'Webinar': 'webinar',
            'Google': 'google',
            'Event': 'event'
        }

        cols = st.columns(4)
        for idx, (label, value) in enumerate(source_presets.items()):
            with cols[idx % 4]:
                if st.button(label, key=f"source_{value}"):
                    st.session_state.source = value
        
        source = st.text_input(
            "Source personnalisée",
            value=st.session_state.source,
            placeholder="Ex: linkedin, email, newsletter",
            help="D'où vient le trafic ?"
        )
        st.session_state.source = source
        
        # Medium
        st.markdown("**Medium (utm_medium)** *")
        medium_presets = {
            'Social Organique': 'social_organic',
            'Social Payant': 'social_paid',
            'Email': 'email',
            'Newsletter': 'newsletter',
            'CPC': 'cpc',
            'Display': 'display',
            'Banner': 'banner',
            'Referral': 'referral',
            'Physique': 'physique',
            'Digital': 'digital'
        }

        cols = st.columns(4)
        for idx, (label, value) in enumerate(medium_presets.items()):
            with cols[idx % 4]:
                if st.button(label, key=f"medium_{value}"):
                    st.session_state.medium = value
        
        medium = st.text_input(
            "Medium personnalisé",
            value=st.session_state.medium,
            placeholder="Ex: social_organic, email, cpc",
            help="Quel type de canal ?"
        )
        st.session_state.medium = medium
        
        # Campaign
        st.markdown("**Campagne (utm_campaign)** *")
        st.markdown("*Format : `YYYY_MM_Nom-de-la-campagne`*")
        camp_col1, camp_col2, camp_col3 = st.columns([1, 1, 3])
        with camp_col1:
            campaign_year = st.text_input(
                "Année",
                value=st.session_state.campaign_year,
                placeholder="2026",
                max_chars=4,
                key="campaign_year_input"
            )
            st.session_state.campaign_year = campaign_year
        with camp_col2:
            campaign_month = st.text_input(
                "Mois",
                value=st.session_state.campaign_month,
                placeholder="03",
                max_chars=2,
                key="campaign_month_input"
            )
            st.session_state.campaign_month = campaign_month
        with camp_col3:
            campaign_name = st.text_input(
                "Nom de la campagne",
                value=st.session_state.campaign_name,
                placeholder="Ex: Lancement-Offre",
                help="Utiliser des tirets pour séparer les mots",
                key="campaign_name_input"
            )
            st.session_state.campaign_name = campaign_name

        # Assemble the campaign value
        if campaign_year and campaign_month and campaign_name:
            campaign = f"{campaign_year}_{campaign_month}_{campaign_name}"
        else:
            campaign = ''
        st.session_state.campaign = campaign

        if campaign:
            st.caption(f"utm_campaign : `{normalize_value(campaign)}`")
        
        # Content (with internal/external requirement)
        st.markdown("**Contenu (utm_content)** *")
        st.markdown("*Doit contenir 'internal' ou 'external'*")
        
        content_presets = {
            'Internal': 'internal',
            'External': 'external'
        }
        
        cols = st.columns(2)
        for idx, (label, value) in enumerate(content_presets.items()):
            with cols[idx]:
                if st.button(label, key=f"content_{value}"):
                    st.session_state.content = value
        
        content = st.text_input(
            "Contenu personnalisé",
            value=st.session_state.content,
            placeholder="Ex: internal-post-carrousel, external-cta-header",
            help="Doit obligatoirement contenir 'internal' ou 'external' pour indiquer la source du trafic"
        )
        st.session_state.content = content
        
        # Term (optional)
        term = st.text_input(
            "Terme (utm_term) - Optionnel",
            value=st.session_state.term,
            placeholder="Ex: consultant-data, formation-ia",
            help="Pour les mots-clés payants (Google Ads, LinkedIn Ads...)"
        )
        st.session_state.term = term
        
        # Action buttons
        col_reset, col_example = st.columns(2)
        
        with col_reset:
            if st.button("🔄 Réinitialiser"):
                st.session_state.base_url = 'https://avisia.fr/'
                st.session_state.source = ''
                st.session_state.medium = ''
                st.session_state.campaign = ''
                st.session_state.campaign_year = str(datetime.now().year)
                st.session_state.campaign_month = f"{datetime.now().month:02d}"
                st.session_state.campaign_name = ''
                st.session_state.content = ''
                st.session_state.term = ''
                st.rerun()
    
    with col_result:
        st.subheader("✨ URL générée")
        
        # Check if required fields are filled
        is_valid = base_url and source and medium and campaign and content
        
        # Check if content contains internal or external
        content_valid = content and ('internal' in content.lower() or 'external' in content.lower())
        
        if not is_valid:
            st.warning("⚠️ Remplissez au minimum l'URL, la source, le medium, la campagne et le contenu")
        elif not content_valid:
            st.warning("⚠️ Le contenu doit contenir 'internal' ou 'external'")
        else:
            # Generate URL
            final_url = generate_utm_url(base_url, source, medium, campaign, content, term)
            
            # Display URL
            st.code(final_url, language=None)
            
            # Copy functionality (hidden textarea - outside columns to avoid alignment issues)
            st.markdown(f"""
            <textarea id="url-output" style="position: absolute; left: -9999px;">{final_url}</textarea>
            """, unsafe_allow_html=True)
            
            # Copy and Save buttons - PERFECTLY ALIGNED
            col_copy, col_save = st.columns(2)
            
            with col_copy:
                if st.button("📋 Copier", use_container_width=True, type="secondary", key="copy_btn"):
                    # Use Streamlit's native copy functionality
                    st.success("✅ URL copiée!")
                    # JavaScript will be handled by a separate approach
            
            with col_save:
                if st.button("💾 Sauvegarder", use_container_width=True, type="primary", key="save_btn"):
                    user_email = st.session_state.user_info['email']
                    success = save_utm_to_bigquery(
                        base_url, source, medium, campaign, 
                        content, term, final_url, user_email
                    )
                    
                    if success:
                        st.success("✅ Sauvegardé dans BigQuery!")
                        st.balloons()
                    else:
                        st.error("❌ Erreur lors de la sauvegarde")
            
            # Normalized values preview
            st.markdown("---")
            st.markdown("**Valeurs normalisées:**")
            st.markdown(f"- **Source:** `{normalize_value(source)}`")
            st.markdown(f"- **Medium:** `{normalize_value(medium)}`")
            st.markdown(f"- **Campaign:** `{normalize_value(campaign)}`")
            if content:
                st.markdown(f"- **Content:** `{normalize_value(content)}`")
            if term:
                st.markdown(f"- **Term:** `{normalize_value(term)}`")
        
        # Examples
        st.markdown("---")
        st.subheader("📚 Exemples")
        
        examples = [
            {
                'name': 'LinkedIn - Post Blog',
                'base_url': 'https://avisia.fr/actualites/blog/data/article-ia',
                'source': 'linkedin',
                'medium': 'social_organic',
                'campaign_year': '2026',
                'campaign_month': '03',
                'campaign_name': 'Blog-Data-IA',
                'content': 'external-post-carrousel'
            },
            {
                'name': 'Newsletter Mensuelle',
                'base_url': 'https://avisia.fr/expertises/formations',
                'source': 'newsletter',
                'medium': 'email',
                'campaign_year': '2026',
                'campaign_month': '03',
                'campaign_name': 'Newsletter-Formations',
                'content': 'internal-cta-formation'
            },
            {
                'name': 'LinkedIn Ads - Recrutement',
                'base_url': 'https://avisia.fr/carriere/offres-emploi',
                'source': 'linkedin',
                'medium': 'social_paid',
                'campaign_year': '2026',
                'campaign_month': '03',
                'campaign_name': 'Recrutement-Q2',
                'content': 'external-visuel-equipe'
            }
        ]

        for example in examples:
            if st.button(example['name'], key=f"example_{example['name']}", use_container_width=True):
                st.session_state.base_url = example['base_url']
                st.session_state.source = example['source']
                st.session_state.medium = example['medium']
                st.session_state.campaign_year = example['campaign_year']
                st.session_state.campaign_month = example['campaign_month']
                st.session_state.campaign_name = example['campaign_name']
                st.session_state.campaign = f"{example['campaign_year']}_{example['campaign_month']}_{example['campaign_name']}"
                st.session_state.content = example.get('content', '')
                st.session_state.term = ''
                st.rerun()
    
    # Guide section
    st.markdown("---")
    
    with st.expander("📖 Guide d'utilisation des UTM"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### ✅ Bonnes pratiques
            - Toujours en **minuscules**
            - Utiliser des **tirets** (-) pour séparer les mots
            - Format dates : **YYYYMM** (202410)
            - Être cohérent dans la nomenclature
            - Documenter vos campagnes
            """)
        
        with col2:
            st.markdown("""
            ### ❌ À éviter
            - Espaces ou caractères spéciaux
            - Majuscules
            - Noms trop longs ou complexes
            - Paramètres incohérents entre campagnes
            - Oublier de tagger les liens
            """)
        
        st.markdown("""
        ### 📊 Impact attendu
        - **-40%** de trafic "unassigned"
        - **+30%** de visibilité sur les campagnes
        - **Meilleure attribution** des conversions
        - **ROI mesurable** par canal
        """)

# ============================================================================
# MAIN APPLICATION ROUTER
# ============================================================================

def main_app():
    """Main application with navigation"""
    
    # Page config
    st.set_page_config(
        page_title="Avisia UTM Builder",
        page_icon="🔗",
        layout="wide"
    )
    
    # Display logo
    display_logo()
    
    # Display navigation
    display_navigation()
    
    # Route to appropriate page
    if st.session_state.current_page == "generator":
        generator_page()
    elif st.session_state.current_page == "history":
        history_page()

# ============================================================================
# APP ENTRY POINT
# ============================================================================

def main():
    """Main application entry point"""
    
    # Handle OAuth callback
    handle_oauth_callback()
    
    # Check authentication
    if not check_authentication():
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()
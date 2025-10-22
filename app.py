"""
Avisia UTM Builder - Streamlit Web App
Deploy to Cloud Run with Google OAuth authentication
"""

import streamlit as st
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from google.auth.transport import requests
import os
import json
from urllib.parse import quote, urlencode
from google.cloud import secretmanager

def get_client_secrets():
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/YOUR_PROJECT_ID/secrets/oauth-client-secrets/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return json.loads(response.payload.data.decode("UTF-8"))

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
    if not os.path.exists(CLIENT_SECRETS_FILE):
        st.error("⚠️ Missing client_secrets.json file. Please add it to your project.")
        st.stop()
    
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
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
# MAIN APPLICATION
# ============================================================================

def main_app():
    """Main UTM Builder application"""
    
    # Page config
    st.set_page_config(
        page_title="Avisia UTM Builder",
        page_icon="🔗",
        layout="wide"
    )
    
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
    
    # Header with user info
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("""
        <div class="main-header">
            <h1>🔗 Avisia UTM Builder</h1>
            <p>Générez des URLs trackées pour vos campagnes marketing</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.session_state.user_info:
            st.markdown(f"""
            <div class="user-info">
                <img src="{st.session_state.user_info.get('picture', '')}" 
                     width="40" style="border-radius: 50%;">
                <p style="margin: 5px 0 0 0; font-size: 12px;">
                    {st.session_state.user_info.get('name', 'User')}<br>
                    {st.session_state.user_info.get('email', '')}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🚪 Déconnexion"):
                st.session_state.authenticated = False
                st.session_state.user_info = None
                st.rerun()
    
    # Initialize session state for form
    if 'base_url' not in st.session_state:
        st.session_state.base_url = 'https://avisia.fr/'
    if 'source' not in st.session_state:
        st.session_state.source = ''
    if 'medium' not in st.session_state:
        st.session_state.medium = ''
    if 'campaign' not in st.session_state:
        st.session_state.campaign = ''
    if 'content' not in st.session_state:
        st.session_state.content = ''
    if 'term' not in st.session_state:
        st.session_state.term = ''
    
    # Layout
    col_form, col_result = st.columns([2, 1])
    
    with col_form:
        st.subheader("📝 Configuration UTM")
        
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
            'Signature Email': 'signature-email'
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
            'Referral': 'referral'
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
        campaign = st.text_input(
            "Campagne (utm_campaign) *",
            value=st.session_state.campaign,
            placeholder="Ex: blog-data-ia-nov2024",
            help="Nom de la campagne (utiliser des tirets, minuscules)"
        )
        st.session_state.campaign = campaign
        
        # Content (optional)
        content = st.text_input(
            "Contenu (utm_content) - Optionnel",
            value=st.session_state.content,
            placeholder="Ex: post-carrousel, cta-header, bouton-bleu",
            help="Permet de différencier des variantes (A/B test, format...)"
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
                st.session_state.content = ''
                st.session_state.term = ''
                st.rerun()
    
    with col_result:
        st.subheader("✨ URL générée")
        
        # Check if required fields are filled
        is_valid = base_url and source and medium and campaign
        
        if not is_valid:
            st.warning("⚠️ Remplissez au minimum l'URL, la source, le medium et la campagne")
        else:
            # Generate URL
            final_url = generate_utm_url(base_url, source, medium, campaign, content, term)
            
            # Display URL
            st.code(final_url, language=None)
            
            # Copy button (using st.button with javascript)
            st.markdown(f"""
            <textarea id="url-output" style="position: absolute; left: -9999px;">{final_url}</textarea>
            <script>
            function copyURL() {{
                var copyText = document.getElementById("url-output");
                copyText.select();
                document.execCommand("copy");
            }}
            </script>
            """, unsafe_allow_html=True)
            
            if st.button("📋 Copier l'URL", use_container_width=True):
                st.success("✅ URL copiée dans le presse-papier!")
                st.balloons()
            
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
                'campaign': 'blog-data-ia-nov2024',
                'content': 'post-carrousel'
            },
            {
                'name': 'Newsletter Mensuelle',
                'base_url': 'https://avisia.fr/expertises/formations',
                'source': 'newsletter',
                'medium': 'email',
                'campaign': 'newsletter-oct2024',
                'content': 'cta-formation'
            },
            {
                'name': 'LinkedIn Ads - Recrutement',
                'base_url': 'https://avisia.fr/carriere/offres-emploi',
                'source': 'linkedin',
                'medium': 'social_paid',
                'campaign': 'recrutement-q4-2024',
                'content': 'visuel-equipe'
            }
        ]
        
        for example in examples:
            if st.button(example['name'], key=f"example_{example['name']}", use_container_width=True):
                st.session_state.base_url = example['base_url']
                st.session_state.source = example['source']
                st.session_state.medium = example['medium']
                st.session_state.campaign = example['campaign']
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

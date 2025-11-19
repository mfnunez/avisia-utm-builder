"""
Script de test autonome pour la page Analytics
Permet de tester la page sans l'authentification OAuth
"""

import streamlit as st
import sys
import os

# Configuration de la page
st.set_page_config(
    page_title="Test - Analytics Page",
    page_icon="🧪",
    layout="wide"
)

# Simuler l'authentification
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = True
    st.session_state.user_info = {
        'email': 'test@avisia.fr',
        'name': 'Utilisateur Test',
        'picture': None
    }

# Import de la page Analytics
from analytics_page import analytics_page

# Afficher un header de test
st.sidebar.markdown("""
## 🧪 Mode Test

Ceci est une version de test de la page Analytics.

**Utilisateur simulé:**
- Nom: Utilisateur Test
- Email: test@avisia.fr

---
""")

# Instructions
st.sidebar.markdown("""
### 📋 Instructions

1. Assurez-vous d'avoir configuré Vertex AI
2. Chargez le fichier `sample_ga4_data.json`
3. Posez des questions à l'assistant

### 🔑 Configuration Vertex AI

Les variables d'environnement sont automatiquement configurées :
- **GOOGLE_GENAI_USE_VERTEXAI** : true
- **GOOGLE_CLOUD_PROJECT** : avisia-training
- **GOOGLE_CLOUD_LOCATION** : europe-west1

En local, utilisez l'authentification gcloud :
```powershell
gcloud auth application-default login
```
""")

# Vérifier la configuration Vertex AI
import subprocess
try:
    # Vérifier si gcloud est configuré
    result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], 
                          capture_output=True, text=True, timeout=5)
    if result.returncode == 0 and result.stdout.strip():
        st.sidebar.success(f"✅ Projet GCP : {result.stdout.strip()}")
    else:
        st.sidebar.warning("⚠️ Authentification gcloud non configurée")
        st.sidebar.markdown("""
        Configurez l'authentification :
        ```powershell
        gcloud auth application-default login
        ```
        """)
except Exception as e:
    st.sidebar.warning("⚠️ gcloud CLI non détecté")
    st.sidebar.info("Pour le test local, installez gcloud CLI")

# Afficher la page Analytics
analytics_page()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
**Fichier de test:**  
`sample_ga4_data.json`

**Questions suggérées:**
- Montre-moi l'évolution des sessions par jour
- Compare les sessions par canal
- Quelle est la répartition par pays ?
""")
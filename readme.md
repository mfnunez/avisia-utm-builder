# 🔗 Avisia UTM Builder - Streamlit App

Application web Streamlit pour générer des URLs avec paramètres UTM, avec authentification Google OAuth.

## 📋 Prérequis

1. **Compte Google Cloud Platform (GCP)**
2. **GitHub account**
3. **Projet GCP avec les APIs activées** :
   - Cloud Run API
   - Cloud Build API
   - Container Registry API

## 🚀 Étape 1 : Configuration Google OAuth

### 1.1 Créer les credentials OAuth

1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Sélectionnez votre projet (ou créez-en un nouveau)
3. Allez dans **APIs & Services > Credentials**
4. Cliquez sur **Create Credentials > OAuth client ID**
5. Choisissez **Web application**
6. Configurez :
   - **Name** : `Avisia UTM Builder`
   - **Authorized JavaScript origins** : 
     - `http://localhost:8501` (pour dev local)
     - `https://YOUR-CLOUD-RUN-URL` (à ajouter après déploiement)
   - **Authorized redirect URIs** :
     - `http://localhost:8501`
     - `https://YOUR-CLOUD-RUN-URL` (à ajouter après déploiement)

7. Cliquez sur **Create**
8. **Téléchargez le JSON** et renommez-le en `client_secrets.json`

### 1.2 Format du fichier client_secrets.json

Votre fichier doit ressembler à :

```json
{
  "web": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uris": ["http://localhost:8501"],
    "javascript_origins": ["http://localhost:8501"]
  }
}
```

## 📁 Structure du projet

```
avisia-utm-builder/
├── app.py                  # Application Streamlit principale
├── requirements.txt        # Dépendances Python
├── Dockerfile             # Configuration Docker
├── cloudbuild.yaml        # Configuration Cloud Build
├── client_secrets.json    # Credentials OAuth (NE PAS COMMIT!)
├── .gitignore            # Fichiers à ignorer
└── README.md             # Ce fichier
```

## 🔧 Étape 2 : Setup GitHub Repository

### 2.1 Créer le repository

```bash
# Créer un nouveau repo sur GitHub : avisia-utm-builder

# Cloner localement
git clone https://github.com/YOUR_USERNAME/avisia-utm-builder.git
cd avisia-utm-builder

# Copier tous les fichiers artifacts dans ce dossier
# (app.py, requirements.txt, Dockerfile, cloudbuild.yaml)
```

### 2.2 Créer .gitignore

```bash
# Créer .gitignore
cat > .gitignore << EOF
# OAuth secrets - NEVER COMMIT!
client_secrets.json
*.json

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv

# Streamlit
.streamlit/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
EOF
```

### 2.3 Commit et push

```bash
git add .
git commit -m "Initial commit - Avisia UTM Builder"
git push origin main
```

## ☁️ Étape 3 : Déploiement sur Cloud Run

### 3.1 Installation et configuration gcloud CLI

```bash
# Installer gcloud CLI
# macOS
brew install --cask google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash

# Windows: Télécharger depuis https://cloud.google.com/sdk/docs/install

# Initialiser
gcloud init

# Sélectionner votre projet
gcloud config set project YOUR_PROJECT_ID

# Authentification
gcloud auth login
```

### 3.2 Activer les APIs nécessaires

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 3.3 Créer un Secret pour client_secrets.json

**Option 1 : Via Secret Manager (Recommandé)**

```bash
# Créer le secret
gcloud secrets create oauth-client-secrets \
  --data-file=client_secrets.json

# Donner l'accès au service Cloud Run
gcloud secrets add-iam-policy-binding oauth-client-secrets \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

Puis modifier `app.py` pour lire depuis Secret Manager :

```python
from google.cloud import secretmanager

def get_client_secrets():
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/YOUR_PROJECT_ID/secrets/oauth-client-secrets/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return json.loads(response.payload.data.decode("UTF-8"))
```

**Option 2 : Build-time secret (Plus simple pour commencer)**

Inclure le fichier dans le build (temporaire, pour test uniquement) :

```bash
# Copier client_secrets.json dans votre repo
cp client_secrets.json ./client_secrets.json

# Temporairement, retirer client_secrets.json du .gitignore pour le build
# ATTENTION : NE PAS PUSH SUR GITHUB PUBLIC!
```

### 3.4 Déployer avec Cloud Build

```bash
# Se placer dans le dossier du projet
cd avisia-utm-builder

# Lancer le build et déploiement
gcloud builds submit --config cloudbuild.yaml

# Ou déployer directement (plus simple)
gcloud run deploy avisia-utm-builder \
  --source . \
  --region=europe-west1 \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars="REDIRECT_URI=https://avisia-utm-builder-XXXXX-ew.a.run.app"
```

### 3.5 Obtenir l'URL de déploiement

```bash
# Afficher l'URL de votre service
gcloud run services describe avisia-utm-builder \
  --region=europe-west1 \
  --format="value(status.url)"

# Exemple de résultat :
# https://avisia-utm-builder-abc123-ew.a.run.app
```

## 🔐 Étape 4 : Finaliser OAuth

### 4.1 Ajouter l'URL Cloud Run aux credentials OAuth

1. Retournez sur [Google Cloud Console > Credentials](https://console.cloud.google.com/apis/credentials)
2. Cliquez sur votre OAuth client ID
3. Ajoutez dans **Authorized redirect URIs** :
   - `https://avisia-utm-builder-XXXXX-ew.a.run.app`
4. Ajoutez dans **Authorized JavaScript origins** :
   - `https://avisia-utm-builder-XXXXX-ew.a.run.app`
5. Sauvegardez

### 4.2 Mettre à jour la variable d'environnement

```bash
gcloud run services update avisia-utm-builder \
  --region=europe-west1 \
  --set-env-vars="REDIRECT_URI=https://avisia-utm-builder-XXXXX-ew.a.run.app"
```

## ✅ Étape 5 : Test de l'application

1. Ouvrez l'URL Cloud Run dans votre navigateur
2. Cliquez sur "Se connecter avec Google"
3. Autorisez l'application
4. Vous devriez être redirigé vers l'application UTM Builder

## 🔄 Mise à jour continue avec GitHub

### Option 1 : Cloud Build Trigger (Automatique)

```bash
# Créer un trigger GitHub
gcloud builds triggers create github \
  --repo-name=avisia-utm-builder \
  --repo-owner=YOUR_GITHUB_USERNAME \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml

# Maintenant, chaque push sur main déclenche un redéploiement automatique!
```

### Option 2 : Déploiement manuel

```bash
# Après chaque modification, push sur GitHub
git add .
git commit -m "Update app"
git push

# Puis redéployer
gcloud builds submit --config cloudbuild.yaml
```

## 🧪 Test en local (avant déploiement)

```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer l'app en local
streamlit run app.py

# Ouvrir http://localhost:8501 dans votre navigateur
```

## 🛡️ Sécurité

### Restreindre l'accès par domaine email

Modifier `app.py` pour ajouter une whitelist :

```python
ALLOWED_DOMAINS = ['avisia.fr']  # Seulement les emails @avisia.fr

def handle_oauth_callback():
    # ... existing code ...
    
    email = id_info.get('email')
    email_domain = email.split('@')[1] if '@' in email else ''
    
    if email_domain not in ALLOWED_DOMAINS:
        st.error(f"❌ Accès refusé. Seuls les emails @avisia.fr sont autorisés.")
        st.session_state.authenticated = False
        st.stop()
    
    # Continue with authentication...
```

### Variables d'environnement sensibles

```bash
# Définir des secrets dans Cloud Run
gcloud run services update avisia-utm-builder \
  --region=europe-west1 \
  --update-secrets=CLIENT_SECRET=oauth-client-secrets:latest
```

## 📊 Monitoring et Logs

### Voir les logs

```bash
# Logs en temps réel
gcloud run services logs tail avisia-utm-builder --region=europe-west1

# Logs dans Cloud Console
# https://console.cloud.google.com/run
```

### Métriques

```bash
# Voir les métriques de votre service
gcloud run services describe avisia-utm-builder \
  --region=europe-west1 \
  --format="yaml(status)"
```

## 🔧 Troubleshooting

### Problème 1 : "Invalid redirect_uri"

**Solution** : Vérifiez que l'URL dans OAuth credentials correspond EXACTEMENT à votre URL Cloud Run

```bash
# Vérifier l'URL actuelle
gcloud run services describe avisia-utm-builder \
  --region=europe-west1 \
  --format="value(status.url)"

# Mettre à jour la variable d'environnement
gcloud run services update avisia-utm-builder \
  --region=europe-west1 \
  --update-env-vars="REDIRECT_URI=https://YOUR_ACTUAL_URL"
```

### Problème 2 : "client_secrets.json not found"

**Solution** : Utiliser Secret Manager ou inclure le fichier dans le build

```bash
# Vérifier que le fichier est présent
docker run --rm -it gcr.io/YOUR_PROJECT_ID/avisia-utm-builder ls -la

# Si absent, rebuilder avec le fichier
```

### Problème 3 : "Permission denied" lors du build

**Solution** : Activer les permissions pour Cloud Build

```bash
# Donner les permissions nécessaires au service account Cloud Build
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)")

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

### Problème 4 : L'app crash au démarrage

**Solution** : Vérifier les logs

```bash
# Voir les logs d'erreur
gcloud run services logs read avisia-utm-builder \
  --region=europe-west1 \
  --limit=50

# Tester localement avec Docker
docker build -t test-utm-builder .
docker run -p 8501:8501 -v $(pwd)/client_secrets.json:/app/client_secrets.json test-utm-builder
```

## 💰 Coûts estimés

Cloud Run est facturé à l'utilisation :
- **Gratuit** : 2 millions de requêtes/mois
- **Pricing après** : ~$0.40 par million de requêtes
- **Stockage** : Négligeable pour cette app

**Estimation pour Avisia** :
- ~1000 utilisations/mois = **GRATUIT**
- ~10000 utilisations/mois = **~$0.50/mois**

## 🚀 Améliorations futures

### 1. Ajouter une base de données

Pour sauvegarder l'historique des URLs générées :

```bash
# Utiliser Firestore
gcloud services enable firestore.googleapis.com
```

Modifier `app.py` :

```python
from google.cloud import firestore

db = firestore.Client()

def save_url_history(user_email, url_data):
    db.collection('utm_urls').add({
        'user': user_email,
        'url': url_data,
        'timestamp': firestore.SERVER_TIMESTAMP
    })
```

### 2. Exporter en CSV

Ajouter un bouton pour exporter l'historique :

```python
import pandas as pd

def export_history():
    # Get user's history from Firestore
    docs = db.collection('utm_urls').where('user', '==', st.session_state.user_info['email']).get()
    
    data = [doc.to_dict() for doc in docs]
    df = pd.DataFrame(data)
    
    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Télécharger l'historique (CSV)",
        data=csv,
        file_name="utm_history.csv",
        mime="text/csv"
    )
```

### 3. Intégration avec Google Analytics

Vérifier automatiquement si les URLs générées sont bien trackées :

```python
from google.analytics.data import BetaAnalyticsDataClient

def verify_utm_tracking(url):
    # Check if URL appears in GA4 data
    # Return tracking status
    pass
```

### 4. API REST

Exposer une API pour générer des URLs programmatiquement :

```python
from fastapi import FastAPI
import uvicorn

app_api = FastAPI()

@app_api.post("/generate-utm")
def generate_utm_api(base_url: str, source: str, medium: str, campaign: str):
    return {"url": generate_utm_url(base_url, source, medium, campaign)}
```

## 📚 Ressources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [GA4 UTM Parameters](https://support.google.com/analytics/answer/10917952)

## 🆘 Support

Pour toute question :
1. Vérifier les logs : `gcloud run services logs tail`
2. Consulter la [documentation Cloud Run](https://cloud.google.com/run/docs)
3. Stack Overflow avec le tag `google-cloud-run`

## 📝 Checklist de déploiement

- [ ] Créer un projet GCP
- [ ] Activer les APIs nécessaires (Cloud Run, Cloud Build, Container Registry)
- [ ] Créer les credentials OAuth 2.0
- [ ] Télécharger `client_secrets.json`
- [ ] Créer le repository GitHub
- [ ] Copier tous les fichiers artifacts
- [ ] Créer `.gitignore` (ne PAS commit client_secrets.json)
- [ ] Push sur GitHub
- [ ] Déployer sur Cloud Run
- [ ] Ajouter l'URL Cloud Run dans OAuth credentials
- [ ] Tester l'authentification
- [ ] (Optionnel) Configurer le déploiement automatique via GitHub trigger

## 🎉 Félicitations !

Votre application est maintenant déployée sur Cloud Run avec authentification Google OAuth !

**URL de votre app** : `https://avisia-utm-builder-XXXXX-ew.a.run.app`

---

**Maintainer** : Équipe Data Avisia  
**Date de création** : Octobre 2025  
**Dernière mise à jour** : Octobre 2025
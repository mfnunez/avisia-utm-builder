# 🔗 Avisia UTM Builder - Streamlit App

Application web Streamlit pour générer des URLs avec paramètres UTM, avec authentification Google OAuth.

---

## 🚀 Déploiement (commande à retenir)

```powershell
gcloud builds submit --config cloudbuild.yaml --region europe-west1 --project avisia-training --gcs-source-staging-dir=gs://avisia-training-cloudbuild-source/source
```

> **Important :** toujours lancer cette commande depuis le répertoire `avisia-utm-builder/` et ne jamais utiliser la GUI Cloud Run ni `deploy.sh` pour déployer du code.

### Pourquoi ces flags ?

| Flag | Raison |
|------|--------|
| `--region europe-west1` | L'organisation GCP interdit les ressources en `us` |
| `--gcs-source-staging-dir` | Force l'upload du code source dans un bucket européen |
| `--config cloudbuild.yaml` | Utilise le pipeline CI/CD défini dans le projet |

### Vérifier que le déploiement est actif

```powershell
gcloud run revisions list --service avisia-utm-builder --region europe-west1 --project avisia-training
```

---

## ⚠️ Points importants à ne pas oublier

### REDIRECT_URI hardcodé dans cloudbuild.yaml
L'URL Cloud Run est fixée en dur dans `cloudbuild.yaml` ligne 21 :
```
REDIRECT_URI=https://avisia-utm-builder-5nzlaom4wq-ew.a.run.app
```
Si l'URL du service Cloud Run change, mettre à jour **aussi** :
1. `cloudbuild.yaml` ligne 21
2. Google Cloud Console → APIs & Services → Credentials → Authorized redirect URIs

### Ne jamais utiliser deploy.sh
Le script `deploy.sh` est obsolète — il pousse vers `gcr.io` (Container Registry) alors que le pipeline actuel utilise Artifact Registry (`europe-west1-docker.pkg.dev`). Il va échouer avec la contrainte régionale.

### Ne jamais modifier le code via la GUI Cloud Run
Les modifications via "Edit & Deploy New Revision" dans la console Cloud Run ne modifient **pas** l'image Docker — elles ne changent que les variables d'environnement. Le code Python (`app.py`, etc.) est baked dans l'image et ne peut être mis à jour que via `gcloud builds submit`.

---

## 🏗️ Architecture CI/CD

```
Code local (app.py, etc.)
        ↓  gcloud builds submit
Bucket GCS staging [europe-west1] (gs://avisia-training-cloudbuild-source)
        ↓  Cloud Build lit le code
Cloud Build [europe-west1]
        ↓  docker build --no-cache
Artifact Registry [europe-west1] (europe-west1-docker.pkg.dev)
        ↓  gcloud run deploy
Cloud Run [europe-west1] (avisia-utm-builder-5nzlaom4wq-ew.a.run.app)
```

---

## 📋 Prérequis

1. **gcloud CLI** installé et authentifié : `gcloud auth login`
2. **Projet configuré** : `gcloud config set project avisia-training`
3. **Bucket staging créé** (une seule fois) :
   ```powershell
   gsutil mb -p avisia-training -l europe-west1 gs://avisia-training-cloudbuild-source
   ```

---

## 🔐 Configuration OAuth

### Credentials Google
- Console : **APIs & Services → Credentials → OAuth Client ID**
- Authorized redirect URIs : `https://avisia-utm-builder-5nzlaom4wq-ew.a.run.app`
- Authorized JavaScript origins : `https://avisia-utm-builder-5nzlaom4wq-ew.a.run.app`

### Secret Manager
Le fichier `client_secrets.json` est stocké dans Secret Manager sous le nom `oauth-client-secrets`.
Pour mettre à jour les secrets OAuth :
```powershell
gcloud secrets versions add oauth-client-secrets --data-file=client_secrets.json --project=avisia-training
```

---

## 📁 Structure du projet

```
avisia-utm-builder/
├── app.py                    # Application Streamlit principale
├── analytics_page.py         # Page Analytics (rapports GA4)
├── requirements.txt          # Dépendances Python (versions épinglées)
├── Dockerfile                # Configuration Docker
├── cloudbuild.yaml           # Pipeline CI/CD Cloud Build
├── utm_schema.json           # Schéma BigQuery
├── .dockerignore             # Fichiers exclus du build Docker
├── .gitignore                # Fichiers exclus du git
└── readme.md                 # Ce fichier
```

---

## 🔧 Dépendances clés et versions

| Package | Version | Raison du pin |
|---------|---------|---------------|
| `google-auth-oauthlib` | `==0.8.0` | Versions ≥1.0 activent PKCE automatiquement, incompatible avec Streamlit |
| `streamlit` | `>=1.30.0` | `st.query_params` requis |

> **Ne pas upgrader `google-auth-oauthlib`** sans tester l'authentification — les versions récentes cassent le flow OAuth avec Streamlit.

---

## 🛠️ Troubleshooting

### Erreur `'us' violates constraint 'constraints/gcp.resourceLocations'`
Toujours utiliser la commande complète avec `--region` et `--gcs-source-staging-dir`.

### Erreur `invalid_grant: Bad Request` ou `Missing code verifier`
Causes possibles :
1. `google-auth-oauthlib` upgradé au-delà de `0.8.0` → vérifier `requirements.txt`
2. Plusieurs reruns Streamlit avec le même code OAuth → `st.query_params.clear()` dans `handle_oauth_callback()` doit rester en place
3. Code déployé ne correspond pas au code local → relancer `gcloud builds submit`

### Les modifications de code ne s'affichent pas après le build
- `--no-cache` est activé dans `cloudbuild.yaml` — le build prend ~3-4 minutes
- Vérifier la révision active : `gcloud run revisions list --service avisia-utm-builder --region europe-west1`
- Ne pas modifier le code via la GUI Cloud Run (ne met pas à jour l'image Docker)

### Erreur `Quota exceeded - Read requests per minute`
Rate limit Cloud Run atteint après trop de tentatives rapides. Attendre 2 minutes et réessayer.

---

## 📊 Configuration Cloud Run actuelle

| Paramètre | Valeur |
|-----------|--------|
| Région | europe-west1 |
| Mémoire | 512Mi |
| CPU | 1 |
| Min instances | 1 |
| Max instances | 1 |
| Timeout | 300s |
| Image | europe-west1-docker.pkg.dev/avisia-training/cloud-run-source-deploy/avisia-utm-builder |

> `max-instances=1` est intentionnel : assure que la session OAuth est toujours gérée par la même instance. À revoir si plusieurs utilisateurs simultanés sont nécessaires.

---

## 🗄️ BigQuery

- **Projet** : `avisia-training`
- **Dataset** : `utm_tracking`
- **Table** : `utm_campaigns`
- **Schéma** : défini dans `utm_schema.json`

---

## 📊 Monitoring

```powershell
# Logs en temps réel
gcloud run services logs tail avisia-utm-builder --region europe-west1

# Logs récents
gcloud run services logs read avisia-utm-builder --region europe-west1 --limit 50

# Status du service
gcloud run services describe avisia-utm-builder --region europe-west1
```

---

**Maintainer** : Équipe Data Avisia
**Dernière mise à jour** : Mars 2026

# =============================================================================
#  EMSP DOCS — Script de scaffolding complet
#  Exécuter depuis le dossier parent du projet :
#    .\setup_emsp.ps1
#  Prérequis : Python 3.12+, pip, git installés et dans le PATH
# =============================================================================

$PROJECT_NAME = "emsp_docs"
$VENV_DIR     = ".venv"
$APPS         = @("core", "accounts", "bibliotheque", "inscription", "espace_etudiant", "administration")

# ─── Couleurs console ────────────────────────────────────────────────────────
function Info  ($msg) { Write-Host "  [•] $msg" -ForegroundColor Cyan    }
function Ok    ($msg) { Write-Host "  [✓] $msg" -ForegroundColor Green   }
function Warn  ($msg) { Write-Host "  [!] $msg" -ForegroundColor Yellow  }
function Title ($msg) { Write-Host "`n━━━  $msg  ━━━" -ForegroundColor Magenta }

# ─── 0. Vérifications préliminaires ─────────────────────────────────────────
Title "Vérifications"
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "  [✗] Python introuvable. Installe Python 3.12+ et relance." -ForegroundColor Red
    exit 1
}
Ok "Python détecté : $(python --version)"

# ─── 1. Création du venv & installation des dépendances ─────────────────────
Title "Environnement virtuel"
python -m venv $VENV_DIR
Ok "Venv créé dans $VENV_DIR"

$pip  = ".\$VENV_DIR\Scripts\pip.exe"
$django_admin = ".\$VENV_DIR\Scripts\django-admin.exe"
$python = ".\$VENV_DIR\Scripts\python.exe"

Info "Installation des paquets (peut prendre quelques minutes)..."
& $pip install --quiet --upgrade pip
& $pip install --quiet `
    django `
    psycopg2-binary `
    django-allauth `
    djangorestframework `
    channels `
    channels-redis `
    redis `
    weasyprint `
    reportlab `
    openpyxl `
    django-import-export `
    django-simple-history `
    django-tables2 `
    django-filter `
    django-ckeditor `
    Pillow `
    python-dotenv `
    whitenoise `
    gunicorn
Ok "Dépendances installées"

# Génère requirements.txt
& $pip freeze | Out-File -Encoding UTF8 requirements.txt
Ok "requirements.txt généré"

# ─── 2. Création du projet Django ────────────────────────────────────────────
Title "Projet Django"
if (Test-Path $PROJECT_NAME) {
    Warn "Dossier $PROJECT_NAME déjà existant — on passe la création du projet"
} else {
    & $django_admin startproject $PROJECT_NAME .
    Ok "Projet '$PROJECT_NAME' créé"
}

# ─── 3. Création des apps ────────────────────────────────────────────────────
Title "Applications Django"
foreach ($app in $APPS) {
    if (Test-Path $app) {
        Warn "App '$app' déjà existante — ignorée"
    } else {
        & $python manage.py startapp $app
        Ok "App '$app' créée"
    }
}

# ─── 4. Arborescence complète des dossiers ───────────────────────────────────
Title "Arborescence dossiers"

# Fonction utilitaire
function MkDir-Safe ($path) {
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
    }
}
function Touch ($path) {
    if (-not (Test-Path $path)) {
        New-Item -ItemType File -Path $path -Force | Out-Null
    }
}

# ── Templates (un dossier par app + layouts partagés) ──
$templateBase = "templates"
MkDir-Safe "$templateBase\base"
MkDir-Safe "$templateBase\partials"
foreach ($app in $APPS) {
    MkDir-Safe "$templateBase\$app"
}

# Fichiers de base
Touch "$templateBase\base\base.html"
Touch "$templateBase\base\base_admin.html"
Touch "$templateBase\base\base_etudiant.html"
Touch "$templateBase\partials\_navbar.html"
Touch "$templateBase\partials\_topbar.html"
Touch "$templateBase\partials\_footer.html"
Touch "$templateBase\partials\_sidebar_etudiant.html"
Touch "$templateBase\partials\_sidebar_admin.html"
Touch "$templateBase\partials\_messages.html"

# Templates core
Touch "$templateBase\core\home.html"
Touch "$templateBase\core\institution.html"
Touch "$templateBase\core\formations.html"
Touch "$templateBase\core\faq.html"

# Templates accounts
Touch "$templateBase\accounts\login.html"
Touch "$templateBase\accounts\register.html"
Touch "$templateBase\accounts\password_change.html"

# Templates bibliothèque
Touch "$templateBase\bibliotheque\liste.html"
Touch "$templateBase\bibliotheque\detail.html"
Touch "$templateBase\bibliotheque\depot.html"
Touch "$templateBase\bibliotheque\mes_documents.html"

# Templates inscription
Touch "$templateBase\inscription\landing.html"
Touch "$templateBase\inscription\etape1_choix.html"
Touch "$templateBase\inscription\etape2_formulaire.html"
Touch "$templateBase\inscription\etape3_recapitulatif.html"
Touch "$templateBase\inscription\etape4_paiement.html"
Touch "$templateBase\inscription\etape5_confirmation.html"
Touch "$templateBase\inscription\statut.html"
Touch "$templateBase\inscription\recu_pdf.html"

# Templates espace étudiant
Touch "$templateBase\espace_etudiant\dashboard.html"
Touch "$templateBase\espace_etudiant\emploi_du_temps.html"
Touch "$templateBase\espace_etudiant\notes.html"
Touch "$templateBase\espace_etudiant\presences.html"
Touch "$templateBase\espace_etudiant\documents.html"
Touch "$templateBase\espace_etudiant\profil.html"
Touch "$templateBase\espace_etudiant\notifications.html"

# Templates administration
Touch "$templateBase\administration\dashboard.html"
Touch "$templateBase\administration\etudiants_liste.html"
Touch "$templateBase\administration\etudiant_detail.html"
Touch "$templateBase\administration\inscriptions.html"
Touch "$templateBase\administration\dossier_detail.html"
Touch "$templateBase\administration\paiements.html"
Touch "$templateBase\administration\notes.html"
Touch "$templateBase\administration\notes_saisie.html"
Touch "$templateBase\administration\presences.html"
Touch "$templateBase\administration\emplois_du_temps.html"
Touch "$templateBase\administration\evenements.html"
Touch "$templateBase\administration\bibliotheque_moderation.html"
Touch "$templateBase\administration\utilisateurs.html"
Touch "$templateBase\administration\parametres.html"
Touch "$templateBase\administration\parametres_tarifs.html"
Touch "$templateBase\administration\parametres_paiements.html"

Ok "Templates créés"

# ── Static files ──
MkDir-Safe "static\css"
MkDir-Safe "static\js"
MkDir-Safe "static\img\carousel"
MkDir-Safe "static\img\icons"
MkDir-Safe "static\fonts"

Touch "static\css\main.css"
Touch "static\css\admin.css"
Touch "static\css\etudiant.css"
Touch "static\js\main.js"
Touch "static\js\admin.js"
Touch "static\js\paiement.js"
Touch "static\js\emploi_du_temps.js"
Ok "Static files créés"

# ── Media ──
MkDir-Safe "media\documents"
MkDir-Safe "media\photos_profil"
MkDir-Safe "media\photos_identite"
MkDir-Safe "media\pieces_jointes"
MkDir-Safe "media\carousel"
MkDir-Safe "media\evenements"
Ok "Dossiers media créés"

# ── Dossiers utils & services dans chaque app ──
foreach ($app in $APPS) {
    Touch "$app\urls.py"
    Touch "$app\forms.py"
    Touch "$app\utils.py"
    MkDir-Safe "$app\templatetags"
    Touch "$app\templatetags\__init__.py"
    Touch "$app\templatetags\${app}_tags.py"
    MkDir-Safe "$app\services"
    Touch "$app\services\__init__.py"
}

# Services spécifiques
Touch "inscription\services\wave.py"
Touch "inscription\services\orange_money.py"
Touch "inscription\services\pdf_recu.py"
Touch "espace_etudiant\services\pdf_releve.py"
Touch "espace_etudiant\services\export_ics.py"
Touch "administration\services\export_excel.py"
Touch "administration\services\pdf_carte_etudiant.py"
Touch "administration\services\notifications.py"
Ok "Services créés"

# ── Dossier de configuration séparé ──
MkDir-Safe "config"
Touch "config\settings_base.py"
Touch "config\settings_dev.py"
Touch "config\settings_prod.py"
Ok "Config créée"

# ── Fixtures ──
MkDir-Safe "fixtures"
Touch "fixtures\filieres.json"
Touch "fixtures\licences.json"
Touch "fixtures\semestres.json"
Touch "fixtures\annees_academiques.json"
Touch "fixtures\tarifs.json"
Ok "Fixtures créées"

# ── Tests ──
foreach ($app in $APPS) {
    MkDir-Safe "$app\tests"
    Touch "$app\tests\__init__.py"
    Touch "$app\tests\test_models.py"
    Touch "$app\tests\test_views.py"
    Touch "$app\tests\test_forms.py"
}
Ok "Tests créés"

# ─── 5. Fichier .env ─────────────────────────────────────────────────────────
Title ".env"
$envContent = @"
# ──────────────────────────────────────────────
#  EMSP DOCS — Variables d'environnement
# ──────────────────────────────────────────────

SECRET_KEY=changeme-generate-a-real-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données PostgreSQL
DB_NAME=emsp_docs
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Email (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=contact@emsp.int
EMAIL_HOST_PASSWORD=changeme

# Paiements mobile
WAVE_MERCHANT_ID=
WAVE_SECRET_KEY=
WAVE_WEBHOOK_SECRET=
ORANGE_MONEY_API_KEY=
ORANGE_MONEY_MERCHANT_CODE=
ORANGE_MONEY_WEBHOOK_SECRET=

# Médias
MEDIA_URL=/media/
MEDIA_ROOT=media/
"@
$envContent | Out-File -Encoding UTF8 ".env"
Touch ".env.example"
Copy-Item ".env" ".env.example"
Ok ".env créé"

# ─── 6. .gitignore ──────────────────────────────────────────────────────────
Title ".gitignore"
$gitignore = @"
.venv/
__pycache__/
*.pyc
*.pyo
.env
media/
staticfiles/
*.sqlite3
.DS_Store
Thumbs.db
"@
$gitignore | Out-File -Encoding UTF8 ".gitignore"
Ok ".gitignore créé"

# ─── 7. Affichage de l'arborescence finale ───────────────────────────────────
Title "Structure finale du projet"
Write-Host ""
Write-Host "  emsp_docs/" -ForegroundColor White
Write-Host "  ├── emsp_docs/          (settings, urls racine, wsgi, asgi)" -ForegroundColor Gray
Write-Host "  ├── core/               (accueil, Filiere, Licence, Semestre…)" -ForegroundColor Gray
Write-Host "  ├── accounts/           (User, rôles, auth)" -ForegroundColor Gray
Write-Host "  ├── bibliotheque/       (Document, dépôt, modération)" -ForegroundColor Gray
Write-Host "  ├── inscription/        (tunnel inscription + paiement mobile)" -ForegroundColor Gray
Write-Host "  ├── espace_etudiant/    (dashboard, notes, présences, EDT)" -ForegroundColor Gray
Write-Host "  ├── administration/     (dashboard admin complet)" -ForegroundColor Gray
Write-Host "  ├── templates/          (tous les .html organisés par app)" -ForegroundColor Gray
Write-Host "  ├── static/             (CSS, JS, images)" -ForegroundColor Gray
Write-Host "  ├── media/              (fichiers uploadés)" -ForegroundColor Gray
Write-Host "  ├── fixtures/           (données initiales JSON)" -ForegroundColor Gray
Write-Host "  ├── config/             (settings séparés dev/prod)" -ForegroundColor Gray
Write-Host "  ├── requirements.txt" -ForegroundColor Gray
Write-Host "  ├── .env" -ForegroundColor Gray
Write-Host "  └── .gitignore" -ForegroundColor Gray
Write-Host ""

# ─── 8. Prochaines étapes ────────────────────────────────────────────────────
Title "Prochaines étapes"
Write-Host @"

  1. Active le venv :
       .\.venv\Scripts\Activate.ps1

  2. Ajoute les apps dans emsp_docs/settings.py → INSTALLED_APPS :
       'core', 'accounts', 'bibliotheque', 'inscription',
       'espace_etudiant', 'administration',
       'rest_framework', 'channels', 'simple_history', ...

  3. Configure la BDD PostgreSQL dans settings.py (lire .env avec python-dotenv)

  4. Applique les migrations initiales :
       python manage.py migrate

  5. Charge les fixtures de base :
       python manage.py loaddata fixtures/filieres.json

  6. Crée le superuser :
       python manage.py createsuperuser

  7. Lance le serveur :
       python manage.py runserver

"@ -ForegroundColor Cyan

Ok "Scaffolding EMSP Docs terminé avec succès !"

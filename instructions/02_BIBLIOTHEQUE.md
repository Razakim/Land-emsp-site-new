# 02 — Module Bibliothèque · Design Prompt Complet
> Module Django : `bibliotheque`  
> Vues : `BibliothequeView`, `DocumentDetailView`, `DepotDocumentView`, `MesDocumentsView`  
> Accès : **Public** (parcourir) · **Étudiant connecté** (télécharger, déposer, commenter)

---

## STRUCTURE GÉNÉRALE DU MODULE

```
[PAGE LISTE — Bibliothèque principale]
  └── Filtres : filière / licence / semestre / type / matière
  └── Grille de documents
  └── Pagination ou infinite scroll

[PAGE DÉTAIL — Document individuel]
  └── Métadonnées complètes
  └── Prévisualisation (PDF inline ou vignette)
  └── Bouton télécharger
  └── Commentaires / discussion

[PAGE DÉPÔT — Soumettre un document]
  └── Formulaire de dépôt enrichi
  └── Upload de fichier
  └── Sélection filière / licence / semestre / matière / type

[PAGE MES DOCUMENTS — Espace personnel]
  └── Documents déposés
  └── Statut de validation
  └── Documents téléchargés / favoris
```

---

## 1. PAGE PRINCIPALE — BIBLIOTHÈQUE

### 1.1 En-tête de page

**Titre** : *"Bibliothèque académique EMSP"*  
**Sous-titre** : *"Cours, TD, corrections et sujets d'examens partagés par les étudiants, organisés par filière, licence et matière."*  
**Stats en ligne** : `[X documents]` · `[X filières]` · `[X contributeurs]` — dynamiques

### 1.2 Barre de recherche principale

**Position** : bien visible, en haut de la zone de contenu  
**Champ** : grand input de recherche full-text  
**Placeholder** : *"Chercher un cours, une matière, un examen…"*  
**Bouton** : `Rechercher`  
**Comportement** : recherche en temps réel (debounce 300ms) sur titre + description + matière + contributeur  
**Tags de recherche récente** : affichés sous le champ pour utilisateurs connectés

### 1.3 Panneau de filtres

**Position** : sidebar gauche (desktop) ou drawer/accordion (mobile)  
**Filtres disponibles** :

| Filtre | Type UI | Valeurs |
|--------|---------|---------|
| **Filière** | Select ou radio buttons | *Digitalisation des Services*, *Finance*, etc. |
| **Licence** | Radio buttons | L1, L2, L3, Master |
| **Semestre** | Boutons toggle | S1, S2, S3, S4, S5, S6 |
| **Type de document** | Checkbox multi | Cours, TD, Examen, Correction, Concours |
| **Matière** | Select dynamique (dépend de la filière) | Listes depuis BDD |
| **Année académique** | Select | 2024–2025, 2025–2026, … |
| **Trier par** | Select | Plus récents / Plus téléchargés / Mieux notés |

**Bouton** : `Réinitialiser les filtres`  
**Affichage des filtres actifs** : tags/chips supprimables au-dessus de la grille

### 1.4 Grille de documents

**Disposition** : 3 colonnes desktop / 2 colonnes tablette / 1 colonne mobile  
**Affichage par défaut** : grille (toggle possible vers liste linéaire)

#### Structure de chaque carte document :

**Haut de carte** :
- Badge type (couleur distincte) : `COURS` / `TD` / `EXAMEN` / `CORRECTION` / `CONCOURS`
- Badge semestre : `S3`
- Icône cadenas si accès réservé aux connectés

**Corps de carte** :
- Nom de la filière (couleur accent, petite typo)
- Titre du document (bold, 2 lignes max, tronqué)
- Description courte (3 lignes max, tronquée)
- Matière concernée

**Pied de carte** :
- Avatar + prénom + initiale du nom du contributeur
- Nombre de téléchargements (icône flèche bas)
- Date de dépôt formatée (`07/04/2026`)
- Bouton d'action :
  - Non connecté → `Accéder après connexion` (redirige vers login)
  - Connecté → `Télécharger` ou `Voir le document`

**Comportement hover** :
- Légère élévation (translateY)
- Bordure colorée en haut selon le type de document

### 1.5 Pagination / Infinite scroll

- Option A (pagination classique) : précédent / pages numérotées / suivant — `?page=2`
- Option B (load more) : bouton `Charger plus de documents` en bas
- Affichage du total : *"Affichage de 15 sur 47 documents"*

---

## 2. PAGE DÉTAIL — DOCUMENT

### 2.1 Breadcrumb

`Accueil › Bibliothèque › Digitalisation des Services › Cours SQL`

### 2.2 En-tête du document

**Gauche** :
- Badge type + badge semestre (même style que les cartes)
- Titre du document (grand, bold)
- Filière + matière + année académique
- Description complète

**Droite / sticky sidebar** :
- Vignette/aperçu du fichier (première page du PDF si possible)
- Bouton principal : `Télécharger` (`.pdf`, `.docx`, taille du fichier)
  - Non connecté : désactivé + message *"Inscris-toi pour télécharger"*
  - Connecté : déclenche le téléchargement + incrémente le compteur
- Bouton secondaire : `Ajouter aux favoris` (icône ♡)
- Bouton : `Signaler un problème`

### 2.3 Métadonnées

Tableau ou liste de définitions :
| Champ | Valeur |
|-------|--------|
| Type | Cours |
| Filière | Digitalisation des Services |
| Licence | L2 |
| Semestre | S3 |
| Matière | Python |
| Année académique | 2025–2026 |
| Contributeur | Abdoulrhamane I. |
| Date de dépôt | 07 avril 2026 |
| Téléchargements | 9 |
| Taille du fichier | 2.4 Mo |
| Format | PDF |
| Statut | ✅ Validé |

### 2.4 Prévisualisation

- Si PDF : iframe ou viewer intégré (PDF.js) pour feuilleter sans télécharger
- Filigrane optionnel sur l'aperçu : *"EMSP Docs — Preview"*
- Bouton `Plein écran` pour agrandir le viewer

### 2.5 Documents similaires

- *"Dans la même matière"* : carousel horizontal de 3–4 cartes
- *"Du même contributeur"* : liste compacte de 3 documents

### 2.6 Commentaires / Discussion

- Titre : *"Discussion (X commentaires)"*
- Accessible uniquement aux étudiants connectés
- Formulaire : textarea + bouton `Commenter`
- Liste de commentaires : avatar, nom, date, texte, bouton répondre
- Bouton de like par commentaire

---

## 3. PAGE DÉPÔT — SOUMETTRE UN DOCUMENT

> Accessible uniquement aux étudiants connectés

### 3.1 En-tête

**Titre** : *"Partager un document"*  
**Description** : *"Contribue à la bibliothèque en partageant tes cours, TD, examens ou corrections. Chaque dépôt est vérifié avant publication."*

### 3.2 Formulaire de dépôt (étapes progressives recommandées)

**Étape 1 — Informations sur le document**
- Titre du document *(requis)*
- Description courte *(requis, max 300 caractères)*
- Type de document *(requis)* : select → Cours / TD / Examen / Correction / Concours
- Matière *(requis)* : select dynamique

**Étape 2 — Classification académique**
- Filière *(requis)* : select (auto-rempli depuis le profil de l'étudiant)
- Licence *(requis)* : L1 / L2 / L3 / Master
- Semestre *(requis)* : S1 à S6
- Année académique *(requis)* : select de l'année en cours (pré-sélectionné)

**Étape 3 — Fichier**
- Zone de drag & drop avec icône et texte : *"Glisse ton fichier ici ou clique pour parcourir"*
- Formats acceptés : `.pdf`, `.docx`, `.pptx`, `.xlsx`
- Taille max : 10 Mo
- Barre de progression lors de l'upload
- Prévisualisation du fichier après upload (nom, taille, icône du format)

**Étape 4 — Confirmation**
- Récapitulatif de toutes les informations saisies
- Case à cocher : *"Je certifie que ce document m'appartient ou que j'ai le droit de le partager"*
- Bouton : `Soumettre pour validation`

### 3.3 Message post-soumission

- Confirmation visuelle (checkmark animé)
- Message : *"Ton document a été soumis ! Il sera vérifié par l'équipe EMSP avant d'être publié."*
- Lien : `Voir mes dépôts →`

---

## 4. PAGE MES DOCUMENTS — ESPACE PERSONNEL

> Accessible uniquement aux étudiants connectés  
> URL : `/bibliotheque/mes-documents/`

### 4.1 Onglets

| Onglet | Contenu |
|--------|---------|
| **Mes dépôts** | Documents que j'ai soumis |
| **Téléchargés** | Documents que j'ai téléchargés |
| **Favoris** | Documents marqués comme favoris |

### 4.2 Onglet "Mes dépôts"

**Chaque ligne affiche** :
- Titre du document
- Type + semestre
- Date de soumission
- **Statut** :
  - 🟡 `En attente de validation`
  - ✅ `Validé — publié`
  - ❌ `Refusé` + motif du refus (cliquable pour voir le détail)
- Bouton : `Modifier` (si en attente) ou `Voir` (si validé)
- Bouton : `Supprimer` (avec confirmation)
- Compteur de téléchargements (si validé)

### 4.3 Onglet "Téléchargés"

- Liste chronologique des documents téléchargés
- Date de téléchargement
- Bouton `Retélécharger`

### 4.4 Onglet "Favoris"

- Liste des documents mis en favoris
- Bouton `Retirer des favoris`
- Bouton `Télécharger`

---

## NOTES TECHNIQUES DJANGO

| Élément | Détail |
|---------|--------|
| Models principaux | `Document`, `Filiere`, `Licence`, `Semestre`, `Matiere`, `TypeDocument`, `Telechargement`, `Favori`, `Commentaire` |
| Recherche full-text | `django.contrib.postgres.search` (SearchVector + SearchQuery) ou `icontains` multi-champs |
| Upload fichiers | `MEDIA_ROOT` configuré + validation de type MIME côté serveur |
| Validation admin | Champ `valide: BooleanField` + workflow de modération |
| Permissions | `@login_required` pour dépôt, téléchargement, favoris, commentaires |
| Compteur téléchargements | Signal `post_save` ou vue dédiée `/document/<id>/download/` qui incrémente avant de servir le fichier |
| Cache | Filtres et stats mis en cache (15 min) pour éviter les requêtes répétées |
| Pagination | `django.core.paginator.Paginator`, 15 documents par page |

# 05 — Dashboard Administration · Design Prompt Complet
> Module Django : `administration`  
> Vues : multiples (une par sous-module)  
> Accès : **Admin / Secrétaire / Professeur** — contrôle d'accès par rôle granulaire  
> Interface : séparée de l'interface étudiante, URL préfixe `/admin-emsp/`

---

## NIVEAUX D'ACCÈS (Rôles)

| Rôle | Accès |
|------|-------|
| **Super Admin** | Tout — configuration globale, création de comptes admin |
| **Administration** | Gestion inscriptions, paiements, étudiants, planning, événements |
| **Secrétariat** | Inscriptions, paiements, dossiers étudiants |
| **Professeur** | Saisie des notes, gestion des présences de ses cours uniquement |
| **Responsable financier** | Paiements, scolarité, cars uniquement |

Chaque vue vérifie le rôle via un décorateur/mixin personnalisé : `@role_required(['admin', 'secretariat'])`

---

## STRUCTURE GÉNÉRALE DU DASHBOARD

```
[SIDEBAR NAVIGATION — fixe gauche, hiérarchique]
[TOPBAR — recherche globale, notifications, profil admin]
[ZONE PRINCIPALE — contenu du sous-module actif]

Sous-modules :
  ├── Vue d'ensemble (home)
  ├── Gestion des étudiants
  ├── Gestion des inscriptions & dossiers
  ├── Gestion des paiements & scolarité
  ├── Gestion des notes
  ├── Gestion des présences & absences
  ├── Emplois du temps & programmation
  ├── Événements & activités
  ├── Gestion des cars / transport
  ├── Bibliothèque (modération)
  ├── Utilisateurs & rôles
  └── Paramètres généraux
```

---

## 1. SIDEBAR DE NAVIGATION ADMIN

**Largeur** : 260px (collapsible → 60px icônes seules)  
**Fond** : très sombre (plus sombre que le reste de l'interface)  

**En-tête sidebar** :
- Logo EMSP + `Administration`
- Nom de l'admin connecté + rôle (ex : *"Secrétariat"*)
- Avatar / initiales

**Groupes de navigation** :

**TABLEAU DE BORD**
- 🏠 Vue d'ensemble

**ACADÉMIQUE**
- 👥 Étudiants
- 📋 Inscriptions & dossiers
- 📊 Notes
- ✅ Présences & absences
- 📅 Emplois du temps
- 🗓️ Événements & activités

**FINANCIER**
- 💰 Paiements & scolarité
- 🚌 Transport / Cars

**CONTENUS**
- 📚 Bibliothèque (modération)
- 📰 Journal / Actualités

**SYSTÈME**
- 👤 Utilisateurs & rôles
- ⚙️ Paramètres

**Badges de notification** sur les liens :
- Inscriptions : nombre de dossiers en attente
- Notes : nombre de saisies en attente
- Paiements : nombre de paiements à vérifier
- Bibliothèque : nombre de documents en attente de validation

---

## 2. TOPBAR ADMIN

**Gauche** : Fil d'Ariane de la page courante (ex : `Administration › Notes › Digitalisation S3`)  
**Centre** : Barre de recherche globale — étudiants, documents, transactions par nom/matricule/référence  
**Droite** :
- 🔔 Icône notifications (badge rouge avec nombre) → dropdown des alertes récentes
- Profil admin (nom + avatar) → menu : Mon profil / Changer de mot de passe / Déconnexion

---

## 3. VUE D'ENSEMBLE — HOME DASHBOARD

### 3.1 KPI Cards (première ligne)

**4 à 6 grandes métriques** :
| KPI | Source | Tendance |
|-----|--------|----------|
| Étudiants inscrits (total) | `Etudiant.objects.filter(statut='inscrit')` | ▲ vs mois dernier |
| Nouveaux dossiers (en attente) | `DemandeInscription.objects.filter(statut='en_attente')` | badge rouge si > 0 |
| Paiements reçus ce mois | Somme des `Paiement` du mois | montant en FCFA |
| Taux de présence global | Moyenne sur tous les étudiants | % + jauge |
| Documents en attente de validation | `Document.objects.filter(valide=False)` | badge orange |
| Événements à venir (7 jours) | `Evenement.objects.filter(date__lte=J+7)` | nombre |

### 3.2 Graphiques d'activité

**Graphique 1 — Inscriptions par mois** :
- Type : courbe ou barres
- Axe X : mois de l'année académique
- Axe Y : nombre d'inscriptions
- Filtre : par filière

**Graphique 2 — Paiements (recettes cumulées)** :
- Type : barres empilées (tranches 1/2/3)
- Axe X : mois
- Axe Y : montants en FCFA

**Graphique 3 — Présences par filière** :
- Type : barres horizontales
- Comparaison filière par filière

### 3.3 Alertes & actions urgentes

Panneau latéral ou section dédiée :
- ⚠️ X dossiers d'inscription en attente de validation
- ⚠️ X paiements signalés à vérifier
- ⚠️ X étudiants avec taux d'assiduité < 75%
- ⚠️ X documents en attente de modération
- Chaque alerte → bouton `Traiter →` vers le sous-module concerné

### 3.4 Activité récente

Timeline des dernières actions :
- *"Inscription validée — Koné A. — il y a 5 min"*
- *"Paiement reçu — Traoré B. — 150 000 FCFA — Wave — il y a 12 min"*
- *"Note saisie — SQL S3 — 28 étudiants — Prof. Diallo — il y a 1h"*

---

## 4. GESTION DES ÉTUDIANTS

### 4.1 Liste des étudiants

**Filtres** :
- Filière / Licence / Semestre / Année académique
- Statut d'inscription : Actif / Suspendu / Diplômé / Abandon
- Recherche par nom / matricule / email

**Tableau** :
| Colonne | Détail |
|---------|--------|
| Photo + Nom complet | Cliquable → fiche étudiant |
| Matricule | EMSP-2026-XXXX |
| Filière | Digitalisation des Services |
| Licence / Semestre | L2 — S3 |
| Statut | Badge coloré |
| Date d'inscription | 22/04/2026 |
| Statut paiement | ✅ À jour / ⚠️ En retard |
| Actions | 👁 Voir · ✏️ Modifier · 🚫 Suspendre |

**Bouton** : `+ Ajouter un étudiant manuellement`  
**Export** : `📥 Exporter la liste (CSV / Excel / PDF)`

### 4.2 Fiche individuelle étudiant

**Onglets** :
| Onglet | Contenu |
|--------|---------|
| **Profil** | Toutes les infos personnelles + photo + documents |
| **Scolarité** | Filière, licence, semestre, statut, historique d'inscriptions |
| **Notes** | Tableau complet de toutes les notes par semestre |
| **Présences** | Taux, calendrier, justifications |
| **Paiements** | Historique complet des paiements, montants, références |
| **Documents** | Documents déposés dans la bibliothèque |
| **Communications** | Emails/SMS envoyés à cet étudiant |

**Actions disponibles** :
- ✏️ Modifier le profil
- 💰 Enregistrer un paiement manuel
- 📄 Générer la carte étudiant (PDF)
- 📧 Envoyer un email
- 🚫 Suspendre / Réactiver l'inscription

---

## 5. GESTION DES INSCRIPTIONS & DOSSIERS

### 5.1 File d'attente des dossiers

**Onglets** :
- `En attente` (badge rouge avec nombre)
- `En cours de traitement`
- `Validés`
- `Refusés`
- `Incomplets`

**Chaque dossier affiché** :
- Nom + prénom + photo d'identité miniature
- Filière demandée + licence
- Date de soumission
- Documents fournis / manquants (icônes ✅ / ❌)
- Boutons : `Examiner le dossier` · `Valider` · `Refuser` · `Demander des compléments`

### 5.2 Vue détaillée d'un dossier

- Toutes les informations du formulaire d'inscription
- Aperçu de chaque document uploadé (viewer en ligne)
- Zone commentaire interne (notes de l'admin, non visible par l'étudiant)
- Boutons de décision :
  - `✅ Valider le dossier` → crée le compte étudiant + envoie email de confirmation
  - `❌ Refuser` → formulaire de motif + envoi d'email de refus
  - `📋 Demander un complément` → sélection des documents manquants + message

---

## 6. GESTION DES PAIEMENTS & SCOLARITÉ

### 6.1 Vue globale des paiements

**Filtres** :
- Par filière / licence / semestre / année académique
- Par statut : Payé / En retard / Partiel / Non payé
- Par moyen de paiement : Wave / Orange Money / Espèces
- Par date (plage)

**Tableau des paiements** :
| Colonne | Détail |
|---------|--------|
| Étudiant | Nom + matricule |
| Filière / Licence | — |
| Montant total dû | XXX XXX FCFA |
| Montant payé | XXX XXX FCFA |
| Reste à payer | XXX XXX FCFA |
| Statut | Badge : À jour / En retard / Partiel |
| Dernier paiement | Date + référence |
| Actions | 💰 Enregistrer / 👁 Voir historique |

**Résumé financier en haut** :
- Recettes totales de l'année : montant
- Recettes du mois : montant
- Montant encore dû (tous étudiants) : montant
- Nombre d'étudiants en retard de paiement

### 6.2 Enregistrement d'un paiement manuel

Formulaire modal ou page dédiée :
- Sélection de l'étudiant (autocomplete par nom ou matricule)
- Montant
- Moyen de paiement
- Référence de transaction (si mobile money)
- Date et heure
- Note interne
- Bouton : `Enregistrer le paiement`

### 6.3 Gestion des paiements de transport (Cars)

**Abonnement mensuel / trimestriel / annuel au service de cars**

**Liste des étudiants inscrits au service de transport** :
- Nom + matricule + ligne de car + statut de paiement
- Bouton `Renouveler` / `Retirer du service`

**Vue des lignes de cars** :
- Nom de la ligne / itinéraire
- Nombre d'étudiants abonnés
- Montant mensuel par étudiant
- Recettes totales de la ligne

---

## 7. GESTION DES NOTES

### 7.1 Navigation hiérarchique

`Filière → Licence → Semestre → Matière → Saisie des notes`

### 7.2 Vue d'ensemble des notes par promo

**Sélecteurs** : Filière + Licence + Semestre + Année académique  

**Tableau récapitulatif par matière** :
| Matière | Professeur | Notes CC saisies | Notes Exam saisies | Statut |
|---------|-----------|-----------------|-------------------|--------|
| SQL | Prof. Diallo | 28/28 ✅ | 28/28 ✅ | Complet |
| Python | Prof. Koné | 28/28 ✅ | 0/28 ❌ | En attente |
| Merise | Prof. Traoré | 25/28 ⚠️ | — | Incomplet |

### 7.3 Saisie des notes (vue professeur ou admin)

**Tableau de saisie** :
- Colonne 1 : Matricule + Nom de l'étudiant
- Colonne 2 : Note CC (input numérique, 0–20, validation en temps réel)
- Colonne 3 : Note Examen (input numérique)
- Colonne 4 : Note finale (calculée automatiquement selon pondération)
- Colonne 5 : Mention (calculée)
- Colonne 6 : Statut (Validé / Non validé)

**Fonctionnalités** :
- Import CSV : `📥 Importer les notes depuis un fichier CSV`
- Bouton `Enregistrer comme brouillon` (non visible par les étudiants)
- Bouton `Publier les notes` (rend visible aux étudiants + notification automatique)
- Historique des modifications (qui a modifié, quand, quelle valeur)

### 7.4 Modification de note

- Toute modification est tracée (audit trail)
- Motif obligatoire pour toute modification post-publication
- Notification automatique à l'étudiant concerné

---

## 8. GESTION DES PRÉSENCES & ABSENCES

### 8.1 Prise des présences (interface professeur)

**Sélection de la séance** :
- Filière + Semestre + Matière + Date + Créneau horaire

**Liste des étudiants avec actions rapides** :
- Chaque étudiant : Nom + Matricule + Photo miniature
- Bouton ou toggle pour chaque étudiant : `✅ Présent` / `❌ Absent`
- Bouton `Tout présent` pour cocher tous d'un coup
- Bouton `Enregistrer les présences`

**Saisie possible depuis mobile** (interface responsive pour les professeurs en salle)

### 8.2 Gestion des justifications d'absence

**File des justifications soumises par les étudiants** :
- Nom de l'étudiant + séance concernée + motif + pièce jointe
- Boutons : `✅ Accepter` / `❌ Refuser` + champ commentaire

### 8.3 Rapports de présences

**Rapport par filière/semestre** :
- Taux moyen par matière
- Étudiants en dessous du seuil (75%) → alerte
- Export CSV/PDF

**Rapport individuel** :
- Génération d'une attestation d'assiduité pour un étudiant

---

## 9. EMPLOIS DU TEMPS & PROGRAMMATION

### 9.1 Vue calendrier globale

- Calendrier mensuel/hebdomadaire affichant toutes les séances de toutes les filières
- Filtres : par filière / professeur / salle / type (cours/TD/examen)
- Couleurs distinctes par filière

### 9.2 Création / modification d'une séance

**Formulaire de création** (via click sur créneau vide ou bouton +) :
| Champ | Type |
|-------|------|
| Filière + Licence + Semestre | Select |
| Matière | Select (filtré selon la filière) |
| Professeur | Select + autocomplete |
| Type | Radio : Cours / TD / Examen / Autre |
| Salle / Amphi | Select (salles disponibles selon créneau) |
| Date | Date picker |
| Heure de début / fin | Time pickers |
| Récurrence | None / Hebdomadaire / Bi-hebdomadaire |
| Remarques | Textarea |

**Vérification de conflits en temps réel** :
- Si la salle est déjà occupée → alerte immédiate
- Si le professeur a déjà un cours → alerte

### 9.3 Gestion des salles

- Liste des salles avec capacité
- Vue de disponibilité d'une salle (calendrier)
- Création / modification / désactivation d'une salle

### 9.4 Publication de l'emploi du temps

- Bouton `Publier l'emploi du temps de la semaine [X]`
- Notification automatique envoyée à tous les étudiants de la filière concernée

### 9.5 Génération et export

- `📥 Générer l'emploi du temps en PDF` (par filière/semestre)
- `📥 Exporter en Excel`
- `📧 Envoyer par email à tous les étudiants de la filière`

---

## 10. ÉVÉNEMENTS & ACTIVITÉS

### 10.1 Calendrier des événements

- Calendrier global de l'école (tous types d'événements)
- Types : Examen · Concours · Conférence · Journée portes ouvertes · Fête académique · Réunion · Sortie

### 10.2 Création d'un événement

**Formulaire** :
| Champ | Type |
|-------|------|
| Titre de l'événement | Input |
| Type | Select |
| Description | Rich text editor (WYSIWYG) |
| Date de début / fin | Date + Time picker |
| Lieu | Input |
| Public cible | Multiselect : Tous / Filière(s) / Licence(s) / Administrateurs uniquement |
| Image/affiche | Upload image |
| Visible sur l'accueil | Checkbox |

### 10.3 Gestion des événements existants

- Liste tableau avec : titre, date, type, public, statut (À venir / En cours / Passé)
- Actions : ✏️ Modifier / 🗑️ Supprimer / 📧 Notifier les étudiants

---

## 11. BIBLIOTHÈQUE — MODÉRATION

### 11.1 File de validation des documents

**Onglets** : `En attente` (badge) · `Validés` · `Refusés`

**Chaque document à modérer** :
- Titre + type + filière + semestre + matière
- Contributeur (nom + matricule)
- Date de soumission
- Aperçu du fichier (bouton `Prévisualiser`)
- Boutons : `✅ Valider et publier` · `❌ Refuser` (avec motif obligatoire)

### 11.2 Gestion des documents publiés

- Recherche + filtres identiques à la bibliothèque publique
- Action supplémentaire : `Dépublier` un document déjà validé
- Stats : téléchargements, date de publication, contributeur

---

## 12. PARAMÈTRES GÉNÉRAUX

### 12.1 Configuration académique

- Gestion des filières (créer / modifier / archiver)
- Gestion des licences
- Gestion des matières par filière
- Gestion des professeurs (créer des comptes professeurs)
- Années académiques (créer la nouvelle année, clôturer l'ancienne)

### 12.2 Configuration des tarifs

- Frais de scolarité par filière + licence
- Frais d'inscription
- Tarifs transport par ligne de car
- Options de paiement en tranches (activer/désactiver, définir les dates d'échéance)

### 12.3 Configuration des paiements mobile

- Numéro marchand Wave
- Numéro marchand Orange Money
- Clés API (stockées de manière sécurisée)
- Webhooks : URL de callback, secrets HMAC

### 12.4 Configuration emails & notifications

- Templates d'emails (confirmation inscription, reçu paiement, publication notes, etc.)
- Expéditeur par défaut
- Activer/désactiver les notifications automatiques

### 12.5 Gestion des utilisateurs & rôles

- Liste de tous les comptes (étudiants + admins + professeurs)
- Création de compte admin / secrétariat / professeur
- Modification des rôles
- Réinitialisation de mot de passe
- Historique de connexion (audit)

---

## NOTES TECHNIQUES DJANGO

| Élément | Détail |
|---------|--------|
| Architecture | Application Django séparée `administration/` avec ses propres templates, URL prefix `/admin-emsp/` |
| Auth & permissions | Mixin `RoleRequiredMixin` vérifiant `request.user.profile.role` |
| Tables de données | `django-tables2` + `django-filter` pour les tableaux filtrables |
| Graphiques | `Chart.js` (frontend) avec données sérialisées via API Django Rest Framework |
| Export Excel/CSV | `openpyxl` ou `django-import-export` |
| Export PDF | `weasyprint` avec templates HTML dédiés |
| WYSIWYG (événements) | `django-ckeditor` ou `TinyMCE` |
| Audit trail | `django-simple-history` sur tous les models critiques (notes, paiements) |
| Notifications temps réel | `Django Channels` (WebSocket) pour les alertes dashboard |
| Import notes CSV | Vue dédiée avec validation ligne par ligne + rapport d'erreurs |
| Sécurité | 2FA obligatoire pour les comptes admin, logs de toutes les actions sensibles |

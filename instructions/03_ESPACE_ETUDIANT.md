# 03 — Espace Étudiant · Design Prompt Complet
> Module Django : `espace_etudiant`  
> Vues : `DashboardEtudiantView`, `EmploiDuTempsView`, `NotesView`, `PresencesView`, `ProfilView`  
> Accès : **Étudiant connecté uniquement** — `@login_required` + `role == 'etudiant'`

---

## STRUCTURE GÉNÉRALE DU MODULE

```
[SIDEBAR DE NAVIGATION — fixe à gauche]
[ZONE PRINCIPALE — contenu de la vue active]

Vues disponibles :
  ├── Tableau de bord (vue par défaut)
  ├── Emploi du temps
  ├── Notes & résultats
  ├── Présences & absences
  ├── Mes documents (bibliothèque personnelle)
  ├── Mon profil
  └── Notifications
```

---

## 1. SIDEBAR DE NAVIGATION

**Position** : fixe à gauche, hauteur 100vh  
**Largeur** : 240px desktop / icônes seules sur tablette / drawer sur mobile  

**Haut de sidebar** :
- Photo de profil de l'étudiant (avatar ou initiales si pas de photo)
- Prénom + Nom
- Filière + Licence + Semestre en cours
- Indicateur de statut : `✅ Inscrit` / `⚠️ Paiement en attente`

**Liens de navigation** :
| Icône | Lien | URL |
|-------|------|-----|
| 🏠 | Tableau de bord | `/etudiant/` |
| 📅 | Emploi du temps | `/etudiant/emploi-du-temps/` |
| 📊 | Notes & résultats | `/etudiant/notes/` |
| ✅ | Présences & absences | `/etudiant/presences/` |
| 📚 | Mes documents | `/etudiant/documents/` |
| 🔔 | Notifications | `/etudiant/notifications/` |
| 👤 | Mon profil | `/etudiant/profil/` |

**Bas de sidebar** :
- Lien : `Déconnexion`
- Version de la plateforme

---

## 2. TABLEAU DE BORD ÉTUDIANT (vue par défaut)

**Titre** : *"Bonjour, [Prénom] 👋"*  
**Sous-titre** : date du jour + résumé du semestre en cours

### 2.1 Carte de statut d'inscription

**Fond coloré selon statut** :
- Vert : *"Inscription validée pour [Année académique]"* + détails de la filière/licence
- Orange : *"Paiement de scolarité en attente"* + bouton `Payer maintenant →`
- Rouge : *"Inscription expirée ou suspendue"* + bouton `Contacter l'administration`

**Contenu** :
- Filière, Licence, Semestre actuel
- Montant payé / montant total de la scolarité
- Barre de progression de paiement (`Ex : 150 000 / 300 000 FCFA — 50%`)

### 2.2 Grille de widgets rapides (4 cartes)

**Carte 1 — Prochain cours** :
- Matière + professeur
- Heure et salle
- Compte à rebours : *"Dans 2h30"*
- Bouton : `Voir l'emploi du temps complet`

**Carte 2 — Mes notes récentes** :
- Dernière note obtenue : matière + note + mention
- Moyenne générale du semestre
- Bouton : `Voir toutes les notes`

**Carte 3 — Présences** :
- Taux de présence du semestre : jauge circulaire (`Ex : 87%`)
- Nombre d'absences justifiées / non justifiées
- Alerte si taux < 75% : `⚠️ Attention, ton taux d'assiduité est faible`
- Bouton : `Voir le détail`

**Carte 4 — Bibliothèque** :
- Nombre de documents téléchargés
- Dernier document consulté
- Bouton : `Accéder à la bibliothèque`

### 2.3 Emploi du temps de la semaine (mini-calendrier)

- Vue semaine compacte : 5 jours (lun–ven), cases des cours
- Chaque case : matière + salle + horaire
- Cours actuel ou prochain mis en évidence
- Lien : `Voir l'emploi du temps complet`

### 2.4 Fil de notifications récentes

- Liste des 3–5 dernières notifications :
  - *"Nouvelle note publiée : Mathématiques — 14/20"*
  - *"Absence enregistrée le 18/04/2026 — Algorithmique"*
  - *"Nouveau document disponible : Cours Python"*
  - *"Rappel : paiement de scolarité dû le 30/04"*
- Bouton : `Voir toutes les notifications`

---

## 3. EMPLOI DU TEMPS

### 3.1 Contrôles de navigation temporelle

- Boutons `← Semaine précédente` / `Semaine suivante →`
- Label de la semaine : *"Semaine du 21 au 25 avril 2026"*
- Bouton `Aujourd'hui` pour revenir à la semaine courante
- Toggle : `Vue semaine` / `Vue mois` / `Vue jour`

### 3.2 Grille horaire (vue semaine)

**Colonnes** : Lundi · Mardi · Mercredi · Jeudi · Vendredi (+ Samedi si nécessaire)  
**Lignes** : Créneaux de 1h de 07h00 à 20h00  

**Chaque bloc de cours affiche** :
- Matière (bold)
- Professeur
- Salle / Amphi
- Horaire (implicite par la position dans la grille)
- Couleur distinctive par matière (cohérence sur toute la semaine)

**États visuels des blocs** :
- Cours passé : opacité réduite
- Cours en cours : bordure colorée + badge `EN COURS`
- Cours à venir aujourd'hui : mise en évidence légère
- Cours annulé : barré + badge `ANNULÉ` (rouge)
- Cours déplacé : badge `MODIFIÉ` (orange)

### 3.3 Légende

- Couleurs des matières
- Types d'événements : `Cours` · `TD` · `Examen` · `Événement`

### 3.4 Événements & examens

- Bandeau dédié en haut de la grille pour les examens, concours et événements de l'école
- Badge coloré bien visible : `EXAMEN le 28/04 — SQL, Amphi A`

### 3.5 Export / Impression

- Bouton `📥 Exporter en PDF`
- Bouton `🔔 Synchroniser avec mon calendrier` (export `.ics` pour Google Calendar / Apple Calendar)

---

## 4. NOTES & RÉSULTATS

### 4.1 Sélecteur de semestre

- Onglets ou select : `S1` · `S2` · `S3` · etc.
- Vue affichée = notes du semestre sélectionné

### 4.2 Résumé du semestre sélectionné

**Bandeau de synthèse** (haut de page) :
- Moyenne générale du semestre (grand chiffre, couleur selon mention)
- Mention : `Très Bien` / `Bien` / `Assez Bien` / `Passable` / `Insuffisant`
- Rang dans la classe (si affiché par l'admin)
- Total de crédits validés / crédits attendus

### 4.3 Tableau des notes par matière

| Colonne | Description |
|---------|-------------|
| Matière | Nom complet de la matière |
| Professeur | Nom du professeur |
| Crédits | Nombre de crédits (ECTS ou équivalent) |
| Note CC | Contrôle continu (sur 20) |
| Note Examen | Note d'examen final (sur 20) |
| Note finale | Calculée (pondération définie par admin) |
| Mention | Bien / Passable / etc. |
| Statut | ✅ Validé / ❌ Non validé / ⏳ En attente |

**Couleur de la note finale** :
- ≥ 16 : vert foncé
- 14–15 : vert clair
- 12–13 : bleu
- 10–11 : orange
- < 10 : rouge

**Ligne de totaux** : moyenne pondérée + total crédits

### 4.4 Historique complet (tous semestres)

- Tableau récapitulatif par semestre avec moyenne + crédits + mention
- Bouton `Télécharger mon relevé de notes (PDF)`

---

## 5. PRÉSENCES & ABSENCES

### 5.1 Synthèse globale

**Jauges circulaires ou barres** :
- Taux global de présence du semestre (ex : `87%`)
- Nombre total de séances : `48`
- Présences : `42`
- Absences justifiées : `3`
- Absences non justifiées : `3`

**Alerte conditionnelle** :
- Si taux < 75% → bannière rouge : *"⚠️ Ton taux d'assiduité est en dessous du seuil requis (75%). Contacte l'administration."*
- Si taux entre 75% et 85% → bannière orange : *"Attention, surveille ton assiduité."*

### 5.2 Taux par matière

Tableau :
| Matière | Séances | Présent | Absent justifié | Absent non justifié | Taux |
|---------|---------|---------|-----------------|---------------------|------|
| SQL | 8 | 7 | 1 | 0 | 87.5% |
| Python | 10 | 9 | 0 | 1 | 90% |
| … | … | … | … | … | … |

Chaque ligne : barre de progression colorée selon le taux

### 5.3 Calendrier des absences

- Vue mensuelle avec jours marqués :
  - 🟢 Présent
  - 🟡 Absent justifié
  - 🔴 Absent non justifié
  - ⬜ Pas de cours

### 5.4 Justification d'absence

**Formulaire** :
- Sélection de la séance concernée (date + matière)
- Motif (textarea)
- Pièce jointe : certificat médical, convocation, etc.
- Bouton : `Soumettre la justification`
- Statut de la justification soumise : `En attente` / `Acceptée` / `Refusée`

---

## 6. MON PROFIL

### 6.1 Section identité

- Photo de profil (modifiable, avec prévisualisation)
- Nom complet, Matricule étudiant
- Filière, Licence, Semestre, Année d'entrée
- Email EMSP (non modifiable)
- Téléphone (modifiable)

### 6.2 Informations académiques (lecture seule)

- Filière, Licence, Semestre en cours
- Statut d'inscription
- Date d'inscription

### 6.3 Sécurité

- Bouton `Changer mon mot de passe`
- Bouton `Activer la double authentification` (si disponible)

### 6.4 Préférences

- Langue de l'interface (Français)
- Notifications par email : toggle activé/désactivé par type (notes, absences, événements)

---

## NOTES TECHNIQUES DJANGO

| Élément | Détail |
|---------|--------|
| Model `Etudiant` | OneToOne avec `User`, champs : `filiere`, `licence`, `semestre`, `matricule`, `photo_profil`, `statut_inscription` |
| Model `Note` | FK vers `Etudiant`, `Matiere`, `Semestre` — champs : `note_cc`, `note_exam`, `note_finale` |
| Model `Presence` | FK vers `Etudiant`, `Seance` — champs : `statut` (present/absent_justifie/absent_non_justifie) |
| Model `Seance` | FK vers `Matiere`, `Professeur`, `Salle` — champs : `date`, `heure_debut`, `heure_fin`, `type_seance` |
| Model `EmploiDuTemps` | Lié à une `Promo`/`Filiere`/`Semestre` — ensemble de `Seance` |
| Permissions | Middleware vérifiant `request.user.etudiant.statut_inscription` |
| Export PDF | `reportlab` ou `weasyprint` pour relevé de notes et emploi du temps |
| Notifications | Model `Notification` + signals Django post-save sur `Note`, `Presence`, etc. |

# 04 — Module Inscription & Paiement · Design Prompt Complet
> Module Django : `inscription`  
> Vues : `InscriptionChoixView`, `FormulaireInscriptionView`, `PaiementView`, `ConfirmationView`, `StatutInscriptionView`  
> Accès : **Public** (création de compte) · **Authentifié** (paiement & suivi)

---

## STRUCTURE GÉNÉRALE DU MODULE

```
[LANDING PAGE — Pourquoi s'inscrire à l'EMSP]
[ÉTAPE 1 — Choix du type d'inscription]
[ÉTAPE 2 — Formulaire selon le profil]
     ├── Nouvelle inscription (L1 / 1ère année)
     └── Ré-inscription (L2, L3, Master — déjà étudiant)
[ÉTAPE 3 — Récapitulatif & montant de scolarité]
[ÉTAPE 4 — Paiement de scolarité]
     ├── Wave
     ├── Orange Money
     └── MTN Money / autres
[ÉTAPE 5 — Confirmation & reçu]
[PAGE STATUT — Suivi de mon inscription]
```

---

## 1. LANDING PAGE INSCRIPTION

**Titre** : *"Rejoindre l'EMSP"*  
**Sous-titre** : *"Inscris-toi en ligne, paie ta scolarité et accède immédiatement à ton espace étudiant."*

**Mise en avant de 3 arguments** :
- ✅ Inscription 100% en ligne
- 📲 Paiement par Wave, Orange Money
- 🎓 Accès immédiat à la bibliothèque et à l'espace étudiant

**Bouton CTA** : `Commencer mon inscription →`

**Lien secondaire** : `Je suis déjà étudiant — me réinscrire →`

---

## 2. STEPPER DE PROGRESSION

**Position** : en haut de toutes les pages du tunnel d'inscription  
**Style** : barre de progression horizontale avec numéros d'étapes et labels

```
① Choix  →  ② Informations  →  ③ Récapitulatif  →  ④ Paiement  →  ⑤ Confirmation
```

- Étape actuelle : remplie + couleur principale
- Étapes complétées : icône ✓
- Étapes à venir : grisées
- Sur mobile : numéro + label de l'étape actuelle seulement (*"Étape 2 sur 5"*)

---

## 3. ÉTAPE 1 — CHOIX DU TYPE D'INSCRIPTION

**Question principale** : *"Quel est ton profil ?"*

**Deux grandes cartes sélectionnables** :

**Carte A — Nouvelle inscription** :
- Icône 🎓
- Titre : *"Je m'inscris pour la première fois à l'EMSP"*
- Description : *"Première année de licence ou entrée dans une nouvelle filière"*
- Sous-options (si applicable) : L1, Master 1ère année

**Carte B — Ré-inscription** :
- Icône 🔄
- Titre : *"Je suis déjà étudiant EMSP — je me réinscris"*
- Description : *"Poursuite de mes études au semestre ou à l'année suivante"*
- Identification automatique : saisie du matricule étudiant existant

**Comportement** : clic sur une carte → elle se surligne → bouton `Continuer` s'active

---

## 4. ÉTAPE 2 — FORMULAIRE D'INSCRIPTION

> Le formulaire est **adaptatif** : les champs affichés varient selon le profil sélectionné à l'étape 1

### 4.1 Informations personnelles (TOUS les profils)

| Champ | Type | Obligatoire |
|-------|------|-------------|
| Nom | Input texte | ✅ |
| Prénom(s) | Input texte | ✅ |
| Date de naissance | Date picker | ✅ |
| Lieu de naissance | Input texte | ✅ |
| Nationalité | Select pays | ✅ |
| Genre | Radio : Masculin / Féminin | ✅ |
| Situation familiale | Select | ✅ |
| Photo d'identité | Upload image (format portrait) | ✅ |

### 4.2 Coordonnées

| Champ | Type | Obligatoire |
|-------|------|-------------|
| Email personnel | Input email | ✅ |
| Numéro de téléphone principal | Input tél. (avec préfixe pays 🇨🇮) | ✅ |
| Numéro de téléphone secondaire | Input tél. | ❌ |
| Adresse de résidence | Textarea | ✅ |
| Quartier / Commune | Input | ✅ |
| Ville | Select | ✅ |

### 4.3 Informations académiques

| Champ | Type | Condition |
|-------|------|-----------|
| Filière souhaitée | Select (liste des filières actives) | Tous |
| Licence (niveau) | Radio : L1 / L2 / L3 / Master | Tous |
| Semestre de départ | Select : S1 / S2 | Tous |
| Année académique | Select (pré-rempli) | Tous |
| Régime d'études | Radio : Journée / Soir | Tous |
| Matricule existant | Input | Ré-inscription uniquement |

### 4.4 Diplômes & parcours antérieur (Nouvelle inscription)

| Champ | Type | Obligatoire |
|-------|------|-------------|
| Dernier diplôme obtenu | Select : BEPC / BAC / Licence / Master / Doctorat | ✅ |
| Année d'obtention | Select année | ✅ |
| Établissement d'origine | Input texte | ✅ |
| Série / Spécialité du BAC | Input (si BAC) | Conditionnel |
| Mention au BAC | Select : Passable / AB / Bien / TB | Conditionnel |
| Relevé de notes | Upload PDF/image | ✅ |
| Copie du diplôme ou attestation | Upload PDF/image | ✅ |

### 4.5 Informations sur le tuteur / parent (si < 25 ans ou L1)

| Champ | Type | Obligatoire |
|-------|------|-------------|
| Nom et prénom du tuteur | Input | ✅ |
| Lien de parenté | Select : Père / Mère / Tuteur légal / Autre | ✅ |
| Téléphone du tuteur | Input tél. | ✅ |
| Profession du tuteur | Input | ❌ |

### 4.6 Informations de santé (optionnel)

- Groupe sanguin : Select
- Allergie(s) connue(s) : Input texte libre
- Personne à contacter en cas d'urgence : Nom + téléphone

### 4.7 Documents à fournir (récapitulatif des uploads)

Zone récapitulative des fichiers requis avec statut (✅ Fourni / ❌ Manquant) :
- Extrait de naissance
- Photo d'identité
- Relevé de notes
- Copie du diplôme
- Certificat de résidence (optionnel)

### 4.8 Validation du formulaire

- Validation en temps réel par champ (rouge si erreur, vert si correct)
- Résumé des erreurs en haut du formulaire si tentative de soumission incomplète
- Boutons : `← Retour` · `Continuer vers le récapitulatif →`
- Sauvegarde automatique de brouillon (localStorage ou session Django) pour ne pas perdre les données

---

## 5. ÉTAPE 3 — RÉCAPITULATIF & MONTANT

### 5.1 Résumé des informations saisies

- Identité : Nom complet, date de naissance, photo miniature
- Filière + Licence + Semestre + Année académique
- Régime d'études

**Bouton** : `Modifier les informations` (retour à l'étape 2)

### 5.2 Détail des frais de scolarité

Tableau des montants :
| Élément | Montant |
|---------|---------|
| Frais d'inscription | XX XXX FCFA |
| Scolarité (année complète) | XXX XXX FCFA |
| Frais de dossier | X XXX FCFA |
| Frais transport (si car) | XX XXX FCFA (optionnel) |
| **TOTAL À PAYER** | **XXX XXX FCFA** |

- Les montants sont **dynamiques** selon la filière et la licence sélectionnées (model `Tarif`)
- Option : paiement en **plusieurs tranches** si autorisé (afficher un plan de paiement)

### 5.3 Plan de paiement (si plusieurs tranches)

| Tranche | Montant | Échéance |
|---------|---------|----------|
| 1ère tranche (à payer maintenant) | XXX XXX FCFA | Immédiat |
| 2ème tranche | XXX XXX FCFA | 30/06/2026 |
| 3ème tranche | XXX XXX FCFA | 30/09/2026 |

**Bouton** : `Confirmer et procéder au paiement →`

---

## 6. ÉTAPE 4 — PAIEMENT DE SCOLARITÉ

### 6.1 Sélection du moyen de paiement

**Titre** : *"Comment souhaitez-vous payer ?"*

**Cartes de moyens de paiement** (grande et cliquable) :

**Wave** :
- Logo Wave
- Texte : *"Payer avec Wave"*
- Description : *"Rapide, disponible 24h/24. Frais : inclus."*
- Disponible sur : 📱 Mobile (lien deep-link wave://) et 💻 Web (QR Code)

**Orange Money** :
- Logo Orange Money
- Texte : *"Payer avec Orange Money"*
- Description : *"Pour tous les utilisateurs Orange CI."*
- Disponible sur : 📱 Mobile (lien deep-link) et 💻 Web (USSD ou API)

**MTN Money (optionnel)** :
- Logo MTN
- Texte : *"Payer avec MTN Money"*

**Paiement en espèces (fallback)** :
- Icône 💵
- Texte : *"Payer en espèces au secrétariat"*
- Description : *"Génère un bon de paiement à présenter à l'école. Valable 48h."*

### 6.2 Détection automatique du contexte

- **Sur mobile** : les options Wave et Orange Money affichent un bouton `Ouvrir l'application →` (deep-link direct)
- **Sur desktop** : affichage d'un **QR Code** à scanner avec l'application mobile Wave / Orange Money

### 6.3 Flux Wave (mobile)

1. Étudiant clique `Payer avec Wave`
2. Deep-link ouvre l'app Wave avec montant pré-rempli et numéro marchand EMSP
3. Étudiant confirme dans l'app Wave
4. Wave envoie un callback à l'API Django (`/inscription/webhook/wave/`)
5. Django valide le paiement → redirige vers la confirmation

### 6.4 Flux Orange Money (mobile)

1. Étudiant clique `Payer avec Orange Money`
2. Deep-link ou code USSD généré automatiquement
3. Confirmation dans l'app ou par USSD
4. Callback API Django (`/inscription/webhook/orange-money/`)
5. Django valide → confirmation

### 6.5 Flux QR Code (desktop)

1. QR Code affiché avec montant et référence unique
2. Étudiant scanne avec son téléphone (app Wave ou OM)
3. Confirme le paiement sur mobile
4. Page desktop se rafraîchit automatiquement (polling ou WebSocket)
5. Confirmation affichée

### 6.6 Récapitulatif de paiement visible en permanence

Bandeau latéral ou en bas de page :
- Montant à payer : **XXX XXX FCFA**
- Référence de la transaction générée
- Délai de session : *"Cette session expire dans 14:32"* (compte à rebours)

---

## 7. ÉTAPE 5 — CONFIRMATION & REÇU

### 7.1 Écran de succès

- Animation : checkmark animé (vert)
- Titre : *"🎉 Inscription confirmée !"*
- Message : *"Ton paiement a bien été reçu. Ton espace étudiant est maintenant actif."*

### 7.2 Résumé du reçu affiché

| Champ | Valeur |
|-------|--------|
| Nom complet | Prénom Nom |
| Matricule attribué | EMSP-2026-XXXX |
| Filière | Digitalisation des Services |
| Licence | L1 |
| Année académique | 2025–2026 |
| Montant payé | XXX XXX FCFA |
| Référence de transaction | TXN-XXXXXXX |
| Date et heure | 22/04/2026 à 14h32 |
| Moyen de paiement | Wave |

### 7.3 Actions disponibles

- Bouton principal : `Accéder à mon espace étudiant →`
- Bouton secondaire : `📥 Télécharger mon reçu en PDF`
- Bouton tertiaire : `📧 Recevoir le reçu par email`

---

## 8. PAGE STATUT D'INSCRIPTION

> URL : `/etudiant/inscription/statut/`  
> Accessible depuis l'espace étudiant pour voir l'état global de son dossier

**Titre** : *"Mon dossier d'inscription"*

**Carte de statut général** :
- Badge coloré : `✅ Validé` / `⏳ En cours de traitement` / `❌ Dossier incomplet`

**Timeline du dossier** :
1. ✅ Formulaire soumis — 22/04/2026
2. ✅ Paiement reçu — 22/04/2026 — XXX XXX FCFA (Wave)
3. ✅ Dossier validé par l'administration — 23/04/2026
4. ✅ Accès à l'espace étudiant activé

**Documents manquants** (si dossier incomplet) :
- Liste des documents à fournir avec bouton `Déposer`

**Historique des paiements** :
| Date | Montant | Moyen | Référence | Statut |
|------|---------|-------|-----------|--------|
| 22/04/2026 | XX XXX FCFA | Wave | TXN-XXX | ✅ Validé |
| 30/06/2026 | XX XXX FCFA | — | — | ⏳ À venir |

---

## NOTES TECHNIQUES DJANGO

| Élément | Détail |
|---------|--------|
| Model `DemandeInscription` | Stocke tout le formulaire, FK vers `User`, statut, filière, licence |
| Model `Tarif` | FK vers `Filiere` + `Licence` — montants par type (inscription, scolarité, transport) |
| Model `Paiement` | FK vers `DemandeInscription` — champs : montant, moyen, référence, statut, date |
| Model `Tranche` | FK vers `Paiement` — pour les paiements multi-tranches |
| Webhooks | Vues dédiées `/webhook/wave/` et `/webhook/orange-money/` — validation de signature HMAC |
| Génération reçu PDF | `weasyprint` ou `reportlab` depuis un template HTML |
| Deep-links mobile | `wave://pay?amount=XXX&merchant_id=YYY` / équivalent OM |
| Session de paiement | UUID unique par session, expiration 15 min, stocké en Redis |
| Email confirmation | `django.core.mail` avec template HTML du reçu en pièce jointe |
| Sécurité | CSRF, rate limiting sur les endpoints de paiement, validation côté serveur de tous les montants |

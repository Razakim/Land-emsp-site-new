# 01 — Page d'Accueil · Design Prompt Complet
> Module Django : `core` / vue : `HomeView`  
> Accès : **Public** (non authentifié)

---

## STRUCTURE GÉNÉRALE DE LA PAGE

```
[TOPBAR STICKY]
[NAVBAR]
[HERO + CAROUSEL]
[SECTION — Chiffres clés]
[SECTION — Présentation de l'école]
[SECTION — Nos formations]
[SECTION — Comment fonctionne la plateforme]
[SECTION — Ressources récentes (aperçu)]
[SECTION — Témoignages / Vie étudiante]
[CTA — Inscription]
[FOOTER]
```

---

## 1. TOPBAR STICKY

**Position** : tout en haut, fixe au scroll, z-index max  
**Hauteur** : fine (30–36px)  
**Contenu** :
- Texte court : *"Accès gratuit pour les étudiants EMSP — Cours, TD, examens partagés par la communauté"*
- Séparateur `·`
- Lien cliquable : *"S'inscrire maintenant →"* (redirige vers `/inscription/`)

**Comportement** : disparaît au scroll vers le bas, réapparaît au scroll vers le haut (comportement smart-header)

---

## 2. NAVBAR

**Position** : sticky sous le topbar  
**Hauteur** : 64px  
**Fond** : semi-transparent avec blur (glassmorphism léger) sur scroll  

**Logo** (gauche) :
- Texte : `EMSP.Docs`
- Badge optionnel : `Bêta` ou version
- Cliquable → `/`

**Liens de navigation** (centre ou droite selon layout) :
| Lien | URL cible |
|------|-----------|
| Accueil | `/` |
| Institution | `/institution/` |
| Formations | `/formations/` |
| Médiathèque | `/bibliotheque/` |
| Journal | `/journal/` |
| Concours | `/concours/` |
| FAQ | `/faq/` |

**Lien actif** : souligné ou coloré différemment (couleur accent de la charte)

**Boutons CTA** (droite) :
- `Se connecter` → `/login/` — style ghost/outline
- `S'inscrire` → `/inscription/` — style plein (couleur principale)

**Version mobile** : menu hamburger → drawer latéral avec tous les liens + boutons CTA

---

## 3. HERO + CAROUSEL D'IMAGES

**Position** : première section visible, pleine hauteur (min 90vh)  
**Disposition** : carousel plein écran en arrière-plan + contenu textuel superposé (z-index supérieur)

### 3.1 Carousel (arrière-plan)

**Type** : slideshow automatique d'images réelles de l'école  
**Transition** : fondu enchaîné (crossfade) ou glissement horizontal — durée 800ms  
**Intervalle** : 5–6 secondes  
**Nombre de slides** : 4 à 6 images  

**Images à prévoir (à charger via Django media ou CDN)** :
| Slide | Sujet suggéré |
|-------|--------------|
| 1 | Vue extérieure du campus / bâtiment principal EMSP |
| 2 | Salle de cours — étudiants en amphithéâtre |
| 3 | Bibliothèque physique ou salle informatique |
| 4 | Remise de diplômes / cérémonie académique |
| 5 | Vie associative, événement étudiant |
| 6 | Vue aérienne ou panoramique du site |

**Overlay** : dégradé sombre (noir 50–70%) sur chaque image pour garantir la lisibilité du texte

**Contrôles** :
- Flèches gauche/droite (visibles au hover ou toujours visibles)
- Indicateurs de position : dots en bas au centre
- Dot actif = étiré/coloré
- Clic sur dot → slide correspondant
- Pause au hover de la souris sur le carousel

**Label de slide** (optionnel, en bas à gauche) :
- Numéro : `01 / 05`
- Titre court du sujet (ex : *"Amphithéâtre principal"*)

### 3.2 Contenu superposé (Hero)

**Positionnement** : centré-gauche verticalement, padding important  

**Éléments de haut en bas** :

1. **Tag / badge animé** :
   - Texte : *"La plateforme académique EMSP"* ou *"Plateforme de partage académique"*
   - Style : petite pastille avec point lumineux (pulsation CSS)

2. **Titre principal** (H1) :
   - Texte : *"La bibliothèque numérique de l'EMSP"*
   - Typographie : grande, serif ou bold display
   - Mise en valeur d'un mot-clé en couleur accent (ex : *"numérique"* en doré)

3. **Sous-titre / description** :
   - Texte : *"Cours, TD, corrections et sujets d'examens partagés par les étudiants, organisés par filière, licence et matière dans un espace clair et fiable."*
   - Police légère, taille 16–18px, largeur max 520px

4. **Boutons CTA (2)** :
   - Principal : `Explorer les ressources` → `/bibliotheque/`
   - Secondaire : `S'inscrire` → `/inscription/`

5. **Mini-stats (3 chiffres)** :
   - `6` Filières actives
   - `4` Licences disponibles
   - `+5` Documents validés *(chiffre dynamique depuis la BDD)*
   - Style : séparés par une bordure fine verticale

---

## 4. SECTION — CHIFFRES CLÉS

**Position** : juste sous le hero, bande horizontale  
**Fond** : légèrement différent du fond principal (surface élevée)  
**Disposition** : 4 colonnes égales, séparées par bordures fines  

**Métriques** (données dynamiques depuis Django ORM) :
| Métrique | Source BDD |
|----------|-----------|
| Nombre de filières actives | `Filiere.objects.filter(active=True).count()` |
| Nombre de licences | `Licence.objects.count()` |
| Nombre de documents validés | `Document.objects.filter(valide=True).count()` |
| Nombre d'étudiants inscrits | `User.objects.filter(role='etudiant').count()` |

**Comportement** : animation de comptage (count-up) au premier affichage dans le viewport  
**Hover** : légère surbrillance + trait de couleur accent en haut de colonne

---

## 5. SECTION — PRÉSENTATION DE L'ÉCOLE

**Position** : section pleine largeur, alternance texte/image  
**Disposition** : 2 colonnes (60/40 ou 50/50)

**Colonne texte** :
- Label de section : *"Institution"* (petite majuscule, couleur accent)
- Titre : *"L'École de Management et Sciences Professionnelles"*
- Paragraphe de présentation : historique, mission, valeurs (texte à fournir par l'école)
- Liste de points forts (icône + texte) :
  - Fondée en ...
  - ... étudiants formés
  - Formations reconnues
  - Partenariats académiques
- Bouton : `En savoir plus → /institution/`

**Colonne image** :
- Photo du bâtiment / directeur / scène académique
- Optionnel : badge flottant avec un chiffre marquant (*"15 ans d'excellence"*)

---

## 6. SECTION — NOS FORMATIONS

**Position** : après la présentation  
**Disposition** : grille de cartes (3 ou 4 par ligne selon le nombre de filières)

**Titre de section** : *"Nos formations"*  
**Sous-titre** : *"6 filières, 4 licences, des parcours adaptés à chaque ambition."*

**Chaque carte de filière affiche** :
- Icône ou couleur identitaire de la filière
- Nom de la filière (ex : *"Digitalisation des Services"*)
- Nombre de licences disponibles
- Nombre de documents disponibles dans la bibliothèque
- Bouton : `Voir les ressources →` (redirige vers la bibliothèque filtrée)

**Données** : `Filiere.objects.all()` avec annotation du count de documents

---

## 7. SECTION — COMMENT FONCTIONNE LA PLATEFORME

**Position** : section sobre, fond alterné  
**Disposition** : liste d'étapes numérotées (stepper horizontal ou vertical)

**Étapes** :
1. **S'inscrire** — *"Crée ton compte en quelques minutes avec ton email EMSP"*
2. **Accéder aux documents** — *"Consulte les cours, TD, examens et concours validés"*
3. **Contribuer** — *"Dépose tes fichiers pour enrichir la bibliothèque"*

**Visuels associés** : illustration ou capture d'écran de l'interface pour chaque étape  
**Animation** : apparition séquentielle au scroll (stagger)

---

## 8. SECTION — RESSOURCES RÉCENTES (aperçu)

**Position** : avant le CTA final  
**Titre** : *"Ressources récentes"*  
**Sous-titre** : *"Les dernières ressources validées, visibles immédiatement."*

**Contenu** : affichage des **5 derniers documents validés** (`Document.objects.filter(valide=True).order_by('-date_ajout')[:5]`)

**Chaque carte document affiche** :
- Badge de type : `Cours` / `TD` / `Examen` / `Concours` (couleur distincte par type)
- Semestre (ex : `S3`)
- Nom de la filière
- Titre du document
- Description courte
- Avatar + nom du contributeur
- Nombre de téléchargements
- Date d'ajout
- Bouton : `Accéder après connexion` → redirige vers `/login/?next=/document/[id]/`

**Footer de section** : bouton `Voir toutes les ressources →` `/bibliotheque/`

---

## 9. SECTION — TÉMOIGNAGES / VIE ÉTUDIANTE

**Position** : optionnel, avant le CTA final  
**Contenu** : 2–3 citations d'étudiants avec photo, nom, filière, promo  
**Disposition** : carousel de cards ou grille fixe  
**Données** : soit statiques (hardcodées dans le template), soit depuis un model `Temoignage`

---

## 10. SECTION CTA — REJOINDRE LA COMMUNAUTÉ

**Position** : avant le footer, section pleine largeur  
**Fond** : accent léger (dégradé ou couleur secondaire) pour se démarquer

**Contenu** :
- Titre : *"Prêt à rejoindre la communauté EMSP ?"*
- Description : *"Ouvre ton compte pour accéder à la bibliothèque, sauvegarder tes favoris et partager tes propres documents."*
- Bouton principal : `S'inscrire maintenant` → `/inscription/`
- Bouton secondaire : `Se connecter` → `/login/`
- Note rassurante : *"Accès gratuit · Inscription en 2 minutes · Espace étudiant immédiat"*

---

## 11. FOOTER

**Disposition** : 4 colonnes + barre de bas de page

**Colonne 1 — Branding** :
- Logo `EMSP.Docs`
- Description courte de la plateforme
- Réseaux sociaux (si existants)

**Colonne 2 — Navigation** :
- Accueil, Formations, Médiathèque, Journal, Concours

**Colonne 3 — Plateforme** :
- S'inscrire, Se connecter, FAQ, Explorer

**Colonne 4 — Contact EMSP** :
- Adresse : *Abidjan, Treichville, Zone 3, Km4*
- Téléphone : *+225 27 21 21 45 60 / 61*
- Email : *contact@emsp.int*

**Barre de bas de page** :
- *"© 2026 EMSP Docs. Tous droits réservés. Plateforme de partage académique pour la communauté EMSP."*
- Tags : `Accès gratuit` · `Communauté EMSP`

---

## NOTES TECHNIQUES DJANGO

- Vue : `HomeView(TemplateView)` dans `core/views.py`
- Template : `core/templates/core/home.html`
- Context transmis : `nb_filieres`, `nb_licences`, `nb_documents`, `derniers_documents` (queryset)
- Le carousel d'images est géré via un model `SlideCarousel(image, titre, ordre, actif)` administrable depuis le Dashboard admin
- Toutes les données de comptage sont annotées/cachées (Redis ou cache Django) pour performance

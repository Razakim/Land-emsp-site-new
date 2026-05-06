-- =============================================================================
--  EMSP DOCS — Schéma SQL Complet
--  SGBD : PostgreSQL 15+
--  Encodage : UTF-8
--  Généré pour : Django 5.x (nommage snake_case, PK = BIGSERIAL)
-- =============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";   -- recherche full-text trigram

-- Nettoyage (ordre inverse des dépendances)
DROP TABLE IF EXISTS
    audit_trail, notification,
    justification_absence, presence, seance,
    emploi_du_temps_seance, emploi_du_temps,
    note,
    tranche, paiement, demande_inscription_document, demande_inscription,
    tarif,
    commentaire, favori, telechargement, document,
    evenement_filiere, evenement,
    slide_carousel, temoignage,
    config_paiement,
    etudiant,
    auth_user_profile,
    -- tables Django auth (référencées uniquement)
    matiere, semestre, licence, filiere,
    annee_academique, salle, type_document
CASCADE;

-- =============================================================================
--  BLOC 1 — RÉFÉRENTIELS DE BASE
-- =============================================================================

-- 1.1 Année académique
CREATE TABLE annee_academique (
    id          BIGSERIAL PRIMARY KEY,
    label       VARCHAR(20)  NOT NULL UNIQUE,   -- ex: "2025-2026"
    active      BOOLEAN      NOT NULL DEFAULT FALSE,
    date_debut  DATE,
    date_fin    DATE,
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- 1.2 Filières
CREATE TABLE filiere (
    id              BIGSERIAL PRIMARY KEY,
    nom             VARCHAR(120) NOT NULL UNIQUE,
    slug            VARCHAR(120) NOT NULL UNIQUE,
    description     TEXT,
    couleur_hex     VARCHAR(7)   DEFAULT '#2563EB',  -- identité visuelle
    active          BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- 1.3 Licences (niveaux)
CREATE TABLE licence (
    id      BIGSERIAL PRIMARY KEY,
    label   VARCHAR(20)  NOT NULL UNIQUE,  -- L1, L2, L3, Master
    ordre   SMALLINT     NOT NULL DEFAULT 1
);
INSERT INTO licence (label, ordre) VALUES
    ('L1', 1), ('L2', 2), ('L3', 3), ('Master', 4);

-- 1.4 Semestres
CREATE TABLE semestre (
    id          BIGSERIAL PRIMARY KEY,
    numero      SMALLINT     NOT NULL,   -- 1 à 6
    label       VARCHAR(5)   NOT NULL,   -- S1 … S6
    filiere_id  BIGINT       REFERENCES filiere(id) ON DELETE CASCADE,
    licence_id  BIGINT       REFERENCES licence(id) ON DELETE SET NULL,
    UNIQUE (numero, filiere_id)
);

-- 1.5 Matières
CREATE TABLE matiere (
    id          BIGSERIAL PRIMARY KEY,
    nom         VARCHAR(120) NOT NULL,
    code        VARCHAR(20)  UNIQUE,
    credits     SMALLINT     NOT NULL DEFAULT 3,
    filiere_id  BIGINT       NOT NULL REFERENCES filiere(id) ON DELETE CASCADE,
    licence_id  BIGINT       REFERENCES licence(id) ON DELETE SET NULL,
    semestre_id BIGINT       REFERENCES semestre(id) ON DELETE SET NULL,
    active      BOOLEAN      NOT NULL DEFAULT TRUE
);

-- 1.6 Salles
CREATE TABLE salle (
    id          BIGSERIAL PRIMARY KEY,
    nom         VARCHAR(60)  NOT NULL UNIQUE,   -- "Amphi A", "Salle 204"
    capacite    SMALLINT,
    type        VARCHAR(20)  DEFAULT 'salle',   -- salle | amphi | labo
    disponible  BOOLEAN      NOT NULL DEFAULT TRUE
);

-- 1.7 Types de document (bibliothèque)
CREATE TABLE type_document (
    id      BIGSERIAL PRIMARY KEY,
    label   VARCHAR(40) NOT NULL UNIQUE,  -- Cours, TD, Examen, Correction, Concours
    couleur VARCHAR(7)  DEFAULT '#6B7280'
);
INSERT INTO type_document (label, couleur) VALUES
    ('Cours',       '#2563EB'),
    ('TD',          '#7C3AED'),
    ('Examen',      '#DC2626'),
    ('Correction',  '#16A34A'),
    ('Concours',    '#D97706');

-- =============================================================================
--  BLOC 2 — UTILISATEURS & AUTHENTIFICATION
-- =============================================================================

-- 2.1 Profil étendu (OneToOne sur auth_user de Django)
--  Note : Django gère la table "auth_user". On crée un profil lié.
CREATE TABLE auth_user_profile (
    id              BIGSERIAL PRIMARY KEY,
    user_id         INTEGER  NOT NULL UNIQUE,   -- FK → auth_user.id (géré par Django)
    role            VARCHAR(30) NOT NULL DEFAULT 'etudiant',
    -- ENUM: etudiant | admin | secretariat | professeur | responsable_financier | superadmin
    telephone       VARCHAR(20),
    photo           VARCHAR(255),               -- chemin fichier media
    langue          VARCHAR(5)  DEFAULT 'fr',
    notif_email_notes       BOOLEAN DEFAULT TRUE,
    notif_email_absences    BOOLEAN DEFAULT TRUE,
    notif_email_evenements  BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- 2.2 Étudiant (extension du profil)
CREATE TABLE etudiant (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             INTEGER     NOT NULL UNIQUE,  -- FK → auth_user.id
    matricule           VARCHAR(20) NOT NULL UNIQUE,  -- ex: EMSP-2026-0001
    filiere_id          BIGINT      NOT NULL REFERENCES filiere(id),
    licence_id          BIGINT      NOT NULL REFERENCES licence(id),
    semestre_actuel_id  BIGINT      REFERENCES semestre(id),
    annee_id            BIGINT      REFERENCES annee_academique(id),
    statut_inscription  VARCHAR(20) NOT NULL DEFAULT 'en_attente',
    -- ENUM: en_attente | inscrit | suspendu | diplome | abandon
    photo_profil        VARCHAR(255),
    date_inscription    DATE,
    created_at          TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- =============================================================================
--  BLOC 3 — INSCRIPTION & PAIEMENT
-- =============================================================================

-- 3.1 Demande d'inscription
CREATE TABLE demande_inscription (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             INTEGER     NOT NULL,           -- FK → auth_user.id
    type_inscription    VARCHAR(20) NOT NULL DEFAULT 'nouvelle',  -- nouvelle | reinscription
    statut              VARCHAR(20) NOT NULL DEFAULT 'en_attente',
    -- ENUM: en_attente | en_cours | valide | refuse | incomplet

    -- Informations personnelles
    nom                 VARCHAR(80)  NOT NULL,
    prenom              VARCHAR(120) NOT NULL,
    date_naissance      DATE         NOT NULL,
    lieu_naissance      VARCHAR(100),
    nationalite         VARCHAR(60),
    genre               VARCHAR(10),                   -- masculin | feminin
    situation_familiale VARCHAR(30),
    photo_identite      VARCHAR(255),

    -- Coordonnées
    email_personnel     VARCHAR(254) NOT NULL,
    telephone_principal VARCHAR(20)  NOT NULL,
    telephone_secondaire VARCHAR(20),
    adresse             TEXT,
    quartier            VARCHAR(80),
    ville               VARCHAR(60),

    -- Parcours académique
    filiere_id          BIGINT       NOT NULL REFERENCES filiere(id),
    licence_id          BIGINT       NOT NULL REFERENCES licence(id),
    semestre_id         BIGINT       REFERENCES semestre(id),
    annee_id            BIGINT       NOT NULL REFERENCES annee_academique(id),
    regime_etudes       VARCHAR(10)  DEFAULT 'journee',  -- journee | soir
    matricule_existant  VARCHAR(20),                     -- ré-inscription uniquement

    -- Diplômes
    dernier_diplome     VARCHAR(30),
    annee_diplome       SMALLINT,
    etablissement_origine VARCHAR(120),
    serie_bac           VARCHAR(40),
    mention_bac         VARCHAR(20),

    -- Tuteur
    tuteur_nom          VARCHAR(120),
    tuteur_lien         VARCHAR(30),
    tuteur_telephone    VARCHAR(20),
    tuteur_profession   VARCHAR(60),

    -- Santé
    groupe_sanguin      VARCHAR(5),
    allergies           TEXT,
    urgence_nom         VARCHAR(120),
    urgence_telephone   VARCHAR(20),

    -- Admin interne
    commentaire_admin   TEXT,
    traite_par_id       INTEGER,                        -- FK → auth_user.id (admin)
    date_traitement     TIMESTAMP,

    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 3.2 Documents liés à la demande
CREATE TABLE demande_inscription_document (
    id              BIGSERIAL PRIMARY KEY,
    demande_id      BIGINT       NOT NULL REFERENCES demande_inscription(id) ON DELETE CASCADE,
    type_doc        VARCHAR(40)  NOT NULL,
    -- extrait_naissance | photo_identite | releve_notes | diplome | certificat_residence | autre
    fichier         VARCHAR(255) NOT NULL,
    fourni          BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- 3.3 Tarifs de scolarité
CREATE TABLE tarif (
    id                  BIGSERIAL PRIMARY KEY,
    filiere_id          BIGINT    NOT NULL REFERENCES filiere(id) ON DELETE CASCADE,
    licence_id          BIGINT    NOT NULL REFERENCES licence(id) ON DELETE CASCADE,
    annee_id            BIGINT    NOT NULL REFERENCES annee_academique(id),
    frais_inscription   NUMERIC(12,2) NOT NULL DEFAULT 0,
    scolarite_annuelle  NUMERIC(12,2) NOT NULL DEFAULT 0,
    frais_dossier       NUMERIC(12,2) NOT NULL DEFAULT 0,
    frais_transport     NUMERIC(12,2) NOT NULL DEFAULT 0,
    paiement_tranches   BOOLEAN   NOT NULL DEFAULT FALSE,
    nb_tranches         SMALLINT  DEFAULT 1,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (filiere_id, licence_id, annee_id)
);

-- 3.4 Paiement
CREATE TABLE paiement (
    id                  BIGSERIAL   PRIMARY KEY,
    demande_id          BIGINT      NOT NULL REFERENCES demande_inscription(id),
    montant             NUMERIC(12,2) NOT NULL,
    moyen               VARCHAR(20) NOT NULL,
    -- ENUM: wave | orange_money | mtn | especes
    reference_transaction VARCHAR(80) UNIQUE,
    statut              VARCHAR(20) NOT NULL DEFAULT 'en_attente',
    -- ENUM: en_attente | valide | echoue | rembourse
    session_uuid        UUID        NOT NULL DEFAULT uuid_generate_v4(),
    session_expires_at  TIMESTAMP,
    qr_code_data        TEXT,
    webhook_payload     JSONB,
    enregistre_par_id   INTEGER,                    -- FK admin si saisie manuelle
    created_at          TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- 3.5 Tranches de paiement
CREATE TABLE tranche (
    id              BIGSERIAL    PRIMARY KEY,
    paiement_id     BIGINT       NOT NULL REFERENCES paiement(id) ON DELETE CASCADE,
    numero          SMALLINT     NOT NULL,
    montant         NUMERIC(12,2) NOT NULL,
    echeance        DATE,
    statut          VARCHAR(20)  NOT NULL DEFAULT 'a_venir',
    -- ENUM: a_venir | paye | en_retard
    date_paiement   TIMESTAMP,
    reference       VARCHAR(80),
    UNIQUE (paiement_id, numero)
);

-- =============================================================================
--  BLOC 4 — BIBLIOTHÈQUE
-- =============================================================================

CREATE TABLE document (
    id              BIGSERIAL    PRIMARY KEY,
    contributeur_id INTEGER      NOT NULL,              -- FK → auth_user.id
    type_id         BIGINT       NOT NULL REFERENCES type_document(id),
    filiere_id      BIGINT       NOT NULL REFERENCES filiere(id),
    licence_id      BIGINT       REFERENCES licence(id),
    semestre_id     BIGINT       REFERENCES semestre(id),
    matiere_id      BIGINT       REFERENCES matiere(id),
    annee_id        BIGINT       REFERENCES annee_academique(id),

    titre           VARCHAR(200) NOT NULL,
    description     TEXT,
    fichier         VARCHAR(255) NOT NULL,
    taille_ko       INTEGER,
    format          VARCHAR(10),                        -- pdf | docx | pptx | xlsx

    valide          BOOLEAN      NOT NULL DEFAULT FALSE,
    valide_par_id   INTEGER,
    date_validation TIMESTAMP,
    motif_refus     TEXT,

    nb_telechargements INTEGER  NOT NULL DEFAULT 0,
    created_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- Index full-text sur titre + description
CREATE INDEX idx_document_search ON document
    USING GIN (to_tsvector('french', titre || ' ' || COALESCE(description, '')));

CREATE TABLE telechargement (
    id          BIGSERIAL PRIMARY KEY,
    document_id BIGINT    NOT NULL REFERENCES document(id) ON DELETE CASCADE,
    user_id     INTEGER   NOT NULL,                    -- FK → auth_user.id
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, user_id)
);

CREATE TABLE favori (
    id          BIGSERIAL PRIMARY KEY,
    document_id BIGINT    NOT NULL REFERENCES document(id) ON DELETE CASCADE,
    user_id     INTEGER   NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, user_id)
);

CREATE TABLE commentaire (
    id          BIGSERIAL PRIMARY KEY,
    document_id BIGINT    NOT NULL REFERENCES document(id) ON DELETE CASCADE,
    auteur_id   INTEGER   NOT NULL,
    parent_id   BIGINT    REFERENCES commentaire(id) ON DELETE CASCADE,   -- thread
    texte       TEXT      NOT NULL,
    nb_likes    INTEGER   NOT NULL DEFAULT 0,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =============================================================================
--  BLOC 5 — ESPACE ÉTUDIANT (EDT, NOTES, PRÉSENCES)
-- =============================================================================

-- 5.1 Emploi du temps (conteneur par promo)
CREATE TABLE emploi_du_temps (
    id          BIGSERIAL PRIMARY KEY,
    filiere_id  BIGINT    NOT NULL REFERENCES filiere(id),
    licence_id  BIGINT    NOT NULL REFERENCES licence(id),
    semestre_id BIGINT    NOT NULL REFERENCES semestre(id),
    annee_id    BIGINT    NOT NULL REFERENCES annee_academique(id),
    publie      BOOLEAN   NOT NULL DEFAULT FALSE,
    publie_le   TIMESTAMP,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (filiere_id, licence_id, semestre_id, annee_id)
);

-- 5.2 Séance
CREATE TABLE seance (
    id                  BIGSERIAL  PRIMARY KEY,
    emploi_du_temps_id  BIGINT     REFERENCES emploi_du_temps(id) ON DELETE SET NULL,
    matiere_id          BIGINT     NOT NULL REFERENCES matiere(id),
    professeur_id       INTEGER    NOT NULL,            -- FK → auth_user.id
    salle_id            BIGINT     REFERENCES salle(id),

    type_seance         VARCHAR(10) NOT NULL DEFAULT 'cours',  -- cours | td | examen | autre
    date                DATE        NOT NULL,
    heure_debut         TIME        NOT NULL,
    heure_fin           TIME        NOT NULL,
    recurrence          VARCHAR(20) DEFAULT 'none',     -- none | hebdomadaire | bi_hebdomadaire
    statut              VARCHAR(15) DEFAULT 'planifie', -- planifie | annule | deplace | en_cours
    remarques           TEXT,
    created_at          TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- Table de jointure EDT ↔ Séance (si une séance appartient à plusieurs EDT)
CREATE TABLE emploi_du_temps_seance (
    emploi_du_temps_id  BIGINT NOT NULL REFERENCES emploi_du_temps(id) ON DELETE CASCADE,
    seance_id           BIGINT NOT NULL REFERENCES seance(id) ON DELETE CASCADE,
    PRIMARY KEY (emploi_du_temps_id, seance_id)
);

-- 5.3 Notes
CREATE TABLE note (
    id              BIGSERIAL   PRIMARY KEY,
    etudiant_id     BIGINT      NOT NULL REFERENCES etudiant(id) ON DELETE CASCADE,
    matiere_id      BIGINT      NOT NULL REFERENCES matiere(id),
    semestre_id     BIGINT      NOT NULL REFERENCES semestre(id),
    annee_id        BIGINT      NOT NULL REFERENCES annee_academique(id),

    note_cc         NUMERIC(4,2),                      -- /20
    note_exam       NUMERIC(4,2),                      -- /20
    note_finale     NUMERIC(4,2),                      -- calculée
    mention         VARCHAR(20),                        -- TB | B | AB | Passable | Insuffisant
    credits_valides BOOLEAN     NOT NULL DEFAULT FALSE,

    publiee         BOOLEAN     NOT NULL DEFAULT FALSE, -- visible étudiant ?
    publiee_le      TIMESTAMP,
    saisie_par_id   INTEGER,                            -- FK → auth_user.id
    modifie_par_id  INTEGER,
    motif_modification TEXT,

    created_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    UNIQUE (etudiant_id, matiere_id, semestre_id, annee_id)
);

-- 5.4 Présences
CREATE TABLE presence (
    id          BIGSERIAL  PRIMARY KEY,
    etudiant_id BIGINT     NOT NULL REFERENCES etudiant(id) ON DELETE CASCADE,
    seance_id   BIGINT     NOT NULL REFERENCES seance(id) ON DELETE CASCADE,
    statut      VARCHAR(25) NOT NULL DEFAULT 'present',
    -- ENUM: present | absent_justifie | absent_non_justifie
    saisie_par_id INTEGER,
    created_at  TIMESTAMP  NOT NULL DEFAULT NOW(),
    UNIQUE (etudiant_id, seance_id)
);

-- 5.5 Justification d'absence
CREATE TABLE justification_absence (
    id              BIGSERIAL   PRIMARY KEY,
    presence_id     BIGINT      NOT NULL UNIQUE REFERENCES presence(id) ON DELETE CASCADE,
    motif           TEXT        NOT NULL,
    piece_jointe    VARCHAR(255),
    statut          VARCHAR(15) NOT NULL DEFAULT 'en_attente',
    -- ENUM: en_attente | acceptee | refusee
    commentaire_admin TEXT,
    traitee_par_id  INTEGER,
    date_traitement TIMESTAMP,
    created_at      TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- =============================================================================
--  BLOC 6 — ÉVÉNEMENTS & CONTENUS
-- =============================================================================

CREATE TABLE evenement (
    id              BIGSERIAL   PRIMARY KEY,
    titre           VARCHAR(200) NOT NULL,
    type            VARCHAR(30)  NOT NULL DEFAULT 'autre',
    -- examen | concours | conference | portes_ouvertes | fete | reunion | sortie | autre
    description     TEXT,
    date_debut      TIMESTAMP   NOT NULL,
    date_fin        TIMESTAMP,
    lieu            VARCHAR(120),
    image_affiche   VARCHAR(255),
    public_tous     BOOLEAN     NOT NULL DEFAULT TRUE,
    visible_accueil BOOLEAN     NOT NULL DEFAULT FALSE,
    cree_par_id     INTEGER,
    created_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- Événement ciblant des filières spécifiques (si public_tous = FALSE)
CREATE TABLE evenement_filiere (
    evenement_id    BIGINT NOT NULL REFERENCES evenement(id) ON DELETE CASCADE,
    filiere_id      BIGINT NOT NULL REFERENCES filiere(id) ON DELETE CASCADE,
    PRIMARY KEY (evenement_id, filiere_id)
);

-- Carousel de la page d'accueil
CREATE TABLE slide_carousel (
    id          BIGSERIAL   PRIMARY KEY,
    image       VARCHAR(255) NOT NULL,
    titre       VARCHAR(120),
    legende     VARCHAR(200),
    ordre       SMALLINT    NOT NULL DEFAULT 0,
    actif       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- Témoignages
CREATE TABLE temoignage (
    id          BIGSERIAL   PRIMARY KEY,
    texte       TEXT        NOT NULL,
    auteur      VARCHAR(80) NOT NULL,
    filiere     VARCHAR(80),
    promo       VARCHAR(20),
    photo       VARCHAR(255),
    actif       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- =============================================================================
--  BLOC 7 — SYSTÈME & CONFIGURATION
-- =============================================================================

-- 7.1 Notifications utilisateur
CREATE TABLE notification (
    id          BIGSERIAL   PRIMARY KEY,
    user_id     INTEGER     NOT NULL,               -- FK → auth_user.id
    type        VARCHAR(30) NOT NULL,
    -- note_publiee | absence | paiement | document_valide | evenement | inscription | autre
    titre       VARCHAR(120),
    message     TEXT        NOT NULL,
    lu          BOOLEAN     NOT NULL DEFAULT FALSE,
    lien        VARCHAR(255),
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_notification_user ON notification (user_id, lu, created_at DESC);

-- 7.2 Audit trail
CREATE TABLE audit_trail (
    id          BIGSERIAL   PRIMARY KEY,
    user_id     INTEGER,                            -- FK → auth_user.id
    action      VARCHAR(20) NOT NULL,               -- create | update | delete | publish
    model_name  VARCHAR(60) NOT NULL,
    object_id   BIGINT,
    champ       VARCHAR(60),
    old_value   TEXT,
    new_value   TEXT,
    ip_address  INET,
    user_agent  TEXT,
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_audit_model ON audit_trail (model_name, object_id);

-- 7.3 Configuration paiements mobile
CREATE TABLE config_paiement (
    id                      BIGSERIAL   PRIMARY KEY,
    wave_merchant_id        VARCHAR(80),
    wave_secret_key         TEXT,                   -- chiffré en base
    wave_webhook_secret     TEXT,
    orange_money_api_key    TEXT,
    orange_money_merchant   VARCHAR(80),
    orange_money_secret     TEXT,
    session_ttl_minutes     SMALLINT    NOT NULL DEFAULT 15,
    updated_at              TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- =============================================================================
--  BLOC 8 — INDEXES SUPPLÉMENTAIRES
-- =============================================================================

CREATE INDEX idx_document_filiere  ON document  (filiere_id, valide, created_at DESC);
CREATE INDEX idx_document_type     ON document  (type_id, valide);
CREATE INDEX idx_note_etudiant     ON note       (etudiant_id, semestre_id, publiee);
CREATE INDEX idx_presence_etudiant ON presence   (etudiant_id, seance_id);
CREATE INDEX idx_seance_date       ON seance     (date, heure_debut);
CREATE INDEX idx_paiement_statut   ON paiement   (statut, created_at DESC);
CREATE INDEX idx_demande_statut    ON demande_inscription (statut, created_at DESC);
CREATE INDEX idx_etudiant_filiere  ON etudiant   (filiere_id, statut_inscription);

-- =============================================================================
--  BLOC 9 — DONNÉES INITIALES
-- =============================================================================

INSERT INTO annee_academique (label, active, date_debut, date_fin) VALUES
    ('2024-2025', FALSE, '2024-10-01', '2025-07-31'),
    ('2025-2026', TRUE,  '2025-10-01', '2026-07-31');

INSERT INTO filiere (nom, slug, couleur_hex) VALUES
    ('Digitalisation des Services',         'digitalisation-services',      '#2563EB'),
    ('Finance & Comptabilité',              'finance-comptabilite',         '#16A34A'),
    ('Management des Organisations',        'management-organisations',     '#7C3AED'),
    ('Commerce & Marketing',                'commerce-marketing',           '#D97706'),
    ('Ressources Humaines',                 'ressources-humaines',          '#DC2626'),
    ('Informatique de Gestion',             'informatique-gestion',         '#0891B2');

-- =============================================================================
--  FIN DU SCHÉMA
-- =============================================================================

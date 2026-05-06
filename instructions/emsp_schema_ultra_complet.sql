-- ============================================================================
-- EMSP SITE PYTHON - SCHEMA SQL ULTRA COMPLET
-- Cible: PostgreSQL 15+
-- Source: modeles Django reels du projet (apps core, bibliotheque, administration)
-- Note: ce schema inclut aussi les tables Django standards (auth, admin, session).
-- ============================================================================

BEGIN;

-- ============================================================================
-- 0) Nettoyage (ordre inverse des dependances)
-- ============================================================================

DROP TABLE IF EXISTS django_session CASCADE;
DROP TABLE IF EXISTS django_admin_log CASCADE;
DROP TABLE IF EXISTS auth_user_user_permissions CASCADE;
DROP TABLE IF EXISTS auth_user_groups CASCADE;
DROP TABLE IF EXISTS auth_group_permissions CASCADE;
DROP TABLE IF EXISTS auth_permission CASCADE;
DROP TABLE IF EXISTS auth_group CASCADE;
DROP TABLE IF EXISTS django_content_type CASCADE;
DROP TABLE IF EXISTS django_migrations CASCADE;

DROP TABLE IF EXISTS administration_inscriptiontransport CASCADE;
DROP TABLE IF EXISTS administration_notebulletin CASCADE;
DROP TABLE IF EXISTS administration_bulletin CASCADE;
DROP TABLE IF EXISTS administration_etudiantprofile CASCADE;
DROP TABLE IF EXISTS administration_professeur_matieres CASCADE;
DROP TABLE IF EXISTS administration_professeur CASCADE;
DROP TABLE IF EXISTS administration_creneauabsence CASCADE;
DROP TABLE IF EXISTS administration_cartransport CASCADE;

DROP TABLE IF EXISTS bibliotheque_rechercherecente CASCADE;
DROP TABLE IF EXISTS bibliotheque_commentaire CASCADE;
DROP TABLE IF EXISTS bibliotheque_favori CASCADE;
DROP TABLE IF EXISTS bibliotheque_telechargement CASCADE;
DROP TABLE IF EXISTS bibliotheque_document CASCADE;
DROP TABLE IF EXISTS bibliotheque_matiere CASCADE;
DROP TABLE IF EXISTS bibliotheque_typedocument CASCADE;
DROP TABLE IF EXISTS bibliotheque_anneeacademique CASCADE;
DROP TABLE IF EXISTS bibliotheque_semestre CASCADE;
DROP TABLE IF EXISTS bibliotheque_licence CASCADE;
DROP TABLE IF EXISTS bibliotheque_filiere CASCADE;

DROP TABLE IF EXISTS core_slidecarousel CASCADE;
DROP TABLE IF EXISTS auth_user CASCADE;

-- ============================================================================
-- 1) Tables Django standards
-- ============================================================================

CREATE TABLE django_migrations (
    id                  BIGSERIAL PRIMARY KEY,
    app                 VARCHAR(255) NOT NULL,
    name                VARCHAR(255) NOT NULL,
    applied             TIMESTAMPTZ NOT NULL
);

CREATE TABLE django_content_type (
    id                  SERIAL PRIMARY KEY,
    app_label           VARCHAR(100) NOT NULL,
    model               VARCHAR(100) NOT NULL,
    UNIQUE (app_label, model)
);

CREATE TABLE auth_permission (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(255) NOT NULL,
    content_type_id     INTEGER NOT NULL REFERENCES django_content_type(id) ON DELETE CASCADE,
    codename            VARCHAR(100) NOT NULL,
    UNIQUE (content_type_id, codename)
);

CREATE TABLE auth_group (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(150) NOT NULL UNIQUE
);

CREATE TABLE auth_group_permissions (
    id                  BIGSERIAL PRIMARY KEY,
    group_id            INTEGER NOT NULL REFERENCES auth_group(id) ON DELETE CASCADE,
    permission_id       INTEGER NOT NULL REFERENCES auth_permission(id) ON DELETE CASCADE,
    UNIQUE (group_id, permission_id)
);

CREATE TABLE auth_user (
    id                  SERIAL PRIMARY KEY,
    password            VARCHAR(128) NOT NULL,
    last_login          TIMESTAMPTZ NULL,
    is_superuser        BOOLEAN NOT NULL DEFAULT FALSE,
    username            VARCHAR(150) NOT NULL UNIQUE,
    first_name          VARCHAR(150) NOT NULL DEFAULT '',
    last_name           VARCHAR(150) NOT NULL DEFAULT '',
    email               VARCHAR(254) NOT NULL DEFAULT '',
    is_staff            BOOLEAN NOT NULL DEFAULT FALSE,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE auth_user_groups (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    group_id            INTEGER NOT NULL REFERENCES auth_group(id) ON DELETE CASCADE,
    UNIQUE (user_id, group_id)
);

CREATE TABLE auth_user_user_permissions (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    permission_id       INTEGER NOT NULL REFERENCES auth_permission(id) ON DELETE CASCADE,
    UNIQUE (user_id, permission_id)
);

CREATE TABLE django_admin_log (
    id                  BIGSERIAL PRIMARY KEY,
    action_time         TIMESTAMPTZ NOT NULL,
    object_id           TEXT NULL,
    object_repr         VARCHAR(200) NOT NULL,
    action_flag         SMALLINT NOT NULL,
    change_message      TEXT NOT NULL,
    content_type_id     INTEGER NULL REFERENCES django_content_type(id) ON DELETE SET NULL,
    user_id             INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE
);

CREATE TABLE django_session (
    session_key         VARCHAR(40) PRIMARY KEY,
    session_data        TEXT NOT NULL,
    expire_date         TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_django_session_expire_date ON django_session(expire_date);

-- ============================================================================
-- 2) App core
-- ============================================================================

CREATE TABLE core_slidecarousel (
    id                  BIGSERIAL PRIMARY KEY,
    titre               VARCHAR(150) NOT NULL,
    image               VARCHAR(100) NOT NULL,
    ordre               INTEGER NOT NULL DEFAULT 0,
    actif               BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX idx_core_slidecarousel_ordre_id ON core_slidecarousel(ordre, id);

-- ============================================================================
-- 3) App bibliotheque
-- ============================================================================

CREATE TABLE bibliotheque_filiere (
    id                  BIGSERIAL PRIMARY KEY,
    nom                 VARCHAR(120) NOT NULL UNIQUE,
    slug                VARCHAR(140) NOT NULL UNIQUE,
    active              BOOLEAN NOT NULL DEFAULT TRUE,
    cycle               VARCHAR(20) NOT NULL DEFAULT 'licence_pro',
    CONSTRAINT chk_bibliotheque_filiere_cycle
        CHECK (cycle IN ('licence_pro', 'master_pro'))
);
CREATE INDEX idx_bibliotheque_filiere_nom ON bibliotheque_filiere(nom);

CREATE TABLE bibliotheque_licence (
    id                  BIGSERIAL PRIMARY KEY,
    code                VARCHAR(20) NOT NULL UNIQUE,
    ordre               SMALLINT NOT NULL DEFAULT 0
);
CREATE INDEX idx_bibliotheque_licence_ordre_code ON bibliotheque_licence(ordre, code);

CREATE TABLE bibliotheque_semestre (
    id                  BIGSERIAL PRIMARY KEY,
    code                VARCHAR(5) NOT NULL UNIQUE,
    ordre               SMALLINT NOT NULL DEFAULT 0
);
CREATE INDEX idx_bibliotheque_semestre_ordre_code ON bibliotheque_semestre(ordre, code);

CREATE TABLE bibliotheque_anneeacademique (
    id                  BIGSERIAL PRIMARY KEY,
    libelle             VARCHAR(20) NOT NULL UNIQUE,
    active              BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX idx_bibliotheque_anneeacademique_libelle_desc ON bibliotheque_anneeacademique(libelle DESC);

CREATE TABLE bibliotheque_typedocument (
    id                  BIGSERIAL PRIMARY KEY,
    code                VARCHAR(20) NOT NULL UNIQUE,
    libelle             VARCHAR(80) NOT NULL,
    couleur             VARCHAR(20) NOT NULL DEFAULT 'primary'
);

CREATE TABLE bibliotheque_matiere (
    id                  BIGSERIAL PRIMARY KEY,
    nom                 VARCHAR(120) NOT NULL,
    active              BOOLEAN NOT NULL DEFAULT TRUE,
    filiere_id          BIGINT NOT NULL REFERENCES bibliotheque_filiere(id) ON DELETE CASCADE,
    UNIQUE (nom, filiere_id)
);
CREATE INDEX idx_bibliotheque_matiere_nom ON bibliotheque_matiere(nom);
CREATE INDEX idx_bibliotheque_matiere_filiere ON bibliotheque_matiere(filiere_id);

CREATE TABLE bibliotheque_document (
    id                      BIGSERIAL PRIMARY KEY,
    titre                   VARCHAR(220) NOT NULL,
    description             TEXT NOT NULL,
    fichier                 VARCHAR(100) NOT NULL,
    reserve_auth            BOOLEAN NOT NULL DEFAULT TRUE,
    valide                  BOOLEAN NOT NULL DEFAULT FALSE,
    motif_refus             VARCHAR(255) NOT NULL DEFAULT '',
    telechargements_count   INTEGER NOT NULL DEFAULT 0,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    annee_academique_id     BIGINT NOT NULL REFERENCES bibliotheque_anneeacademique(id) ON DELETE RESTRICT,
    contributeur_id         INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    filiere_id              BIGINT NOT NULL REFERENCES bibliotheque_filiere(id) ON DELETE RESTRICT,
    licence_id              BIGINT NOT NULL REFERENCES bibliotheque_licence(id) ON DELETE RESTRICT,
    matiere_id              BIGINT NOT NULL REFERENCES bibliotheque_matiere(id) ON DELETE RESTRICT,
    semestre_id             BIGINT NOT NULL REFERENCES bibliotheque_semestre(id) ON DELETE RESTRICT,
    type_document_id        BIGINT NOT NULL REFERENCES bibliotheque_typedocument(id) ON DELETE RESTRICT
);
CREATE INDEX idx_bibliotheque_document_created_at_desc ON bibliotheque_document(created_at DESC);
CREATE INDEX idx_bibliotheque_document_valide ON bibliotheque_document(valide);
CREATE INDEX idx_bibliotheque_document_filiere ON bibliotheque_document(filiere_id);
CREATE INDEX idx_bibliotheque_document_matiere ON bibliotheque_document(matiere_id);

CREATE TABLE bibliotheque_telechargement (
    id                  BIGSERIAL PRIMARY KEY,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    document_id         BIGINT NOT NULL REFERENCES bibliotheque_document(id) ON DELETE CASCADE,
    utilisateur_id      INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE
);
CREATE INDEX idx_bibliotheque_telechargement_created_at_desc ON bibliotheque_telechargement(created_at DESC);
CREATE INDEX idx_bibliotheque_telechargement_user_doc ON bibliotheque_telechargement(utilisateur_id, document_id);

CREATE TABLE bibliotheque_favori (
    id                  BIGSERIAL PRIMARY KEY,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    document_id         BIGINT NOT NULL REFERENCES bibliotheque_document(id) ON DELETE CASCADE,
    utilisateur_id      INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    UNIQUE (utilisateur_id, document_id)
);
CREATE INDEX idx_bibliotheque_favori_created_at_desc ON bibliotheque_favori(created_at DESC);

CREATE TABLE bibliotheque_commentaire (
    id                  BIGSERIAL PRIMARY KEY,
    contenu             TEXT NOT NULL,
    likes               INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    document_id         BIGINT NOT NULL REFERENCES bibliotheque_document(id) ON DELETE CASCADE,
    parent_id           BIGINT NULL REFERENCES bibliotheque_commentaire(id) ON DELETE CASCADE,
    utilisateur_id      INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE
);
CREATE INDEX idx_bibliotheque_commentaire_created_at_desc ON bibliotheque_commentaire(created_at DESC);
CREATE INDEX idx_bibliotheque_commentaire_doc ON bibliotheque_commentaire(document_id);
CREATE INDEX idx_bibliotheque_commentaire_parent ON bibliotheque_commentaire(parent_id);

CREATE TABLE bibliotheque_rechercherecente (
    id                  BIGSERIAL PRIMARY KEY,
    requete             VARCHAR(120) NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    utilisateur_id      INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE
);
CREATE INDEX idx_bibliotheque_rechercherecente_created_at_desc ON bibliotheque_rechercherecente(created_at DESC);
CREATE INDEX idx_bibliotheque_rechercherecente_user ON bibliotheque_rechercherecente(utilisateur_id);

-- ============================================================================
-- 4) App administration
-- ============================================================================

CREATE TABLE administration_professeur (
    id                  BIGSERIAL PRIMARY KEY,
    nom_complet         VARCHAR(150) NOT NULL,
    email               VARCHAR(254) NOT NULL UNIQUE,
    telephone           VARCHAR(30) NOT NULL DEFAULT '',
    actif               BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_administration_professeur_nom ON administration_professeur(nom_complet);

CREATE TABLE administration_professeur_matieres (
    id                  BIGSERIAL PRIMARY KEY,
    professeur_id       BIGINT NOT NULL REFERENCES administration_professeur(id) ON DELETE CASCADE,
    matiere_id          BIGINT NOT NULL REFERENCES bibliotheque_matiere(id) ON DELETE CASCADE,
    UNIQUE (professeur_id, matiere_id)
);
CREATE INDEX idx_administration_professeur_matieres_matiere ON administration_professeur_matieres(matiere_id);

CREATE TABLE administration_creneauabsence (
    id                  BIGSERIAL PRIMARY KEY,
    libelle             VARCHAR(120) NOT NULL,
    heure_debut         TIME NOT NULL,
    heure_fin           TIME NOT NULL,
    ordre               SMALLINT NOT NULL DEFAULT 0,
    actif               BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (heure_debut, heure_fin)
);
CREATE INDEX idx_administration_creneauabsence_ordre_debut ON administration_creneauabsence(ordre, heure_debut);

CREATE TABLE administration_etudiantprofile (
    id                  BIGSERIAL PRIMARY KEY,
    matricule           VARCHAR(40) NOT NULL UNIQUE,
    telephone           VARCHAR(30) NOT NULL DEFAULT '',
    actif               BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    filiere_id          BIGINT NULL REFERENCES bibliotheque_filiere(id) ON DELETE SET NULL,
    licence_id          BIGINT NULL REFERENCES bibliotheque_licence(id) ON DELETE SET NULL,
    semestre_id         BIGINT NULL REFERENCES bibliotheque_semestre(id) ON DELETE SET NULL,
    utilisateur_id      INTEGER NOT NULL UNIQUE REFERENCES auth_user(id) ON DELETE CASCADE
);
CREATE INDEX idx_administration_etudiantprofile_matricule ON administration_etudiantprofile(matricule);
CREATE INDEX idx_administration_etudiantprofile_filiere ON administration_etudiantprofile(filiere_id);
CREATE INDEX idx_administration_etudiantprofile_licence ON administration_etudiantprofile(licence_id);
CREATE INDEX idx_administration_etudiantprofile_semestre ON administration_etudiantprofile(semestre_id);

CREATE TABLE administration_bulletin (
    id                      BIGSERIAL PRIMARY KEY,
    moyenne                 NUMERIC(5,2) NOT NULL DEFAULT 0.00,
    decision                VARCHAR(20) NOT NULL DEFAULT 'ajourne',
    appreciation            VARCHAR(255) NOT NULL DEFAULT '',
    publie                  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    annee_academique_id     BIGINT NOT NULL REFERENCES bibliotheque_anneeacademique(id) ON DELETE RESTRICT,
    etudiant_id             BIGINT NOT NULL REFERENCES administration_etudiantprofile(id) ON DELETE CASCADE,
    semestre_id             BIGINT NOT NULL REFERENCES bibliotheque_semestre(id) ON DELETE RESTRICT,
    CONSTRAINT chk_administration_bulletin_decision
        CHECK (decision IN ('admis', 'rattrapage', 'ajourne')),
    UNIQUE (etudiant_id, annee_academique_id, semestre_id)
);
CREATE INDEX idx_administration_bulletin_annee_semestre ON administration_bulletin(annee_academique_id, semestre_id);
CREATE INDEX idx_administration_bulletin_etudiant ON administration_bulletin(etudiant_id);

CREATE TABLE administration_notebulletin (
    id                  BIGSERIAL PRIMARY KEY,
    coefficient         SMALLINT NOT NULL DEFAULT 1,
    note_cc             NUMERIC(4,2) NOT NULL DEFAULT 0.00,
    note_examen         NUMERIC(4,2) NOT NULL DEFAULT 0.00,
    note_finale         NUMERIC(4,2) NOT NULL DEFAULT 0.00,
    observation         VARCHAR(255) NOT NULL DEFAULT '',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    bulletin_id         BIGINT NOT NULL REFERENCES administration_bulletin(id) ON DELETE CASCADE,
    matiere_id          BIGINT NOT NULL REFERENCES bibliotheque_matiere(id) ON DELETE RESTRICT,
    professeur_id       BIGINT NULL REFERENCES administration_professeur(id) ON DELETE SET NULL,
    UNIQUE (bulletin_id, matiere_id)
);
CREATE INDEX idx_administration_notebulletin_matiere ON administration_notebulletin(matiere_id);
CREATE INDEX idx_administration_notebulletin_professeur ON administration_notebulletin(professeur_id);

CREATE TABLE administration_cartransport (
    id                      BIGSERIAL PRIMARY KEY,
    nom                     VARCHAR(120) NOT NULL,
    immatriculation         VARCHAR(40) NOT NULL UNIQUE,
    axe_principal           VARCHAR(20) NOT NULL DEFAULT 'cocody',
    chauffeur               VARCHAR(120) NOT NULL DEFAULT '',
    telephone_chauffeur     VARCHAR(30) NOT NULL DEFAULT '',
    capacite                SMALLINT NOT NULL DEFAULT 20,
    actif                   BOOLEAN NOT NULL DEFAULT TRUE,
    observations            VARCHAR(255) NOT NULL DEFAULT '',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_administration_cartransport_axe
        CHECK (axe_principal IN ('cocody', 'yopougon', 'bingerville', 'abobo', 'bassam'))
);
CREATE INDEX idx_administration_cartransport_nom_immat ON administration_cartransport(nom, immatriculation);
CREATE INDEX idx_administration_cartransport_axe ON administration_cartransport(axe_principal);

CREATE TABLE administration_inscriptiontransport (
    id                  BIGSERIAL PRIMARY KEY,
    axe                 VARCHAR(20) NOT NULL,
    statut              VARCHAR(20) NOT NULL DEFAULT 'en_attente',
    date_inscription    DATE NOT NULL DEFAULT CURRENT_DATE,
    commentaire         VARCHAR(255) NOT NULL DEFAULT '',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    car_id              BIGINT NULL REFERENCES administration_cartransport(id) ON DELETE SET NULL,
    etudiant_id         BIGINT NOT NULL REFERENCES administration_etudiantprofile(id) ON DELETE CASCADE,
    CONSTRAINT chk_administration_inscriptiontransport_axe
        CHECK (axe IN ('cocody', 'yopougon', 'bingerville', 'abobo', 'bassam')),
    CONSTRAINT chk_administration_inscriptiontransport_statut
        CHECK (statut IN ('en_attente', 'validee', 'suspendue')),
    UNIQUE (etudiant_id, axe)
);
CREATE INDEX idx_administration_inscriptiontransport_created_at_desc ON administration_inscriptiontransport(created_at DESC);
CREATE INDEX idx_administration_inscriptiontransport_axe_statut ON administration_inscriptiontransport(axe, statut);

-- ============================================================================
-- 5) Donnees de reference (issues des migrations/projet)
-- ============================================================================

-- Filieres
INSERT INTO bibliotheque_filiere (nom, slug, active, cycle) VALUES
('LOGISTIQUE ET NUMERIQUE', 'logistique-et-numerique', TRUE, 'licence_pro'),
('FINANCE DIGITALE', 'finance-digitale', TRUE, 'licence_pro'),
('MARKETING DIGITAL', 'marketing-digital', TRUE, 'licence_pro'),
('DIGITALISATION DES SERVICES', 'digitalisation-des-services', TRUE, 'licence_pro'),
('GESTION DES ACTIVITES REGLEMENTEES', 'gestion-des-activites-reglementees', TRUE, 'licence_pro'),
('LOGISTIQUE ET E-COMMERCE', 'logistique-et-e-commerce', TRUE, 'master_pro'),
('FINANCE ET MANAGEMENT DES ENTREPRISES DU RISQUE', 'finance-et-management-des-entreprises-du-risque', TRUE, 'master_pro'),
('MARKETING DIGITAL ET E-BUSINESS', 'marketing-digital-et-e-business', TRUE, 'master_pro'),
('TRANSFORMATION NUMERIQUE DES ORGANISATIONS', 'transformation-numerique-des-organisations', TRUE, 'master_pro'),
('MASTERE SPECIALISE EN REGULATION DU NUMERIQUE', 'mastere-specialise-en-regulation-du-numerique', TRUE, 'master_pro')
ON CONFLICT (nom) DO NOTHING;

-- Annees academiques
INSERT INTO bibliotheque_anneeacademique (libelle, active) VALUES
('2023-2024', FALSE),
('2024-2025', FALSE),
('2025-2026', FALSE),
('2026-2027', TRUE)
ON CONFLICT (libelle) DO NOTHING;

-- Semestres
INSERT INTO bibliotheque_semestre (code, ordre) VALUES
('S1', 1), ('S2', 2), ('S3', 3), ('S4', 4),
('S5', 5), ('S6', 6), ('S7', 7), ('S8', 8)
ON CONFLICT (code) DO NOTHING;

-- Licences / niveaux
INSERT INTO bibliotheque_licence (code, ordre) VALUES
('L1', 1), ('L2', 2), ('L3', 3), ('M1', 4), ('M2', 5)
ON CONFLICT (code) DO NOTHING;

-- Creneaux absences
INSERT INTO administration_creneauabsence (libelle, heure_debut, heure_fin, ordre, actif) VALUES
('Cours du matin', '08:00', '10:00', 1, TRUE),
('Cours milieu de matinee', '10:15', '12:15', 2, TRUE),
('Cours apres-midi 1', '13:30', '15:30', 3, TRUE),
('Cours apres-midi 2', '15:45', '17:45', 4, TRUE)
ON CONFLICT (heure_debut, heure_fin) DO NOTHING;

-- Type documents exemples
INSERT INTO bibliotheque_typedocument (code, libelle, couleur) VALUES
('COURS', 'Cours', 'primary'),
('TD', 'Travaux diriges', 'info'),
('EXAM', 'Examen', 'danger'),
('CORR', 'Correction', 'success')
ON CONFLICT (code) DO NOTHING;

COMMIT;

-- ============================================================================
-- Fin de schema
-- ============================================================================

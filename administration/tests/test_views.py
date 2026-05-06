from datetime import time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from administration.models import (
    Bulletin,
    CarTransport,
    CreneauAbsence,
    EtudiantProfile,
    Evenement,
    InscriptionTransport,
    Justification,
    NoteBulletin,
    Paiement,
    Presence,
    Professeur,
    Seance,
    Scolarite,
)
from bibliotheque.models import AnneeAcademique, Document, Filiere, Licence, Matiere, Semestre, TypeDocument
from inscription.models import Dossier, Inscription


class AdministrationViewsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin-pass-123",
        )
        self.client.force_login(self.admin_user)
        self.filiere, _ = Filiere.objects.get_or_create(
            nom="LOGISTIQUE ET NUMERIQUE",
            defaults={"cycle": "licence_pro", "active": True},
        )
        self.licence, _ = Licence.objects.get_or_create(code="L2", defaults={"ordre": 2})
        self.semestre, _ = Semestre.objects.get_or_create(code="S3", defaults={"ordre": 3})

    def test_create_evenement_from_admin_page(self):
        response = self.client.post(
            reverse("administration:evenements"),
            data={
                "action": "create_evenement",
                "titre": "Conference Test",
                "type": "conference",
                "date": "2026-05-20",
                "heure": "09:30",
                "lieu": "Amphi A",
                "public_cible": "Tous",
                "description": "Session academique",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Evenement.objects.filter(titre="Conference Test").exists())

    def test_create_paiement_is_pending_verification(self):
        user = get_user_model().objects.create_user(
            username="etu_payment",
            email="etu.payment@example.com",
            password="etu-pass-123",
            first_name="Pay",
            last_name="Student",
        )
        etudiant = EtudiantProfile.objects.create(
            utilisateur=user,
            matricule="26FPAYM",
            filiere=self.filiere,
            licence=self.licence,
            semestre=self.semestre,
            actif=True,
        )
        Scolarite.objects.create(etudiant=etudiant, total_du=Decimal("950000.00"))

        response = self.client.post(
            reverse("administration:paiements"),
            data={
                "action": "create_paiement",
                "etudiant": etudiant.id,
                "montant": "150000",
                "moyen": "wave",
                "date": "2026-05-10",
                "reference": "WAVE-TEST-001",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        paiement = Paiement.objects.get(reference="WAVE-TEST-001")
        self.assertEqual(paiement.statut, Paiement.STATUT_EN_ATTENTE)

    def test_bibliotheque_moderation_validate_and_refuse(self):
        type_document, _ = TypeDocument.objects.get_or_create(code="TD", defaults={"libelle": "TD"})
        matiere = Matiere.objects.create(nom="Moderation", filiere=self.filiere, active=True)
        document = Document.objects.create(
            titre="Document Test",
            description="A moderer",
            fichier=SimpleUploadedFile("doc.pdf", b"fake-pdf"),
            filiere=self.filiere,
            licence=self.licence,
            semestre=self.semestre,
            matiere=matiere,
            type_document=type_document,
            annee_academique=AnneeAcademique.objects.create(libelle="2040-2041", active=True),
            contributeur=self.admin_user,
            valide=False,
        )

        self.client.post(
            reverse("administration:bibliotheque_moderation"),
            data={"action": "validate_document", "object_id": document.id},
        )
        document.refresh_from_db()
        self.assertTrue(document.valide)

        self.client.post(
            reverse("administration:bibliotheque_moderation"),
            data={"action": "refuse_document", "object_id": document.id, "motif_refus": "Fichier illisible"},
        )
        document.refresh_from_db()
        self.assertFalse(document.valide)
        self.assertEqual(document.motif_refus, "Fichier illisible")

    def test_global_search_redirects_to_student_detail(self):
        user = get_user_model().objects.create_user(
            username="etu_search_global",
            email="search.global@example.com",
            password="etu-pass-123",
            first_name="Global",
            last_name="Search",
        )
        etudiant = EtudiantProfile.objects.create(
            utilisateur=user,
            matricule="26FSRHM",
            filiere=self.filiere,
            licence=self.licence,
            semestre=self.semestre,
            actif=True,
        )

        response = self.client.get(reverse("administration:global_search"), {"q": "26FSRHM"})
        self.assertRedirects(response, reverse("administration:etudiant_detail", args=[etudiant.id]))

    def test_create_etudiant_from_admin_list(self):
        response = self.client.post(
            reverse("administration:etudiants_liste"),
            data={
                "action": "create_etudiant",
                "prenom": "Aminata",
                "nom": "Kone",
                "email": "aminata.kone@example.com",
                "matricule": "EMSP-2026-0042",
                "telephone": "+2250700000000",
                "filiere": self.filiere.id,
                "licence": self.licence.id,
                "semestre": self.semestre.id,
                "actif": "True",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(EtudiantProfile.objects.filter(matricule="EMSP-2026-0042").exists())

    def test_create_etudiant_without_matricule_generates_one(self):
        response = self.client.post(
            reverse("administration:etudiants_liste"),
            data={
                "action": "create_etudiant",
                "prenom": "Fatou",
                "nom": "NGuessan",
                "email": "fatou.nguessan@example.com",
                "matricule": "",
                "telephone": "+2250100000000",
                "filiere": self.filiere.id,
                "licence": self.licence.id,
                "semestre": self.semestre.id,
                "actif": "True",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        etudiant = EtudiantProfile.objects.get(utilisateur__email="fatou.nguessan@example.com")
        self.assertRegex(etudiant.matricule, r"^26F[A-Z]{3}M$")

    def test_etudiants_list_filters_by_filiere_licence_matricule_and_text(self):
        etudiant_user = get_user_model().objects.create_user(
            username="etu_filter",
            email="filter@example.com",
            password="etu-pass-123",
            first_name="Filter",
            last_name="Visible",
        )
        etudiant = EtudiantProfile.objects.create(
            utilisateur=etudiant_user,
            matricule="26FZZZM",
            filiere=self.filiere,
            licence=self.licence,
            semestre=self.semestre,
            actif=True,
        )
        other_filiere = Filiere.objects.create(nom="FILIERE CACHEE", active=True)
        other_user = get_user_model().objects.create_user(
            username="etu_hidden",
            email="hidden@example.com",
            password="etu-pass-123",
            first_name="Hidden",
            last_name="Student",
        )
        EtudiantProfile.objects.create(
            utilisateur=other_user,
            matricule="26FYYYM",
            filiere=other_filiere,
            licence=self.licence,
            semestre=self.semestre,
            actif=True,
        )

        response = self.client.get(
            reverse("administration:etudiants_liste"),
            {
                "filiere": self.filiere.id,
                "licence": self.licence.id,
                "matricule": "ZZZ",
                "q": "Visible",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, etudiant.matricule)
        self.assertNotContains(response, "26FYYYM")

    def test_bulletin_button_uses_student_notes_url(self):
        etudiant_user = get_user_model().objects.create_user(
            username="etu_bulletin_button",
            email="bulletin.button@example.com",
            password="etu-pass-123",
            first_name="Bulletin",
            last_name="Button",
        )
        etudiant = EtudiantProfile.objects.create(
            utilisateur=etudiant_user,
            matricule="26FBBBM",
            filiere=self.filiere,
            licence=self.licence,
            semestre=self.semestre,
            actif=True,
        )

        response = self.client.get(reverse("administration:etudiants_liste"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'{reverse("administration:notes")}?matricule={etudiant.matricule}')

    def test_create_professeur_from_dedicated_page(self):
        matiere = Matiere.objects.create(nom="Reseaux", filiere=self.filiere, active=True)
        response = self.client.post(
            reverse("administration:professeurs"),
            data={
                "action": "create_professeur",
                "nom_complet": "Mamadou Toure",
                "email": "mamadou.toure@example.com",
                "telephone": "+2250102030405",
                "actif": "True",
                "matieres": [matiere.id],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        professeur = Professeur.objects.get(email="mamadou.toure@example.com")
        self.assertTrue(professeur.matieres.filter(pk=matiere.pk).exists())

    def test_search_professeur_by_name_email_or_phone(self):
        Professeur.objects.create(
            nom_complet="Mariam Coulibaly",
            email="mariam.coulibaly@example.com",
            telephone="+2250505050505",
            actif=True,
        )
        Professeur.objects.create(
            nom_complet="Jean Cache",
            email="jean.cache@example.com",
            telephone="+2250101010101",
            actif=True,
        )

        response = self.client.get(reverse("administration:professeurs"), {"q": "050505"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mariam Coulibaly")
        self.assertNotContains(response, "Jean Cache")

    def test_update_professeur_and_assigned_matieres(self):
        matiere_initiale = Matiere.objects.create(nom="Marketing digital", filiere=self.filiere, active=True)
        matiere_finale = Matiere.objects.create(nom="Finance digitale", filiere=self.filiere, active=True)
        professeur = Professeur.objects.create(
            nom_complet="Ancien Nom",
            email="ancien.prof@example.com",
            telephone="+2250000000000",
            actif=True,
        )
        professeur.matieres.add(matiere_initiale)

        response = self.client.post(
            reverse("administration:professeurs"),
            data={
                "action": "update_professeur",
                "object_id": professeur.id,
                "nom_complet": "Nouveau Nom",
                "email": "nouveau.prof@example.com",
                "telephone": "+2250707070707",
                "actif": "False",
                "matieres": [matiere_finale.id],
            },
            follow=True,
        )

        professeur.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(professeur.nom_complet, "Nouveau Nom")
        self.assertEqual(professeur.email, "nouveau.prof@example.com")
        self.assertEqual(professeur.telephone, "+2250707070707")
        self.assertFalse(professeur.actif)
        self.assertFalse(professeur.matieres.filter(pk=matiere_initiale.pk).exists())
        self.assertTrue(professeur.matieres.filter(pk=matiere_finale.pk).exists())

    def test_delete_professeur(self):
        professeur = Professeur.objects.create(
            nom_complet="Professeur A Supprimer",
            email="delete.prof@example.com",
            telephone="+2250909090909",
            actif=True,
        )

        response = self.client.post(
            reverse("administration:professeurs"),
            data={
                "action": "delete_professeur",
                "object_id": professeur.id,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Professeur.objects.filter(pk=professeur.pk).exists())

    def test_etudiant_detail_page_loads(self):
        etudiant_user = get_user_model().objects.create_user(
            username="etu1",
            email="etu1@example.com",
            password="etu-pass-123",
            first_name="Etu",
            last_name="Demo",
        )
        etudiant = EtudiantProfile.objects.create(
            utilisateur=etudiant_user,
            matricule="EMSP-2026-0101",
            filiere=self.filiere,
            licence=self.licence,
            semestre=self.semestre,
            actif=True,
        )
        response = self.client.get(reverse("administration:etudiant_detail", args=[etudiant.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "EMSP-2026-0101")

    def test_create_transport_car_from_financial_section(self):
        response = self.client.post(
            reverse("administration:transport_cars"),
            data={
                "action": "create_car",
                "nom": "Car Abidjan Nord",
                "immatriculation": "ABJ-4567-CI",
                "axe_principal": "cocody",
                "chauffeur": "Kouassi Jean",
                "telephone_chauffeur": "+2250707007007",
                "capacite": 32,
                "actif": "True",
                "observations": "Circuit Yopougon - EMSP",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(CarTransport.objects.filter(immatriculation="ABJ-4567-CI").exists())

    def test_create_transport_subscription_for_student(self):
        etudiant_user = get_user_model().objects.create_user(
            username="etu_transport",
            email="etu.transport@example.com",
            password="etu-pass-123",
            first_name="Etu",
            last_name="Transport",
        )
        etudiant = EtudiantProfile.objects.create(
            utilisateur=etudiant_user,
            matricule="EMSP-2026-0999",
            filiere=self.filiere,
            licence=self.licence,
            semestre=self.semestre,
            actif=True,
        )
        car = CarTransport.objects.create(
            nom="Car Axe Cocody",
            immatriculation="ABJ-9999-CI",
            axe_principal="cocody",
            capacite=30,
            actif=True,
        )

        response = self.client.post(
            reverse("administration:transport_cars"),
            data={
                "action": "create_inscription_transport",
                "etudiant": etudiant.id,
                "axe": "cocody",
                "car": car.id,
                "statut": "validee",
                "commentaire": "Inscription test",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(InscriptionTransport.objects.filter(etudiant=etudiant, axe="cocody").exists())

    def test_bulletin_pdf_by_matricule(self):
        etudiant_user = get_user_model().objects.create_user(
            username="etu_pdf",
            email="etu.pdf@example.com",
            password="etu-pass-123",
            first_name="Etu",
            last_name="Pdf",
        )
        etudiant = EtudiantProfile.objects.create(
            utilisateur=etudiant_user,
            matricule="EMSP-2026-8888",
            filiere=self.filiere,
            licence=self.licence,
            semestre=self.semestre,
            actif=True,
        )
        annee, _ = AnneeAcademique.objects.get_or_create(libelle="2031-2032", defaults={"active": True})
        bulletin = Bulletin.objects.create(etudiant=etudiant, annee_academique=annee, semestre=self.semestre)
        matiere = Matiere.objects.create(nom="Data Science Test", filiere=self.filiere, active=True)
        NoteBulletin.objects.create(
            bulletin=bulletin,
            matiere=matiere,
            coefficient=2,
            note_cc=12,
            note_examen=14,
        )

        response = self.client.get(reverse("administration:bulletin_pdf_matricule"), {"matricule": "EMSP-2026-8888"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_notes_page_filters_and_marks_matiere_completion(self):
        etudiant_user = get_user_model().objects.create_user(
            username="etu_notes_filter",
            email="etu.notes.filter@example.com",
            password="etu-pass-123",
            first_name="Etu",
            last_name="Notes",
        )
        etudiant = EtudiantProfile.objects.create(
            utilisateur=etudiant_user,
            matricule="26FNTEM",
            filiere=self.filiere,
            licence=self.licence,
            semestre=self.semestre,
            actif=True,
        )
        annee, _ = AnneeAcademique.objects.get_or_create(libelle="2032-2033", defaults={"active": True})
        bulletin = Bulletin.objects.create(etudiant=etudiant, annee_academique=annee, semestre=self.semestre)
        matiere_complete = Matiere.objects.create(nom="Architecture reseau", filiere=self.filiere, active=True)
        matiere_incomplete = Matiere.objects.create(nom="Securite applicative", filiere=self.filiere, active=True)
        NoteBulletin.objects.create(
            bulletin=bulletin,
            matiere=matiere_complete,
            coefficient=1,
            note_cc=13,
            note_examen=15,
        )

        response = self.client.get(
            reverse("administration:notes"),
            {
                "filiere": self.filiere.id,
                "licence": self.licence.id,
                "semestre": self.semestre.id,
                "annee_academique": annee.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Architecture reseau")
        self.assertContains(response, "Securite applicative")
        self.assertContains(response, '<span class="badge bg-label-success">Complet</span>', html=True)
        self.assertContains(response, '<span class="badge bg-label-danger">En attente</span>', html=True)
        self.assertContains(response, "Etu Notes")
        self.assertContains(response, etudiant.matricule)

    def test_notes_pdf_generator_prefills_matricule_from_query(self):
        response = self.client.get(reverse("administration:notes"), {"matricule": "26FPREM"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="26FPREM"')

    def test_notes_menu_badge_counts_incomplete_note_entries(self):
        etudiant_user = get_user_model().objects.create_user(
            username="etu_incomplete_note",
            email="etu.incomplete.note@example.com",
            password="etu-pass-123",
            first_name="Incomplete",
            last_name="Note",
        )
        etudiant = EtudiantProfile.objects.create(
            utilisateur=etudiant_user,
            matricule="26FINCM",
            filiere=self.filiere,
            licence=self.licence,
            semestre=self.semestre,
            actif=True,
        )
        annee, _ = AnneeAcademique.objects.get_or_create(libelle="2033-2034", defaults={"active": True})
        bulletin = Bulletin.objects.create(etudiant=etudiant, annee_academique=annee, semestre=self.semestre)
        matiere = Matiere.objects.create(nom="Projet tutoriel", filiere=self.filiere, active=True)
        NoteBulletin.objects.create(
            bulletin=bulletin,
            matiere=matiere,
            coefficient=1,
            note_cc=0,
            note_examen=12,
        )

        response = self.client.get(reverse("administration:notes"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<span class="badge bg-warning rounded-pill ms-auto">1</span>', html=True)

    def test_inscriptions_page_filters_dossiers_by_status_and_counts_pending(self):
        pending = Inscription.objects.create(
            prenom="Awa",
            nom="Pending",
            email="awa.pending@example.com",
            filiere=self.filiere,
            licence=self.licence,
            statut=Inscription.STATUT_EN_ATTENTE,
        )
        validated = Inscription.objects.create(
            prenom="Awa",
            nom="Validated",
            email="awa.validated@example.com",
            filiere=self.filiere,
            licence=self.licence,
            statut=Inscription.STATUT_VALIDEE,
        )
        Dossier.objects.create(inscription=pending, documents_fournis=4, documents_requis=6)
        Dossier.objects.create(inscription=validated, documents_fournis=6, documents_requis=6)

        response = self.client.get(reverse("administration:inscriptions"), {"statut": Inscription.STATUT_EN_ATTENTE})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Awa Pending")
        self.assertNotContains(response, "Awa Validated")
        self.assertContains(response, '<span class="badge bg-danger ms-1">1</span>', html=True)

    def test_validate_dossier_creates_student_account_and_profile(self):
        inscription = Inscription.objects.create(
            prenom="Nadia",
            nom="Kouame",
            email="nadia.kouame@example.com",
            telephone="+2250700001111",
            filiere=self.filiere,
            licence=self.licence,
            statut=Inscription.STATUT_EN_ATTENTE,
        )
        dossier = Dossier.objects.create(inscription=inscription, documents_fournis=6, documents_requis=6)

        response = self.client.post(
            reverse("administration:inscriptions"),
            data={"action": "validate_dossier", "object_id": dossier.id},
            follow=True,
        )

        inscription.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(inscription.statut, Inscription.STATUT_VALIDEE)
        self.assertTrue(get_user_model().objects.filter(email="nadia.kouame@example.com").exists())
        self.assertIsNotNone(inscription.etudiant_profile)
        self.assertEqual(inscription.etudiant_profile.filiere, self.filiere)
        self.assertRegex(inscription.etudiant_profile.matricule, r"^26F[A-Z]{3}M$")

    def test_refuse_dossier_updates_status(self):
        inscription = Inscription.objects.create(
            prenom="Refus",
            nom="Demo",
            email="refus.demo@example.com",
            filiere=self.filiere,
            licence=self.licence,
            statut=Inscription.STATUT_EN_ATTENTE,
        )
        dossier = Dossier.objects.create(inscription=inscription)

        response = self.client.post(
            reverse("administration:inscriptions"),
            data={"action": "refuse_dossier", "object_id": dossier.id},
            follow=True,
        )

        inscription.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(inscription.statut, Inscription.STATUT_REFUSEE)

    def test_export_filtered_inscriptions_as_csv(self):
        inscription = Inscription.objects.create(
            prenom="Export",
            nom="Demo",
            email="export.demo@example.com",
            telephone="+2250101010101",
            filiere=self.filiere,
            licence=self.licence,
            statut=Inscription.STATUT_EN_ATTENTE,
        )
        Dossier.objects.create(inscription=inscription, documents_fournis=3, documents_requis=6)

        response = self.client.get(
            reverse("administration:inscriptions"),
            {"statut": Inscription.STATUT_EN_ATTENTE, "export": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("dossiers_inscription.csv", response["Content-Disposition"])
        self.assertContains(response, "Export Demo")

    def test_dossier_detail_can_mark_incomplete_and_save_comment(self):
        inscription = Inscription.objects.create(
            prenom="Detail",
            nom="Demo",
            email="detail.demo@example.com",
            filiere=self.filiere,
            licence=self.licence,
            statut=Inscription.STATUT_EN_COURS,
        )
        dossier = Dossier.objects.create(inscription=inscription)

        response = self.client.post(
            reverse("administration:dossier_detail", args=[dossier.id]),
            data={
                "action": "mark_incomplete",
                "commentaire_interne": "Piece manquante",
            },
            follow=True,
        )

        dossier.refresh_from_db()
        inscription.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(dossier.commentaire_interne, "Piece manquante")
        self.assertEqual(inscription.statut, Inscription.STATUT_INCOMPLETE)

    def test_presences_page_loads_students_from_filters(self):
        etudiant_user = get_user_model().objects.create_user(
            username="etu_presence",
            email="etu.presence@example.com",
            password="etu-pass-123",
            first_name="Etu",
            last_name="Presence",
        )
        etudiant = EtudiantProfile.objects.create(
            utilisateur=etudiant_user,
            matricule="26FPRSM",
            filiere=self.filiere,
            licence=self.licence,
            semestre=self.semestre,
            actif=True,
        )
        matiere = Matiere.objects.create(nom="Presence SQL", filiere=self.filiere, active=True)
        creneau, _ = CreneauAbsence.objects.get_or_create(
            heure_debut=time(8, 0),
            heure_fin=time(10, 0),
            defaults={"libelle": "Matin", "ordre": 1, "actif": True},
        )

        response = self.client.get(
            reverse("administration:presences"),
            {"filiere": self.filiere.id, "matiere": matiere.id, "date": "2026-05-03", "creneau": creneau.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, etudiant.nom_complet)
        self.assertContains(response, etudiant.matricule)

    def test_save_presences_records_present_and_absent_students(self):
        matiere = Matiere.objects.create(nom="Presence Python", filiere=self.filiere, active=True)
        creneau, _ = CreneauAbsence.objects.get_or_create(
            heure_debut=time(14, 0),
            heure_fin=time(16, 0),
            defaults={"libelle": "Apres-midi", "ordre": 2, "actif": True},
        )
        present_user = get_user_model().objects.create_user(username="present", email="present@example.com")
        absent_user = get_user_model().objects.create_user(username="absent", email="absent@example.com")
        present = EtudiantProfile.objects.create(
            utilisateur=present_user,
            matricule="26FPREM",
            filiere=self.filiere,
            licence=self.licence,
            semestre=self.semestre,
            actif=True,
        )
        absent = EtudiantProfile.objects.create(
            utilisateur=absent_user,
            matricule="26FABSM",
            filiere=self.filiere,
            licence=self.licence,
            semestre=self.semestre,
            actif=True,
        )

        response = self.client.post(
            reverse("administration:presences"),
            data={
                "action": "save_presences",
                "filiere": self.filiere.id,
                "matiere": matiere.id,
                "date": "2026-05-03",
                "creneau": creneau.id,
                "present_etudiants": [present.id],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Presence.objects.get(etudiant=present, matiere=matiere).present)
        self.assertFalse(Presence.objects.get(etudiant=absent, matiere=matiere).present)

    def test_save_presences_links_matching_seance(self):
        matiere = Matiere.objects.create(nom="Presence Seance", filiere=self.filiere, active=True)
        professeur = Professeur.objects.create(
            nom_complet="Prof Seance",
            email="prof.seance@example.com",
            actif=True,
        )
        creneau, _ = CreneauAbsence.objects.get_or_create(
            heure_debut=time(8, 0),
            heure_fin=time(10, 0),
            defaults={"libelle": "Matin", "ordre": 1, "actif": True},
        )
        seance = Seance.objects.create(
            filiere=self.filiere,
            matiere=matiere,
            professeur=professeur,
            date="2026-05-05",
            heure_debut=time(8, 0),
            heure_fin=time(10, 0),
        )
        user = get_user_model().objects.create_user(
            username="etu_seance_presence",
            email="etu.seance.presence@example.com",
            password="etu-pass-123",
            first_name="Seance",
            last_name="Presence",
        )
        etudiant = EtudiantProfile.objects.create(
            utilisateur=user,
            matricule="26FSPRM",
            filiere=self.filiere,
            licence=self.licence,
            semestre=self.semestre,
            actif=True,
        )

        self.client.post(
            reverse("administration:presences"),
            data={
                "action": "save_presences",
                "filiere": self.filiere.id,
                "matiere": matiere.id,
                "date": "2026-05-05",
                "creneau": creneau.id,
                "present_etudiants": [str(etudiant.id)],
            },
        )

        self.assertEqual(Presence.objects.get(etudiant=etudiant, matiere=matiere).seance, seance)

    def test_create_seance_from_emplois_du_temps(self):
        matiere = Matiere.objects.create(nom="Programmation", filiere=self.filiere, active=True)
        professeur = Professeur.objects.create(
            nom_complet="Prof Calendrier",
            email="prof.calendrier@example.com",
            actif=True,
        )

        response = self.client.post(
            reverse("administration:emplois_du_temps"),
            data={
                "action": "create_seance",
                "filiere": self.filiere.id,
                "matiere": matiere.id,
                "professeur": professeur.id,
                "date": "2026-05-06",
                "heure_debut": "09:00",
                "heure_fin": "11:00",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Seance.objects.filter(matiere=matiere, professeur=professeur, date="2026-05-06").exists())

    def test_emplois_du_temps_exports(self):
        matiere = Matiere.objects.create(nom="Export Planning", filiere=self.filiere, active=True)
        professeur = Professeur.objects.create(
            nom_complet="Prof Export",
            email="prof.export@example.com",
            actif=True,
        )
        Seance.objects.create(
            filiere=self.filiere,
            matiere=matiere,
            professeur=professeur,
            date="2026-05-07",
            heure_debut=time(13, 0),
            heure_fin=time(15, 0),
        )

        excel_response = self.client.get(reverse("administration:emplois_du_temps_export_excel"))
        pdf_response = self.client.get(reverse("administration:emplois_du_temps_export_pdf"))

        self.assertEqual(excel_response.status_code, 200)
        self.assertEqual(pdf_response.status_code, 200)
        self.assertIn("spreadsheetml.sheet", excel_response["Content-Type"])
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")

    def test_accept_justification_marks_presence_present(self):
        matiere = Matiere.objects.create(nom="Presence Justif", filiere=self.filiere, active=True)
        creneau, _ = CreneauAbsence.objects.get_or_create(
            heure_debut=time(17, 0),
            heure_fin=time(19, 0),
            defaults={"libelle": "Soir", "ordre": 3, "actif": True},
        )
        etudiant_user = get_user_model().objects.create_user(username="justif", email="justif@example.com")
        etudiant = EtudiantProfile.objects.create(
            utilisateur=etudiant_user,
            matricule="26FJUSM",
            filiere=self.filiere,
            licence=self.licence,
            semestre=self.semestre,
            actif=True,
        )
        presence = Presence.objects.create(
            etudiant=etudiant,
            matiere=matiere,
            date="2026-05-03",
            creneau=creneau,
            present=False,
        )
        justification = Justification.objects.create(presence=presence, motif="Maladie")

        response = self.client.post(
            reverse("administration:presences"),
            data={"action": "accept_justification", "object_id": justification.id},
            follow=True,
        )

        justification.refresh_from_db()
        presence.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(justification.statut, Justification.STATUT_ACCEPTEE)
        self.assertTrue(presence.present)

    def test_student_attendance_rate_and_dashboard_alert_under_75(self):
        matiere = Matiere.objects.create(nom="Presence Dashboard", filiere=self.filiere, active=True)
        creneau, _ = CreneauAbsence.objects.get_or_create(
            heure_debut=time(9, 0),
            heure_fin=time(11, 0),
            defaults={"libelle": "Dashboard", "ordre": 4, "actif": True},
        )
        etudiant_user = get_user_model().objects.create_user(username="low_attendance", email="low@example.com")
        etudiant = EtudiantProfile.objects.create(
            utilisateur=etudiant_user,
            matricule="26FLOWM",
            filiere=self.filiere,
            licence=self.licence,
            semestre=self.semestre,
            actif=True,
        )
        Presence.objects.create(etudiant=etudiant, matiere=matiere, date="2026-05-01", creneau=creneau, present=True)
        Presence.objects.create(etudiant=etudiant, matiere=matiere, date="2026-05-02", creneau=creneau, present=False)
        Presence.objects.create(etudiant=etudiant, matiere=matiere, date="2026-05-03", creneau=creneau, present=False)

        response = self.client.get(reverse("administration:dashboard"))

        self.assertEqual(etudiant.taux_assiduite, 33)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Assiduite &lt; 75%")
        self.assertContains(response, '<span class="badge bg-label-danger me-auto ms-2">1</span>', html=True)

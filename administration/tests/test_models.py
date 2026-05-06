from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from administration.models import Bulletin, EtudiantProfile, NoteBulletin
from bibliotheque.models import AnneeAcademique, Filiere, Licence, Matiere, Semestre


class BulletinModelTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="etudiant1",
            email="etudiant1@example.com",
            password="test-pass-123",
            first_name="Test",
            last_name="Etudiant",
        )
        self.filiere = Filiere.objects.create(nom="INFORMATIQUE TEST")
        self.licence, _ = Licence.objects.get_or_create(code="LT1", defaults={"ordre": 99})
        self.semestre, _ = Semestre.objects.get_or_create(code="S9", defaults={"ordre": 9})
        self.annee, _ = AnneeAcademique.objects.get_or_create(libelle="2030-2031", defaults={"active": True})
        self.etudiant = EtudiantProfile.objects.create(
            utilisateur=self.user,
            matricule="EMSP-TEST-0001",
            filiere=self.filiere,
            licence=self.licence,
            semestre=self.semestre,
            actif=True,
        )
        self.bulletin = Bulletin.objects.create(
            etudiant=self.etudiant,
            annee_academique=self.annee,
            semestre=self.semestre,
        )

    def test_note_save_recalculates_bulletin_moyenne(self):
        matiere = Matiere.objects.create(nom="SQL", filiere=self.filiere, active=True)
        NoteBulletin.objects.create(
            bulletin=self.bulletin,
            matiere=matiere,
            coefficient=2,
            note_cc=Decimal("14"),
            note_examen=Decimal("16"),
        )

        self.bulletin.refresh_from_db()
        self.assertEqual(self.bulletin.moyenne, Decimal("15.20"))
        self.assertEqual(self.bulletin.decision, Bulletin.DECISION_ADMIS)

    def test_bulletin_mention(self):
        self.bulletin.moyenne = Decimal("14.20")
        self.assertEqual(self.bulletin.mention, "Bien")

    def test_etudiant_matricule_is_generated_when_missing(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="auto_matricule",
            email="auto.matricule@example.com",
            password="test-pass-123",
            first_name="Auto",
            last_name="Matricule",
        )

        etudiant = EtudiantProfile.objects.create(
            utilisateur=user,
            annee_entree=2026,
            filiere=self.filiere,
            licence=self.licence,
            semestre=self.semestre,
            actif=True,
        )

        self.assertRegex(etudiant.matricule, r"^26F[A-Z]{3}M$")

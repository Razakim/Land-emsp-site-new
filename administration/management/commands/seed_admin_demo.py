from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from bibliotheque.models import AnneeAcademique, Document, Filiere, Licence, Matiere, Semestre, TypeDocument
from inscription.models import Dossier, Inscription
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


class Command(BaseCommand):
    help = "Cree des donnees demo pour remplir les listes administratives."

    def handle(self, *args, **options):
        User = get_user_model()
        admin_group, _ = Group.objects.get_or_create(name="Administration")
        admin, created = User.objects.get_or_create(
            username="admin.demo",
            defaults={
                "first_name": "Admin",
                "last_name": "Demo",
                "email": "admin.demo@emsp.int",
                "is_staff": True,
            },
        )
        if created:
            admin.set_password("AdminDemo2026!")
            admin.save()
        admin_group.user_set.add(admin)

        filiere_names = [
            "DIGITALISATION DES SERVICES",
            "FINANCE DIGITALE",
            "LOGISTIQUE ET NUMERIQUE",
            "MARKETING DIGITAL",
            "GESTION DES ACTIVITES REGLEMENTEES",
        ]
        filieres = [
            Filiere.objects.get_or_create(nom=name, defaults={"cycle": Filiere.CYCLE_LICENCE_PRO, "active": True})[0]
            for name in filiere_names
        ]
        licences = [
            Licence.objects.get_or_create(code=code, defaults={"ordre": idx})[0]
            for idx, code in enumerate(("L1", "L2", "L3", "M1", "M2"), start=1)
        ]
        semestres = [
            Semestre.objects.get_or_create(code=f"S{idx}", defaults={"ordre": idx})[0]
            for idx in range(1, 9)
        ]
        annee = AnneeAcademique.objects.get_or_create(libelle="2026-2027", defaults={"active": True})[0]
        type_doc = TypeDocument.objects.get_or_create(code="cours", defaults={"libelle": "Cours", "couleur": "primary"})[0]

        matiere_names = [
            "Bases de donnees",
            "Transformation numerique",
            "Comptabilite digitale",
            "Marketing operationnel",
            "Droit du numerique",
            "Logistique appliquee",
            "Gestion de projet",
            "Communication professionnelle",
            "Analyse financiere",
            "Cybersecurite",
            "Intelligence artificielle",
            "Statistiques appliquees",
            "E-commerce",
            "Management des risques",
            "Anglais professionnel",
            "Programmation web",
            "Systemes d'information",
            "Entrepreneuriat",
            "Data visualisation",
            "Audit et controle",
        ]
        matieres = []
        for idx, name in enumerate(matiere_names):
            matieres.append(
                Matiere.objects.get_or_create(
                    nom=name,
                    filiere=filieres[idx % len(filieres)],
                    defaults={"code": f"MAT{idx + 1:03d}", "semestre": semestres[idx % len(semestres)], "active": True},
                )[0]
            )

        first_names = [
            "Aminata",
            "Mamadou",
            "Fatou",
            "Yao",
            "Nadia",
            "Ibrahim",
            "Awa",
            "Kevin",
            "Mariam",
            "Souleymane",
            "Ines",
            "Kouassi",
            "Sarah",
            "Karim",
            "Estelle",
            "Junior",
            "Rokia",
            "Didier",
            "Nathalie",
            "Moussa",
        ]
        last_names = [
            "Kone",
            "Traore",
            "Kouame",
            "Coulibaly",
            "Ouattara",
            "Diallo",
            "Bamba",
            "Soro",
            "Toure",
            "Nguessan",
            "Diaby",
            "Amani",
            "Konan",
            "Koffi",
            "Bakayoko",
            "Kouassi",
            "Fofana",
            "Yapi",
            "Ble",
            "Cisse",
        ]

        etudiants = []
        for idx in range(20):
            username = f"etu.demo.{idx + 1:02d}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first_names[idx],
                    "last_name": last_names[idx],
                    "email": f"{first_names[idx].lower()}.{last_names[idx].lower()}@emsp.edu",
                },
            )
            if created:
                user.set_password("Etudiant2026!")
                user.save()
            etudiant, _ = EtudiantProfile.objects.get_or_create(
                utilisateur=user,
                defaults={
                    "telephone": f"+225 07 00 00 {idx + 1:02d}",
                    "filiere": filieres[idx % len(filieres)],
                    "licence": licences[idx % len(licences)],
                    "semestre": semestres[idx % len(semestres)],
                    "actif": True,
                },
            )
            etudiants.append(etudiant)

        professeurs = []
        for idx in range(20):
            professeur, _ = Professeur.objects.get_or_create(
                email=f"prof.demo.{idx + 1:02d}@emsp.edu",
                defaults={
                    "nom_complet": f"Dr. {first_names[idx]} {last_names[-idx - 1]}",
                    "telephone": f"+225 05 00 00 {idx + 1:02d}",
                    "actif": True,
                },
            )
            professeur.matieres.add(matieres[idx % len(matieres)])
            professeurs.append(professeur)

        cars = []
        axes = [choice[0] for choice in CarTransport.AXE_CHOICES]
        for idx in range(20):
            cars.append(
                CarTransport.objects.get_or_create(
                    immatriculation=f"EMSP-CAR-{idx + 1:03d}",
                    defaults={
                        "nom": f"Car EMSP {idx + 1:02d}",
                        "axe_principal": axes[idx % len(axes)],
                        "chauffeur": f"Chauffeur {first_names[idx]}",
                        "telephone_chauffeur": f"+225 01 00 00 {idx + 1:02d}",
                        "capacite": 30 + (idx % 10),
                        "actif": True,
                        "observations": "Circuit demo operationnel",
                    },
                )[0]
            )

        today = timezone.localdate()
        creneau, _ = CreneauAbsence.objects.get_or_create(
            heure_debut=time(8, 0),
            heure_fin=time(10, 0),
            defaults={"libelle": "Matinee 08h-10h", "ordre": 1, "actif": True},
        )
        for idx, etudiant in enumerate(etudiants):
            scolarite, _ = Scolarite.objects.get_or_create(
                etudiant=etudiant,
                defaults={"total_du": Decimal("650000.00"), "date_echeance": today + timedelta(days=30 + idx)},
            )
            scolarite.total_du = Decimal("650000.00")
            scolarite.date_echeance = today + timedelta(days=30 - idx)
            scolarite.save(update_fields=["total_du", "date_echeance", "updated_at"])
            Paiement.objects.get_or_create(
                reference=f"DEMO-PAY-{idx + 1:04d}",
                defaults={
                    "scolarite": scolarite,
                    "montant": Decimal("650000.00") if idx % 4 == 0 else Decimal("250000.00") + Decimal(idx * 5000),
                    "moyen": Paiement.MOYEN_WAVE if idx % 2 == 0 else Paiement.MOYEN_ORANGE,
                    "date": today - timedelta(days=idx),
                    "statut": Paiement.STATUT_VERIFIE if idx % 3 else Paiement.STATUT_EN_ATTENTE,
                },
            )
            if idx % 5 == 0:
                Paiement.objects.get_or_create(
                    reference=f"DEMO-PART-{idx + 1:04d}",
                    defaults={
                        "scolarite": scolarite,
                        "montant": Decimal("125000.00"),
                        "moyen": Paiement.MOYEN_ESPECES,
                        "date": today - timedelta(days=idx + 2),
                        "statut": Paiement.STATUT_REJETE,
                    },
                )
            InscriptionTransport.objects.get_or_create(
                etudiant=etudiant,
                axe=axes[idx % len(axes)],
                defaults={"car": cars[idx % len(cars)], "statut": InscriptionTransport.STATUT_VALIDEE},
            )
            inscription, _ = Inscription.objects.get_or_create(
                email=etudiant.utilisateur.email,
                defaults={
                    "prenom": etudiant.utilisateur.first_name,
                    "nom": etudiant.utilisateur.last_name,
                    "telephone": etudiant.telephone,
                    "filiere": etudiant.filiere,
                    "licence": etudiant.licence,
                    "statut": [
                        Inscription.STATUT_EN_ATTENTE,
                        Inscription.STATUT_EN_COURS,
                        Inscription.STATUT_VALIDEE,
                        Inscription.STATUT_INCOMPLETE,
                    ][idx % 4],
                    "utilisateur": etudiant.utilisateur,
                    "etudiant_profile": etudiant,
                },
            )
            Dossier.objects.get_or_create(
                inscription=inscription,
                defaults={
                    "documents_requis": 6,
                    "documents_fournis": 6 - (idx % 3),
                    "commentaire_interne": "Pieces simulees: CNI, extrait, diplome, photo, recu, formulaire.",
                },
            )
            present = idx % 4 != 1
            presence, _ = Presence.objects.get_or_create(
                etudiant=etudiant,
                matiere=matieres[idx % len(matieres)],
                date=today - timedelta(days=idx % 10),
                creneau=creneau,
                defaults={"present": present},
            )
            if idx % 4 == 2:
                presence.present = False
                presence.save(update_fields=["present", "updated_at"])
                Justification.objects.get_or_create(
                    presence=presence,
                    defaults={
                        "motif": "Rendez-vous medical documente.",
                        "statut": Justification.STATUT_ACCEPTEE,
                        "commentaire": "Justificatif simule accepte.",
                    },
                )
            bulletin, _ = Bulletin.objects.get_or_create(
                etudiant=etudiant,
                annee_academique=annee,
                semestre=semestres[idx % len(semestres)],
                defaults={"publie": idx % 2 == 0},
            )
            NoteBulletin.objects.get_or_create(
                bulletin=bulletin,
                matiere=matieres[idx % len(matieres)],
                defaults={
                    "professeur": professeurs[idx % len(professeurs)],
                    "coefficient": 2 + (idx % 3),
                    "note_cc": Decimal("10.00") + Decimal(idx % 8),
                    "note_examen": Decimal("9.00") + Decimal(idx % 10),
                    "observation": "Evaluation demo.",
                },
            )

        event_types = [choice[0] for choice in Evenement.TYPE_CHOICES]
        for idx in range(20):
            Evenement.objects.get_or_create(
                titre=f"Activite EMSP Demo {idx + 1:02d}",
                defaults={
                    "type": event_types[idx % len(event_types)],
                    "date": today + timedelta(days=idx + 1),
                    "heure": time(9 + (idx % 8), 0),
                    "lieu": f"Amphi {chr(65 + idx % 4)}",
                    "public_cible": "Etudiants et professeurs",
                    "description": "Evenement de demonstration.",
                },
            )

        week_start = today - timedelta(days=today.weekday())
        slot_pairs = [(time(8, 0), time(10, 0)), (time(10, 0), time(12, 0)), (time(13, 0), time(15, 0)), (time(15, 0), time(17, 0))]
        created_seances = 0
        idx = 0
        while created_seances < 20:
            day = week_start + timedelta(days=idx % 6)
            start, end = slot_pairs[idx % len(slot_pairs)]
            _, created = Seance.objects.get_or_create(
                filiere=filieres[idx % len(filieres)],
                matiere=matieres[idx % len(matieres)],
                professeur=professeurs[idx % len(professeurs)],
                date=day,
                heure_debut=start,
                heure_fin=end,
                defaults={"salle": f"Salle {chr(65 + idx % 4)}{100 + idx % 12}"},
            )
            if created:
                created_seances += 1
            idx += 1

        for idx in range(20):
            document, created = Document.objects.get_or_create(
                titre=f"Support de cours demo {idx + 1:02d}",
                defaults={
                    "description": "Document de demonstration pour alimenter la bibliotheque.",
                    "filiere": filieres[idx % len(filieres)],
                    "licence": licences[idx % len(licences)],
                    "semestre": semestres[idx % len(semestres)],
                    "matiere": matieres[idx % len(matieres)],
                    "type_document": type_doc,
                    "annee_academique": annee,
                    "contributeur": admin,
                    "reserve_auth": True,
                    "valide": idx % 3 != 0,
                },
            )
            if created:
                document.fichier.save(
                    f"support_demo_{idx + 1:02d}.txt",
                    ContentFile("Support de cours demo EMSP."),
                    save=True,
                )

        self.stdout.write(self.style.SUCCESS("Donnees demo creees ou completees avec succes."))

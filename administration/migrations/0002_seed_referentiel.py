from django.db import migrations
from django.utils.text import slugify


def seed_referentiel(apps, schema_editor):
    Filiere = apps.get_model("bibliotheque", "Filiere")
    AnneeAcademique = apps.get_model("bibliotheque", "AnneeAcademique")
    Semestre = apps.get_model("bibliotheque", "Semestre")
    CreneauAbsence = apps.get_model("administration", "CreneauAbsence")

    licence_pro = [
        "LOGISTIQUE ET NUMERIQUE",
        "FINANCE DIGITALE",
        "MARKETING DIGITAL",
        "DIGITALISATION DES SERVICES",
        "GESTION DES ACTIVITES REGLEMENTEES",
    ]
    master_pro = [
        "LOGISTIQUE ET E-COMMERCE",
        "FINANCE ET MANAGEMENT DES ENTREPRISES DU RISQUE",
        "MARKETING DIGITAL ET E-BUSINESS",
        "TRANSFORMATION NUMERIQUE DES ORGANISATIONS",
        "MASTERE SPECIALISE EN REGULATION DU NUMERIQUE",
    ]

    def unique_slug_for_nom(nom):
        base_slug = slugify(nom) or "filiere"
        slug = base_slug
        index = 2
        while Filiere.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{index}"
            index += 1
        return slug

    def ensure_filiere(nom, cycle):
        filiere, created = Filiere.objects.get_or_create(
            nom=nom,
            defaults={"cycle": cycle, "active": True, "slug": unique_slug_for_nom(nom)},
        )
        if not created and not filiere.slug:
            filiere.slug = unique_slug_for_nom(filiere.nom)
            filiere.save(update_fields=["slug"])

    for nom in licence_pro:
        ensure_filiere(nom, "licence_pro")
    for nom in master_pro:
        ensure_filiere(nom, "master_pro")

    for libelle in ("2023-2024", "2024-2025", "2025-2026", "2026-2027"):
        AnneeAcademique.objects.get_or_create(libelle=libelle, defaults={"active": libelle == "2026-2027"})

    semestres = [("S1", 1), ("S2", 2), ("S3", 3), ("S4", 4), ("S5", 5), ("S6", 6), ("S7", 7), ("S8", 8)]
    for code, ordre in semestres:
        Semestre.objects.get_or_create(code=code, defaults={"ordre": ordre})

    creneaux = [
        ("Cours du matin", "08:00", "10:00", 1),
        ("Cours milieu de matinee", "10:15", "12:15", 2),
        ("Cours apres-midi 1", "13:30", "15:30", 3),
        ("Cours apres-midi 2", "15:45", "17:45", 4),
    ]
    for libelle, start, end, ordre in creneaux:
        CreneauAbsence.objects.get_or_create(
            heure_debut=start,
            heure_fin=end,
            defaults={"libelle": libelle, "ordre": ordre, "actif": True},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("administration", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_referentiel, migrations.RunPython.noop),
    ]

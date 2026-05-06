from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("administration", "0002_seed_referentiel"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("bibliotheque", "0002_filiere_cycle"),
    ]

    operations = [
        migrations.CreateModel(
            name="EtudiantProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("matricule", models.CharField(max_length=40, unique=True)),
                ("telephone", models.CharField(blank=True, max_length=30)),
                ("actif", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "filiere",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="etudiants",
                        to="bibliotheque.filiere",
                    ),
                ),
                (
                    "licence",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="etudiants",
                        to="bibliotheque.licence",
                    ),
                ),
                (
                    "semestre",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="etudiants",
                        to="bibliotheque.semestre",
                    ),
                ),
                (
                    "utilisateur",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profil_etudiant",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("matricule",),
            },
        ),
        migrations.CreateModel(
            name="Bulletin",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("moyenne", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=5)),
                (
                    "decision",
                    models.CharField(
                        choices=[("admis", "Admis"), ("rattrapage", "Rattrapage"), ("ajourne", "Ajourne")],
                        default="ajourne",
                        max_length=20,
                    ),
                ),
                ("appreciation", models.CharField(blank=True, max_length=255)),
                ("publie", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "annee_academique",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="bulletins",
                        to="bibliotheque.anneeacademique",
                    ),
                ),
                (
                    "etudiant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="bulletins",
                        to="administration.etudiantprofile",
                    ),
                ),
                (
                    "semestre",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="bulletins",
                        to="bibliotheque.semestre",
                    ),
                ),
            ],
            options={
                "ordering": ("-annee_academique__libelle", "semestre__ordre"),
                "unique_together": {("etudiant", "annee_academique", "semestre")},
            },
        ),
        migrations.CreateModel(
            name="NoteBulletin",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("coefficient", models.PositiveSmallIntegerField(default=1)),
                ("note_cc", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=4)),
                ("note_examen", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=4)),
                ("note_finale", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=4)),
                ("observation", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "bulletin",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notes",
                        to="administration.bulletin",
                    ),
                ),
                (
                    "matiere",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="notes_bulletins",
                        to="bibliotheque.matiere",
                    ),
                ),
                (
                    "professeur",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="notes_bulletins",
                        to="administration.professeur",
                    ),
                ),
            ],
            options={
                "ordering": ("matiere__nom",),
                "unique_together": {("bulletin", "matiere")},
            },
        ),
    ]

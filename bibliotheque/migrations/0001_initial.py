# Generated manually for bibliotheque module initialization.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AnneeAcademique",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("libelle", models.CharField(max_length=20, unique=True)),
                ("active", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Annee academique",
                "verbose_name_plural": "Annees academiques",
                "ordering": ("-libelle",),
            },
        ),
        migrations.CreateModel(
            name="Filiere",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nom", models.CharField(max_length=120, unique=True)),
                ("slug", models.SlugField(blank=True, max_length=140, unique=True)),
                ("active", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Filiere",
                "verbose_name_plural": "Filieres",
                "ordering": ("nom",),
            },
        ),
        migrations.CreateModel(
            name="Licence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=20, unique=True)),
                ("ordre", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "ordering": ("ordre", "code"),
            },
        ),
        migrations.CreateModel(
            name="Semestre",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=5, unique=True)),
                ("ordre", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "ordering": ("ordre", "code"),
            },
        ),
        migrations.CreateModel(
            name="TypeDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=20, unique=True)),
                ("libelle", models.CharField(max_length=80)),
                ("couleur", models.CharField(default="primary", max_length=20)),
            ],
            options={
                "ordering": ("libelle",),
            },
        ),
        migrations.CreateModel(
            name="Matiere",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nom", models.CharField(max_length=120)),
                ("active", models.BooleanField(default=True)),
                ("filiere", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="matieres", to="bibliotheque.filiere")),
            ],
            options={
                "ordering": ("nom",),
                "unique_together": {("nom", "filiere")},
            },
        ),
        migrations.CreateModel(
            name="Document",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titre", models.CharField(max_length=220)),
                ("description", models.TextField(max_length=1000)),
                ("fichier", models.FileField(upload_to="bibliotheque/documents/%Y/%m/")),
                ("reserve_auth", models.BooleanField(default=True)),
                ("valide", models.BooleanField(default=False)),
                ("motif_refus", models.CharField(blank=True, max_length=255)),
                ("telechargements_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("annee_academique", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="documents", to="bibliotheque.anneeacademique")),
                ("contributeur", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="documents_deposes", to=settings.AUTH_USER_MODEL)),
                ("filiere", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="documents", to="bibliotheque.filiere")),
                ("licence", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="documents", to="bibliotheque.licence")),
                ("matiere", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="documents", to="bibliotheque.matiere")),
                ("semestre", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="documents", to="bibliotheque.semestre")),
                ("type_document", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="documents", to="bibliotheque.typedocument")),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="Commentaire",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("contenu", models.TextField(max_length=1200)),
                ("likes", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="commentaires", to="bibliotheque.document")),
                ("parent", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="reponses", to="bibliotheque.commentaire")),
                ("utilisateur", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="commentaires_bibliotheque", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="RechercheRecente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("requete", models.CharField(max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("utilisateur", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recherches_bibliotheque", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="Telechargement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="telechargements", to="bibliotheque.document")),
                ("utilisateur", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="telechargements_bibliotheque", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="Favori",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="favoris", to="bibliotheque.document")),
                ("utilisateur", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="favoris_bibliotheque", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ("-created_at",),
                "unique_together": {("utilisateur", "document")},
            },
        ),
    ]

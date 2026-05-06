from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("bibliotheque", "0002_filiere_cycle"),
    ]

    operations = [
        migrations.CreateModel(
            name="CreneauAbsence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("libelle", models.CharField(max_length=120)),
                ("heure_debut", models.TimeField()),
                ("heure_fin", models.TimeField()),
                ("ordre", models.PositiveSmallIntegerField(default=0)),
                ("actif", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ("ordre", "heure_debut"),
                "unique_together": {("heure_debut", "heure_fin")},
            },
        ),
        migrations.CreateModel(
            name="Professeur",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nom_complet", models.CharField(max_length=150)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("telephone", models.CharField(blank=True, max_length=30)),
                ("actif", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "matieres",
                    models.ManyToManyField(blank=True, related_name="professeurs", to="bibliotheque.matiere"),
                ),
            ],
            options={
                "ordering": ("nom_complet",),
            },
        ),
    ]

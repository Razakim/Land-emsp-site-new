from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("administration", "0012_alter_etudiantprofile_matricule"),
    ]

    operations = [
        migrations.AddField(
            model_name="seance",
            name="salle",
            field=models.CharField(blank=True, max_length=80),
        ),
    ]

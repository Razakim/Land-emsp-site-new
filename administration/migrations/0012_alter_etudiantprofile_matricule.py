from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("administration", "0011_evenement_scolarite_paiement"),
    ]

    operations = [
        migrations.AlterField(
            model_name="etudiantprofile",
            name="matricule",
            field=models.CharField(blank=True, max_length=120, unique=True),
        ),
    ]

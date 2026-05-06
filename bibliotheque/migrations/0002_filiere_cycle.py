from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bibliotheque", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="filiere",
            name="cycle",
            field=models.CharField(
                choices=[
                    ("licence_pro", "Licences professionnelles"),
                    ("master_pro", "Masters professionnels"),
                ],
                default="licence_pro",
                max_length=20,
            ),
        ),
    ]

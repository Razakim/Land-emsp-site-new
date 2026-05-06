# Generated manually for photo field addition

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administration', '0006_etudiantprofile_annee_entree_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='etudiantprofile',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='etudiants/photos/'),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='document_type',
            field=models.CharField(
                choices=[('CEDULA', 'Cédula'), ('PASAPORTE', 'Pasaporte'), ('RNC', 'RNC')],
                default='CEDULA',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='patient',
            name='insurance_provider',
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='insurance_number',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
    ]

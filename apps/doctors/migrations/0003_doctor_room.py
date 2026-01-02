import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinics', '0002_clinic_company'),
        ('doctors', '0002_doctor_company_created_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctor',
            name='room',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='doctors', to='clinics.room'),
        ),
    ]

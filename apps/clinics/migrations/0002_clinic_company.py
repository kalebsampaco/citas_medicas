import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('clinics', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='clinic',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='clinics', to='accounts.company'),
        ),
    ]

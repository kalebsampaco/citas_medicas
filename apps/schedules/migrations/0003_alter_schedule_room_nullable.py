from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0002_schedule_availability_timestamps'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schedule',
            name='room',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='schedules', to='clinics.room'),
        ),
    ]

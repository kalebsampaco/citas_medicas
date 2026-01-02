# Generated manually to add current_step and context_data to ChatSession
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0002_chatactionlog"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatsession",
            name="current_step",
            field=models.CharField(
                choices=[
                    ("initial", "Inicial: mostrar opciones"),
                    ("selecting_action", "Seleccionar acción (agendar/ver agenda)"),
                    ("getting_patient_cedula", "Solicitando cédula del paciente"),
                    ("selecting_doctor", "Seleccionar médico"),
                    ("selecting_date", "Seleccionar fecha"),
                    ("confirming_appointment", "Confirmar agendamiento"),
                    ("completed", "Completado"),
                ],
                default="initial",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="chatsession",
            name="context_data",
            field=models.JSONField(blank=True, default=dict, help_text="Datos temporales: cedula, doctor_id, date, etc."),
        ),
    ]

# Backend Django - Citas Médicas

API RESTful para gestión integral de citas médicas con roles, notificaciones WhatsApp vía Twilio y auditoría.

## Estructura de Apps

- **accounts**: usuarios con roles `ADMIN` y `OPERATOR`
- **patients**: gestión de pacientes con datos personales y contactos
- **doctors**: médicos y especialidades
- **clinics**: clínicas y consultorios (Room)
- **schedules**: disponibilidad de médicos en consultorios
- **appointments**: citas con estados (`PENDING`, `CONFIRMED`, `RESCHEDULED`, `CANCELLED`, `COMPLETED`, `NO_SHOW`) y acciones de auditoría
- **notifications**: tracking de envíos WhatsApp con Twilio
- **audit**: log de acciones (futuro)
- **common**: utilidades compartidas

## Configuración

### Variables de entorno (`.env`)
```env
SECRET_KEY=dev-secret
DEBUG=True
ALLOWED_HOSTS=["*"]
DB_NAME=citas
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_SENDER=whatsapp:+14155238886
```

### Instalación
```bash
pip install poetry
poetry install
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Endpoints principales

- `POST /api/auth/users/` - crear usuario
- `GET /api/patients/` - listar pacientes
- `POST /api/patients/` - crear paciente
- `GET /api/doctors/` - listar médicos
- `GET /api/clinics/clinics/` - listar clínicas
- `GET /api/clinics/rooms/` - listar consultorios
- `GET /api/schedules/?doctor=1&date=2025-12-15` - disponibilidad
- `POST /api/appointments/` - crear cita
- `GET /api/appointments/{id}/actions/` - historial de acciones
- `POST /api/notifications/whatsapp/send/{appointment_id}/` - enviar recordatorio
- `POST /api/notifications/whatsapp/webhook/` - webhook Twilio (sin auth)

## Integración Twilio WhatsApp

### Flujo de confirmación de cita
1. Backend envía recordatorio 2 días antes vía `POST /whatsapp/send/{id}/`
2. Paciente responde: "Confirmar", "Reprogramar" o "Cancelar"
3. Twilio envía webhook a `/whatsapp/webhook/`
4. Backend actualiza `status` de `Appointment` y registra `AppointmentAction`

### Configurar webhook en Twilio
En Twilio Console (Sandbox o Sender), configurar:
- **Inbound Message URL**: `https://tu-dominio.com/api/notifications/whatsapp/webhook/`
- **Method**: POST

## Docker

### Build
```bash
docker build -t citas-backend:dev .
```

### Run
```bash
docker run -p 8000:8000 --env-file .env citas-backend:dev
```

## Deploy en AWS ECS/Fargate
1. Push imagen a ECR
2. Task definition con variables de entorno desde Secrets Manager
3. ALB con listener HTTPS (ACM)
4. RDS PostgreSQL en VPC privada
5. ElastiCache Redis para Celery
6. S3 para media (STATIC_URL, MEDIA_URL)

"""Servicios para el asistente de chat con soporte Ollama/OpenAI."""
import json
import re
from datetime import datetime
from typing import Dict, List, Optional

import requests
from apps.appointments.models import Appointment, AppointmentStatus
from apps.doctors.models import Doctor
from apps.patients.models import Patient
from apps.schedules.models import Schedule
from django.conf import settings
from django.db.models import Q

SYSTEM_PROMPT = """Eres un asistente de citas médicas profesional y amable de una clínica. Consideras que se trabaja de lunes a sábado (los sábados son día laboral).

FLUJO CONVERSACIONAL:
El chat guía al usuario a través de estos pasos:
1. INICIAL: Mostrar opción de "Agendar cita" o "Ver agenda de médico"
2. Si AGENDAMIENTO:
   a. Pedir documento del paciente
   b. Buscar paciente y mostrar listado de médicos (con números)
   c. Pedir que seleccione médico por número
   d. Mostrar disponibilidad (fechas y horarios)
   e. Pedir que seleccione una cita
   f. Confirmar y crear cita
3. Si VER AGENDA:
   a. Mostrar listado de médicos
   b. Pedir que seleccione médico por número
   c. Mostrar disponibilidad del médico

FORMATO DE RESPUESTA (OBLIGATORIO):
Siempre devuelve JSON:
{
    "message": "Texto amigable para el usuario",
    "action": "show_initial_menu|process_patient_cedula|show_doctors|select_doctor|show_availability|create_appointment|show_doctor_availability",
    "data": {
        "cedula": "documento si aplica",
        "doctor_id": "id del médico si aplica (integer)",
        "schedule_id": "id del horario si aplica",
        "patient_id": "id del paciente si aplica"
    }
}

INSTRUCCIONES CRÍTICAS:
1. Cuando el usuario envíe un documento/cédula (números):
   action="process_patient_cedula", data={cedula: "valor"}
2. Cuando el usuario seleccione un médico con formato "ID|Nombre" (ej: "1|Dr. Pérez"):
   - EXTRAE el doctor_id del número ANTES del |
   - action="select_doctor", data={doctor_id: <número>}
   - Confirma el médico seleccionado en el mensaje
   - NO ejecutes show_doctors de nuevo
3. Cuando el usuario seleccione un horario: retorna los datos del horario
4. Responde SIEMPRE con JSON válido, nunca texto plano después del JSON.
5. Sé amable, claro y objetivo.
"""


def _detect_user_role(user) -> str:
    if getattr(user, "is_super_admin", False):
        return "super_admin"
    if getattr(user, "is_company_admin", False):
        return "company_admin"
    if getattr(user, "is_staff", False):
        return "staff"
    return "user"


def _build_prompt(user_message: str, chat_history: List, user_role: str, current_step: str = "initial") -> str:
    history_text = "\n".join([f"{msg.role.upper()}: {msg.content}" for msg in chat_history[-10:]])
    role_note = """Recuerda:
- SUPER_ADMIN/COMPANY_ADMIN/STAFF pueden ver/agendar para cualquier paciente de su empresa.
- Otros roles: limitar acciones y responde indicando falta de permisos.
"""

    step_context = {
        "initial": "El usuario está iniciando. Muestra un menú con las opciones: 1) Agendar cita para un paciente, 2) Ver agenda de un médico.",
        "selecting_action": "Espera que el usuario seleccione 1 o 2.",
        "getting_patient_cedula": "El usuario eligió agendar. Pide el documento del paciente (cédula, pasaporte, etc).",
        "selecting_doctor": "Ya tienes el documento del paciente. Busca el paciente por documento, confirma el nombre encontrado, y luego SIEMPRE ejecuta action='show_doctors' para mostrar el listado de médicos numerado.",
        "selecting_date": "El usuario acaba de seleccionar un médico. Si el mensaje contiene el formato 'ID|Nombre', EXTRAE el doctor_id (el número antes del |) y ejecuta action='select_doctor' con ese doctor_id. Esto mostrará la disponibilidad del médico.",
        "confirming_appointment": "Confirma que desea agendar a esa hora y procede a crear la cita.",
        "view_doctor_agenda": "El usuario eligió ver agenda. Muestra listado de médicos numerado y pide seleccione uno para ver su disponibilidad.",
        "completed": "La acción se completó. Pregunta si desea hacer algo más.",
    }

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Paso actual: {current_step}\n"
        f"Contexto del paso: {step_context.get(current_step, '')}\n"
        f"Rol del usuario: {user_role}\n"
        f"{role_note}\n"
        f"--- Historial ---\n{history_text}\n\n"
        f"Usuario: {user_message}\n"
        f"Asistente:"
    )
    return prompt


def _parse_ai_message(ai_message: str) -> Dict:
    """Parsea la respuesta de la IA, incluso si trae texto extra."""

    raw = ai_message or ""
    message = raw
    action = None
    action_data: Dict = {}

    def _try_load(candidate: Optional[str]) -> Optional[Dict]:
        if not candidate:
            return None
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    def _extract_json_block(text: str) -> Optional[str]:
        fence = re.search(r"\{.*\}", text, flags=re.DOTALL)
        return fence.group(0) if fence else None

    parsed = _try_load(raw)

    if not parsed:
        stripped = raw.strip().strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
        parsed = _try_load(stripped)

    if not parsed:
        candidate = _extract_json_block(raw)
        parsed = _try_load(candidate)

    if parsed:
        message = parsed.get("message", message)
        action = parsed.get("action")
        action_data = parsed.get("data") or {}

    return {"message": message, "action": action, "action_data": action_data, "raw": raw}


def _ollama_generate(prompt: str) -> str:
    response = requests.post(
        f"{settings.OLLAMA_URL}/api/generate",
        json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False, "temperature": 0.6},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("response", "").strip()


def _openai_generate(prompt: str) -> str:
    import openai

    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY no configurado")
    openai.api_key = api_key
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=500,
    )
    return completion.choices[0].message.content.strip()


def get_ai_response(user_message: str, chat_history: List, user, current_step: str = "initial") -> Dict:
    """Obtiene respuesta del modelo configurado y la parsea, pasando el step actual."""

    user_role = _detect_user_role(user)
    prompt = _build_prompt(user_message, chat_history, user_role, current_step)

    try:
        if getattr(settings, "LLM_PROVIDER", "ollama") == "openai":
            raw = _openai_generate(prompt)
        else:
            raw = _ollama_generate(prompt)
    except Exception as exc:  # pragma: no cover - manejo de red
        return {"message": f"No se pudo contactar a la IA: {exc}", "action": None, "action_data": None, "raw": ""}

    return _parse_ai_message(raw)


def _company_filter(qs, user):
    company_id = getattr(user, "company_id", None)
    if not company_id:
        return qs.none()
    return qs.filter(doctor__company_id=company_id) if qs.model is Schedule else qs.filter(patient__company_id=company_id)


def _resolve_doctor_id(doctor_id: Optional[int], doctor_name: Optional[str], user) -> Optional[int]:
    if doctor_id:
        return doctor_id
    if not doctor_name:
        return None
    company_id = getattr(user, "company_id", None)
    qs = Doctor.objects.all()
    if company_id:
        qs = qs.filter(company_id=company_id)
    qs = qs.filter(Q(first_name__icontains=doctor_name) | Q(last_name__icontains=doctor_name) | Q(specialty__icontains=doctor_name))
    doc = qs.first()
    return doc.id if doc else None


def find_patient_by_cedula(cedula: str, user) -> Optional[Dict]:
    """Busca paciente por documento. Retorna dict con id, nombre, etc. o None."""
    company_id = getattr(user, "company_id", None)
    qs = Patient.objects.all()
    if company_id:
        qs = qs.filter(company_id=company_id)
    patient = qs.filter(document_number=cedula.strip()).first()
    if patient:
        return {
            "id": patient.id,
            "document_number": patient.document_number,
            "name": f"{patient.first_name} {patient.last_name}",
            "first_name": patient.first_name,
            "last_name": patient.last_name,
        }
    return None


def get_doctors_list(user) -> List[Dict]:
    """Lista todos los médicos de la empresa del usuario o todos si no hay company_id."""
    company_id = getattr(user, "company_id", None)
    qs = Doctor.objects.all()
    if company_id:
        qs = qs.filter(company_id=company_id)
    # Si no hay company_id o si no hay médicos con ese company_id, trae todos
    doctors = list(qs.order_by("first_name"))
    if not doctors:
        doctors = list(Doctor.objects.all().order_by("first_name"))
    return [
        {
            "id": doc.id,
            "name": f"Dr(a). {doc.first_name} {doc.last_name}",
            "specialty": doc.specialty or "General",
        }
        for doc in doctors
    ]


def get_doctor_availability_for_selection(doctor_id: int, user, date: Optional[str] = None) -> Dict:
    """Obtiene disponibilidad de un médico para mostrar en selección de fecha."""
    result = get_doctor_availability(doctor_id, date, user)
    if "error" in result:
        return result

    # Agrupar slots por fecha
    by_date = {}
    for slot in result.get("slots", []):
        date_str = slot["date"]
        if date_str not in by_date:
            by_date[date_str] = []
        by_date[date_str].append({
            "schedule_id": slot["schedule_id"],
            "time": slot["start_time"],
            "end_time": slot["end_time"],
        })

    return {
        "doctor_id": doctor_id,
        "available_dates": by_date,
    }


def get_doctor_availability(doctor_id: Optional[int], date: Optional[str], user, doctor_name: Optional[str] = None) -> Dict:
    doctor_id = _resolve_doctor_id(doctor_id, doctor_name, user)
    if not doctor_id:
        return {"error": "No se pudo identificar el médico"}

    qs = Schedule.objects.filter(doctor_id=doctor_id, is_available=True)
    qs = _company_filter(qs, user)
    if date:
        qs = qs.filter(date=date)

    slots = []
    for schedule in qs:
        if Appointment.objects.filter(schedule=schedule).exists():
            continue
        slots.append(
            {
                "schedule_id": schedule.id,
                "doctor_id": doctor_id,
                "date": schedule.date.isoformat(),
                "start_time": schedule.start_time.strftime("%H:%M"),
                "end_time": schedule.end_time.strftime("%H:%M"),
                "room_id": schedule.room_id,
                "room_name": str(schedule.room) if schedule.room else None,
                "slot_minutes": schedule.slot_minutes,
            }
        )
    return {"doctor_id": doctor_id, "slots": slots}


def create_appointment_from_action(action_data: Dict, user) -> Dict:
    doctor_id = _resolve_doctor_id(action_data.get("doctor_id"), action_data.get("doctor_name"), user)
    patient_id = action_data.get("patient_id")
    schedule_id = action_data.get("schedule_id")

    if not all([doctor_id, patient_id, schedule_id]):
        return {"type": "error", "message": "doctor_id, patient_id y schedule_id son requeridos"}

    schedule = Schedule.objects.filter(id=schedule_id, doctor_id=doctor_id, is_available=True).first()
    if not schedule:
        return {"type": "error", "message": "Horario no disponible"}

    schedule = _company_filter(Schedule.objects.filter(id=schedule.id), user).first()
    if not schedule:
        return {"type": "error", "message": "No tienes acceso a este horario"}

    if Appointment.objects.filter(schedule=schedule).exists():
        return {"type": "error", "message": "Ese horario ya fue tomado"}

    try:
        doctor = Doctor.objects.get(id=doctor_id)
    except Doctor.DoesNotExist:
        return {"type": "error", "message": "Médico no encontrado"}

    try:
        patient = Patient.objects.get(id=patient_id)
    except Patient.DoesNotExist:
        return {"type": "error", "message": "Paciente no encontrado"}

    room = schedule.room or doctor.room
    if not room:
        return {"type": "error", "message": "El médico no tiene consultorio asignado"}

    start_dt = datetime.combine(schedule.date, schedule.start_time)
    end_dt = datetime.combine(schedule.date, schedule.end_time)

    appointment = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        room=room,
        schedule=schedule,
        start_datetime=start_dt,
        end_datetime=end_dt,
        status=AppointmentStatus.PENDING,
    )

    schedule.is_available = False
    schedule.save(update_fields=["is_available"])

    return {
        "type": "success",
        "message": "Cita agendada correctamente",
        "appointment_id": appointment.id,
        "start": start_dt,
        "doctor": str(doctor),
        "patient": str(patient),
    }


def get_patient_appointments(patient_id: int, user) -> Dict:
    qs = Appointment.objects.filter(patient_id=patient_id)
    company_id = getattr(user, "company_id", None)
    if company_id:
        qs = qs.filter(patient__company_id=company_id)

    data = [
        {
            "id": appt.id,
            "doctor": str(appt.doctor),
            "start_datetime": appt.start_datetime,
            "status": appt.status,
        }
        for appt in qs.order_by("-start_datetime")
    ]
    return {"appointments": data, "count": len(data)}


def process_action(action: Optional[str], action_data: Optional[Dict], user, session=None) -> Optional[Dict]:
    """Procesa acciones según el paso de la conversación."""

    if not action:
        return None

    action_data = action_data or {}

    if action == "show_initial_menu":
        return {
            "type": "menu",
            "options": [
                {"id": 1, "label": "Agendar cita para un paciente"},
                {"id": 2, "label": "Ver agenda de un médico"},
            ],
        }

    if action == "process_patient_cedula":
        cedula = action_data.get("cedula", "")
        patient = find_patient_by_cedula(cedula, user)
        if not patient:
            return {"type": "error", "message": f"No se encontró paciente con documento {cedula}"}
        if session:
            session.context_data["patient_id"] = patient["id"]
            session.context_data["patient_name"] = patient["name"]
            session.current_step = "selecting_doctor"
            session.save()
        # Retornar paciente encontrado con lista de médicos para que el flujo continúe
        doctors = get_doctors_list(user)
        return {
            "type": "patient_and_doctors",
            "patient": patient,
            "doctors": doctors,
        }

    if action == "show_doctors":
        doctors = get_doctors_list(user)
        if not doctors:
            return {"type": "error", "message": "No hay médicos disponibles"}
        return {
            "type": "doctors_list",
            "doctors": doctors,
        }

    if action == "select_doctor":
        doctor_id = action_data.get("doctor_id")
        if not doctor_id:
            return {"type": "error", "message": "doctor_id es requerido"}
        if session:
            session.context_data["doctor_id"] = doctor_id
            session.current_step = "selecting_date"
            session.save()
        # Retorna también la disponibilidad del médico seleccionado
        availability = get_doctor_availability_for_selection(doctor_id, user)
        if "error" in availability:
            return {"type": "availability", "data": availability}
        return {
            "type": "availability",
            "data": availability,
        }

    if action == "show_availability":
        doctor_id = action_data.get("doctor_id")
        if not doctor_id:
            return {"type": "error", "message": "doctor_id es requerido"}
        availability = get_doctor_availability_for_selection(doctor_id, user)
        if "error" in availability:
            return {"type": "error", "message": availability["error"]}
        return {
            "type": "availability",
            "data": availability,
        }

    if action == "create_appointment":
        doctor_id = action_data.get("doctor_id")
        schedule_id = action_data.get("schedule_id")
        patient_id = action_data.get("patient_id")

        # Intenta obtener del contexto si no vienen en los datos
        if session and session.context_data:
            doctor_id = doctor_id or session.context_data.get("doctor_id")
            patient_id = patient_id or session.context_data.get("patient_id")

        if not all([doctor_id, patient_id, schedule_id]):
            return {"type": "error", "message": "doctor_id, patient_id y schedule_id son requeridos"}

        result = create_appointment_from_action(
            {"doctor_id": doctor_id, "patient_id": patient_id, "schedule_id": schedule_id},
            user
        )

        if session:
            session.current_step = "completed"
            session.context_data.clear()
            session.save()

        return result

    if action == "view_doctor_availability":
        return {
            "type": "availability",
            "data": get_doctor_availability(
                action_data.get("doctor_id"),
                action_data.get("date"),
                user,
                action_data.get("doctor_name"),
            ),
        }

    if action == "view_patient_appointments":
        patient_id = action_data.get("patient_id")
        if not patient_id:
            return {"type": "error", "message": "patient_id es requerido"}
        return {
            "type": "appointments",
            "data": get_patient_appointments(patient_id, user),
        }

    return {"type": "error", "message": "Acción no reconocida"}

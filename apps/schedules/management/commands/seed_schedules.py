from datetime import date, time, timedelta

from apps.doctors.models import Doctor
from apps.schedules.models import Schedule
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed recurring schedules for a doctor"

    def add_arguments(self, parser):
        parser.add_argument("--doctor", type=int, required=True, help="Doctor ID")
        parser.add_argument("--days", type=int, default=30, help="How many days from today")
        parser.add_argument("--start", type=str, default="20:00", help="Start time HH:MM")
        parser.add_argument("--end", type=str, default="22:00", help="End time HH:MM")
        parser.add_argument("--slot", type=int, default=20, help="Slot minutes")
        parser.add_argument("--weekdays", action="store_true", help="Only Monday-Friday")

    def handle(self, *args, **options):
        doctor_id = options["doctor"]
        days = options["days"]
        start_h, start_m = map(int, options["start"].split(":"))
        end_h, end_m = map(int, options["end"].split(":"))
        slot = options["slot"]
        weekdays_only = options["weekdays"]

        doctor = Doctor.objects.get(pk=doctor_id)
        room = doctor.room

        start_date = date.today()
        created = 0
        for i in range(days):
            dt = start_date + timedelta(days=i)
            if weekdays_only and dt.weekday() >= 5:
                continue
            obj, ok = Schedule.objects.get_or_create(
                doctor=doctor,
                room=room,
                date=dt,
                start_time=time(start_h, start_m),
                end_time=time(end_h, end_m),
                defaults={"slot_minutes": slot, "is_available": True},
            )
            created += 1 if ok else 0

        self.stdout.write(self.style.SUCCESS(f"Schedules created: {created}"))

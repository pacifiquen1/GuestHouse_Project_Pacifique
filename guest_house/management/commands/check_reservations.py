from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from guest_house.models import Reservation

class Command(BaseCommand):
    help = "Send reminders after 2 minutes and cancel reservations after 5 minutes if unpaid."

    def handle(self, *args, **kwargs):
        now = timezone.now()

        # Step 1: Find reservations needing a reminder
        reminders = Reservation.objects.filter(
            status="pending",
            reminder_sent=False,
            created_at__lte=now - timedelta(minutes=2)
        )
        for res in reminders:
            self.stdout.write(
                f"[REMINDER] Reservation {res.id} for {res.guest.full_name} ({res.guest.phone})"
            )
            res.reminder_sent = True
            res.save()

        # Step 2: Find reservations to cancel
        expired = Reservation.objects.filter(
            status="pending",
            created_at__lte=now - timedelta(minutes=5)
        )
        for res in expired:
            res.status = "cancelled"
            res.save()
            self.stdout.write(
                f"[CANCELLED] Reservation {res.id} (no payment within 5 minutes)."
            )

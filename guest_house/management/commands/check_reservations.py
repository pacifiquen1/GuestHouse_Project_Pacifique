from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from guest_house.models import Reservation

from decouple import config
import africastalking
import os


class Command(BaseCommand):
    help = "Send SMS reminders after 2 minutes and cancel reservations 3 minutes later (5 minutes total) if unpaid."

    def handle(self, *args, **kwargs):
        now = timezone.now()

        # Initialize Africa's Talking
        username = config("AT_USERNAME", default="sandbox")
        api_key = config("AT_API_KEY")
        africastalking.initialize(username, api_key)
        sms = africastalking.SMS

        # Paths for log files
        reminder_log_file = os.path.join(os.getcwd(), "reminders_log.txt")
        cancellation_log_file = os.path.join(os.getcwd(), "cancellations_log.txt")

        def log_message(msg: str, log_file: str):
            """Helper to log messages in both console and log file."""
            self.stdout.write(msg)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{timezone.now()} - {msg}\n")

        def format_phone_for_sms(phone: str) -> str:
            """Convert 10-digit Rwandan phone numbers into E.164 format (+250)."""
            if phone.startswith("07") and len(phone) == 10:
                return "+250" + phone[1:]
            return phone  # Assume already in correct format

        # STEP 1: Send reminders after 2 minutes
        reminders = Reservation.objects.filter(
            status="pending",
            reminder_sent=False,
            created_at__lte=now - timedelta(minutes=2)
        )

        for res in reminders:
            text = f"⏰ Reminder: Your reservation {res.id} is still pending. Please make payment to confirm."
            recipient = format_phone_for_sms(res.guest.phone)

            try:
                response = sms.send(text, [recipient])
                log_message(
                    f"[REMINDER] Reservation {res.id} -> SMS sent to {recipient} | Response: {response}",
                    reminder_log_file
                )
                res.reminder_sent = True  # Only mark reminder if SMS actually sent
                res.save()
            except Exception as e:
                log_message(
                    f"[REMINDER] Reservation {res.id} -> Failed to send SMS: {e}",
                    reminder_log_file
                )

        # STEP 2: Cancel reservations after 5 minutes (3 minutes after reminder)
        expired = Reservation.objects.filter(
            status="pending",
            reminder_sent=True,  # Only cancel if reminder was sent
            created_at__lte=now - timedelta(minutes=5)
        )

        for res in expired:
            res.status = "cancelled"
            res.save()

            text = f"❌ Your reservation {res.id} has been cancelled due to no payment within the allowed time."
            recipient = format_phone_for_sms(res.guest.phone)

            try:
                response = sms.send(text, [recipient])
                log_message(
                    f"[CANCELLED] Reservation {res.id} -> SMS sent to {recipient} | Response: {response}",
                    cancellation_log_file
                )
            except Exception as e:
                log_message(
                    f"[CANCELLED] Reservation {res.id} -> Failed to send SMS: {e}",
                    cancellation_log_file
                )

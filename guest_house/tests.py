from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, timedelta
from .models import Guest, Room, DebitCard, Reservation, Transaction


class GuestHouseAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create a guest
        self.guest = Guest.objects.create(
            first_name="Alice",
            last_name="Doe",
            email="alice@example.com",
            phone="+250712345678"
        )

        # Create a room
        self.room = Room.objects.create(
            name="Room A",
            price_per_night=50.00,
            is_available=True
        )

        # Create a debit card
        self.card = DebitCard.objects.create(
            guest=self.guest,
            cardholder_name="Alice Doe",
            card_number="1234567812345678",
            balance=0.00,
            cvc="123",
            expiration_date="12/30",
            is_active=True
        )

    def test_deposit(self):
        """Test depositing funds into debit card"""
        deposit_amount = 100.00
        response = self.client.post("/api/deposits/", {
            "card_number": self.card.card_number,
            "amount": deposit_amount
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.card.refresh_from_db()
        self.assertEqual(float(self.card.balance), deposit_amount)

    def test_reservation_and_payment_flow(self):
        """Test making a reservation and paying for it"""
        # Deposit money
        deposit_amount = 100.00
        self.client.post("/api/deposits/", {
            "card_number": self.card.card_number,
            "amount": deposit_amount
        }, format="json")
        check_in = date.today()
        check_out = check_in + timedelta(days=2)

        # Create reservation
        response = self.client.post("/api/reservations/", {
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@example.com",
            "phone": "+250789012345",
            "room_id": self.room.id,
            "check_in_date": check_in,
            "check_out_date": check_out,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        reservation_id = response.json().get("reservation_id")
        self.assertIsNotNone(reservation_id)

        # Verify room is no longer available
        self.room.refresh_from_db()
        self.assertFalse(self.room.is_available)

        # Make payment
        self.client.post("/api/payments/", {
            "card_number": self.card.card_number,
            "cvc": self.card.cvc,
            "amount": 100.00,  # total_cost should be 50 * 2 = 100
            "reservation_id": reservation_id,
        }, format="json")

        # Verify transaction history and final balance
        self.card.refresh_from_db()
        self.assertEqual(float(self.card.balance), 0.00)

        reservation = Reservation.objects.get(id=reservation_id)
        self.assertEqual(reservation.status, "paid")

        # Verify transaction history
        transactions = Transaction.objects.all()
        self.assertEqual(transactions.count(), 2)

    def test_room_taken(self):
        """Test trying to reserve a room that is already taken"""
        # First, book the room to make it unavailable
        self.room.is_available = False
        self.room.save()
        check_in = date.today()
        check_out = check_in + timedelta(days=1)
        
        # Try to reserve the same room
        response = self.client.post("/api/reservations/", {
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@example.com",
            "phone": "+250789012345",
            "room_id": self.room.id,
            "check_in_date": check_in,
            "check_out_date": check_out,
        }, format="json")

        # Assert that the request fails with the correct error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This room is currently taken.", str(response.content))
        

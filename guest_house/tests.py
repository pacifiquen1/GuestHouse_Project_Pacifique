from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, timedelta
from .models import Guest, Room, DebitCard, Reservation


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
        reservation_id = response.json()["reservation_id"]
        total_cost = float(response.json()["total_cost"])

        # Pay for reservation
        response = self.client.post("/api/payments/", {
            "card_number": self.card.card_number,
            "cvc": self.card.cvc,
            "amount": total_cost,
            "reservation_id": reservation_id,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify reservation status updated
        reservation = Reservation.objects.get(id=reservation_id)
        self.assertEqual(reservation.status, "paid")

        # Verify card balance reduced correctly
        self.card.refresh_from_db()
        expected_balance = deposit_amount - total_cost
        self.assertEqual(float(self.card.balance), expected_balance)

    def test_transaction_history(self):
        """Test that deposits and payments appear in transaction history with correct amounts, order, and balance updates"""
        # Deposit money
        deposit_amount = 50.00
        self.client.post("/api/deposits/", {
            "card_number": self.card.card_number,
            "amount": deposit_amount
        }, format="json")

        # Create a reservation
        check_in = date.today()
        check_out = check_in + timedelta(days=1)
        reservation_cost = 50.00
        reservation = Reservation.objects.create(
            guest=self.guest,
            room=self.room,
            check_in_date=check_in,
            check_out_date=check_out,
            total_cost=reservation_cost,
            status="pending"
        )

        # Make payment
        self.client.post("/api/payments/", {
            "card_number": self.card.card_number,
            "cvc": self.card.cvc,
            "amount": reservation_cost,
            "reservation_id": reservation.id,
        }, format="json")

        # Check transaction history
        response = self.client.get("/api/transactions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        transactions = response.json()
        self.assertGreaterEqual(len(transactions), 2)

        # First should be deposit, then payment
        first_tx = transactions[0]
        second_tx = transactions[1]

        self.assertEqual(first_tx["transaction_type"], "deposit")
        self.assertEqual(float(first_tx["amount"]), deposit_amount)

        self.assertEqual(second_tx["transaction_type"], "payment")
        self.assertEqual(float(second_tx["amount"]), reservation_cost)

        # Verify final balance = deposit - payment
        self.card.refresh_from_db()
        expected_balance = deposit_amount - reservation_cost
        self.assertEqual(float(self.card.balance), expected_balance)

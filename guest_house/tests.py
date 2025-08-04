from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Room, Meal, Guest, Reservation, DebitCard, Transaction

class GuestModelTest(TestCase):
    def test_create_guest(self):
        guest = Guest.objects.create(name="John Doe", email="john.doe@example.com")
        self.assertEqual(guest.name, "John Doe")
        self.assertEqual(guest.email, "john.doe@example.com")
        self.assertTrue(isinstance(guest, Guest))
        self.assertEqual(str(guest), "John Doe")

class RoomModelTest(TestCase):
    def test_create_room(self):
        room = Room.objects.create(number='101', type='single', capacity=1, price_per_night=50.00)
        self.assertEqual(room.number, '101')
        self.assertEqual(room.type, 'single')
        self.assertEqual(room.capacity, 1)
        self.assertEqual(room.price_per_night, 50.00)
        self.assertTrue(room.is_available)
        self.assertEqual(str(room), "Room 101 (Single)")

class MealModelTest(TestCase):
    def test_create_meal(self):
        meal = Meal.objects.create(name="Dinner", price=25.00)
        self.assertEqual(meal.name, "Dinner")
        self.assertEqual(meal.price, 25.00)
        self.assertEqual(str(meal), "Dinner")

class DebitCardModelTest(TestCase):
    def test_create_debit_card(self):
        card = DebitCard.objects.create(card_number="1234567890123456", cardholder_name="Jane Doe", expiry_date="2026-12-31", cvv="789", balance=100.00)
        self.assertEqual(card.card_number, "1234567890123456")
        self.assertEqual(card.cardholder_name, "Jane Doe")
        self.assertEqual(str(card), "Card ending in 3456 (Jane Doe)")

class ReservationAPITests(APITestCase):
    def setUp(self):
        self.guest = Guest.objects.create(name="Test Guest", email="test@example.com")
        self.room_single = Room.objects.create(number="101", type="single", capacity=1, price_per_night=50.00, is_available=True)
        self.meal_breakfast = Meal.objects.create(name="Breakfast", price=10.00)

    def test_create_reservation_room_only(self):
        url = reverse('reservation-list')
        data = {
            'guest_name': 'New Guest',
            'guest_email': 'new.guest@example.com',
            'room_id': self.room_single.id,
            'check_in_date': '2025-04-28',
            'check_out_date': '2025-04-30'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), 1)
        reservation = Reservation.objects.get()
        self.assertEqual(reservation.room, self.room_single)
        self.assertEqual(reservation.guest.email, 'new.guest@example.com')
        self.assertEqual(reservation.total_cost, 100.00)
        self.assertFalse(Room.objects.get(id=self.room_single.id).is_available)

    def test_create_reservation_meal_only(self):
        url = reverse('reservation-list')
        data = {
            'guest_name': 'Another Guest',
            'guest_email': 'another.guest@example.com',
            'meal_id': self.meal_breakfast.id,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), 1)
        reservation = Reservation.objects.get()
        self.assertEqual(reservation.meal, self.meal_breakfast)
        self.assertEqual(reservation.guest.email, 'another.guest@example.com')
        self.assertEqual(reservation.total_cost, 10.00)
        self.assertIsNone(reservation.room)

    def test_get_reservation_list(self):
        Reservation.objects.create(guest=self.guest, room=self.room_single, check_in_date='2025-04-29', check_out_date='2025-04-30', total_cost=50.00)
        url = reverse('reservation-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

class PaymentAPITests(APITestCase):
    def setUp(self):
        self.guest = Guest.objects.create(name="Payment Guest", email="payment@example.com")
        self.room = Room.objects.create(number="201", type="double", capacity=2, price_per_night=100.00, is_available=True)
        self.reservation = Reservation.objects.create(guest=self.guest, room=self.room, check_in_date="2025-04-25", check_out_date="2025-04-27", total_cost=200.00)
        self.debit_card_sufficient = DebitCard.objects.create(card_number="1111222233334444", cardholder_name="Rich Guy", expiry_date="2026-12-31", cvv="111", balance=500.00)
        self.debit_card_insufficient = DebitCard.objects.create(card_number="5555666677778888", cardholder_name="Poor Guy", expiry_date="2026-12-31", cvv="222", balance=50.00)
        self.payment_url = reverse('process-payment')

    def test_successful_payment(self):
        data = {
            'reservation_id': self.reservation.id,
            'card_number': self.debit_card_sufficient.card_number,
            'expiry_date': '2026-12-31',
            'cvv': '111'
        }
        response = self.client.post(self.payment_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Reservation.objects.get(id=self.reservation.id).payment_status, 'paid')
        self.assertEqual(DebitCard.objects.get(id=self.debit_card_sufficient.id).balance, 300.00)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(Transaction.objects.get().status, 'success')
        self.assertEqual(Transaction.objects.get().transaction_type, 'withdrawal')
        self.assertEqual(float(Transaction.objects.get().amount), 200.00)

    def test_payment_insufficient_funds(self):
        data = {
            'reservation_id': self.reservation.id,
            'card_number': self.debit_card_insufficient.card_number,
            'expiry_date': '2026-12-31',
            'cvv': '222'
        }
        response = self.client.post(self.payment_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.get(id=self.reservation.id).payment_status, 'failed')
        self.assertEqual(DebitCard.objects.get(id=self.debit_card_insufficient.id).balance, 50.00)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(Transaction.objects.get().status, 'failed')
        self.assertEqual(Transaction.objects.get().transaction_type, 'withdrawal')
        self.assertEqual(float(Transaction.objects.get().amount), 200.00)

    def test_payment_invalid_card(self):
        data = {
            'reservation_id': self.reservation.id,
            'card_number': '9999999999999999',  # Non-existent card
            'expiry_date': '2027-01-01',
            'cvv': '333'
        }
        response = self.client.post(self.payment_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.get(id=self.reservation.id).payment_status, 'failed')
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(Transaction.objects.get().status, 'failed')
        self.assertIsNone(Transaction.objects.get().card)

    def test_payment_invalid_reservation(self):
        invalid_reservation_id = 999
        data = {
            'reservation_id': invalid_reservation_id,
            'card_number': self.debit_card_sufficient.card_number,
            'expiry_date': '2026-12-31',
            'cvv': '111'
        }
        response = self.client.post(self.payment_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Transaction.objects.count(), 0) # No transaction should be created

class TransactionAPITests(APITestCase):
    def setUp(self):
        self.guest = Guest.objects.create(name="Transaction Guest", email="transaction@example.com")
        self.room = Room.objects.create(number="401", type="single", capacity=1, price_per_night=60.00)
        self.reservation = Reservation.objects.create(guest=self.guest, room=self.room, check_in_date="2025-05-01", check_out_date="2025-05-02", total_cost=60.00, payment_status='paid')
        self.debit_card = DebitCard.objects.create(card_number="1234000056780000", cardholder_name="Bill Gates", expiry_date="2027-06-30", cvv="456", balance=1000.00)
        self.transaction = Transaction.objects.create(card=self.debit_card, reservation=self.reservation, amount=60.00, transaction_type='withdrawal', status='success')
        self.list_url = reverse('transaction-list')
        self.detail_url = reverse('transaction-detail', kwargs={'pk': self.transaction.id})

    def test_get_transaction_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['amount'], '60.00')

    def test_get_transaction_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['amount'], '60.00')
        self.assertEqual(response.data['transaction_type'], 'withdrawal')
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Room, Meal, Guest, Reservation, DebitCard, Transaction
from .serializers import (
    RoomSerializer, MealSerializer, GuestSerializer, DebitCardSerializer,
    TransactionSerializer, ReservationSerializer, ReservationCreateSerializer,
    PaymentSerializer, DepositSerializer
)

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

class MealViewSet(viewsets.ModelViewSet):
    queryset = Meal.objects.all()
    serializer_class = MealSerializer

class GuestViewSet(viewsets.ModelViewSet):
    queryset = Guest.objects.all()
    serializer_class = GuestSerializer

class DebitCardViewSet(viewsets.ModelViewSet):
    queryset = DebitCard.objects.all()
    serializer_class = DebitCardSerializer

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ReservationCreateSerializer
        return ReservationSerializer

    def create(self, request, *args, **kwargs):
        serializer = ReservationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        guest, _ = Guest.objects.get_or_create(
            email=data['guest_email'],
            defaults={'name': data['guest_name']}
        )

        # ✅ Use check_in_date and check_out_date from validated data
        reservation = Reservation(
            guest=guest,
            check_in_date=data['check_in_date'],
            check_out_date=data['check_out_date']
        )
        total_cost = 0

        if data.get('room_id'):
            try:
                with transaction.atomic():
                    room = Room.objects.select_for_update().get(pk=data['room_id'], is_available=True)
                    reservation.room = room
                    days = (data['check_out_date'] - data['check_in_date']).days
                    total_cost += room.price_per_night * days
                    room.is_available = False
                    room.save()
            except Room.DoesNotExist:
                return Response(
                    {"error": f"Room with ID {data['room_id']} is not available."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if data.get('meal_id'):
            try:
                meal = Meal.objects.get(pk=data['meal_id'])
                reservation.meal = meal
                total_cost += meal.price
            except Meal.DoesNotExist:
                return Response(
                    {"error": f"Meal with ID {data['meal_id']} does not exist."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if total_cost == 0:
            return Response(
                {"error": "Reservation must include at least a room or a meal."},
                status=status.HTTP_400_BAD_REQUEST
            )

        reservation.total_cost = total_cost
        reservation.save()

        payment_url = "/api/payments/"
        return Response({
            "message": "Reservation created. Redirecting to payment...",
            "payment_url": payment_url,
            "reservation_id": reservation.id,
            "total_cost": reservation.total_cost
        }, status=status.HTTP_201_CREATED)
    
class TransactionListView(generics.ListAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

class TransactionDetailView(generics.RetrieveAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

@api_view(['POST'])
def process_payment(request):
    serializer = PaymentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    card_number = data['card_number']
    cvc = data['cvc']
    amount = data['amount']
    reservation_id = data['reservation_id']

    try:
        debit_card = DebitCard.objects.get(card_number=card_number, cvc=cvc)
    except DebitCard.DoesNotExist:
        return Response({"error": "Invalid card number or CVC."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        reservation = Reservation.objects.get(id=reservation_id)
    except Reservation.DoesNotExist:
        return Response({"error": "Reservation not found."}, status=status.HTTP_404_NOT_FOUND)

    # 🔒 Prevent payment if reservation is already paid
    if reservation.status == 'paid':
        return Response({
            "error": "This reservation has already been paid."
        }, status=status.HTTP_400_BAD_REQUEST)

    if debit_card.balance < amount:
        return Response({"error": "Insufficient funds."}, status=status.HTTP_400_BAD_REQUEST)

    if amount != reservation.total_cost:
        return Response({
            "error": "Exact amount must be paid.",
            "expected_amount": float(reservation.total_cost),
            "provided_amount": float(amount)
        }, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        debit_card.balance -= amount
        debit_card.save()

        Transaction.objects.create(
            debit_card=debit_card,
            amount=-amount,
            transaction_type='payment',
            reservation=reservation
        )

        # Mark reservation as paid.
        reservation.status = 'paid'
        reservation.save()

    return Response({
        "message": f"Payment of {amount} successful.",
        "card_last_4": card_number[-4:]
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
def deposit_funds(request):
    serializer = DepositSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    card_number = data['card_number']
    amount = data['amount']

    try:
        debit_card = DebitCard.objects.get(card_number=card_number)
    except DebitCard.DoesNotExist:
        return Response({"error": "Invalid card number."}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        debit_card.balance += amount
        debit_card.save()
        Transaction.objects.create(
            debit_card=debit_card,
            amount=amount,
            transaction_type='deposit'
        )

    return Response({
        "message": f"Deposit of {amount} successful.",
        "card_last_4": card_number[-4:]
    }, status=status.HTTP_200_OK)
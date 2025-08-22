from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from django.db import transaction
from .models import Room, Meal, Guest, Reservation, DebitCard, Transaction
from .serializers import (
    RoomSerializer, MealSerializer, GuestSerializer, DebitCardSerializer,
    TransactionSerializer, ReservationSerializer, ReservationCreateSerializer,
    PaymentSerializer, DepositSerializer
)


# -----------------------------
# CRUD VIEWSETS
# -----------------------------
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


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for transactions"""
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


# -----------------------------
# RESERVATION
# -----------------------------
class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return ReservationCreateSerializer
        return ReservationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reservation = serializer.save()

        return Response({
            "message": "Reservation created. Redirecting to payment...",
            "payment_url": "/api/payments/",
            "reservation_id": reservation.id,
            "total_cost": reservation.total_cost
        }, status=status.HTTP_201_CREATED)


# -----------------------------
# PAYMENT
# -----------------------------
class PaymentViewSet(viewsets.ViewSet):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    serializer_class = PaymentSerializer

    def list(self, request):
        """Show info on how to use payment endpoint"""
        serializer = self.get_serializer()
        return Response({
            "message": "Payment endpoint - POST JSON to process payments",
            "required_fields": list(serializer.fields.keys()),
            "method": "POST",
            "form": serializer.data if hasattr(serializer, 'data') else {}
        })

    def get_serializer(self, *args, **kwargs):
        kwargs.setdefault('context', self.get_serializer_context())
        return self.serializer_class(*args, **kwargs)

    def get_serializer_context(self):
        return {
            'request': getattr(self, 'request', None),
            'format': getattr(self, 'format_kwarg', None),
            'view': self
        }

    def create(self, request):
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Payment processed successfully."}, status=status.HTTP_200_OK)


# -----------------------------
# DEPOSIT
# -----------------------------
class DepositViewSet(viewsets.ViewSet):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    serializer_class = DepositSerializer

    def list(self, request):
        """Show info on how to use deposit endpoint"""
        serializer = self.get_serializer()
        return Response({
            "message": "Deposit endpoint - POST JSON to deposit funds",
            "required_fields": list(serializer.fields.keys()),
            "method": "POST",
            "form": serializer.data if hasattr(serializer, 'data') else {}
        })

    def get_serializer(self, *args, **kwargs):
        kwargs.setdefault('context', self.get_serializer_context())
        return self.serializer_class(*args, **kwargs)

    def get_serializer_context(self):
        return {
            'request': getattr(self, 'request', None),
            'format': getattr(self, 'format_kwarg', None),
            'view': self
        }

    def create(self, request):
        serializer = DepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        card_number = serializer.validated_data['card_number']
        amount = serializer.validated_data['amount']

        try:
            debit_card = DebitCard.objects.get(card_number=card_number, is_active=True)
        except DebitCard.DoesNotExist:
            return Response({"error": "Invalid or inactive card number."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            debit_card.balance += amount
            debit_card.save()
            txn = Transaction.objects.create(
                debit_card=debit_card,
                amount=amount,
                transaction_type='deposit'
            )

        return Response({
            "message": f"Successfully deposited {amount} to card ending in {debit_card.card_number[-4:]}.",
            "new_balance": debit_card.balance,
            "transaction_id": txn.id
        }, status=status.HTTP_200_OK)

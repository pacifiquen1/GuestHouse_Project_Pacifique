from rest_framework import serializers
from django.core.validators import RegexValidator
from django.db import transaction
from .models import Room, Meal, Guest, Reservation, DebitCard, Transaction


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'


class MealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meal
        fields = '__all__'


class GuestSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(
        max_length=13,
        validators=[
            RegexValidator(
                regex=r'^(?:\+2507\d{8}|07\d{8})$',
                message="Phone must be in format '07XXXXXXXX' or '+2507XXXXXXXX'."
            )
        ]
    )

    class Meta:
        model = Guest
        fields = ['id', 'first_name', 'last_name', 'email', 'phone']

    def validate_phone(self, value):
        """Always normalize to +250 format"""
        if value.startswith("07") and len(value) == 10:
            return "+250" + value[1:]
        elif value.startswith("+250") and len(value) == 13:
            return value
        raise serializers.ValidationError("Invalid phone number format.")


class DebitCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebitCard
        fields = '__all__'
        extra_kwargs = {
            'card_number': {'write_only': True},
            'cvc': {'write_only': True}
        }


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('timestamp',)


class ReservationSerializer(serializers.ModelSerializer):
    guest = GuestSerializer(read_only=True)

    class Meta:
        model = Reservation
        fields = '__all__'
        read_only_fields = ('total_cost', 'status')  # ✅ system-controlled


class ReservationCreateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    email = serializers.EmailField()
    phone = serializers.CharField(
        max_length=13,
        validators=[
            RegexValidator(
                regex=r'^(?:\+2507\d{8}|07\d{8})$',
                message="Phone must be in format '07XXXXXXXX' or '+2507XXXXXXXX'."
            )
        ]
    )
    room_id = serializers.IntegerField(required=False)
    meal_id = serializers.IntegerField(required=False)
    check_in_date = serializers.DateField()
    check_out_date = serializers.DateField()

    def validate(self, attrs):
        if not attrs.get('room_id') and not attrs.get('meal_id'):
            raise serializers.ValidationError("At least a room or a meal must be selected.")

        if attrs['check_out_date'] <= attrs['check_in_date']:
            raise serializers.ValidationError("Check-out date must be after check-in date.")

        phone = attrs['phone']
        if phone.startswith("07") and len(phone) == 10:
            attrs['phone'] = "+250" + phone[1:]
        elif not (phone.startswith("+250") and len(phone) == 13):
            raise serializers.ValidationError({"phone": "Invalid phone number format."})

        return attrs

    def create(self, validated_data):
        guest, _ = Guest.objects.get_or_create(
            email=validated_data['email'],
            defaults={
                'first_name': validated_data['first_name'],
                'last_name': validated_data['last_name'],
                'phone': validated_data['phone']
            }
        )

        reservation = Reservation(
            guest=guest,
            check_in_date=validated_data['check_in_date'],
            check_out_date=validated_data['check_out_date']
        )

        total_cost = 0

        if validated_data.get("room_id"):
            with transaction.atomic():
                room = Room.objects.select_for_update().get(
                    pk=validated_data["room_id"], is_available=True
                )
                reservation.room = room
                days = (validated_data["check_out_date"] - validated_data["check_in_date"]).days
                total_cost += room.price_per_night * days
                room.is_available = False
                room.save()

        if validated_data.get("meal_id"):
            meal = Meal.objects.get(pk=validated_data["meal_id"])
            reservation.meal = meal
            total_cost += meal.price

        reservation.total_cost = total_cost
        reservation.save()
        return reservation


class PaymentSerializer(serializers.Serializer):
    card_number = serializers.CharField(max_length=20)
    cvc = serializers.CharField(max_length=4)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    reservation_id = serializers.IntegerField()

    def validate(self, attrs):
        try:
            card = DebitCard.objects.get(
                card_number=attrs['card_number'], cvc=attrs['cvc'], is_active=True
            )
        except DebitCard.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive card details.")

        if card.balance < attrs['amount']:
            raise serializers.ValidationError("Insufficient balance.")

        try:
            reservation = Reservation.objects.get(
                id=attrs['reservation_id'], status="pending"
            )
        except Reservation.DoesNotExist:
            raise serializers.ValidationError("Reservation not found or already processed.")

        attrs['card'] = card
        attrs['reservation'] = reservation
        return attrs

    def create(self, validated_data):
        card = validated_data['card']
        reservation = validated_data['reservation']
        amount = validated_data['amount']

        with transaction.atomic():
            card.balance -= amount
            card.save()

            reservation.status = "paid"
            reservation.save()

            txn = Transaction.objects.create(
                debit_card=card,
                amount=amount,
                transaction_type='payment',
                reservation=reservation
            )

        return txn


class DepositSerializer(serializers.Serializer):
    card_number = serializers.CharField(max_length=20)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

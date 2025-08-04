from rest_framework import serializers
from .models import Room, Meal, Guest, Reservation, DebitCard, Transaction
from django.core.validators import RegexValidator

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
        max_length=10,
        min_length=10,
        validators=[
            RegexValidator(
                regex='^[0-9]{10}$',
                message='Phone number must be exactly 10 digits (numbers only)'
            )
        ]
    )

    class Meta:
        model = Guest
        fields = ['id', 'first_name', 'last_name', 'email', 'phone']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }

    def validate_phone(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits.")
        return value

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

class ReservationCreateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    email = serializers.EmailField()
    phone = serializers.CharField(
        max_length=10,
        min_length=10,
        validators=[
            RegexValidator(
                regex='^[0-9]{10}$',
                message='Phone number must be exactly 10 digits'
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

        if not attrs['phone'].isdigit():
            raise serializers.ValidationError({"phone": "Must contain only digits"})

        return attrs

class PaymentSerializer(serializers.Serializer):
    card_number = serializers.CharField(max_length=20)
    cvc = serializers.CharField(max_length=4)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    reservation_id = serializers.IntegerField()

class DepositSerializer(serializers.Serializer):
    card_number = serializers.CharField(max_length=20)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)